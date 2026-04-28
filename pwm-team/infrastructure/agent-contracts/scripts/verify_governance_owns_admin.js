// Stream-5 exit-signal #2 verifier.
//
// Asserts that every PWM admin contract has its `governance()` set to
// the canonical PWMGovernance address for the current network.
//
// PWM does NOT use a Gnosis Safe for protocol admin — PWMGovernance is
// itself a 3-of-5 multisig over the 5 founder wallets (see
// `multisig/README.md`). This script verifies the wiring is correct.
//
// Usage:
//   cd pwm-team/infrastructure/agent-contracts
//   npx hardhat run scripts/verify_governance_owns_admin.js --network base
//   npx hardhat run scripts/verify_governance_owns_admin.js --network baseSepolia
//   npx hardhat run scripts/verify_governance_owns_admin.js --network testnet
//
// Exit code 0 if all 5 admin contracts point at PWMGovernance.
// Exit code 1 (process.exitCode) on any mismatch.
//
// Per MAINNET_DEPLOY_PLAN.md Stream 5 exit signal #2.

const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

// 5 contracts that have a `governance()` getter and point at PWMGovernance.
const ADMIN_CONTRACTS = [
  "PWMTreasury",
  "PWMReward",
  "PWMStaking",
  "PWMCertificate",
  "PWMMinting",
];

const NETWORK_TO_SLOT = {
  base: "base",
  baseSepolia: "baseSepolia",
  arbitrum: "arbitrum",
  arbSepolia: "arbSepolia",
  optimism: "optimism",
  mainnet: "mainnet",
  sepolia: "testnet",
  hardhat: "local",
  localhost: "local",
};

function loadAddresses() {
  const p = path.join(__dirname, "..", "addresses.json");
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

async function main() {
  const networkName = hre.network.name;
  const slot = NETWORK_TO_SLOT[networkName];
  if (!slot) {
    console.error(`Unknown network '${networkName}'. Add a NETWORK_TO_SLOT entry.`);
    process.exitCode = 1;
    return;
  }
  const addrs = loadAddresses()[slot];
  if (!addrs) {
    console.error(`addresses.json has no '${slot}' slot.`);
    process.exitCode = 1;
    return;
  }

  const govAddr = addrs.PWMGovernance;
  if (!govAddr) {
    console.error(`addresses.json[${slot}].PWMGovernance is null.`);
    process.exitCode = 1;
    return;
  }

  console.log(`Network: ${networkName} (slot: ${slot})`);
  console.log(`Expected PWMGovernance: ${govAddr}`);
  console.log();

  let pass = 0;
  let fail = 0;
  const failures = [];

  for (const cname of ADMIN_CONTRACTS) {
    const cAddr = addrs[cname];
    if (!cAddr) {
      console.log(`  ✗ ${cname}: address null in addresses.json`);
      fail++;
      failures.push(`${cname}: address null`);
      continue;
    }
    const c = await hre.ethers.getContractAt(cname, cAddr);
    let actual;
    try {
      actual = await c.governance();
    } catch (e) {
      console.log(`  ✗ ${cname}: governance() reverted (${e.message})`);
      fail++;
      failures.push(`${cname}: governance() revert`);
      continue;
    }
    const ok = actual.toLowerCase() === govAddr.toLowerCase();
    if (ok) {
      console.log(`  ✓ ${cname} @ ${cAddr}: governance() = ${actual}`);
      pass++;
    } else {
      console.log(`  ✗ ${cname} @ ${cAddr}: governance() = ${actual} (expected ${govAddr})`);
      fail++;
      failures.push(`${cname}: ${actual} != ${govAddr}`);
    }
  }

  console.log();
  console.log("================================================================");
  console.log(`PASS: ${pass} / ${ADMIN_CONTRACTS.length}`);
  console.log(`FAIL: ${fail}`);
  if (fail > 0) {
    console.log("\nFailures:");
    for (const f of failures) console.log(`  - ${f}`);
    console.log(
      "\nFix: run `npx hardhat run scripts/transfer_admin_to_governance.js " +
      `--network ${networkName}` + "` to re-point the admin contracts."
    );
    process.exitCode = 1;
    return;
  }

  console.log("All 5 admin contracts correctly pointed at PWMGovernance.");
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
