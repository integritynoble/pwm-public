// Mainnet deployment — gated. Reuses deploy/testnet.js main() which routes to
// the "mainnet" slot when hre.network.name === "mainnet". Do NOT run this until
// (a) both audit firms have signed off, and (b) the 3-of-5 multisig owns the
// initial admin key. Set PWM_MAINNET_CONFIRM=1 to bypass the safety guard.

const hre = require("hardhat");
const { main } = require("./testnet");

(async () => {
  if (hre.network.name !== "mainnet") {
    console.error(`Refusing to run mainnet.js on network='${hre.network.name}'. Use --network mainnet.`);
    process.exitCode = 1; return;
  }
  if (process.env.PWM_MAINNET_CONFIRM !== "1") {
    console.error("Refusing to deploy to mainnet without PWM_MAINNET_CONFIRM=1 in env.");
    process.exitCode = 1; return;
  }
  await main();
})();
