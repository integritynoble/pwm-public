const { expect } = require("chai");
const { ethers } = require("hardhat");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));
const BURN = "0x000000000000000000000000000000000000dEaD";

describe("PWMStaking", function () {
  let staking, reward, treasury, gov, staker, challenger, outsider;

  beforeEach(async () => {
    [gov, staker, challenger, outsider] = await ethers.getSigners();
    const T = await ethers.getContractFactory("PWMTreasury");
    treasury = await T.deploy(gov.address);
    const R = await ethers.getContractFactory("PWMReward");
    reward = await R.deploy(gov.address);
    await treasury.waitForDeployment();
    await reward.waitForDeployment();
    const S = await ethers.getContractFactory("PWMStaking");
    staking = await S.deploy(gov.address);
    await staking.waitForDeployment();

    await reward.connect(gov).setCertificate(outsider.address); // placeholder
    await reward.connect(gov).setMinting(outsider.address);     // placeholder
    await reward.connect(gov).setStaking(await staking.getAddress());
    await reward.connect(gov).setTreasury(await treasury.getAddress());
    await treasury.connect(gov).setReward(await reward.getAddress());
    await staking.connect(gov).setReward(await reward.getAddress());
  });

  it("defaults: L1=10, L2=2, L3=1 PWM", async () => {
    expect(await staking.stakeAmount(1)).to.equal(ethers.parseEther("10"));
    expect(await staking.stakeAmount(2)).to.equal(ethers.parseEther("2"));
    expect(await staking.stakeAmount(3)).to.equal(ethers.parseEther("1"));
  });

  it("stake: rejects bad layer / zero hash / wrong amount / duplicate", async () => {
    const h = H("art");
    await expect(staking.connect(staker).stake(0, h, { value: ethers.parseEther("1") }))
      .to.be.revertedWith("PWMStaking: bad layer");
    await expect(staking.connect(staker).stake(4, h, { value: ethers.parseEther("1") }))
      .to.be.revertedWith("PWMStaking: bad layer");
    await expect(staking.connect(staker).stake(1, ethers.ZeroHash, { value: ethers.parseEther("10") }))
      .to.be.revertedWith("PWMStaking: zero hash");
    await expect(staking.connect(staker).stake(1, h, { value: ethers.parseEther("9") }))
      .to.be.revertedWith("PWMStaking: wrong amount");

    await staking.connect(staker).stake(1, h, { value: ethers.parseEther("10") });
    await expect(staking.connect(staker).stake(1, h, { value: ethers.parseEther("10") }))
      .to.be.revertedWith("PWMStaking: already staked");
    const [who, layer, amt, status] = await staking.stakeOf(h);
    expect(who).to.equal(staker.address);
    expect(layer).to.equal(1);
    expect(amt).to.equal(ethers.parseEther("10"));
    expect(status).to.equal(1);
  });

  it("graduate: 50% back to staker, 50% seeds benchmark pool", async () => {
    const h = H("bench");
    await staking.connect(staker).stake(3, h, { value: ethers.parseEther("1") });
    const before = await ethers.provider.getBalance(staker.address);

    await expect(staking.connect(gov).graduate(h, h))
      .to.emit(staking, "Graduated")
      .and.to.emit(reward, "PoolSeeded");

    const after = await ethers.provider.getBalance(staker.address);
    expect(after - before).to.equal(ethers.parseEther("0.5"));
    expect(await reward.poolOf(h)).to.equal(ethers.parseEther("0.5"));
    const s = await staking.stakeOf(h);
    expect(s[3]).to.equal(2); // Graduated
  });

  it("slashForChallenge: 50% to dead address, 50% to challenger", async () => {
    const h = H("bad");
    await staking.connect(staker).stake(2, h, { value: ethers.parseEther("2") });
    const before = await ethers.provider.getBalance(challenger.address);
    const burnBefore = await ethers.provider.getBalance(BURN);

    await expect(staking.connect(gov).slashForChallenge(h, challenger.address))
      .to.emit(staking, "ChallengeUpheld");

    expect((await ethers.provider.getBalance(challenger.address)) - before)
      .to.equal(ethers.parseEther("1"));
    expect((await ethers.provider.getBalance(BURN)) - burnBefore)
      .to.equal(ethers.parseEther("1"));
  });

  it("slashForFraud: 100% burned", async () => {
    const h = H("fraud");
    await staking.connect(staker).stake(1, h, { value: ethers.parseEther("10") });
    const burnBefore = await ethers.provider.getBalance(BURN);
    await expect(staking.connect(gov).slashForFraud(h))
      .to.emit(staking, "FraudSlashed");
    expect((await ethers.provider.getBalance(BURN)) - burnBefore)
      .to.equal(ethers.parseEther("10"));
  });

  it("resolution is governance-only and one-shot", async () => {
    const h = H("one");
    await staking.connect(staker).stake(3, h, { value: ethers.parseEther("1") });
    await expect(staking.connect(outsider).graduate(h, h))
      .to.be.revertedWith("PWMStaking: not governance");
    await staking.connect(gov).graduate(h, h);
    await expect(staking.connect(gov).graduate(h, h))
      .to.be.revertedWith("PWMStaking: not active");
    await expect(staking.connect(gov).slashForFraud(h))
      .to.be.revertedWith("PWMStaking: not active");
  });

  it("setStakeAmount changes the required stake", async () => {
    await staking.connect(gov).setStakeAmount(3, ethers.parseEther("5"));
    expect(await staking.stakeAmount(3)).to.equal(ethers.parseEther("5"));
    await expect(staking.connect(staker).stake(3, H("new"), { value: ethers.parseEther("1") }))
      .to.be.revertedWith("PWMStaking: wrong amount");
    await staking.connect(staker).stake(3, H("new"), { value: ethers.parseEther("5") });
  });

  it("setGovernance: rejects zero, rejects non-governance, transfers cleanly", async () => {
    await expect(staking.connect(gov).setGovernance(ethers.ZeroAddress))
      .to.be.revertedWith("PWMStaking: zero governance");
    await expect(staking.connect(outsider).setGovernance(outsider.address))
      .to.be.revertedWith("PWMStaking: not governance");
    await expect(staking.connect(gov).setGovernance(outsider.address))
      .to.emit(staking, "GovernanceUpdated").withArgs(outsider.address);
    expect(await staking.governance()).to.equal(outsider.address);
  });

  it("setReward: zero rejected; non-governance rejected", async () => {
    await expect(staking.connect(gov).setReward(ethers.ZeroAddress))
      .to.be.revertedWith("PWMStaking: zero reward");
    await expect(staking.connect(outsider).setReward(outsider.address))
      .to.be.revertedWith("PWMStaking: not governance");
  });

  it("setStakeAmount: bad layer + zero amount + non-governance", async () => {
    // bad layer (out of LAYER_PRINCIPLE..LAYER_BENCHMARK range)
    await expect(staking.connect(gov).setStakeAmount(99, 1))
      .to.be.revertedWith("PWMStaking: bad layer");
    // zero amount on a valid layer (1 = LAYER_SPEC)
    await expect(staking.connect(gov).setStakeAmount(1, 0))
      .to.be.revertedWith("PWMStaking: zero amount");
    // non-governance blocked
    await expect(staking.connect(outsider).setStakeAmount(1, 1))
      .to.be.revertedWith("PWMStaking: not governance");
  });

  it("constructor rejects zero governance", async () => {
    const S = await ethers.getContractFactory("PWMStaking");
    await expect(S.deploy(ethers.ZeroAddress))
      .to.be.revertedWith("PWMStaking: zero governance");
  });
});
