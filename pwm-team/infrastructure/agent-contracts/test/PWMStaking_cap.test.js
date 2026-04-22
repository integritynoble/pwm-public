const { expect } = require("chai");
const { ethers } = require("hardhat");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));
const LAYER_PRINCIPLE = 1;
const LAYER_SPEC = 2;
const LAYER_BENCHMARK = 3;

/**
 * Tests for the pre-mainnet TVL cap `maxTotalStakeWei` on PWMStaking.
 * See contracts/PWMStaking.sol and AUDIT_FREE_PATH.md Track D.
 *
 * The contract tracks totalActiveStakeWei as a running sum — incremented on
 * stake(), decremented on graduate/slashForChallenge/slashForFraud.
 */
describe("PWMStaking — maxTotalStakeWei cap", function () {
  let staking, reward, treasury, gov, a, b, c, outsider;

  beforeEach(async () => {
    [gov, a, b, c, outsider] = await ethers.getSigners();

    const T = await ethers.getContractFactory("PWMTreasury");
    treasury = await T.deploy(gov.address);
    await treasury.waitForDeployment();

    const R = await ethers.getContractFactory("PWMReward");
    reward = await R.deploy(gov.address);
    await reward.waitForDeployment();

    const S = await ethers.getContractFactory("PWMStaking");
    staking = await S.deploy(gov.address);
    await staking.waitForDeployment();

    await staking.connect(gov).setReward(await reward.getAddress());
    await reward.connect(gov).setStaking(await staking.getAddress());
    await reward.connect(gov).setCertificate(gov.address); // placeholder
    await reward.connect(gov).setMinting(gov.address);     // placeholder
    await reward.connect(gov).setTreasury(await treasury.getAddress());
    await treasury.connect(gov).setReward(await reward.getAddress());
  });

  it("cap defaults to zero (unlimited) — existing behavior preserved", async () => {
    expect(await staking.maxTotalStakeWei()).to.equal(0n);
    expect(await staking.totalActiveStakeWei()).to.equal(0n);
    // With cap=0, multiple stakes should succeed regardless of total.
    await staking.connect(a).stake(LAYER_PRINCIPLE, H("a1"), { value: ethers.parseEther("10") });
    await staking.connect(b).stake(LAYER_PRINCIPLE, H("a2"), { value: ethers.parseEther("10") });
    expect(await staking.totalActiveStakeWei()).to.equal(ethers.parseEther("20"));
  });

  it("only governance can setMaxTotalStakeWei", async () => {
    await expect(staking.connect(outsider).setMaxTotalStakeWei(100n))
      .to.be.revertedWith("PWMStaking: not governance");
    await expect(staking.connect(gov).setMaxTotalStakeWei(100n))
      .to.emit(staking, "MaxTotalStakeWeiUpdated").withArgs(100n);
    expect(await staking.maxTotalStakeWei()).to.equal(100n);
  });

  it("blocks a stake that would push total over the cap", async () => {
    await staking.connect(gov).setMaxTotalStakeWei(ethers.parseEther("12"));
    // L1 = 10 ether, L2 = 2 ether, L3 = 1 ether by default.
    // First L1 stake: 10 <= 12, OK.
    await staking.connect(a).stake(LAYER_PRINCIPLE, H("a1"), { value: ethers.parseEther("10") });
    // L2 stake: 10 + 2 = 12, exactly at cap, OK.
    await staking.connect(a).stake(LAYER_SPEC, H("a2"), { value: ethers.parseEther("2") });
    expect(await staking.totalActiveStakeWei()).to.equal(ethers.parseEther("12"));
    // Any further stake overshoots.
    await expect(
      staking.connect(b).stake(LAYER_BENCHMARK, H("a3"), { value: ethers.parseEther("1") })
    ).to.be.revertedWith("PWMStaking: total stake cap exceeded");
    // Total untouched.
    expect(await staking.totalActiveStakeWei()).to.equal(ethers.parseEther("12"));
  });

  it("totalActiveStakeWei decrements on graduate", async () => {
    await staking.connect(gov).setMaxTotalStakeWei(ethers.parseEther("12"));
    await staking.connect(a).stake(LAYER_PRINCIPLE, H("g1"), { value: ethers.parseEther("10") });
    // Graduate — half back to staker, half to reward pool; totalActive decrements by full amount.
    await staking.connect(gov).graduate(H("g1"), H("bench-for-g1"));
    expect(await staking.totalActiveStakeWei()).to.equal(0n);
    // After graduation, cap frees up — a new stake fits.
    await staking.connect(b).stake(LAYER_PRINCIPLE, H("g2"), { value: ethers.parseEther("10") });
  });

  it("totalActiveStakeWei decrements on slashForFraud", async () => {
    await staking.connect(gov).setMaxTotalStakeWei(ethers.parseEther("10"));
    await staking.connect(a).stake(LAYER_PRINCIPLE, H("f1"), { value: ethers.parseEther("10") });
    expect(await staking.totalActiveStakeWei()).to.equal(ethers.parseEther("10"));
    await staking.connect(gov).slashForFraud(H("f1"));
    expect(await staking.totalActiveStakeWei()).to.equal(0n);
  });

  it("totalActiveStakeWei decrements on slashForChallenge", async () => {
    await staking.connect(gov).setMaxTotalStakeWei(ethers.parseEther("10"));
    await staking.connect(a).stake(LAYER_PRINCIPLE, H("c1"), { value: ethers.parseEther("10") });
    await staking.connect(gov).slashForChallenge(H("c1"), outsider.address);
    expect(await staking.totalActiveStakeWei()).to.equal(0n);
  });

  it("lowering the cap below current total does not refund; only blocks new stakes", async () => {
    await staking.connect(gov).setMaxTotalStakeWei(ethers.parseEther("10"));
    await staking.connect(a).stake(LAYER_PRINCIPLE, H("l1"), { value: ethers.parseEther("10") });
    // Lower cap to zero.
    await staking.connect(gov).setMaxTotalStakeWei(1n);
    // Total is still 10 ether — no forced refund.
    expect(await staking.totalActiveStakeWei()).to.equal(ethers.parseEther("10"));
    // Further stakes are blocked.
    await expect(
      staking.connect(b).stake(LAYER_BENCHMARK, H("l2"), { value: ethers.parseEther("1") })
    ).to.be.revertedWith("PWMStaking: total stake cap exceeded");
  });

  it("cap of zero reverts to unlimited", async () => {
    await staking.connect(gov).setMaxTotalStakeWei(ethers.parseEther("5"));
    await staking.connect(a).stake(LAYER_BENCHMARK, H("z1"), { value: ethers.parseEther("1") });
    // Attempting to exceed the small cap fails.
    await expect(
      staking.connect(b).stake(LAYER_PRINCIPLE, H("z2"), { value: ethers.parseEther("10") })
    ).to.be.revertedWith("PWMStaking: total stake cap exceeded");
    // Lift the cap.
    await staking.connect(gov).setMaxTotalStakeWei(0n);
    // Now the big stake goes through.
    await staking.connect(b).stake(LAYER_PRINCIPLE, H("z3"), { value: ethers.parseEther("10") });
  });
});
