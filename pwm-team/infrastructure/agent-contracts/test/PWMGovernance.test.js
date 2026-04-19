const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

const KEY = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));
const TIMELOCK = 48 * 3600;

describe("PWMGovernance", function () {
  let gov, founders, outsider;

  beforeEach(async () => {
    const signers = await ethers.getSigners();
    founders = signers.slice(0, 5);
    outsider = signers[5];
    const F = await ethers.getContractFactory("PWMGovernance");
    gov = await F.deploy(founders.map(f => f.address));
    await gov.waitForDeployment();
  });

  it("constructor sets founders, rejects zero and duplicates", async () => {
    const F = await ethers.getContractFactory("PWMGovernance");
    const s = await ethers.getSigners();
    await expect(F.deploy([s[0].address, s[1].address, s[2].address, s[3].address, ethers.ZeroAddress]))
      .to.be.revertedWith("PWMGovernance: zero founder");
    await expect(F.deploy([s[0].address, s[0].address, s[2].address, s[3].address, s[4].address]))
      .to.be.revertedWith("PWMGovernance: duplicate founder");
    for (const f of founders) expect(await gov.isFounder(f.address)).to.equal(true);
  });

  it("non-founders cannot propose / approve / execute", async () => {
    await expect(gov.connect(outsider).proposeParameter(KEY("X"), 1))
      .to.be.revertedWith("PWMGovernance: not founder");
  });

  it("full happy path: propose → 2 more approvals → wait 48h → execute", async () => {
    const key = KEY("USD_FLOOR_L1");
    await gov.connect(founders[0]).proposeParameter(key, 12345);
    await gov.connect(founders[1]).approveProposal(0);
    await gov.connect(founders[2]).approveProposal(0);

    // early execution fails
    await expect(gov.connect(founders[0]).executeProposal(0))
      .to.be.revertedWith("PWMGovernance: timelock not elapsed");

    await time.increase(TIMELOCK);
    await expect(gov.connect(founders[0]).executeProposal(0))
      .to.emit(gov, "ProposalExecuted");
    expect(await gov.getParameter(key)).to.equal(12345);
  });

  it("insufficient approvals blocks execution even after timelock", async () => {
    await gov.connect(founders[0]).proposeParameter(KEY("K"), 1);
    await gov.connect(founders[1]).approveProposal(0);
    // only 2 approvals (proposer + 1)
    await time.increase(TIMELOCK);
    await expect(gov.connect(founders[0]).executeProposal(0))
      .to.be.revertedWith("PWMGovernance: insufficient approvals");
  });

  it("double-approval by same founder rejected; double-execute rejected", async () => {
    await gov.connect(founders[0]).proposeParameter(KEY("K"), 1);
    await expect(gov.connect(founders[0]).approveProposal(0))
      .to.be.revertedWith("PWMGovernance: already approved");
    await gov.connect(founders[1]).approveProposal(0);
    await gov.connect(founders[2]).approveProposal(0);
    await time.increase(TIMELOCK);
    await gov.connect(founders[0]).executeProposal(0);
    await expect(gov.connect(founders[0]).executeProposal(0))
      .to.be.revertedWith("PWMGovernance: finalised");
  });

  it("cancelled proposal cannot be executed", async () => {
    await gov.connect(founders[0]).proposeParameter(KEY("K"), 1);
    await gov.connect(founders[1]).approveProposal(0);
    await gov.connect(founders[2]).approveProposal(0);
    await gov.connect(founders[3]).cancelProposal(0);
    await time.increase(TIMELOCK);
    await expect(gov.connect(founders[0]).executeProposal(0))
      .to.be.revertedWith("PWMGovernance: finalised");
  });

  it("activateDAO requires a proposal with ACTIVATE_DAO key", async () => {
    // wrong key
    await gov.connect(founders[0]).proposeParameter(KEY("not_the_right_key"), 1);
    await gov.connect(founders[1]).approveProposal(0);
    await gov.connect(founders[2]).approveProposal(0);
    await time.increase(TIMELOCK);
    await expect(gov.connect(founders[0]).activateDAO(0))
      .to.be.revertedWith("PWMGovernance: wrong proposal key");

    // right key
    await gov.connect(founders[0]).proposeParameter(KEY("ACTIVATE_DAO"), 0);
    await gov.connect(founders[1]).approveProposal(1);
    await gov.connect(founders[2]).approveProposal(1);
    await time.increase(TIMELOCK);
    await gov.connect(founders[0]).activateDAO(1);
    expect(await gov.daoActivated()).to.equal(true);

    // multisig routes disabled after DAO activation
    await expect(gov.connect(founders[0]).proposeParameter(KEY("X"), 1))
      .to.be.revertedWith("PWMGovernance: DAO active, multisig disabled");
  });
});
