import argparse
import json
import os
import sys
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from brownie import network

from . import (
    Diamond,
    DiamondCutFacet,
    DiamondLoupeFacet,
    InventoryFacet,
    OwnershipFacet,
    abi,
)

FACETS: Dict[str, Any] = {
    "DiamondCutFacet": DiamondCutFacet,
    "DiamondLoupeFacet": DiamondLoupeFacet,
    "OwnershipFacet": OwnershipFacet,
    "InventoryFacet": InventoryFacet,
}

FACET_INIT_CALLDATA: Dict[str, Callable] = {
    "InventoryFacet": lambda address, *args: InventoryFacet.InventoryFacet(
        address
    ).contract.init.encode_input(*args)
}

DIAMOND_FACET_PRECEDENCE: List[str] = [
    "DiamondCutFacet",
    "OwnershipFacet",
    "DiamondLoupeFacet",
]

FACET_PRECEDENCE: List[str] = [
    "DiamondCutFacet",
    "OwnershipFacet",
    "DiamondLoupeFacet",
]


class EngineFeatures(Enum):
    INVENTORY = "InventoryFacet"


def feature_from_facet_name(facet_name: str) -> Optional[EngineFeatures]:
    try:
        return EngineFeatures(facet_name)
    except ValueError:
        return None


FEATURE_FACETS: Dict[EngineFeatures, List[str]] = {
    EngineFeatures.INVENTORY: ["InventoryFacet"]
}

FEATURE_IGNORES: Dict[EngineFeatures, List[str]] = {
    EngineFeatures.INVENTORY: {"methods": ["init"], "selectors": []}
}

FACET_ACTIONS: Dict[str, int] = {"add": 0, "replace": 1, "remove": 2}

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def facet_cut(
    diamond_address: str,
    facet_name: str,
    facet_address: str,
    action: str,
    transaction_config: Dict[str, Any],
    initializer_address: str = ZERO_ADDRESS,
    ignore_methods: Optional[List[str]] = None,
    ignore_selectors: Optional[List[str]] = None,
    methods: Optional[List[str]] = None,
    selectors: Optional[List[str]] = None,
    feature: Optional[EngineFeatures] = None,
    initializer_args: Optional[List[Any]] = None,
) -> Any:
    """
    Cuts the given facet onto the given Diamond contract.

    Resolves selectors in the precedence order defined by FACET_PRECEDENCE (highest precedence first).
    """
    assert (
        facet_name in FACETS
    ), f"Invalid facet: {facet_name}. Choices: {','.join(FACETS)}."

    assert (
        action in FACET_ACTIONS
    ), f"Invalid cut action: {action}. Choices: {','.join(FACET_ACTIONS)}."

    facet_precedence = FACET_PRECEDENCE
    if feature is not None:
        facet_precedence = DIAMOND_FACET_PRECEDENCE + FEATURE_FACETS[feature]

    if ignore_methods is None:
        ignore_methods = []
    if ignore_selectors is None:
        ignore_selectors = []
    if methods is None:
        methods = []
    if selectors is None:
        selectors = []

    project_dir = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    abis = abi.project_abis(project_dir)

    reserved_selectors: Set[str] = set()
    for facet in facet_precedence:
        facet_abi = abis.get(facet, [])
        if facet == facet_name:
            # Add feature ignores to reserved_selectors then break out of facet iteration
            if feature is not None:
                feature_ignores = FEATURE_IGNORES[feature]
                for item in facet_abi:
                    if (
                        item["type"] == "function"
                        and item["name"] in feature_ignores["methods"]
                    ):
                        reserved_selectors.add(abi.encode_function_signature(item))

                for selector in feature_ignores["selectors"]:
                    reserved_selectors.add(selector)

            break

        for item in facet_abi:
            if item["type"] == "function":
                reserved_selectors.add(abi.encode_function_signature(item))

    facet_function_selectors: List[str] = []
    facet_abi = abis.get(facet_name, [])

    logical_operator = all
    method_predicate = lambda method: method not in ignore_methods
    selector_predicate = (
        lambda selector: selector not in reserved_selectors
        and selector not in ignore_selectors
    )

    if len(methods) > 0 or len(selectors) > 0:
        logical_operator = any
        method_predicate = lambda method: method in methods
        selector_predicate = lambda selector: selector in selectors

    for item in facet_abi:
        if item["type"] == "function":
            item_selector = abi.encode_function_signature(item)
            if logical_operator(
                [method_predicate(item["name"]), selector_predicate(item_selector)]
            ):
                facet_function_selectors.append(item_selector)

    target_address = facet_address
    if FACET_ACTIONS[action] == 2:
        target_address = ZERO_ADDRESS

    diamond_cut_action = [
        target_address,
        FACET_ACTIONS[action],
        facet_function_selectors,
    ]

    diamond = DiamondCutFacet.DiamondCutFacet(diamond_address)
    calldata = b""
    if FACET_INIT_CALLDATA.get(facet_name) is not None:
        if initializer_args is None:
            initializer_args = []
        calldata = FACET_INIT_CALLDATA[facet_name](
            initializer_address, *initializer_args
        )
    transaction = diamond.diamond_cut(
        [diamond_cut_action], initializer_address, calldata, transaction_config
    )
    return transaction


