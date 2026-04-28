const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));
const ZERO = ethers.ZeroHash;
const DAY = 24 * 3600;

describe("PWMCertificate", function () {
  let registry, reward, treasury, cert, staking;
  let gov, submitter, challenger, ac, cp, l1c, l2c, l3c;

  const principleId = 1;

  async function registerChain() {
    const p = H("p"), s = H("s"), b = H("b");
    await registry.register(p, ZERO, 1, l1c.address);
    await registry.register(s, p,    2, l2c.address);
    await registry.register(b, s,    3, l3c.address);
    return { p, s, b };
  }

  beforeEach(async () => {
    [gov, submitter, challenger, ac, cp, l1c, l2c, l3c] = await ethers.getSigners();

    const Reg = await ethers.getContractFactory("PWMRegistry");
    registry = await Reg.deploy();
    const T = await ethers.getContractFactory("PWMTreasury");
    treasury = await T.deploy(gov.address);
    const R = await ethers.getContractFactory("PWMReward");
    reward = await R.deploy(gov.address);
    const C = await ethers.getContractFactory("PWMCertificate");
    cert = await C.deploy(gov.address);
    const S = await ethers.getContractFactory("PWMStaking");
    staking = await S.deploy(gov.address);
    await Promise.all([
      registry.waitForDeployment(), treasury.waitForDeployment(),
      reward.waitForDeployment(), cert.waitForDeployment(), staking.waitForDeployment(),
    ]);

    await reward.connect(gov).setCertificate(await cert.getAddress());
    await reward.connect(gov).setMinting(gov.address); // placeholder
    await reward.connect(gov).setStaking(await staking.getAddress());
    await reward.connect(gov).setTreasury(await treasury.getAddress());
    await treasury.connect(gov).setReward(await reward.getAddress());
    await cert.connect(gov).setRegistry(await registry.getAddress());
    await cert.connect(gov).setReward(await reward.getAddress());
  });

  function baseArgs({ b, certHash, delta = 0, rank = 1 }) {
    return {
      certHash,
      benchmarkHash: b,
      principleId,
      l1Creator: l1c.address,
      l2Creator: l2c.address,
      l3Creator: l3c.address,
      acWallet:  ac.address,
      cpWallet:  cp.address,
      shareRatioP: 5000,
      Q_int: 80,
      delta,
      rank,
    };
  }

  it("submit: rejects bad inputs, emits event", async () => {
    const { b } = await registerChain();
    const ch = H("cert1");

    // registry wasn't set initially; prove wiring works by unsetting-style test:
    // already set, so just exercise validation paths
    const good = baseArgs({ b, certHash: ch });
    await expect(cert.connect(submitter).submit({ ...good, certHash: ZERO }))
      .to.be.revertedWith("PWMCertificate: zero cert");
    await expect(cert.connect(submitter).submit({ ...good, shareRatioP: 999 }))
      .to.be.revertedWith("PWMCertificate: p out of range");
    await expect(cert.connect(submitter).submit({ ...good, shareRatioP: 9001 }))
      .to.be.revertedWith("PWMCertificate: p out of range");
    await expect(cert.connect(submitter).submit({ ...good, acWallet: ethers.ZeroAddress }))
      .to.be.revertedWith("PWMCertificate: zero AC/CP");
    await expect(cert.connect(submitter).submit({ ...good, benchmarkHash: H("unregistered") }))
      .to.be.revertedWith("PWMCertificate: benchmark not registered");

    await expect(cert.connect(submitter).submit(good))
      .to.emit(cert, "CertificateSubmitted");
    await expect(cert.connect(submitter).submit(good))
      .to.be.revertedWith("PWMCertificate: already submitted");
  });

  it("finalize blocked until window passes, then triggers distribute", async () => {
    const { b } = await registerChain();
    const ch = H("cert-fin");
    await reward.connect(gov).setMinting(gov.address); // already set, idempotent
    // seed the pool so distribute has something to draw
    await reward.connect(gov).depositBounty(b, { value: ethers.parseEther("100") });

    await cert.connect(submitter).submit(baseArgs({ b, certHash: ch, rank: 1 }));
    await expect(cert.finalize(ch)).to.be.revertedWith("PWMCertificate: window open");

    await time.increase(7 * DAY + 1);
    await expect(cert.finalize(ch))
      .to.emit(cert, "CertificateFinalized")
      .and.to.emit(reward, "DrawSettled");

    // pool reduced by 40%
    expect(await reward.poolOf(b)).to.equal(ethers.parseEther("60"));

    await expect(cert.finalize(ch)).to.be.revertedWith("PWMCertificate: not pending");
  });

  it("extended 14-day window when delta ≥ 10", async () => {
    const { b } = await registerChain();
    const ch = H("cert-delta");
    await reward.connect(gov).depositBounty(b, { value: ethers.parseEther("10") });
    await cert.connect(submitter).submit(baseArgs({ b, certHash: ch, delta: 10 }));
    await time.increase(7 * DAY + 1);
    await expect(cert.finalize(ch)).to.be.revertedWith("PWMCertificate: window open");
    await time.increase(7 * DAY);
    await cert.finalize(ch); // now past 14 days total
  });

  it("challenge: blocks finalize; upheld → rejected; not upheld → reinstated", async () => {
    const { b } = await registerChain();
    await reward.connect(gov).depositBounty(b, { value: ethers.parseEther("10") });

    // Flow A: challenge upheld
    const chA = H("A");
    await cert.connect(submitter).submit(baseArgs({ b, certHash: chA }));
    await cert.connect(challenger).challenge(chA, "0x1234");
    await time.increase(7 * DAY + 1);
    await expect(cert.finalize(chA)).to.be.revertedWith("PWMCertificate: not pending");
    await cert.connect(gov).resolveChallenge(chA, true);
    await expect(cert.finalize(chA)).to.be.revertedWith("PWMCertificate: not pending");

    // Flow B: challenge rejected
    const chB = H("B");
    await cert.connect(submitter).submit(baseArgs({ b, certHash: chB }));
    await cert.connect(challenger).challenge(chB, "0x");
    await cert.connect(gov).resolveChallenge(chB, false);
    await time.increase(7 * DAY + 1);
    await cert.finalize(chB);
  });

  it("challenge must be within window", async () => {
    const { b } = await registerChain();
    const ch = H("late");
    await cert.connect(submitter).submit(baseArgs({ b, certHash: ch }));
    await time.increase(7 * DAY + 1);
    await expect(cert.connect(challenger).challenge(ch, "0x"))
      .to.be.revertedWith("PWMCertificate: window closed");
  });

  it("windowEndOf returns 0 for unknown cert and correct value once submitted", async () => {
    expect(await cert.windowEndOf(H("unknown"))).to.equal(0);
    const { b } = await registerChain();
    const ch = H("known");
    await cert.connect(submitter).submit(baseArgs({ b, certHash: ch }));
    const c = await cert.certificates(ch);
    expect(await cert.windowEndOf(ch)).to.equal(c.submittedAt + BigInt(7 * DAY));
  });

  it("setGovernance: rejects zero, rejects non-governance, transfers cleanly", async () => {
    await expect(cert.connect(gov).setGovernance(ethers.ZeroAddress))
      .to.be.revertedWith("PWMCertificate: zero governance");
    await expect(cert.connect(submitter).setGovernance(submitter.address))
      .to.be.revertedWith("PWMCertificate: not governance");
    await expect(cert.connect(gov).setGovernance(submitter.address))
      .to.emit(cert, "GovernanceUpdated").withArgs(submitter.address);
    expect(await cert.governance()).to.equal(submitter.address);
  });

  it("setRegistry / setReward / setMinting: zero rejected; non-governance rejected", async () => {
    for (const fn of ["setRegistry", "setReward", "setMinting"]) {
      await expect(cert.connect(gov)[fn](ethers.ZeroAddress))
        .to.be.reverted;
      await expect(cert.connect(submitter)[fn](submitter.address))
        .to.be.revertedWith("PWMCertificate: not governance");
    }
  });

  it("constructor rejects zero governance", async () => {
    const C = await ethers.getContractFactory("PWMCertificate");
    await expect(C.deploy(ethers.ZeroAddress))
      .to.be.revertedWith("PWMCertificate: zero governance");
  });

  it("submit: shareRatioP out of range, zero AC/CP, zero creator", async () => {
    const { b } = await registerChain();
    const lowP = baseArgs({ b, certHash: H("low") });
    lowP.shareRatioP = 999;
    await expect(cert.connect(submitter).submit(lowP))
      .to.be.revertedWith("PWMCertificate: p out of range");
    const highP = baseArgs({ b, certHash: H("high") });
    highP.shareRatioP = 9001;
    await expect(cert.connect(submitter).submit(highP))
      .to.be.revertedWith("PWMCertificate: p out of range");
    const noAc = baseArgs({ b, certHash: H("noac") });
    noAc.acWallet = ethers.ZeroAddress;
    await expect(cert.connect(submitter).submit(noAc))
      .to.be.revertedWith("PWMCertificate: zero AC/CP");
    const noL1 = baseArgs({ b, certHash: H("nol1") });
    noL1.l1Creator = ethers.ZeroAddress;
    await expect(cert.connect(submitter).submit(noL1))
      .to.be.revertedWith("PWMCertificate: zero creator");
  });

  it("challenge: rejects non-pending cert", async () => {
    const { b } = await registerChain();
    const ch = H("chal-not-pending");
    await cert.connect(submitter).submit(baseArgs({ b, certHash: ch }));
    await cert.connect(challenger).challenge(ch, "0x");
    // status is now Challenged; another challenge() should fail
    await expect(cert.connect(challenger).challenge(ch, "0x"))
      .to.be.revertedWith("PWMCertificate: not pending");
  });

  it("resolveChallenge: rejects non-challenged + supports upheld=false reinstate", async () => {
    const { b } = await registerChain();
    const ch = H("resolve-test");
    await cert.connect(submitter).submit(baseArgs({ b, certHash: ch }));
    // Not yet challenged → resolve must revert
    await expect(cert.connect(gov).resolveChallenge(ch, true))
      .to.be.revertedWith("PWMCertificate: not challenged");
    await cert.connect(challenger).challenge(ch, "0x");
    // upheld=false reinstates to Pending
    await cert.connect(gov).resolveChallenge(ch, false);
    expect((await cert.certificates(ch)).status).to.equal(1); // Status.Pending
  });
});
