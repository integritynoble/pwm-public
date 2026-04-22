/**
 * ⚠️  DEPRECATED — use scripts/register_genesis.py instead  ⚠️
 *
 * This JS implementation cannot produce hashes that match what
 * `pwm-node mine` computes as benchmarkHash. JavaScript's JSON.stringify
 * loses the int/float distinction (26.0 → "26"), while Python's
 * json.dumps preserves it (26.0 → "26.0"). The two produce different
 * canonical-JSON bytes and therefore different keccak256 hashes.
 *
 * Running this script would register artifacts under hashes that the CLI
 * cannot match — every certificate submission would revert with "benchmark
 * not registered". The earlier sha256(file_bytes) form was also wrong.
 *
 * USE INSTEAD:
 *   export PWM_RPC_URL=<your-rpc>
 *   export PWM_PRIVATE_KEY=0x<deployer-key>
 *   python3 scripts/register_genesis.py --network <baseSepolia|base|arbSepolia|arbitrum|optimism|testnet>
 *
 * Register CASSI (#003) and CACTI (#004) L1/L2/L3 artifacts on PWMRegistry.
 *
 * This script is kept for historical reference and for the `--dry-run`
 * plan print only — it BAILS OUT before sending any transaction.
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

// Hashing convention MUST match scripts/register_genesis_sepolia.py and
// pwm-team/infrastructure/agent-cli/pwm_node/commands/mine.py:
//   artifactHash = keccak256(canonical_json(artifact_obj))
// where canonical_json = JSON.stringify with sort_keys=true and compact
// separators ",", ":".
//
// An earlier version of this file used sha256(file_bytes), which does not
// match what `pwm-node mine` computes as benchmarkHash — every CLI-built
// certificate would revert on-chain because the hash wouldn't resolve to a
// registered L3 artifact. See CHECKLIST_EXECUTION_REPORT.md §6b for the
// canonical hash audit.
function canonicalJsonBytes(obj) {
  // Recursively sort object keys to match Python's json.dumps(sort_keys=True).
  const sortKeys = (v) => {
    if (Array.isArray(v)) return v.map(sortKeys);
    if (v !== null && typeof v === "object") {
      return Object.keys(v).sort().reduce((acc, k) => {
        acc[k] = sortKeys(v[k]);
        return acc;
      }, {});
    }
    return v;
  };
  // Compact separators (no spaces) to match separators=(",", ":")
  return Buffer.from(JSON.stringify(sortKeys(obj)), "utf8");
}

function artifactHash(obj) {
  // keccak256 as 0x + 64 hex (ethers does the hex; padding not needed since
  // keccak always produces 32 bytes).
  return ethers.keccak256(canonicalJsonBytes(obj));
}

async function main() {
  console.error("");
  console.error("==================================================================");
  console.error("  This JS register_genesis.js is DEPRECATED.");
  console.error("  Its JSON.stringify-based hash does NOT match what pwm-node mine");
  console.error("  computes; running it would register artifacts that the CLI can't");
  console.error("  reference.");
  console.error("");
  console.error("  Use the Python version instead:");
  console.error("    python3 scripts/register_genesis.py --network <net>");
  console.error("");
  console.error("  Re-run this JS script with PWM_ALLOW_DEPRECATED=1 only if you");
  console.error("  explicitly want the broken behavior (you almost certainly don't).");
  console.error("==================================================================");
  console.error("");
  if (process.env.PWM_ALLOW_DEPRECATED !== "1") {
    process.exitCode = 1;
    return;
  }

  const [signer] = await ethers.getSigners();
  console.log("Signer:", signer.address);
  console.log("Balance:", ethers.formatEther(await ethers.provider.getBalance(signer.address)), "ETH");

  // Load addresses. Route by hardhat network name:
  //   sepolia → testnet, mainnet → mainnet,
  //   base / arbitrum / optimism → same-named slot,
  //   baseSepolia / arbSepolia → same-named slot,
  //   anything else → local.
  const addrsPath = path.join(__dirname, "..", "addresses.json");
  const addrs = JSON.parse(fs.readFileSync(addrsPath, "utf8"));
  const netName = hre.network.name;
  let slot;
  if (netName === "sepolia") slot = "testnet";
  else if (netName === "mainnet") slot = "mainnet";
  else if (["base", "arbitrum", "optimism", "baseSepolia", "arbSepolia"].includes(netName)) slot = netName;
  else slot = "local";
  if (!addrs[slot] || !addrs[slot].PWMRegistry) {
    throw new Error(
      `addresses.json[${slot}].PWMRegistry not set. Run deploy/l2.js first, ` +
      `or pick a different --network.`
    );
  }
  const registryAddr = addrs[slot].PWMRegistry;
  console.log("PWMRegistry:", registryAddr, `(slot: ${slot})`);

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

  // Compute all hashes via keccak256(canonical_json). MUST match the
  // convention used by register_genesis_sepolia.py and pwm-node mine, else
  // certs submitted via the CLI will fail benchmarkHash lookup on-chain.
  const hashes = {};
  for (const art of artifacts) {
    const filePath = path.join(genesisDir, art.file);
    const obj = JSON.parse(fs.readFileSync(filePath, "utf8"));
    const hash = artifactHash(obj);
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
