// Extract ABI + bytecode for each PWM contract and publish them into the
// coordination/interfaces/contracts_abi/ directory consumed by downstream agents.
//
// Usage:  npx hardhat run scripts/publish_abi.js

const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

const CONTRACTS = [
  "PWMRegistry",
  "PWMMinting",
  "PWMStaking",
  "PWMCertificate",
  "PWMReward",
  "PWMTreasury",
  "PWMGovernance",
];

async function main() {
  await hre.run("compile");
  const root = path.resolve(__dirname, "..");
  const artifactsDir = path.join(root, "artifacts", "contracts");
  const destDir = path.resolve(
    root, "..", "..", "coordination", "agent-coord", "interfaces", "contracts_abi"
  );
  fs.mkdirSync(destDir, { recursive: true });

  const manifest = {};
  for (const name of CONTRACTS) {
    const src = path.join(artifactsDir, `${name}.sol`, `${name}.json`);
    if (!fs.existsSync(src)) throw new Error(`Missing artifact for ${name}: ${src}`);
    const artifact = JSON.parse(fs.readFileSync(src, "utf8"));
    const out = {
      contractName: artifact.contractName,
      abi: artifact.abi,
      bytecode: artifact.bytecode,
      deployedBytecode: artifact.deployedBytecode,
    };
    fs.writeFileSync(path.join(destDir, `${name}.json`), JSON.stringify(out, null, 2) + "\n");
    manifest[name] = {
      functions: artifact.abi.filter((x) => x.type === "function").length,
      events: artifact.abi.filter((x) => x.type === "event").length,
    };
    console.log(`  wrote ${path.join(destDir, name + ".json")}`);
  }

  // Also copy addresses.json alongside for consumer convenience.
  const addrSrc = path.join(root, "addresses.json");
  const addrDest = path.resolve(destDir, "..", "addresses.json");
  fs.copyFileSync(addrSrc, addrDest);
  console.log(`  wrote ${addrDest}`);

  console.log("\nABI manifest:", JSON.stringify(manifest, null, 2));
}

main().catch((e) => { console.error(e); process.exitCode = 1; });