def diamond(
    owner_address: str,
    transaction_config: Dict[str, Any],
    diamond_cut_address: Optional[str] = None,
    diamond_address: Optional[str] = None,
    diamond_loupe_address: Optional[str] = None,
    ownership_address: Optional[str] = None,
    verify_contracts: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Deploy diamond along with all its basic facets and attach those facets to the diamond.

    Return addresses of all the deployed contracts with the contract names as keys.
    """
    result: Dict[str, Any] = {"contracts": {}, "attached": []}

    if diamond_cut_address is None:
        try:
            diamond_cut_facet = DiamondCutFacet.DiamondCutFacet(None)
            diamond_cut_facet.deploy(transaction_config)
        except Exception as e:
            print(e)
            result["error"] = "Failed to deploy DiamondCutFacet"
            return result
        result["contracts"]["DiamondCutFacet"] = diamond_cut_facet.address
    else:
        result["contracts"]["DiamondCutFacet"] = diamond_cut_address
        diamond_cut_facet = DiamondCutFacet.DiamondCutFacet(diamond_cut_address)

    if diamond_address is None:
        try:
            diamond = Diamond.Diamond(None)
            diamond.deploy(owner_address, diamond_cut_facet.address, transaction_config)
        except Exception as e:
            print(e)
            result["error"] = "Failed to deploy Diamond"
            return result
        result["contracts"]["Diamond"] = diamond.address
    else:
        result["contracts"]["Diamond"] = diamond_address
        diamond = Diamond.Diamond(diamond_address)

    if diamond_loupe_address is None:
        try:
            diamond_loupe_facet = DiamondLoupeFacet.DiamondLoupeFacet(None)
            diamond_loupe_facet.deploy(transaction_config)
        except Exception as e:
            print(e)
            result["error"] = "Failed to deploy DiamondLoupeFacet"
            return result
        result["contracts"]["DiamondLoupeFacet"] = diamond_loupe_facet.address
    else:
        result["contracts"]["DiamondLoupeFacet"] = diamond_loupe_address
        diamond_loupe_facet = DiamondLoupeFacet.DiamondLoupeFacet(diamond_loupe_address)

    if ownership_address is None:
        try:
            ownership_facet = OwnershipFacet.OwnershipFacet(None)
            ownership_facet.deploy(transaction_config)
        except Exception as e:
            print(e)
            result["error"] = "Failed to deploy OwnershipFacet"
            return result
        result["contracts"]["OwnershipFacet"] = ownership_facet.address
    else:
        result["contracts"]["OwnershipFacet"] = ownership_address
        ownership_facet = OwnershipFacet.OwnershipFacet(ownership_address)

    try:
        facet_cut(
            diamond.address,
            "DiamondLoupeFacet",
            diamond_loupe_facet.address,
            "add",
            transaction_config,
        )
    except Exception as e:
        print(e)
        result["error"] = "Failed to attach DiamondLoupeFacet"
        return result
    result["attached"].append("DiamondLoupeFacet")

    try:
        facet_cut(
            diamond.address,
            "OwnershipFacet",
            ownership_facet.address,
            "add",
            transaction_config,
        )
    except Exception as e:
        print(e)
        result["error"] = "Failed to attach OwnershipFacet"
        return result
    result["attached"].append("OwnershipFacet")

    if verify_contracts:
        try:
            diamond_cut_facet.verify_contract()
            diamond.verify_contract()
            diamond_loupe_facet.verify_contract()
            ownership_facet.verify_contract()

        except Exception as e:
            print(e)
            result["error"] = "Failed to verify Diamond Facets"
            return result
    result["verified_diamond_facets"] = True
    return result


def systems(
    admin_terminus_address: str,
    admin_terminus_pool_id: int,
    subject_erc721_address: str,
    transaction_config: Dict[str, Any],
    diamond_cut_address: Optional[str] = None,
    diamond_address: Optional[str] = None,
    diamond_loupe_address: Optional[str] = None,
    ownership_address: Optional[str] = None,
    inventory_facet_address: Optional[str] = None,
    verify_contracts: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Deploys an EIP2535 Diamond contract and an InventoryFacet and mounts the InventoryFacet onto the Diamond contract.

    Returns the addresses and attachments.
    """
    deployment_info = diamond(
        owner_address=transaction_config["from"].address,
        transaction_config=transaction_config,
        diamond_cut_address=diamond_cut_address,
        diamond_address=diamond_address,
        diamond_loupe_address=diamond_loupe_address,
        ownership_address=ownership_address,
        verify_contracts=verify_contracts,
    )

    if inventory_facet_address is None:
        inventory_facet = InventoryFacet.InventoryFacet(None)
        inventory_facet.deploy(transaction_config=transaction_config)
    else:
        inventory_facet = InventoryFacet.InventoryFacet(inventory_facet_address)

    if verify_contracts:
        inventory_facet.verify_contract()

    deployment_info["contracts"]["InventoryFacet"] = inventory_facet.address

    facet_cut(
        deployment_info["contracts"]["Diamond"],
        "InventoryFacet",
        inventory_facet.address,
        "add",
        transaction_config,
        initializer_address=inventory_facet.address,
        feature=EngineFeatures.INVENTORY,
        initializer_args=[
            admin_terminus_address,
            admin_terminus_pool_id,
            subject_erc721_address,
        ],
    )
    deployment_info["attached"].append("InventoryFacet")

    return deployment_info


def handle_facet_cut(args: argparse.Namespace) -> None:
    network.connect(args.network)
    diamond_address = args.address
    action = args.action
    facet_name = args.facet_name
    facet_address = args.facet_address
    transaction_config = Diamond.get_transaction_config(args)
    facet_cut(
        diamond_address,
        facet_name,
        facet_address,
        action,
        transaction_config,
        initializer_address=args.initializer_address,
        ignore_methods=args.ignore_methods,
        ignore_selectors=args.ignore_selectors,
        methods=args.methods,
        selectors=args.selectors,
        initializer_args=args.initializer_args,
    )


def handle_systems(args: argparse.Namespace) -> None:
    network.connect(args.network)
    transaction_config = InventoryFacet.get_transaction_config(args)
    result = systems(
        admin_terminus_address=args.admin_terminus_address,
        admin_terminus_pool_id=args.admin_terminus_pool_id,
        subject_erc721_address=args.subject_erc721_address,
        transaction_config=transaction_config,
        diamond_cut_address=args.diamond_cut_address,
        diamond_address=args.diamond_address,
        diamond_loupe_address=args.diamond_loupe_address,
        ownership_address=args.ownership_address,
        inventory_facet_address=args.inventory_facet_address,
        verify_contracts=args.verify_contracts,
    )
    if args.outfile is not None:
        with args.outfile:
            json.dump(result, args.outfile)
    json.dump(result, sys.stdout, indent=4)


def generate_cli():
    parser = argparse.ArgumentParser(
        description="CLI to manage Lootbox contract",
    )
    parser.set_defaults(func=lambda _: parser.print_help())
    subcommands = parser.add_subparsers()

    facet_cut_parser = subcommands.add_parser(
        "facet-cut",
        help="Operate on facets of a Diamond contract",
        description="Operate on facets of a Diamond contract",
    )
    Diamond.add_default_arguments(facet_cut_parser, transact=True)
    facet_cut_parser.add_argument(
        "--facet-name",
        required=True,
        choices=FACETS,
        help="Name of facet to cut into or out of diamond",
    )
    facet_cut_parser.add_argument(
        "--facet-address",
        required=False,
        default=ZERO_ADDRESS,
        help=f"Address of deployed facet (default: {ZERO_ADDRESS})",
    )
    facet_cut_parser.add_argument(
        "--action",
        required=True,
        choices=FACET_ACTIONS,
        help="Diamond cut action to take on entire facet",
    )
    facet_cut_parser.add_argument(
        "--initializer-address",
        default=ZERO_ADDRESS,
        required=True,
        help=f"Address of contract to run as initializer after cut (default: {ZERO_ADDRESS})",
    )
    facet_cut_parser.add_argument(
        "--initializer-args", nargs="*", help="Arguments to initializer"
    )
    facet_cut_parser.add_argument(
        "--ignore-methods",
        nargs="+",
        help="Names of methods to ignore when cutting a facet onto or off of the diamond",
    )
    facet_cut_parser.add_argument(
        "--ignore-selectors",
        nargs="+",
        help="Method selectors to ignore when cutting a facet onto or off of the diamond",
    )
    facet_cut_parser.add_argument(
        "--methods",
        nargs="+",
        help="Names of methods to add (if set, --ignore-methods and --ignore-selectors are not used)",
    )
    facet_cut_parser.add_argument(
        "--selectors",
        nargs="+",
        help="Selectors to add (if set, --ignore-methods and --ignore-selectors are not used)",
    )
    facet_cut_parser.set_defaults(func=handle_facet_cut)

    contracts_parser = subcommands.add_parser(
        "systems",
        description="Deploy G7 diamond contract",
    )
    Diamond.add_default_arguments(contracts_parser, transact=True)
    contracts_parser.add_argument(
        "--verify-contracts",
        action="store_true",
        help="Verify contracts",
    )
    contracts_parser.add_argument(
        "--admin-terminus-address",
        required=True,
        help="Address of Terminus contract defining access control for this GardenOfForkingPaths contract",
    )
    contracts_parser.add_argument(
        "--admin-terminus-pool-id",
        required=True,
        type=int,
        help="Pool ID of Terminus pool for administrators of this GardenOfForkingPaths contract",
    )
    contracts_parser.add_argument(
        "--subject-erc721-address",
        required=True,
        help="Address of ERC721 contract that the Inventory modifies",
    )
    contracts_parser.add_argument(
        "--diamond-cut-address",
        required=False,
        default=None,
        help="Address to deployed DiamondCutFacet. If provided, this command skips deployment of a new DiamondCutFacet.",
    )
    contracts_parser.add_argument(
        "--diamond-address",
        required=False,
        default=None,
        help="Address to deployed Diamond contract. If provided, this command skips deployment of a new Diamond contract and simply mounts the required facets onto the existing Diamond contract. Assumes that there is no collision of selectors.",
    )
    contracts_parser.add_argument(
        "--diamond-loupe-address",
        required=False,
        default=None,
        help="Address to deployed DiamondLoupeFacet. If provided, this command skips deployment of a new DiamondLoupeFacet. It mounts the existing DiamondLoupeFacet onto the Diamond.",
    )
    contracts_parser.add_argument(
        "--ownership-address",
        required=False,
        default=None,
        help="Address to deployed OwnershipFacet. If provided, this command skips deployment of a new OwnershipFacet. It mounts the existing OwnershipFacet onto the Diamond.",
    )
    contracts_parser.add_argument(
        "--inventory-facet-address",
        required=False,
        default=None,
        help="Address to deployed InventoryFacet. If provided, this command skips deployment of a new InventoryFacet. It mounts the existing InventoryFacet onto the Diamond.",
    )
    contracts_parser.add_argument(
        "-o",
        "--outfile",
        type=argparse.FileType("w"),
        default=None,
        help="(Optional) file to write deployed addresses to",
    )
    contracts_parser.set_defaults(func=handle_systems)

    return parser
