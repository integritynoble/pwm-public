// Export the 7 production-contract ABIs from `artifacts/contracts/*` to
// `pwm-team/coordination/agent-coord/interfaces/contracts_abi/<Name>.json`,
// the canonical location every other agent (web frontend, indexer, CLI,
// off-chain scoring engine) reads from.
//
// Per pwm-team/coordination/MAINNET_DEPLOY_AUDIT_2026-04-28.md Gap 10.
// The agent-contracts CLAUDE.md says "after M1.1, copy ABI files" — this
// script does it deterministically and is safe to re-run after every recompile.
//
// Usage:
//   cd pwm-team/infrastructure/agent-contracts
//   npx hardhat compile
//   node scripts/export-abis.js
//
// Or as a Hardhat task:
//   npx hardhat run scripts/export-abis.js
//
// Output schema preserves the existing canonical-interfaces shape:
//   { contractName, abi, bytecode, deployedBytecode }

const fs = require("fs");
const path = require("path");

const PROD_CONTRACTS = [
  "PWMRegistry",
  "PWMGovernance",
  "PWMTreasury",
  "PWMReward",
  "PWMStaking",
  "PWMCertificate",
  "PWMMinting",
];

function repoRoot() {
  // scripts/export-abis.js → ../.. = agent-contracts/, ../../../../ = pwm/
  return path.resolve(__dirname, "..", "..", "..", "..");
}

function loadArtifact(name) {
  const p = path.join(__dirname, "..", "artifacts", "contracts", `${name}.sol`, `${name}.json`);
  if (!fs.existsSync(p)) {
    throw new Error(`Artifact not found: ${p}. Run \`npx hardhat compile\` first.`);
  }
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function writeInterface(name, artifact) {
  const out = {
    contractName: artifact.contractName,
    abi: artifact.abi,
    bytecode: artifact.bytecode,
    deployedBytecode: artifact.deployedBytecode,
  };
  const dst = path.join(
    repoRoot(),
    "pwm-team", "coordination", "agent-coord", "interfaces", "contracts_abi",
    `${name}.json`
  );
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.writeFileSync(dst, JSON.stringify(out, null, 2) + "\n");
  return dst;
}

function main() {
  console.log("Exporting ABIs to coordination/agent-coord/interfaces/contracts_abi/");
  console.log();
  let updated = 0;
  let unchanged = 0;
  for (const name of PROD_CONTRACTS) {
    const a = loadArtifact(name);
    const dst = path.join(
      repoRoot(),
      "pwm-team", "coordination", "agent-coord", "interfaces", "contracts_abi",
      `${name}.json`
    );
    let prevContent = "";
    if (fs.existsSync(dst)) prevContent = fs.readFileSync(dst, "utf8");
    writeInterface(name, a);
    const newContent = fs.readFileSync(dst, "utf8");
    if (prevContent === newContent) {
      console.log(`  - ${name}: unchanged`);
      unchanged++;
    } else if (prevContent === "") {
      console.log(`  + ${name}: created`);
      updated++;
    } else {
      console.log(`  ~ ${name}: updated`);
      updated++;
    }
  }
  console.log();
  console.log(`Updated/created: ${updated}`);
  console.log(`Unchanged:       ${unchanged}`);
  if (updated > 0) {
    console.log();
    console.log("Don't forget: `git add pwm-team/coordination/agent-coord/interfaces/contracts_abi/` " +
                "and commit, so other agents see the new ABIs.");
  }
}

if (require.main === module) {
  main();
}
module.exports = { main };
