require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      viaIR: true,
    },
  },
  networks: {
    hardhat: {
      // Per-account balance large enough to fund Zeno emission tests where a
      // single mintFor can move millions of "PWM" (native) into reward pools.
      accounts: { count: 20, accountsBalance: "1000000000000000000000000000" }, // 1e9 ETH
    },
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 11155111,
    },
    // --- L2 mainnets (cheap gas, same Solidity) ---
    base: {
      url: process.env.BASE_RPC_URL || "https://mainnet.base.org",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 8453,
    },
    arbitrum: {
      url: process.env.ARB_RPC_URL || "https://arb1.arbitrum.io/rpc",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 42161,
    },
    optimism: {
      url: process.env.OP_RPC_URL || "https://mainnet.optimism.io",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 10,
    },
    // --- L2 testnets (free) ---
    baseSepolia: {
      url: process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 84532,
    },
    arbSepolia: {
      url: process.env.ARB_SEPOLIA_RPC_URL || "https://sepolia-rollup.arbitrum.io/rpc",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 421614,
    },
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    artifacts: "./artifacts",
    cache: "./cache",
  },
  // Block-explorer keys for `npx hardhat verify` and the bundled
  // scripts/verify-all.js task. Set BASESCAN_API_KEY for Base L2 verification
  // (works on both Base mainnet and Base Sepolia per Etherscan v2 unified API),
  // ETHERSCAN_API_KEY for Ethereum L1 / Sepolia, ARBISCAN_API_KEY for
  // Arbitrum, OPTIMISTIC_ETHERSCAN_API_KEY for Optimism.
  etherscan: {
    apiKey: {
      mainnet:     process.env.ETHERSCAN_API_KEY    || "",
      sepolia:     process.env.ETHERSCAN_API_KEY    || "",
      base:        process.env.BASESCAN_API_KEY     || "",
      baseSepolia: process.env.BASESCAN_API_KEY     || "",
      arbitrumOne: process.env.ARBISCAN_API_KEY     || "",
      arbSepolia:  process.env.ARBISCAN_API_KEY     || "",
      optimisticEthereum: process.env.OPTIMISTIC_ETHERSCAN_API_KEY || "",
    },
    customChains: [
      {
        network: "base",
        chainId: 8453,
        urls: { apiURL: "https://api.basescan.org/api", browserURL: "https://basescan.org" },
      },
      {
        network: "baseSepolia",
        chainId: 84532,
        urls: { apiURL: "https://api-sepolia.basescan.org/api", browserURL: "https://sepolia.basescan.org" },
      },
    ],
  },
  // STEP_1 PASS advisory (2026-04-28): integration tests timed out on first
  // cold-cache run (Mocha default 40 s) on a slower verifier. Bumping the
  // global timeout to 120 s makes verification deterministic on first run
  // while staying low enough to fail fast on a real hang.
  mocha: {
    timeout: 120_000,
  },
};
