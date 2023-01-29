# contracts

Main repo for Game7 contracts

## Contributing

Please if you want to contribute in the project, do the PR taking or creating a issue and then aim the PR for `develop` not main.

The contributing guide is in progress...

## Setup

### Using Python and [eth-brownie](https://github.com/eth-brownie/brownie)

First, set up a Python3 environment:

- Check if you have Python3 installed on your system: `python3 --version`.
- If the above command errors out, you need to install Python3. You can find instructions for how to
do this at https://python.org.
- Create a Python virtual environment in the root of this directory: `python3 -m venv .game7`
- Activate the virtual environment: `source .game7/bin/activate` (when you are finished working in this
code base, you can deactivate the virtual environment using the `deactivate` command).
- Install the `game7ctl` package: `pip install -e game7ctl/`

Following these steps will make the `game7ctl` command available in your shell. You can use this command-line
tool to deploy and interact with the smart contracts in this repository. For more details:

```
game7ctl --help
```

#### Development

To compile the smart contracts using `brownie`, run the following command from the project root directory:

```
brownie compile
```

To set up a *development* environment, you have to also install the developer dependencies using:

```
pip install -e "game7ctl/[dev]"
```

You can then run Python tests by invoking:

```
bash game7ctl/test.sh
```

If you make a change to any of the smart contracts in the [`contracts/`](./contracts/) directory, you
can regenerate the Python interface to that contract using:

```
moonworm generate-brownie -p . -o game7ctl/game7ctl -n $CONTRACT_NAME
```

For example, after modifying `InventoryFacet`, you would run:

```
moonworm generate-brownie -p . -o game7ctl/game7ctl -n InventoryFacet
```

If you want to register your contract for automatic regeneration, please add it to the `IMPORTANT_CONTRACTS` array in
[./game7ctl/regen.bash](`regen.bash`).

- - -

## Deploying contracts

### `game7ctl`

Once you have set up `game7ctl`, you can use it to deploy the contracts in this repository. For example,
to deploy the Inventory contract as a Diamond proxy, you would use the `game7ctl core inventory-gogogo` command.

To see all the parameters you can pass in the deployment, run:

```
$ game7ctl core inventory-gogogo --help
usage: game7ctl inventory-gogogo [-h] --network NETWORK [--address ADDRESS] --sender SENDER [--password PASSWORD] [--gas-price GAS_PRICE] [--max-fee-per-gas MAX_FEE_PER_GAS]
                                 [--max-priority-fee-per-gas MAX_PRIORITY_FEE_PER_GAS] [--confirmations CONFIRMATIONS] [--nonce NONCE] [--value VALUE] [--verbose] --admin-terminus-address
                                 ADMIN_TERMINUS_ADDRESS --admin-terminus-pool-id ADMIN_TERMINUS_POOL_ID --subject-erc721-address SUBJECT_ERC721_ADDRESS
                                 [--diamond-cut-address DIAMOND_CUT_ADDRESS] [--diamond-address DIAMOND_ADDRESS] [--diamond-loupe-address DIAMOND_LOUPE_ADDRESS]
                                 [--ownership-address OWNERSHIP_ADDRESS] [--inventory-facet-address INVENTORY_FACET_ADDRESS] [-o OUTFILE]

Deploy Inventory diamond contract

options:
  -h, --help            show this help message and exit
  --network NETWORK     Name of brownie network to connect to
  --address ADDRESS     Address of deployed contract to connect to
  --sender SENDER       Path to keystore file for transaction sender
  --password PASSWORD   Password to keystore file (if you do not provide it, you will be prompted for it)
  --gas-price GAS_PRICE
                        Gas price at which to submit transaction
  --max-fee-per-gas MAX_FEE_PER_GAS
                        Max fee per gas for EIP1559 transactions
  --max-priority-fee-per-gas MAX_PRIORITY_FEE_PER_GAS
                        Max priority fee per gas for EIP1559 transactions
  --confirmations CONFIRMATIONS
                        Number of confirmations to await before considering a transaction completed
  --nonce NONCE         Nonce for the transaction (optional)
  --value VALUE         Value of the transaction in wei(optional)
  --verbose             Print verbose output
  --admin-terminus-address ADMIN_TERMINUS_ADDRESS
                        Address of Terminus contract defining access control for this GardenOfForkingPaths contract
  --admin-terminus-pool-id ADMIN_TERMINUS_POOL_ID
                        Pool ID of Terminus pool for administrators of this GardenOfForkingPaths contract
  --subject-erc721-address SUBJECT_ERC721_ADDRESS
                        Address of ERC721 contract that the Inventory modifies
  --diamond-cut-address DIAMOND_CUT_ADDRESS
                        Address to deployed DiamondCutFacet. If provided, this command skips deployment of a new DiamondCutFacet.
  --diamond-address DIAMOND_ADDRESS
                        Address to deployed Diamond contract. If provided, this command skips deployment of a new Diamond contract and simply mounts the required facets onto the existing
                        Diamond contract. Assumes that there is no collision of selectors.
  --diamond-loupe-address DIAMOND_LOUPE_ADDRESS
                        Address to deployed DiamondLoupeFacet. If provided, this command skips deployment of a new DiamondLoupeFacet. It mounts the existing DiamondLoupeFacet onto the Diamond.
  --ownership-address OWNERSHIP_ADDRESS
                        Address to deployed OwnershipFacet. If provided, this command skips deployment of a new OwnershipFacet. It mounts the existing OwnershipFacet onto the Diamond.
  --inventory-facet-address INVENTORY_FACET_ADDRESS
                        Address to deployed InventoryFacet. If provided, this command skips deployment of a new InventoryFacet. It mounts the existing InventoryFacet onto the Diamond.
  -o OUTFILE, --outfile OUTFILE
                        (Optional) file to write deployed addresses to
```

#### Notes on arguments

##### `--network`

`--network` should be a `brownie` network. You can add networks to `brownie` using the `brownie networks add` command.

For example, to add a new Polygon RPC endpoint, you would run:

```
brownie networks add Polygon $NETWORK_NAME host=$JSONRPC_URL chainid=137 explorer=https://api.polygonscan.com/api multicall2=0xc8E51042792d7405184DfCa245F2d27B94D013b6
```

The only keys which are not optional are `chainid` and `host`.

Then, you could pass `--network $NETWORK_NAME` as an argument to `game7ctl core inventory-gogogo`.

##### `--sender`

The CLI says that `--sender` should be a keystore file, but it can also be a `brownie account`. To import
an existing Ethereum account into `brownie`, use:

```
brownie accounts new $ACCOUNT_NAME
```

This will prompt you for the account private key and a password with which to encrypt the account on disk.

Then you can pass `--sender $ACCOUNT_NAME` to `game7ctl`.

The preferred way of using `--sender` is still by passing a keystore file.

`brownie` will always prompt you to unlock the account with a password.
