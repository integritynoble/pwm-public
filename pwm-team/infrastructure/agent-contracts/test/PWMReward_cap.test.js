const { expect } = require("chai");
const { ethers } = require("hardhat");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));

/**
 * Tests for the pre-mainnet TVL cap `maxBenchmarkPoolWei` on PWMReward.
 * See contracts/PWMReward.sol and AUDIT_FREE_PATH.md Track D.
 */
describe("PWMReward — maxBenchmarkPoolWei cap", function () {
  let reward, treasury, gov, cert, staker, minter, outsider, bountyPayer;

  beforeEach(async () => {
    [gov, cert, staker, minter, outsider, bountyPayer] = await ethers.getSigners();

    const T = await ethers.getContractFactory("PWMTreasury");
    treasury = await T.deploy(gov.address);
    await treasury.waitForDeployment();

    const R = await ethers.getContractFactory("PWMReward");
    reward = await R.deploy(gov.address);
    await reward.waitForDeployment();

    await reward.connect(gov).setCertificate(cert.address);
    await reward.connect(gov).setMinting(minter.address);
    await reward.connect(gov).setStaking(staker.address);
    await reward.connect(gov).setTreasury(await treasury.getAddress());
  });

  it("cap defaults to zero (unlimited) — existing behavior preserved", async () => {
    expect(await reward.maxBenchmarkPoolWei()).to.equal(0n);
    const bh = H("b1");
    // Large deposit with cap=0 should succeed.
    const big = ethers.parseEther("1000000");
    await expect(reward.connect(minter).depositMinting(bh, { value: big }))
      .to.emit(reward, "PoolSeeded");
    expect(await reward.pool(bh)).to.equal(big);
  });

  it("only governance can setMaxBenchmarkPoolWei", async () => {
    await expect(reward.connect(outsider).setMaxBenchmarkPoolWei(100n))
      .to.be.revertedWith("PWMReward: not governance");
    await expect(reward.connect(gov).setMaxBenchmarkPoolWei(100n))
      .to.emit(reward, "MaxBenchmarkPoolWeiUpdated").withArgs(100n);
    expect(await reward.maxBenchmarkPoolWei()).to.equal(100n);
  });

  it("blocks seedBPool inflow that would exceed the cap", async () => {
    const bh = H("b2");
    const cap = ethers.parseEther("10");
    await reward.connect(gov).setMaxBenchmarkPoolWei(cap);

    // First: seed half of the cap, OK.
    await reward.connect(staker).seedBPool(bh, { value: ethers.parseEther("4") });
    // Second: add 5 more → total 9, still <= cap 10, OK.
    await reward.connect(staker).seedBPool(bh, { value: ethers.parseEther("5") });
    // Third: add 2 more → total 11, exceeds cap 10, revert.
    await expect(
      reward.connect(staker).seedBPool(bh, { value: ethers.parseEther("2") })
    ).to.be.revertedWith("PWMReward: pool cap exceeded");
    expect(await reward.pool(bh)).to.equal(ethers.parseEther("9"));
  });

  it("blocks depositMinting inflow that would exceed the cap", async () => {
    const bh = H("b3");
    await reward.connect(gov).setMaxBenchmarkPoolWei(ethers.parseEther("3"));
    await reward.connect(minter).depositMinting(bh, { value: ethers.parseEther("3") });
    // Any additional wei is over the cap.
    await expect(
      reward.connect(minter).depositMinting(bh, { value: 1n })
    ).to.be.revertedWith("PWMReward: pool cap exceeded");
  });

  it("blocks depositBounty inflow that would exceed the cap", async () => {
    const bh = H("b4");
    await reward.connect(gov).setMaxBenchmarkPoolWei(ethers.parseEther("1"));
    await expect(
      reward.connect(bountyPayer).depositBounty(bh, { value: ethers.parseEther("1.5") })
    ).to.be.revertedWith("PWMReward: pool cap exceeded");
  });

  it("cap applies per-benchmark — different pools cap independently", async () => {
    const bh1 = H("bench-a");
    const bh2 = H("bench-b");
    await reward.connect(gov).setMaxBenchmarkPoolWei(ethers.parseEther("2"));
    await reward.connect(staker).seedBPool(bh1, { value: ethers.parseEther("2") });
    // bh1 is at cap; bh2 is still at 0 — can accept up to cap.
    await reward.connect(staker).seedBPool(bh2, { value: ethers.parseEther("2") });
    expect(await reward.pool(bh1)).to.equal(ethers.parseEther("2"));
    expect(await reward.pool(bh2)).to.equal(ethers.parseEther("2"));
  });

  it("raising the cap allows further inflows; lowering it does NOT refund", async () => {
    const bh = H("b5");
    await reward.connect(gov).setMaxBenchmarkPoolWei(ethers.parseEther("5"));
    await reward.connect(staker).seedBPool(bh, { value: ethers.parseEther("5") });
    // Raise cap.
    await reward.connect(gov).setMaxBenchmarkPoolWei(ethers.parseEther("10"));
    await reward.connect(staker).seedBPool(bh, { value: ethers.parseEther("5") });
    expect(await reward.pool(bh)).to.equal(ethers.parseEther("10"));
    // Lower cap below current pool.
    await reward.connect(gov).setMaxBenchmarkPoolWei(ethers.parseEther("1"));
    // Pool balance is preserved (not forcibly refunded).
    expect(await reward.pool(bh)).to.equal(ethers.parseEther("10"));
    // Further inflows are blocked.
    await expect(
      reward.connect(staker).seedBPool(bh, { value: 1n })
    ).to.be.revertedWith("PWMReward: pool cap exceeded");
  });

  it("cap of zero reverts to unlimited", async () => {
    const bh = H("b6");
    await reward.connect(gov).setMaxBenchmarkPoolWei(ethers.parseEther("1"));
    await reward.connect(staker).seedBPool(bh, { value: ethers.parseEther("1") });
    await expect(
      reward.connect(staker).seedBPool(bh, { value: 1n })
    ).to.be.revertedWith("PWMReward: pool cap exceeded");
    // Disable the cap.
    await reward.connect(gov).setMaxBenchmarkPoolWei(0n);
    // Now unlimited inflows work.
    await reward.connect(staker).seedBPool(bh, { value: ethers.parseEther("100") });
    expect(await reward.pool(bh)).to.equal(ethers.parseEther("101"));
  });
});
