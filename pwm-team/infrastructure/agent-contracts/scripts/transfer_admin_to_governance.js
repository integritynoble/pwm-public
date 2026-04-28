// Stream-5 mainnet day runbook step 4 helper — idempotent.
//
// For each PWM admin contract on the current network, ensures its
// `governance()` points at the canonical PWMGovernance address. If a
// contract already points at PWMGovernance, it's skipped. If it
// points elsewhere, this script calls `setGovernance(PWMGovernance)`
// from the deployer key.
//
// PWM does NOT use a Gnosis Safe for protocol admin — PWMGovernance is
// the multisig (3-of-5 over founder wallets). See `multisig/README.md`.
//
// Usage:
//   cd pwm-team/infrastructure/agent-contracts
//   PWM_PRIVATE_KEY=$DEPLOYER_PK npx hardhat run scripts/transfer_admin_to_governance.js --network base
//
// IMPORTANT: this script can ONLY be run by the current `governance()`
// holder of each admin contract. After deploy, that's the deployer's
// hot key. Once admin transfers to PWMGovernance, ONLY a PWMGovernance
// proposal can re-run this. Do NOT lose deployer key access until
// every admin is correctly pointed.
//
// Per MAINNET_DEPLOY_PLAN.md Mainnet Day Runbook step 4.

const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

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
  if (!govAddr) {
    console.error(`addresses.json[${slot}].PWMGovernance is null`);
    process.exitCode = 1;
    return;
  }

  // Refuse to run on mainnet without explicit confirm.
  if (slot === "mainnet" || slot === "base") {
    if (process.env.PWM_MAINNET_CONFIRM !== "1") {
      console.error(
        `Refusing to run on '${networkName}' without PWM_MAINNET_CONFIRM=1. ` +
        "This script sends transactions; double-check the target network."
      );
      process.exitCode = 1;
      return;
    }
  }

  const [signer] = await hre.ethers.getSigners();
  console.log(`Network: ${networkName} (slot: ${slot})`);
  console.log(`Signer:  ${signer.address}`);
  console.log(`Target PWMGovernance: ${govAddr}`);
  console.log();

  let migrated = 0;
  let skipped = 0;
  let failed = 0;

  for (const cname of ADMIN_CONTRACTS) {
    const cAddr = addrs[cname];
    if (!cAddr) {
      console.log(`  ✗ ${cname}: address null; cannot migrate`);
      failed++;
      continue;
    }
    const c = await hre.ethers.getContractAt(cname, cAddr);
    let current;
    try {
      current = await c.governance();
    } catch (e) {
      console.log(`  ✗ ${cname}: governance() reverted (${e.message})`);
      failed++;
      continue;
    }
    if (current.toLowerCase() === govAddr.toLowerCase()) {
      console.log(`  - ${cname}: already at ${current}; skip`);
      skipped++;
      continue;
    }
    console.log(`  → ${cname}: ${current} → ${govAddr} ...`);
    try {
      const tx = await c.connect(signer).setGovernance(govAddr);
      const rcpt = await tx.wait();
      console.log(`    ✓ tx ${tx.hash} mined in block ${rcpt.blockNumber}`);
      migrated++;
    } catch (e) {
      console.log(`    ✗ tx failed: ${e.message}`);
      failed++;
    }
  }

  console.log();
  console.log("================================================================");
  console.log(`migrated: ${migrated}`);
  console.log(`skipped:  ${skipped}`);
  console.log(`failed:   ${failed}`);
  if (failed > 0) {
    process.exitCode = 1;
    return;
  }
  console.log(
    "All admin contracts now point at PWMGovernance. Run " +
    "verify_governance_owns_admin.js to double-check."
  );
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
