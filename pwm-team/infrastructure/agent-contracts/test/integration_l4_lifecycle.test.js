const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));
const ZERO = ethers.ZeroHash;
const DAY = 24 * 3600;

describe("Integration — full L4 lifecycle", function () {
  it("register → stake → submit cert → wait → finalize → verify payouts", async function () {
    const [gov, sp, cp, l1c, l2c, l3c, challenger, funder] = await ethers.getSigners();

    const Registry   = await ethers.getContractFactory("PWMRegistry");
    const Governance = await ethers.getContractFactory("PWMGovernance");
    const Treasury   = await ethers.getContractFactory("PWMTreasury");
    const Staking    = await ethers.getContractFactory("PWMStaking");
    const Reward     = await ethers.getContractFactory("PWMReward");
    const Certificate = await ethers.getContractFactory("PWMCertificate");
    const Minting    = await ethers.getContractFactory("PWMMinting");

    const registry = await Registry.deploy();
    const governance = await Governance.deploy([
      gov.address, sp.address, cp.address, l1c.address, l2c.address,
    ]);
    const treasury = await Treasury.deploy(gov.address);
    const staking  = await Staking.deploy(gov.address);
    const reward   = await Reward.deploy(gov.address);
    const certificate = await Certificate.deploy(gov.address);
    const minting  = await Minting.deploy(gov.address);
    await Promise.all([
      registry.waitForDeployment(), governance.waitForDeployment(),
      treasury.waitForDeployment(), staking.waitForDeployment(),
      reward.waitForDeployment(), certificate.waitForDeployment(),
      minting.waitForDeployment(),
    ]);

    // Wire cross-contract addresses (gov is the admin for M1.1)
    await reward.connect(gov).setCertificate(await certificate.getAddress());
    await reward.connect(gov).setStaking(await staking.getAddress());
    await reward.connect(gov).setMinting(await minting.getAddress());
    await reward.connect(gov).setTreasury(await treasury.getAddress());
    await treasury.connect(gov).setReward(await reward.getAddress());
    await staking.connect(gov).setReward(await reward.getAddress());
    await certificate.connect(gov).setRegistry(await registry.getAddress());
    await certificate.connect(gov).setReward(await reward.getAddress());
    await minting.connect(gov).setCertificate(await certificate.getAddress());
    await minting.connect(gov).setReward(await reward.getAddress());

    // 1. Register L1/L2/L3
    const pHash = H("principle:integration");
    const sHash = H("spec:integration");
    const bHash = H("benchmark:integration");
    await registry.register(pHash, ZERO, 1, l1c.address);
    await registry.register(sHash, pHash, 2, l2c.address);
    await registry.register(bHash, sHash, 3, l3c.address);

    // 2. Stake L2 spec (2 PWM) and L3 benchmark (1 PWM)
    await staking.connect(l2c).stake(2, sHash, { value: ethers.parseEther("2") });
    await staking.connect(l3c).stake(3, bHash, { value: ethers.parseEther("1") });

    // 3. Seed benchmark pool via a bounty deposit (stand-in for pre-promotion B_k)
    await reward.connect(funder).depositBounty(bHash, { value: ethers.parseEther("100") });
    expect(await reward.poolOf(bHash)).to.equal(ethers.parseEther("100"));

    // 4. Submit an L4 certificate
    const certHash = H("cert:integration");
    const principleId = 42;
    await certificate.connect(sp).submit({
      certHash,
      benchmarkHash: bHash,
      principleId,
      l1Creator: l1c.address,
      l2Creator: l2c.address,
      l3Creator: l3c.address,
      acWallet:  sp.address,  // SP acts as AC for this test
      cpWallet:  cp.address,
      shareRatioP: 6000, // p=0.60 → AC gets 0.60*55%=33% of D; CP 0.40*55%=22%
      Q_int: 80,
      delta: 0,          // 7-day window
      rank: 1,           // Rank 1 → 40% of pool
    });

    // 5. Advance past challenge window
    await time.increase(7 * DAY + 1);

    // Snapshot balances (wei) pre-finalize
    const [bSP, bCP, bL1, bL2, bL3] = await Promise.all([
      ethers.provider.getBalance(sp.address),
      ethers.provider.getBalance(cp.address),
      ethers.provider.getBalance(l1c.address),
      ethers.provider.getBalance(l2c.address),
      ethers.provider.getBalance(l3c.address),
    ]);

    // 6. Finalize — distributes the draw
    const tx = await certificate.connect(challenger).finalize(certHash);
    await tx.wait();

    // Expected draw = 40% of 100 PWM = 40 PWM
    const pool0 = 100n * 10n ** 18n;
    const D = (pool0 * 4000n) / 10000n; // 40 ETH
    const bps = 10_000n;
    const p = 6000n;
    const acExp = (D * p * 5500n) / (bps * bps);
    const cpExp = (D * (bps - p) * 5500n) / (bps * bps);
    const l3Exp = (D * 1500n) / bps;
    const l2Exp = (D * 1000n) / bps;
    const l1Exp = (D *  500n) / bps;
    const tkExp = D - acExp - cpExp - l3Exp - l2Exp - l1Exp;

    expect((await ethers.provider.getBalance(sp.address)) - bSP).to.equal(acExp);
    expect((await ethers.provider.getBalance(cp.address)) - bCP).to.equal(cpExp);
    expect((await ethers.provider.getBalance(l3c.address)) - bL3).to.equal(l3Exp);
    expect((await ethers.provider.getBalance(l2c.address)) - bL2).to.equal(l2Exp);
    expect((await ethers.provider.getBalance(l1c.address)) - bL1).to.equal(l1Exp);
    expect(await treasury.balanceOf(principleId)).to.equal(tkExp);

    // 7. Pool rollover: exactly what's left (pool0 − D = 60 PWM)
    const remaining = await reward.poolOf(bHash);
    expect(remaining).to.equal(pool0 - D);

    // 8. L3 graduation: 50% back to staker, 50% seeds pool
    const l3StakerBefore = await ethers.provider.getBalance(l3c.address);
    const l3PoolBefore   = await reward.poolOf(bHash);
    await staking.connect(gov).graduate(bHash, bHash);
    const l3StakerAfter = await ethers.provider.getBalance(l3c.address);
    expect(l3StakerAfter - l3StakerBefore).to.equal(ethers.parseEther("0.5"));
    expect(await reward.poolOf(bHash)).to.equal(l3PoolBefore + ethers.parseEther("0.5"));
  });

  it("rollover: two successive certs at rank 2 then rank 3", async () => {
    const [gov, sp, cp, l1c, l2c, l3c, funder] = await ethers.getSigners();

    const Registry = await ethers.getContractFactory("PWMRegistry");
    const Reward   = await ethers.getContractFactory("PWMReward");
    const Treasury = await ethers.getContractFactory("PWMTreasury");
    const Certificate = await ethers.getContractFactory("PWMCertificate");
    const Staking = await ethers.getContractFactory("PWMStaking");

    const registry = await Registry.deploy();
    const treasury = await Treasury.deploy(gov.address);
    const reward = await Reward.deploy(gov.address);
    const certificate = await Certificate.deploy(gov.address);
    const staking = await Staking.deploy(gov.address);
    await Promise.all([registry.waitForDeployment(), treasury.waitForDeployment(),
      reward.waitForDeployment(), certificate.waitForDeployment(), staking.waitForDeployment()]);

    await reward.connect(gov).setCertificate(await certificate.getAddress());
    await reward.connect(gov).setStaking(await staking.getAddress());
    await reward.connect(gov).setMinting(gov.address); // placeholder
    await reward.connect(gov).setTreasury(await treasury.getAddress());
    await treasury.connect(gov).setReward(await reward.getAddress());
    await certificate.connect(gov).setRegistry(await registry.getAddress());
    await certificate.connect(gov).setReward(await reward.getAddress());

    const p = H("p2"), s = H("s2"), b = H("b2");
    await registry.register(p, ZERO, 1, l1c.address);
    await registry.register(s, p,    2, l2c.address);
    await registry.register(b, s,    3, l3c.address);
    await reward.connect(funder).depositBounty(b, { value: ethers.parseEther("1000") });

    const baseCert = (ch, rank) => ({
      certHash: ch, benchmarkHash: b, principleId: 1,
      l1Creator: l1c.address, l2Creator: l2c.address, l3Creator: l3c.address,
      acWallet: sp.address, cpWallet: cp.address, shareRatioP: 5000,
      Q_int: 80, delta: 0, rank,
    });
    await certificate.connect(sp).submit(baseCert(H("c-r2"), 2));
    await certificate.connect(sp).submit(baseCert(H("c-r3"), 3));
    await time.increase(7 * DAY + 1);
    await certificate.finalize(H("c-r2"));
    await certificate.finalize(H("c-r3"));

    // 1000 → after rank2 (5%): 950. After rank3 (2% of 950): 931
    const after2 = 1000n * 10n ** 18n - (1000n * 10n ** 18n * 500n) / 10000n;
    const after3 = after2 - (after2 * 200n) / 10000n;
    expect(await reward.poolOf(b)).to.equal(after3);
  });
});
