// Verify all 7 PWM contracts on Etherscan/Basescan/etc.
//
// Reads `addresses.json[<slot>]` for the current --network and runs
// `hre.run("verify:verify", ...)` against each contract with the correct
// constructor args. Idempotent: contracts that are already verified are
// reported as such and don't fail the run.
//
// Per pwm-team/coordination/MAINNET_DEPLOY_AUDIT_2026-04-28.md Gap 8.
// Replaces the manual one-`npx hardhat verify`-per-contract step in the
// mainnet day runbook.
//
// Usage:
//   cd pwm-team/infrastructure/agent-contracts
//   BASESCAN_API_KEY=$KEY npx hardhat run scripts/verify-all.js --network base
//   BASESCAN_API_KEY=$KEY npx hardhat run scripts/verify-all.js --network baseSepolia
//   ETHERSCAN_API_KEY=$KEY npx hardhat run scripts/verify-all.js --network sepolia
//
// Exit code 0 if all 7 are verified (or already-verified). Exit 1 on any
// hard failure (network error after retries, source mismatch, etc.).

const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

const NETWORK_TO_SLOT = {
  base: "base",
  baseSepolia: "baseSepolia",
  arbitrum: "arbitrum",
  arbSepolia: "arbSepolia",
  optimism: "optimism",
  mainnet: "mainnet",
  sepolia: "testnet",
};

function loadAddresses() {
  const p = path.join(__dirname, "..", "addresses.json");
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

async function verifyOne(name, address, constructorArguments) {
  if (!address) {
    return { name, status: "SKIP", reason: "address null in addresses.json" };
  }
  try {
    await hre.run("verify:verify", { address, constructorArguments });
    return { name, status: "VERIFIED", address };
  } catch (e) {
    const msg = (e.message || String(e));
    if (/already verified|Already Verified/i.test(msg)) {
      return { name, status: "ALREADY_VERIFIED", address };
    }
    if (/does not have bytecode/i.test(msg)) {
      return { name, status: "FAIL", address, reason: "no bytecode at address (deploy not landed?)" };
    }
    return { name, status: "FAIL", address, reason: msg.split("\n")[0] };
  }
}

async function main() {
  const networkName = hre.network.name;
  const slot = NETWORK_TO_SLOT[networkName];
  if (!slot) {
    console.error(`Unknown network '${networkName}'. Add to NETWORK_TO_SLOT.`);
    process.exitCode = 1;
    return;
  }
  const addrs = loadAddresses()[slot];
  if (!addrs) {
    console.error(`addresses.json has no '${slot}' slot.`);
    process.exitCode = 1;
    return;
  }

  console.log(`Network: ${networkName} (slot: ${slot})`);
  console.log(`Verifying 7 contracts in addresses.json[${slot}]:\n`);

  const initialGov = addrs.deployer || addrs.PWMGovernance;
  if (!initialGov) {
    console.error(`Cannot determine initialGovernance for ${slot} (deployer + PWMGovernance both null).`);
    process.exitCode = 1;
    return;
  }

  const founders = addrs.founders;
  if (!Array.isArray(founders) || founders.length !== 5) {
    console.error(`addresses.json[${slot}].founders must list exactly 5 addresses.`);
    process.exitCode = 1;
    return;
  }

  const results = [];

  // PWMGovernance(address[5] founders)
  results.push(await verifyOne("PWMGovernance", addrs.PWMGovernance, [founders]));

  // PWMRegistry() — no constructor args
  results.push(await verifyOne("PWMRegistry", addrs.PWMRegistry, []));

  // The other 5 take (address initialGovernance) — at deploy time, that was
  // the deployer key. After governance handoff, governance() points at
  // PWMGovernance, but the constructor argument is still the deployer.
  for (const name of ["PWMTreasury", "PWMReward", "PWMStaking", "PWMCertificate", "PWMMinting"]) {
    results.push(await verifyOne(name, addrs[name], [initialGov]));
  }

  // Report
  let pass = 0, alreadyPass = 0, fail = 0, skip = 0;
  console.log("\n================================================================");
  for (const r of results) {
    const tag = r.status === "VERIFIED" ? "✓ VERIFIED"
              : r.status === "ALREADY_VERIFIED" ? "✓ already verified"
              : r.status === "SKIP" ? "- SKIP"
              : "✗ FAIL";
    const detail = r.address ? ` @ ${r.address}` : "";
    const reason = r.reason ? ` — ${r.reason}` : "";
    console.log(`  ${tag.padEnd(20)} ${r.name.padEnd(16)}${detail}${reason}`);
    if (r.status === "VERIFIED") pass++;
    else if (r.status === "ALREADY_VERIFIED") alreadyPass++;
    else if (r.status === "SKIP") skip++;
    else fail++;
  }
  console.log("================================================================");
  console.log(`Newly verified: ${pass}`);
  console.log(`Already verified: ${alreadyPass}`);
  console.log(`Skipped: ${skip}`);
  console.log(`Failed: ${fail}`);

  if (fail > 0) {
    process.exitCode = 1;
    return;
  }
  if (pass + alreadyPass + skip < 7) {
    process.exitCode = 1;
    return;
  }
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
