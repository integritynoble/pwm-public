const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("PWMTreasury", function () {
  let treasury, gov, reward, winner, rando;

  beforeEach(async () => {
    [gov, reward, winner, rando] = await ethers.getSigners();
    const F = await ethers.getContractFactory("PWMTreasury");
    treasury = await F.deploy(gov.address);
    await treasury.waitForDeployment();
    await treasury.connect(gov).setReward(reward.address);
  });

  it("constructor sets governance and rejects zero", async () => {
    const F = await ethers.getContractFactory("PWMTreasury");
    await expect(F.deploy(ethers.ZeroAddress))
      .to.be.revertedWith("PWMTreasury: zero governance");
    expect(await treasury.governance()).to.equal(gov.address);
  });

  it("only reward may call receive15pct; funds accumulate per principle", async () => {
    const amt = ethers.parseEther("1.5");
    await expect(treasury.connect(rando).receive15pct(1, amt, { value: amt }))
      .to.be.revertedWith("PWMTreasury: not reward");
    await expect(treasury.connect(reward).receive15pct(1, amt, { value: amt }))
      .to.emit(treasury, "FundsReceived");
    expect(await treasury.balanceOf(1)).to.equal(amt);
    // second deposit accumulates
    await treasury.connect(reward).receive15pct(1, amt, { value: amt });
    expect(await treasury.balanceOf(1)).to.equal(amt * 2n);
    // separate principle is isolated
    expect(await treasury.balanceOf(2)).to.equal(0n);
  });

  it("receive15pct reverts if msg.value != amount", async () => {
    await expect(treasury.connect(reward).receive15pct(1, ethers.parseEther("1"), {
      value: ethers.parseEther("0.5"),
    })).to.be.revertedWith("PWMTreasury: value mismatch");
  });

  it("pays bounty up to 50% of T_k, then new cap applies", async () => {
    const fund = ethers.parseEther("10");
    await treasury.connect(reward).receive15pct(1, fund, { value: fund });

    // > 50% rejected
    await expect(treasury.connect(gov).payAdversarialBounty(1, winner.address, ethers.parseEther("6")))
      .to.be.revertedWith("PWMTreasury: exceeds 50% cap");

    // exactly 50% ok
    const before = await ethers.provider.getBalance(winner.address);
    await treasury.connect(gov).payAdversarialBounty(1, winner.address, ethers.parseEther("5"));
    const after = await ethers.provider.getBalance(winner.address);
    expect(after - before).to.equal(ethers.parseEther("5"));
    expect(await treasury.balanceOf(1)).to.equal(ethers.parseEther("5"));

    // now of the remaining 5, 50% = 2.5; trying to pay 3 fails
    await expect(treasury.connect(gov).payAdversarialBounty(1, winner.address, ethers.parseEther("3")))
      .to.be.revertedWith("PWMTreasury: exceeds 50% cap");
  });

  it("bounty rejects zero amount / zero winner / non-governance", async () => {
    const fund = ethers.parseEther("10");
    await treasury.connect(reward).receive15pct(1, fund, { value: fund });
    await expect(treasury.connect(rando).payAdversarialBounty(1, winner.address, 1))
      .to.be.revertedWith("PWMTreasury: not governance");
    await expect(treasury.connect(gov).payAdversarialBounty(1, ethers.ZeroAddress, 1))
      .to.be.revertedWith("PWMTreasury: zero winner");
    await expect(treasury.connect(gov).payAdversarialBounty(1, winner.address, 0))
      .to.be.revertedWith("PWMTreasury: zero amount");
  });

  it("setGovernance/setReward: only governance, rejects zero", async () => {
    await expect(treasury.connect(rando).setGovernance(rando.address))
      .to.be.revertedWith("PWMTreasury: not governance");
    await expect(treasury.connect(gov).setGovernance(ethers.ZeroAddress))
      .to.be.revertedWith("PWMTreasury: zero governance");
    await treasury.connect(gov).setGovernance(rando.address);
    expect(await treasury.governance()).to.equal(rando.address);
    // old governance now rejected
    await expect(treasury.connect(gov).setReward(reward.address))
      .to.be.revertedWith("PWMTreasury: not governance");
  });
});
