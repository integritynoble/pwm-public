// Quick balance checker for the Sepolia deployer wallet.
// Usage:  node scripts/check_balance.js
// Reads SEPOLIA_RPC_URL and DEPLOYER_ADDRESS (or derives from DEPLOYER_PRIVATE_KEY) from .env.

require("dotenv").config();
const { JsonRpcProvider, Wallet, formatEther } = require("ethers");

async function main() {
  const rpc = process.env.SEPOLIA_RPC_URL;
  if (!rpc) throw new Error("SEPOLIA_RPC_URL not set in .env");

  let address = process.env.DEPLOYER_ADDRESS;
  if (!address) {
    if (!process.env.DEPLOYER_PRIVATE_KEY) {
      throw new Error("Neither DEPLOYER_ADDRESS nor DEPLOYER_PRIVATE_KEY set");
    }
    address = new Wallet(process.env.DEPLOYER_PRIVATE_KEY).address;
  }

  const provider = new JsonRpcProvider(rpc);
  const [chainId, block, balance] = await Promise.all([
    provider.getNetwork().then((n) => n.chainId),
    provider.getBlockNumber(),
    provider.getBalance(address),
  ]);

  console.log("RPC        :", rpc);
  console.log("ChainId    :", chainId.toString(), chainId === 11155111n ? "(Sepolia)" : "(UNEXPECTED)");
  console.log("Block      :", block);
  console.log("Address    :", address);
  console.log("Balance    :", formatEther(balance), "ETH");
  if (balance === 0n) {
    console.log("\nWallet is empty. Drip from a faucet:");
    console.log("  https://sepoliafaucet.com            (0.5 / day, Alchemy login)");
    console.log("  https://cloud.google.com/application/web3/faucet/ethereum/sepolia");
    console.log("  https://faucets.chain.link           (GitHub verify)");
    console.log("  https://sepolia-faucet.pk910.de      (PoW, no signup)");
  } else {
    console.log("\nFunded — ready for deploy:");
    console.log("  npx hardhat run deploy/testnet.js --network sepolia");
  }
}

main().catch((e) => { console.error(e.message || e); process.exitCode = 1; });
