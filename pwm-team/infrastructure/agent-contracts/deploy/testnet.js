// PWM M1.1 deployment script
//
// Deploys the 7 core contracts in dependency order and wires every
// cross-contract address via each contract's governance setters.
//
// Run locally:   npx hardhat run deploy/testnet.js
// Run on sepolia: npx hardhat run deploy/testnet.js --network sepolia
//   (requires SEPOLIA_RPC_URL and DEPLOYER_PRIVATE_KEY in .env)
//
// Writes the deployed addresses to addresses.json. For local/in-process
// hardhat runs, writes under key "local" and leaves "testnet" untouched.

const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const { ethers, network } = hre;
  const [deployer, f1, f2, f3, f4] = await ethers.getSigners();
  console.log(`Network: ${network.name} (chainId=${network.config.chainId ?? "n/a"})`);
  console.log(`Deployer: ${deployer.address}`);

  // Founders for the 3-of-5 multisig. For live testnet, override via
  // FOUNDER_ADDRESSES env var (comma-separated). Otherwise use first 5 signers.
  let founders;
  if (process.env.FOUNDER_ADDRESSES) {
    founders = process.env.FOUNDER_ADDRESSES.split(",").map((s) => s.trim());
    if (founders.length !== 5) throw new Error("FOUNDER_ADDRESSES must list 5 addresses");
  } else {
    founders = [deployer.address, f1?.address, f2?.address, f3?.address, f4?.address]
      .filter(Boolean);
    if (founders.length !== 5) {
      throw new Error("Need 5 signer accounts or FOUNDER_ADDRESSES env var");
    }
  }
  console.log("Founders:", founders);

  // 1. PWMGovernance — founders hardcoded at deploy; later contracts point back
  //    at the *deployer* as governance for wiring, then governance handoff can
  //    be performed via setGovernance() once multisig is ready to operate.
  console.log("\nDeploying PWMGovernance…");
  const Governance = await ethers.getContractFactory("PWMGovernance");
  const governance = await Governance.deploy(founders);
  await governance.waitForDeployment();
  const govAddr = await governance.getAddress();
  console.log("  PWMGovernance:", govAddr);

  const adminAddr = deployer.address; // initial admin for setters (reassign to multisig later)

  console.log("\nDeploying PWMRegistry…");
  const Registry = await ethers.getContractFactory("PWMRegistry");
  const registry = await Registry.deploy();
  await registry.waitForDeployment();
  const registryAddr = await registry.getAddress();
  console.log("  PWMRegistry:", registryAddr);

  console.log("\nDeploying PWMTreasury…");
  const Treasury = await ethers.getContractFactory("PWMTreasury");
  const treasury = await Treasury.deploy(adminAddr);
  await treasury.waitForDeployment();
  const treasuryAddr = await treasury.getAddress();
  console.log("  PWMTreasury:", treasuryAddr);

  console.log("\nDeploying PWMReward…");
  const Reward = await ethers.getContractFactory("PWMReward");
  const reward = await Reward.deploy(adminAddr);
  await reward.waitForDeployment();
  const rewardAddr = await reward.getAddress();
  console.log("  PWMReward:", rewardAddr);

  console.log("\nDeploying PWMStaking…");
  const Staking = await ethers.getContractFactory("PWMStaking");
  const staking = await Staking.deploy(adminAddr);
  await staking.waitForDeployment();
  const stakingAddr = await staking.getAddress();
  console.log("  PWMStaking:", stakingAddr);

  console.log("\nDeploying PWMCertificate…");
  const Certificate = await ethers.getContractFactory("PWMCertificate");
  const certificate = await Certificate.deploy(adminAddr);
  await certificate.waitForDeployment();
  const certAddr = await certificate.getAddress();
  console.log("  PWMCertificate:", certAddr);

  console.log("\nDeploying PWMMinting…");
  const Minting = await ethers.getContractFactory("PWMMinting");
  const minting = await Minting.deploy(adminAddr);
  await minting.waitForDeployment();
  const mintingAddr = await minting.getAddress();
  console.log("  PWMMinting:", mintingAddr);

  // ----- cross-contract wiring -----
  // Wiring is done while admin == deployer because each setX() requires
  // the current governance to call it. After wiring, hand off admin to
  // PWMGovernance.
  console.log("\nWiring addresses…");
  await (await reward.setCertificate(certAddr)).wait();
  await (await reward.setStaking(stakingAddr)).wait();
  await (await reward.setMinting(mintingAddr)).wait();
  await (await reward.setTreasury(treasuryAddr)).wait();
  await (await treasury.setReward(rewardAddr)).wait();
  await (await staking.setReward(rewardAddr)).wait();
  await (await certificate.setRegistry(registryAddr)).wait();
  await (await certificate.setReward(rewardAddr)).wait();
  await (await certificate.setMinting(mintingAddr)).wait();
  await (await minting.setCertificate(certAddr)).wait();
  await (await minting.setReward(rewardAddr)).wait();
  console.log("  wiring complete.");

  // ----- governance handoff -----
  // CRITICAL: after wiring is done, transfer admin from the deployer to
  // PWMGovernance. Without this step, all 5 admin contracts remain
  // controlled by the deployer's single key — a single-key root for the
  // entire protocol. Set PWM_SKIP_GOVERNANCE_HANDOFF=1 only for local
  // hardhat testing where you need the deployer as admin for further calls.
  if (process.env.PWM_SKIP_GOVERNANCE_HANDOFF === "1") {
    console.log("\nSkipping governance handoff (PWM_SKIP_GOVERNANCE_HANDOFF=1).");
    console.log("  ⚠ admin remains the deployer — DO NOT do this on mainnet.");
  } else {
    console.log("\nHanding off admin to PWMGovernance…");
    await (await reward.setGovernance(govAddr)).wait();
    console.log("  ✓ PWMReward.governance =", govAddr);
    await (await staking.setGovernance(govAddr)).wait();
    console.log("  ✓ PWMStaking.governance =", govAddr);
    await (await certificate.setGovernance(govAddr)).wait();
    console.log("  ✓ PWMCertificate.governance =", govAddr);
    await (await minting.setGovernance(govAddr)).wait();
    console.log("  ✓ PWMMinting.governance =", govAddr);
    await (await treasury.setGovernance(govAddr)).wait();
    console.log("  ✓ PWMTreasury.governance =", govAddr);
    console.log("  governance handoff complete — admin is now PWMGovernance.");
  }

  // ----- persist addresses -----
  const addressesPath = path.join(__dirname, "..", "addresses.json");
  const current = JSON.parse(fs.readFileSync(addressesPath, "utf8"));
  const record = {
    network: network.name,
    chainId: network.config.chainId ?? null,
    PWMGovernance:  govAddr,
    PWMRegistry:    registryAddr,
    PWMTreasury:    treasuryAddr,
    PWMReward:      rewardAddr,
    PWMStaking:     stakingAddr,
    PWMCertificate: certAddr,
    PWMMinting:     mintingAddr,
    deployedAt:     new Date().toISOString(),
    deployer:       deployer.address,
    founders,
  };

  // Route by network: sepolia writes "testnet", mainnet writes "mainnet",
  // anything else writes "local". Never overwrite a populated slot implicitly —
  // require PWM_ALLOW_OVERWRITE=1 to replace existing real addresses.
  let slot;
  if (network.name === "sepolia") slot = "testnet";
  else if (network.name === "mainnet") slot = "mainnet";
  else if (network.name === "base") slot = "base";
  else if (network.name === "arbitrum") slot = "arbitrum";
  else if (network.name === "optimism") slot = "optimism";
  else if (network.name === "baseSepolia") slot = "baseSepolia";
  else if (network.name === "arbSepolia") slot = "arbSepolia";
  else slot = "local";

  const existing = current[slot] || {};
  const hasReal = Object.values(existing).some(
    (v) => typeof v === "string" && /^0x[0-9a-fA-F]+$/.test(v) && BigInt(v) !== 0n
  );
  if (hasReal && process.env.PWM_ALLOW_OVERWRITE !== "1") {
    console.warn(
      `\nRefusing to overwrite populated addresses.json[${slot}] without PWM_ALLOW_OVERWRITE=1.`
    );
    console.warn("Printing deployment record only:");
    console.warn(JSON.stringify(record, null, 2));
    return record;
  }

  current[slot] = record;
  fs.writeFileSync(addressesPath, JSON.stringify(current, null, 2) + "\n");
  console.log(`\nWrote addresses.json[${slot}].`);
  return record;
}

if (require.main === module) {
  main().catch((err) => {
    console.error(err);
    process.exitCode = 1;
  });
}

module.exports = { main };
