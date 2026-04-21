/**
 * Register CASSI (#003) and CACTI (#004) L1/L2/L3 artifacts on PWMRegistry.
 *
 * Usage:
 *   DEPLOYER_PRIVATE_KEY=0x... SEPOLIA_RPC_URL=https://... \
 *     npx hardhat run scripts/register_genesis.js --network sepolia
 *
 * This makes 6 on-chain calls:
 *   L1-003 (parent=0x0), L1-004 (parent=0x0)
 *   L2-003 (parent=L1-003 hash), L2-004 (parent=L1-004 hash)
 *   L3-003 (parent=L2-003 hash), L3-004 (parent=L2-004 hash)
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

async function main() {
  const [signer] = await ethers.getSigners();
  console.log("Signer:", signer.address);
  console.log("Balance:", ethers.formatEther(await ethers.provider.getBalance(signer.address)), "ETH");

  // Load addresses
  const addrsPath = path.join(__dirname, "..", "addresses.json");
  const addrs = JSON.parse(fs.readFileSync(addrsPath, "utf8"));
  const network = hre.network.name === "sepolia" ? "testnet" : "local";
  const registryAddr = addrs[network].PWMRegistry;
  console.log("PWMRegistry:", registryAddr, `(${network})`);

  // Get contract
  const Registry = await ethers.getContractAt("PWMRegistry", registryAddr);

  // Compute hashes for all 6 artifacts
  const genesisDir = path.join(__dirname, "..", "..", "..", "pwm_product", "genesis");
  const artifacts = [
    { id: "L1-003", layer: 1, file: "l1/L1-003.json", parent: null },
    { id: "L1-004", layer: 1, file: "l1/L1-004.json", parent: null },
    { id: "L2-003", layer: 2, file: "l2/L2-003.json", parent: "L1-003" },
    { id: "L2-004", layer: 2, file: "l2/L2-004.json", parent: "L1-004" },
    { id: "L3-003", layer: 3, file: "l3/L3-003.json", parent: "L2-003" },
    { id: "L3-004", layer: 3, file: "l3/L3-004.json", parent: "L2-004" },
  ];

  // Compute all hashes first
  const hashes = {};
  for (const art of artifacts) {
    const filePath = path.join(genesisDir, art.file);
    const content = fs.readFileSync(filePath);
    const hash = "0x" + crypto.createHash("sha256").update(content).digest("hex");
    hashes[art.id] = hash;
    console.log(`  ${art.id}: ${hash.slice(0, 20)}...`);
  }

  // Register in order (L1 first, then L2, then L3)
  const ZERO = "0x" + "0".repeat(64);
  const results = [];

  for (const art of artifacts) {
    const hash = hashes[art.id];
    const parentHash = art.parent ? hashes[art.parent] : ZERO;

    // Check if already registered
    const existing = await Registry.getArtifact(hash);
    if (existing[3] > 0n) { // timestamp > 0
      console.log(`  ${art.id}: already registered, skipping`);
      results.push({ id: art.id, status: "already_registered", hash });
      continue;
    }

    console.log(`  Registering ${art.id} (layer=${art.layer}, parent=${art.parent || "none"})...`);
    const tx = await Registry.register(hash, parentHash, art.layer, signer.address);
    console.log(`    tx: ${tx.hash}`);
    const receipt = await tx.wait();
    console.log(`    confirmed in block ${receipt.blockNumber}, gas: ${receipt.gasUsed.toString()}`);
    results.push({
      id: art.id,
      status: "registered",
      hash,
      tx: tx.hash,
      block: receipt.blockNumber,
      gas: receipt.gasUsed.toString(),
    });
  }

  // Summary
  console.log("\n=== Registration Summary ===");
  for (const r of results) {
    console.log(`  ${r.id}: ${r.status} (hash=${r.hash.slice(0, 20)}...)${r.tx ? " tx=" + r.tx.slice(0, 20) + "..." : ""}`);
  }

  // Verify all registered
  console.log("\n=== Verification ===");
  for (const art of artifacts) {
    const result = await Registry.getArtifact(hashes[art.id]);
    const registered = result[3] > 0n;
    console.log(`  ${art.id}: ${registered ? "OK" : "FAIL"}`);
  }

  // Write results to file for record-keeping
  const outputPath = path.join(__dirname, "..", "genesis_registration_results.json");
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  console.log(`\nResults written to ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
