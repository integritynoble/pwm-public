const { expect } = require("chai");
const { ethers } = require("hardhat");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));
const bps = 10_000n;

// Helpers
const split = (draw, pBps) => {
  const d = BigInt(draw);
  const ac = (d * BigInt(pBps) * 5500n) / (bps * bps);
  const cp = (d * (bps - BigInt(pBps)) * 5500n) / (bps * bps);
  const l3 = (d * 1500n) / bps;
  const l2 = (d * 1000n) / bps;
  const l1 = (d * 500n) / bps;
  const tk = d - ac - cp - l3 - l2 - l1;
  return { ac, cp, l3, l2, l1, tk };
};

describe("PWMReward", function () {
  let reward, treasury, gov, cert, staker, minter;
  let ac, cp, l1c, l2c, l3c, outsider;

  beforeEach(async () => {
    [gov, cert, staker, minter, ac, cp, l1c, l2c, l3c, outsider] = await ethers.getSigners();

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
    await treasury.connect(gov).setReward(await reward.getAddress());
  });

  it("rankBps matches spec", async () => {
    expect(await reward.rankBps(1)).to.equal(4000);
    expect(await reward.rankBps(2)).to.equal(500);
    expect(await reward.rankBps(3)).to.equal(200);
    for (let r = 4; r <= 10; r++) expect(await reward.rankBps(r)).to.equal(100);
    expect(await reward.rankBps(11)).to.equal(0);
    expect(await reward.rankBps(255)).to.equal(0);
  });

  it("pool seeding gated: seedBPool only staking, depositMinting only minting; bounty open", async () => {
    const bh = H("benchmark");
    await expect(reward.connect(outsider).seedBPool(bh, { value: 1n }))
      .to.be.revertedWith("PWMReward: not staking");
    await expect(reward.connect(outsider).depositMinting(bh, { value: 1n }))
      .to.be.revertedWith("PWMReward: not minting");

    await expect(reward.connect(staker).seedBPool(bh, { value: ethers.parseEther("1") }))
      .to.emit(reward, "PoolSeeded");
    await expect(reward.connect(minter).depositMinting(bh, { value: ethers.parseEther("2") }))
      .to.emit(reward, "PoolSeeded");
    await expect(reward.connect(outsider).depositBounty(bh, { value: ethers.parseEther("3") }))
      .to.emit(reward, "PoolSeeded");

    expect(await reward.poolOf(bh)).to.equal(ethers.parseEther("6"));
  });

  it("distribute: rank 1 draws 40%, splits across 6 buckets, buckets sum to D", async () => {
    const bh = H("bm1");
    const total = ethers.parseEther("100");
    await reward.connect(minter).depositMinting(bh, { value: total });

    // Pre-fund all recipients with 0 (default) — we'll check delta.
    const beforeAC = await ethers.provider.getBalance(ac.address);
    const beforeCP = await ethers.provider.getBalance(cp.address);
    const beforeL1 = await ethers.provider.getBalance(l1c.address);
    const beforeL2 = await ethers.provider.getBalance(l2c.address);
    const beforeL3 = await ethers.provider.getBalance(l3c.address);

    const d = {
      benchmarkHash: bh,
      principleId: 42,
      l1Creator: l1c.address,
      l2Creator: l2c.address,
      l3Creator: l3c.address,
      acWallet:  ac.address,
      cpWallet:  cp.address,
      shareRatioP: 6000, // 60/40 AC/CP of the 55% slice
      rank: 1,
    };
    const certHash = H("cert1");
    await expect(reward.connect(cert).distribute(certHash, d))
      .to.emit(reward, "DrawSettled");

    const drawAmt = (total * 4000n) / 10000n; // 40 PWM
    const exp = split(drawAmt, 6000);

    expect((await ethers.provider.getBalance(ac.address)) - beforeAC).to.equal(exp.ac);
    expect((await ethers.provider.getBalance(cp.address)) - beforeCP).to.equal(exp.cp);
    expect((await ethers.provider.getBalance(l1c.address)) - beforeL1).to.equal(exp.l1);
    expect((await ethers.provider.getBalance(l2c.address)) - beforeL2).to.equal(exp.l2);
    expect((await ethers.provider.getBalance(l3c.address)) - beforeL3).to.equal(exp.l3);
    expect(await treasury.balanceOf(42)).to.equal(exp.tk);

    // pool reduces by drawAmt
    expect(await reward.poolOf(bh)).to.equal(total - drawAmt);

    // sum equals D
    expect(exp.ac + exp.cp + exp.l1 + exp.l2 + exp.l3 + exp.tk).to.equal(drawAmt);
  });

  it("distribute: rank 11+ is a pure rollover (pool untouched, no payments)", async () => {
    const bh = H("bm2");
    const total = ethers.parseEther("50");
    await reward.connect(minter).depositMinting(bh, { value: total });
    const d = {
      benchmarkHash: bh, principleId: 1,
      l1Creator: l1c.address, l2Creator: l2c.address, l3Creator: l3c.address,
      acWallet: ac.address, cpWallet: cp.address, shareRatioP: 5000, rank: 11,
    };
    await reward.connect(cert).distribute(H("cert-rollover"), d);
    expect(await reward.poolOf(bh)).to.equal(total);
    expect(await treasury.balanceOf(1)).to.equal(0);
  });

  it("distribute: rank 2 then rank 3 reduce pool cumulatively", async () => {
    const bh = H("bm3");
    const total = ethers.parseEther("100");
    await reward.connect(minter).depositMinting(bh, { value: total });

    const dBase = {
      benchmarkHash: bh, principleId: 7,
      l1Creator: l1c.address, l2Creator: l2c.address, l3Creator: l3c.address,
      acWallet: ac.address, cpWallet: cp.address, shareRatioP: 5000,
    };
    await reward.connect(cert).distribute(H("c-r2"), { ...dBase, rank: 2 });
    const after2 = total - (total * 500n) / 10000n; // 5% off 100 = 95
    expect(await reward.poolOf(bh)).to.equal(after2);
    await reward.connect(cert).distribute(H("c-r3"), { ...dBase, rank: 3 });
    const after3 = after2 - (after2 * 200n) / 10000n;
    expect(await reward.poolOf(bh)).to.equal(after3);
  });

  it("distribute: access control, replay, bad inputs", async () => {
    const bh = H("bm4");
    await reward.connect(minter).depositMinting(bh, { value: ethers.parseEther("10") });
    const d = {
      benchmarkHash: bh, principleId: 1,
      l1Creator: l1c.address, l2Creator: l2c.address, l3Creator: l3c.address,
      acWallet: ac.address, cpWallet: cp.address, shareRatioP: 5000, rank: 1,
    };
    await expect(reward.connect(outsider).distribute(H("x"), d))
      .to.be.revertedWith("PWMReward: not certificate");

    await reward.connect(cert).distribute(H("dup"), d);
    await expect(reward.connect(cert).distribute(H("dup"), d))
      .to.be.revertedWith("PWMReward: already settled");

    await expect(reward.connect(cert).distribute(H("low-p"), { ...d, shareRatioP: 999 }))
      .to.be.revertedWith("PWMReward: p out of range");
    await expect(reward.connect(cert).distribute(H("high-p"), { ...d, shareRatioP: 9001 }))
      .to.be.revertedWith("PWMReward: p out of range");
  });

  it("distribute: drawAmt rounds to 0 (balance*rbps < BPS_DENOM) — emits zero-draw, pool intact", async () => {
    // rank 4 → rbps=100 → drawAmt = balance*100/10000 = balance/100.
    // For balance = 50 wei, drawAmt = 0; pool stays at 50.
    const bh = H("tiny-pool");
    await reward.connect(minter).depositMinting(bh, { value: 50n });
    const d = {
      benchmarkHash: bh, principleId: 1,
      l1Creator: l1c.address, l2Creator: l2c.address, l3Creator: l3c.address,
      acWallet: ac.address, cpWallet: cp.address, shareRatioP: 5000, rank: 4,
    };
    await expect(reward.connect(cert).distribute(H("cert-zero-draw"), d))
      .to.emit(reward, "DrawSettled").withArgs(H("cert-zero-draw"), bh, 4, 0n, 50n);
    expect(await reward.poolOf(bh)).to.equal(50n);
  });

  it("setGovernance: rejects zero, rejects non-governance, transfers cleanly", async () => {
    await expect(reward.connect(gov).setGovernance(ethers.ZeroAddress))
      .to.be.revertedWith("PWMReward: zero governance");
    await expect(reward.connect(outsider).setGovernance(outsider.address))
      .to.be.revertedWith("PWMReward: not governance");
    await expect(reward.connect(gov).setGovernance(outsider.address))
      .to.emit(reward, "GovernanceUpdated").withArgs(outsider.address);
    expect(await reward.governance()).to.equal(outsider.address);
  });

  it("setCertificate / setMinting / setStaking / setTreasury: zero rejected; non-governance rejected", async () => {
    for (const fn of ["setCertificate", "setMinting", "setStaking", "setTreasury"]) {
      await expect(reward.connect(gov)[fn](ethers.ZeroAddress))
        .to.be.reverted;
      await expect(reward.connect(outsider)[fn](outsider.address))
        .to.be.revertedWith("PWMReward: not governance");
    }
  });

  it("constructor rejects zero governance", async () => {
    const R = await ethers.getContractFactory("PWMReward");
    await expect(R.deploy(ethers.ZeroAddress))
      .to.be.revertedWith("PWMReward: zero governance");
  });

  it("seedBPool / depositMinting / depositBounty: revert on zero / unset deps", async () => {
    const bh = H("zero-tests");
    // seedBPool requires non-zero msg.value
    await expect(reward.connect(staker).seedBPool(bh, { value: 0n }))
      .to.be.reverted;
    // depositMinting requires onlyMinting (here minter set to gov.address as placeholder
    // — outsider call should revert)
    await expect(reward.connect(outsider).depositMinting(bh, { value: 1n }))
      .to.be.reverted;
  });
});
