// L2 deployment — Base, Arbitrum, or Optimism.
// Same 7 contracts, same wiring, much cheaper gas (~$1-$10 total).
//
// Usage:
//   npx hardhat run deploy/l2.js --network base
//   npx hardhat run deploy/l2.js --network arbitrum
//   npx hardhat run deploy/l2.js --network optimism
//
// Testnets (free):
//   npx hardhat run deploy/l2.js --network baseSepolia
//   npx hardhat run deploy/l2.js --network arbSepolia
//
// Requires DEPLOYER_PRIVATE_KEY in .env (same key works on all EVM chains).

const hre = require("hardhat");
const { main } = require("./testnet");

const L2_NETWORKS = [
  "base", "arbitrum", "optimism",
  "baseSepolia", "arbSepolia",
];

(async () => {
  if (!L2_NETWORKS.includes(hre.network.name)) {
    console.error(
      `l2.js is for L2 networks (${L2_NETWORKS.join(", ")}), ` +
      `not '${hre.network.name}'. Use deploy/testnet.js for Sepolia ` +
      `or deploy/mainnet.js for Ethereum mainnet.`
    );
    process.exitCode = 1;
    return;
  }
  console.log(`=== PWM L2 Deploy on ${hre.network.name} (chainId=${hre.network.config.chainId}) ===\n`);
  await main();
})();
