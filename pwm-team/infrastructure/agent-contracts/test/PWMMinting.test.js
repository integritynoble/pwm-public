const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));
const DAY = 24 * 3600;

describe("PWMMinting", function () {
  let minting, reward, treasury, staking, gov, cert, funder, outsider;

  beforeEach(async () => {
    [gov, cert, funder, outsider] = await ethers.getSigners();

    const T = await ethers.getContractFactory("PWMTreasury");
    treasury = await T.deploy(gov.address);
    const R = await ethers.getContractFactory("PWMReward");
    reward = await R.deploy(gov.address);
    const S = await ethers.getContractFactory("PWMStaking");
    staking = await S.deploy(gov.address);
    const M = await ethers.getContractFactory("PWMMinting");
    minting = await M.deploy(gov.address);
    await Promise.all([
      treasury.waitForDeployment(), reward.waitForDeployment(),
      staking.waitForDeployment(), minting.waitForDeployment(),
    ]);

    await reward.connect(gov).setCertificate(cert.address);
    await reward.connect(gov).setMinting(await minting.getAddress());
    await reward.connect(gov).setStaking(await staking.getAddress());
    await reward.connect(gov).setTreasury(await treasury.getAddress());
    await treasury.connect(gov).setReward(await reward.getAddress());
    await minting.connect(gov).setCertificate(cert.address);
    await minting.connect(gov).setReward(await reward.getAddress());
    // Small emission rate so Hardhat starting balances (10k ETH) can fund it.
    // Default 100 bps of 17.22M ≈ 172k PWM — too large for tests.
    await minting.connect(gov).setEpochEmissionBps(1); // 0.01% of remaining
  });

  async function promote(id, delta, benchmarkHash) {
    await minting.connect(gov).setPrincipleBenchmark(id, benchmarkHash);
    await minting.connect(gov).setDelta(id, delta);
    await minting.connect(gov).setPromotion(id, true);
  }

  it("M_POOL constant is 17.22M * 1e18", async () => {
    expect(await minting.M_POOL()).to.equal(17_220_000n * 10n ** 18n);
  });

  it("promotion requires delta + benchmark to be set first", async () => {
    await expect(minting.connect(gov).setPromotion(1, true))
      .to.be.revertedWith("PWMMinting: benchmark unset");
    await minting.connect(gov).setPrincipleBenchmark(1, H("b1"));
    await expect(minting.connect(gov).setPromotion(1, true))
      .to.be.revertedWith("PWMMinting: delta unset");
    await minting.connect(gov).setDelta(1, 2);
    await minting.connect(gov).setPromotion(1, true);
    expect(await minting.promotedCount()).to.equal(1);
    await minting.connect(gov).setPromotion(1, false);
    expect(await minting.promotedCount()).to.equal(0);
  });

  it("weightOf: promoted → δ × max(activity,1); unpromoted → 0", async () => {
    expect(await minting.weightOf(1)).to.equal(0);
    await promote(1, 3, H("b1"));
    expect(await minting.weightOf(1)).to.equal(3);
    await minting.connect(cert).updateActivity(1, H("b1"), 5);
    expect(await minting.weightOf(1)).to.equal(15);
  });

  it("updateActivity only callable by PWMCertificate", async () => {
    await expect(minting.connect(outsider).updateActivity(1, H("b1"), 1))
      .to.be.revertedWith("PWMMinting: not certificate");
  });

  it("epochEmit: emits to single principle, reduces remaining, M_emitted tracks", async () => {
    await promote(1, 1, H("b1"));
    // budget at 1 bps of 17.22M = 1722 PWM — fund 2000 PWM
    await funder.sendTransaction({ to: await minting.getAddress(), value: ethers.parseEther("2000") });

    await expect(minting.epochEmit())
      .to.emit(minting, "EpochEmitted")
      .and.to.emit(reward, "PoolSeeded");

    const rem = await minting.remaining();
    const emitted = (await minting.M_POOL()) - rem;
    expect(await minting.M_emitted()).to.equal(emitted);
    expect(emitted).to.be.gt(0n);
    // 1 bps of 17_220_000 PWM = 1722 PWM
    expect(emitted).to.equal(ethers.parseEther("1722"));
    expect(await reward.poolOf(H("b1"))).to.equal(emitted);
  });

  it("epochEmit: reverts if contract balance < budget", async () => {
    await promote(1, 1, H("b1"));
    // Contract unfunded: budget = 1722 PWM > 0 balance → underfunded
    await expect(minting.epochEmit()).to.be.revertedWith("PWMMinting: underfunded");
  });

  it("epochEmit: cooldown enforced between epochs", async () => {
    await promote(1, 1, H("b1"));
    await funder.sendTransaction({ to: await minting.getAddress(), value: ethers.parseEther("5000") });
    await minting.epochEmit();
    await expect(minting.epochEmit()).to.be.revertedWith("PWMMinting: cooldown active");
    await time.increase(DAY);
    await minting.epochEmit();
  });

  it("epochEmit: share proportional to weight across promoted principles", async () => {
    await promote(1, 1, H("b1"));
    await promote(2, 2, H("b2"));
    await promote(3, 3, H("b3"));
    // budget = 1722 PWM, split 1/6 : 2/6 : 3/6 → 287 : 574 : 861 (approximately)
    await funder.sendTransaction({ to: await minting.getAddress(), value: ethers.parseEther("2000") });
    await minting.epochEmit();

    const p1 = await reward.poolOf(H("b1"));
    const p2 = await reward.poolOf(H("b2"));
    const p3 = await reward.poolOf(H("b3"));
    expect(p2).to.be.closeTo(p1 * 2n, 10n);
    expect(p3).to.be.closeTo(p1 * 3n, 10n);
  });

  it("epochEmit: reverts if no promoted principles", async () => {
    await funder.sendTransaction({ to: await minting.getAddress(), value: ethers.parseEther("10") });
    await expect(minting.epochEmit())
      .to.be.revertedWith("PWMMinting: no promoted principles");
  });

  it("setEpochEmissionBps: bounds and governance-gated", async () => {
    await expect(minting.connect(gov).setEpochEmissionBps(0))
      .to.be.revertedWith("PWMMinting: bps out of range");
    await expect(minting.connect(gov).setEpochEmissionBps(10_001))
      .to.be.revertedWith("PWMMinting: bps out of range");
    await expect(minting.connect(outsider).setEpochEmissionBps(50))
      .to.be.revertedWith("PWMMinting: not governance");
  });
});
