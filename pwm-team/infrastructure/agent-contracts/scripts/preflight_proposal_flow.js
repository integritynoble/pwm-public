// Preflight helper: exercise the PWMGovernance 3-of-5 proposal lifecycle
// against a Hardhat fork. Used by scripts/preflight_step5_fork.sh.
//
// Runs:
//   1. Founder #1 calls proposeParameter("PREFLIGHT_TEST_KEY", 42)
//   2. Founders #2 + #3 call approveProposal
//   3. evm_increaseTime to skip the 48 h timelock
//   4. Founder #1 calls executeProposal
//   5. Reads back parameters[key] and asserts == 42
//
// Exits 0 on success, non-zero on any step failing or the parameter
// not having flipped to the expected value.
//
// Founders are read from addresses.json[<slot>].founders. The slot is
// derived from hre.network.name (localhost → local, baseSepolia →
// baseSepolia, etc.) following the same convention as the existing
// verify_governance_owns_admin.js helper.

const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

const NETWORK_TO_SLOT = {
  base: "base",
  baseSepolia: "baseSepolia",
  mainnet: "mainnet",
  sepolia: "testnet",
  hardhat: "local",
  localhost: "local",
};

// 48 h + 1 min slack
const TIMELOCK_FAST_FORWARD_SEC = 48 * 3600 + 60;
const TEST_PARAM_KEY = "PREFLIGHT_TEST_KEY";
const TEST_PARAM_VALUE = 42n;

function loadAddresses() {
  const p = path.join(__dirname, "..", "addresses.json");
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

async function main() {
  const networkName = hre.network.name;
  const slot = NETWORK_TO_SLOT[networkName];
  if (!slot) {
    console.error(`Unknown network '${networkName}'`);
    process.exitCode = 1;
    return;
  }
  const addrs = loadAddresses()[slot];
  if (!addrs) {
    console.error(`addresses.json has no '${slot}' slot`);
    process.exitCode = 1;
    return;
  }

  const govAddr = addrs.PWMGovernance;
  const founders = addrs.founders || [];
  if (!govAddr || founders.length !== 5) {
    console.error(`addresses.json[${slot}] needs PWMGovernance + 5 founders; got ${founders.length}`);
    process.exitCode = 1;
    return;
  }

  console.log(`Network:   ${networkName} (slot: ${slot})`);
  console.log(`PWMGov:    ${govAddr}`);
  console.log(`Founders:  ${founders.map(f => f.slice(0, 10)).join(", ")}`);
  console.log();

  // Get the 5 founder signers. On a hardhat fork, the founders are
  // hardhat's deterministic accounts (deploy/testnet.js's getSigners()
  // fallback). Each signer is fully funded.
  const signers = await hre.ethers.getSigners();
  const founderSigners = founders.map(addr => {
    const s = signers.find(s => s.address.toLowerCase() === addr.toLowerCase());
    if (!s) {
      throw new Error(`No signer for founder ${addr} (signers available: ${signers.slice(0, 7).map(s => s.address).join(", ")})`);
    }
    return s;
  });
  const [f1, f2, f3, f4, f5] = founderSigners;

  // Connect to PWMGovernance as f1
  const Governance = await hre.ethers.getContractFactory("PWMGovernance");
  const gov = Governance.attach(govAddr);

  // ---- Step A: f1 proposes -------------------------------------------------
  const keyBytes32 = hre.ethers.keccak256(hre.ethers.toUtf8Bytes(TEST_PARAM_KEY));
  console.log(`A. f1 (${f1.address.slice(0, 10)}…) proposeParameter(${TEST_PARAM_KEY}, ${TEST_PARAM_VALUE})`);
  const txProp = await gov.connect(f1).proposeParameter(keyBytes32, TEST_PARAM_VALUE);
  const rcptProp = await txProp.wait();
  // Find the ProposalCreated event to extract the proposal ID
  const proposalEvent = rcptProp.logs
    .map(l => { try { return gov.interface.parseLog(l); } catch { return null; } })
    .filter(p => p && p.name === "ProposalCreated")[0];
  if (!proposalEvent) {
    console.error("   ✗ no ProposalCreated event");
    process.exitCode = 1;
    return;
  }
  const proposalId = proposalEvent.args[0];
  console.log(`   ✓ proposal id = ${proposalId} (tx ${txProp.hash})`);

  // ---- Step B: f2 + f3 approve --------------------------------------------
  console.log(`B. f2 (${f2.address.slice(0, 10)}…) approveProposal(${proposalId})`);
  const tx2 = await gov.connect(f2).approveProposal(proposalId);
  await tx2.wait();
  console.log(`   ✓ tx ${tx2.hash}`);

  console.log(`C. f3 (${f3.address.slice(0, 10)}…) approveProposal(${proposalId})`);
  const tx3 = await gov.connect(f3).approveProposal(proposalId);
  await tx3.wait();
  console.log(`   ✓ tx ${tx3.hash}`);

  // Sanity: read approval count via the proposals mapping
  const proposalRead = await gov.proposals(proposalId);
  console.log(`   approvals = ${proposalRead.approvals} (expected 3)`);
  if (Number(proposalRead.approvals) !== 3) {
    console.error("   ✗ approval count != 3");
    process.exitCode = 1;
    return;
  }

  // ---- Step D: skip 48 h via evm_increaseTime + evm_mine -----------------
  console.log(`D. evm_increaseTime(${TIMELOCK_FAST_FORWARD_SEC}s) — skip 48 h timelock`);
  await hre.network.provider.send("evm_increaseTime", [TIMELOCK_FAST_FORWARD_SEC]);
  await hre.network.provider.send("evm_mine", []);
  console.log("   ✓ chain time advanced");

  // ---- Step E: any founder executes ---------------------------------------
  console.log(`E. f1 executeProposal(${proposalId})`);
  const txExec = await gov.connect(f1).executeProposal(proposalId);
  const rcptExec = await txExec.wait();
  console.log(`   ✓ tx ${txExec.hash}`);

  // ---- Step F: read back parameter ----------------------------------------
  const newValue = await gov.parameters(keyBytes32);
  console.log(`F. PWMGovernance.parameters(${TEST_PARAM_KEY}) = ${newValue}`);
  if (newValue !== TEST_PARAM_VALUE) {
    console.error(`   ✗ expected ${TEST_PARAM_VALUE}, got ${newValue}`);
    process.exitCode = 1;
    return;
  }

  console.log("\n✓ Proposal lifecycle PASSED — propose → 3-of-5 approvals → 48 h timelock skipped → execute → parameter set.");
}

main().catch(err => {
  console.error("Preflight proposal flow failed:", err);
  process.exitCode = 1;
});
