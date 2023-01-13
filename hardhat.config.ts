/* eslint-disable node/no-unpublished-import */
import { config as dotEnvConfig } from "dotenv";
import { HardhatUserConfig, task } from "hardhat/config";
import "@nomiclabs/hardhat-waffle";
import "@nomiclabs/hardhat-etherscan";
import "@typechain/hardhat";
import "hardhat-gas-reporter";
import "solidity-coverage";
import "hardhat-docgen";
import "hardhat-tracer";
import "@tenderly/hardhat-tenderly";
import "@nomicfoundation/hardhat-chai-matchers";
import "@nomiclabs/hardhat-ethers";
import "hardhat-storage-layout";
import "hardhat-finder";

dotEnvConfig();

function getWallet(): Array<string> {
  return process.env.DEPLOYER_WALLET_PRIVATE_KEY !== undefined
    ? [process.env.DEPLOYER_WALLET_PRIVATE_KEY]
    : [];
}

// This is a sample Hardhat task. To learn how to create your own go to
// https://hardhat.org/guides/create-task.html
task("accounts", "Prints the list of accounts", async (taskArgs, hre) => {
  const accounts = await hre.ethers.getSigners();

  for (const account of accounts) {
    console.log(account.address);
  }
});

task("storage-layout", "Prints the storage layout", async (_, hre) => {
  await hre.storageLayout.export();
});

const config: HardhatUserConfig = {
  solidity: {
    version: process.env.SOLC_VERSION || "0.8.17",
    settings: {
      optimizer: {
        enabled:
          (process.env.SOLIDITY_OPTIMIZER &&
            "true" === process.env.SOLIDITY_OPTIMIZER.toLowerCase()) ||
          false,
        runs:
          (process.env.SOLIDITY_OPTIMIZER_RUNS &&
            Boolean(parseInt(process.env.SOLIDITY_OPTIMIZER_RUNS)) &&
            parseInt(process.env.SOLIDITY_OPTIMIZER_RUNS)) ||
          200,
      },
      outputSelection: {
        "*": {
          "*": ["storageLayout"],
        },
      },
    },
  },
  docgen: {
    path: "./docs",
    clear: true,
    runOnCompile: false,
  },
  gasReporter: {
    enabled:
      (process.env.REPORT_GAS &&
        "true" === process.env.REPORT_GAS.toLowerCase()) ||
      false,
    coinmarketcap: process.env.COINMARKETCAP_API_KEY || "",
    gasPriceApi:
      process.env.GAS_PRICE_API ||
      "https://api.etherscan.io/api?module=proxy&action=eth_gasPrice",
    token: "ETH",
    currency: "USD",
  },
  networks: {
    hardhat: {
      allowUnlimitedContractSize:
        (process.env.ALLOW_UNLIMITED_CONTRACT_SIZE &&
          "true" === process.env.ALLOW_UNLIMITED_CONTRACT_SIZE.toLowerCase()) ||
        false,
    },
    custom: {
      url: process.env.CUSTOM_NETWORK_URL || "",
      accounts: {
        count:
          (process.env.CUSTOM_NETWORK_ACCOUNTS_COUNT &&
            Boolean(parseInt(process.env.CUSTOM_NETWORK_ACCOUNTS_COUNT)) &&
            parseInt(process.env.CUSTOM_NETWORK_ACCOUNTS_COUNT)) ||
          0,
        mnemonic: process.env.CUSTOM_NETWORK_ACCOUNTS_MNEMONIC || "",
        path: process.env.CUSTOM_NETWORK_ACCOUNTS_PATH || "",
      },
    },
    // TODO: Check this networks for the phase 2
    // arbitrumTestnet: {
    //     url: process.env.ARBITRUM_TESTNET_RPC_URL || '',
    //     accounts: getWallet(),
    // },
    // avalancheFujiTestnet: {
    //     url: process.env.AVALANCHE_FUJI_TESTNET_RPC_URL || '',
    //     accounts: getWallet(),
    // },
    // bscTestnet: {
    //     url: process.env.BSC_TESTNET_RPC_URL || '',
    //     accounts: getWallet(),
    // },
    goerli: {
      url: process.env.GOERLI_RPC_URL || "",
      accounts: getWallet(),
    },
    polygonMumbai: {
      url: process.env.POLYGON_MUMBAI_RPC_URL || "",
      accounts: getWallet(),
    },
    mantleTestNet: {
      url: process.env.MANTLE_TESTNET_RPC_URL || "",
      accounts: getWallet(),
    },
  },
  etherscan: {
    apiKey: {
      // arbitrumTestnet: process.env.ARBISCAN_API_KEY || '',
      // avalancheFujiTestnet: process.env.SNOWTRACE_API_KEY || '',
      // bscTestnet: process.env.BSCSCAN_API_KEY || '',
      goerli: process.env.ETHERSCAN_API_KEY || "",
      polygonMumbai: process.env.POLYGONSCAN_API_KEY || "",
      mantleTestNet: process.env.MANTLESCAN_API_KEY || "",
      custom: process.env.CUSTOM_EXPLORER_API_KEY || "",
    },
    customChains: [
      {
        network: "custom",
        chainId:
          (process.env.CUSTOM_NETWORK_CHAIN_ID &&
            Boolean(parseInt(process.env.CUSTOM_NETWORK_CHAIN_ID)) &&
            parseInt(process.env.CUSTOM_NETWORK_CHAIN_ID)) ||
          0,
        urls: {
          apiURL: process.env.CUSTOM_NETWORK_API_URL || "",
          browserURL: process.env.CUSTOM_NETWORK_BROWSER_URL || "",
        },
      },
    ],
  },
};

export default config;
