#!/usr/bin/env bash

# Expects a Python environment to be active in which `dao` has been installed for development.
# You can set up the local copy of `dao` for development using:
# pip install -e .[dev]

set -e

SCRIPT_DIR="$(dirname $(realpath $0))"

usage() {
    echo "Usage: $0"
    echo
    echo "Regenerates Python interfaces to all important smart contracts"
}

if [ "$1" = "-h" ] || [ "$1" = "--help" ]
then
    usage
    exit 2
fi

IMPORTANT_CONTRACTS=( \
    "Diamond" \
    "DiamondCutFacet" \
    "DiamondLoupeFacet" \
    "InventoryFacet" \
    "MockERC20" \
    "MockERC721" \
    "MockTerminus" \
    "OwnershipFacet" \
)

cd $SCRIPT_DIR

for contract_name in "${IMPORTANT_CONTRACTS[@]}"
do
    echo "Regenerating Python interface for: $contract_name"
    moonworm generate-brownie -p .. -o game7ctl/ -n "$contract_name"
done
