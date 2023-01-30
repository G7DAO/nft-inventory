# Code generated by moonworm : https://github.com/bugout-dev/moonworm
# Moonworm version : 0.5.3

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from brownie import Contract, network, project
from brownie.network.contract import ContractContainer
from eth_typing.evm import ChecksumAddress


PROJECT_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUILD_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "build", "contracts")


def boolean_argument_type(raw_value: str) -> bool:
    TRUE_VALUES = ["1", "t", "y", "true", "yes"]
    FALSE_VALUES = ["0", "f", "n", "false", "no"]

    if raw_value.lower() in TRUE_VALUES:
        return True
    elif raw_value.lower() in FALSE_VALUES:
        return False

    raise ValueError(
        f"Invalid boolean argument: {raw_value}. Value must be one of: {','.join(TRUE_VALUES + FALSE_VALUES)}"
    )


def bytes_argument_type(raw_value: str) -> str:
    return raw_value


def get_abi_json(abi_name: str) -> List[Dict[str, Any]]:
    abi_full_path = os.path.join(BUILD_DIRECTORY, f"{abi_name}.json")
    if not os.path.isfile(abi_full_path):
        raise IOError(
            f"File does not exist: {abi_full_path}. Maybe you have to compile the smart contracts?"
        )

    with open(abi_full_path, "r") as ifp:
        build = json.load(ifp)

    abi_json = build.get("abi")
    if abi_json is None:
        raise ValueError(f"Could not find ABI definition in: {abi_full_path}")

    return abi_json


def contract_from_build(abi_name: str) -> ContractContainer:
    # This is workaround because brownie currently doesn't support loading the same project multiple
    # times. This causes problems when using multiple contracts from the same project in the same
    # python project.
    PROJECT = project.main.Project("moonworm", Path(PROJECT_DIRECTORY))

    abi_full_path = os.path.join(BUILD_DIRECTORY, f"{abi_name}.json")
    if not os.path.isfile(abi_full_path):
        raise IOError(
            f"File does not exist: {abi_full_path}. Maybe you have to compile the smart contracts?"
        )

    with open(abi_full_path, "r") as ifp:
        build = json.load(ifp)

    return ContractContainer(PROJECT, build)


class InventoryFacet:
    def __init__(self, contract_address: Optional[ChecksumAddress]):
        self.contract_name = "InventoryFacet"
        self.address = contract_address
        self.contract = None
        self.abi = get_abi_json("InventoryFacet")
        if self.address is not None:
            self.contract: Optional[Contract] = Contract.from_abi(
                self.contract_name, self.address, self.abi
            )

    def deploy(self, transaction_config):
        contract_class = contract_from_build(self.contract_name)
        deployed_contract = contract_class.deploy(transaction_config)
        self.address = deployed_contract.address
        self.contract = deployed_contract
        return deployed_contract.tx

    def assert_contract_is_instantiated(self) -> None:
        if self.contract is None:
            raise Exception("contract has not been instantiated")

    def verify_contract(self):
        self.assert_contract_is_instantiated()
        contract_class = contract_from_build(self.contract_name)
        contract_class.publish_source(self.contract)

    def admin_terminus_info(
        self, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.adminTerminusInfo.call(block_identifier=block_number)

    def assign_slot_to_subject_token_id(
        self, to_subject_token_id: int, slot_id: int, transaction_config
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.assignSlotToSubjectTokenId(
            to_subject_token_id, slot_id, transaction_config
        )

    def create_slot(
        self, unequippable: bool, slot_type: int, slot_uri: str, transaction_config
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.createSlot(
            unequippable, slot_type, slot_uri, transaction_config
        )

    def equip(
        self,
        subject_token_id: int,
        slot: int,
        item_type: int,
        item_address: ChecksumAddress,
        item_token_id: int,
        amount: int,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.equip(
            subject_token_id,
            slot,
            item_type,
            item_address,
            item_token_id,
            amount,
            transaction_config,
        )

    def get_equipped_item(
        self,
        subject_token_id: int,
        slot: int,
        block_number: Optional[Union[str, int]] = "latest",
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getEquippedItem.call(
            subject_token_id, slot, block_identifier=block_number
        )

    def get_slot_by_id(
        self,
        subject_token_id: int,
        slot_id: int,
        block_number: Optional[Union[str, int]] = "latest",
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getSlotById.call(
            subject_token_id, slot_id, block_identifier=block_number
        )

    def get_slot_uri(
        self, slot_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getSlotURI.call(slot_id, block_identifier=block_number)

    def get_subject_token_slots(
        self, subject_token_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getSubjectTokenSlots.call(
            subject_token_id, block_identifier=block_number
        )

    def init(
        self,
        admin_terminus_address: ChecksumAddress,
        admin_terminus_pool_id: int,
        contract_address: ChecksumAddress,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.init(
            admin_terminus_address,
            admin_terminus_pool_id,
            contract_address,
            transaction_config,
        )

    def mark_item_as_equippable_in_slot(
        self,
        slot: int,
        item_type: int,
        item_address: ChecksumAddress,
        item_pool_id: int,
        max_amount: int,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.markItemAsEquippableInSlot(
            slot, item_type, item_address, item_pool_id, max_amount, transaction_config
        )

    def max_amount_of_item_in_slot(
        self,
        slot: int,
        item_type: int,
        item_address: ChecksumAddress,
        item_pool_id: int,
        block_number: Optional[Union[str, int]] = "latest",
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.maxAmountOfItemInSlot.call(
            slot, item_type, item_address, item_pool_id, block_identifier=block_number
        )

    def num_slots(self, block_number: Optional[Union[str, int]] = "latest") -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.numSlots.call(block_identifier=block_number)

    def on_erc1155_batch_received(
        self,
        arg1: ChecksumAddress,
        arg2: ChecksumAddress,
        arg3: List,
        arg4: List,
        arg5: bytes,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.onERC1155BatchReceived(
            arg1, arg2, arg3, arg4, arg5, transaction_config
        )

    def on_erc1155_received(
        self,
        arg1: ChecksumAddress,
        arg2: ChecksumAddress,
        arg3: int,
        arg4: int,
        arg5: bytes,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.onERC1155Received(
            arg1, arg2, arg3, arg4, arg5, transaction_config
        )

    def on_erc721_received(
        self,
        arg1: ChecksumAddress,
        arg2: ChecksumAddress,
        arg3: int,
        arg4: bytes,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.onERC721Received(
            arg1, arg2, arg3, arg4, transaction_config
        )

    def set_slot_uri(self, new_slot_uri: str, slot_id: int, transaction_config) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.setSlotUri(new_slot_uri, slot_id, transaction_config)

    def slot_is_unequippable(
        self, slot_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.slotIsUnequippable.call(
            slot_id, block_identifier=block_number
        )

    def subject(self, block_number: Optional[Union[str, int]] = "latest") -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.subject.call(block_identifier=block_number)

    def supports_interface(
        self, interface_id: bytes, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.supportsInterface.call(
            interface_id, block_identifier=block_number
        )

    def unequip(
        self,
        subject_token_id: int,
        slot: int,
        unequip_all: bool,
        amount: int,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.unequip(
            subject_token_id, slot, unequip_all, amount, transaction_config
        )


def get_transaction_config(args: argparse.Namespace) -> Dict[str, Any]:
    signer = network.accounts.load(args.sender, args.password)
    transaction_config: Dict[str, Any] = {"from": signer}
    if args.gas_price is not None:
        transaction_config["gas_price"] = args.gas_price
    if args.max_fee_per_gas is not None:
        transaction_config["max_fee"] = args.max_fee_per_gas
    if args.max_priority_fee_per_gas is not None:
        transaction_config["priority_fee"] = args.max_priority_fee_per_gas
    if args.confirmations is not None:
        transaction_config["required_confs"] = args.confirmations
    if args.nonce is not None:
        transaction_config["nonce"] = args.nonce
    return transaction_config


def add_default_arguments(parser: argparse.ArgumentParser, transact: bool) -> None:
    parser.add_argument(
        "--network", required=True, help="Name of brownie network to connect to"
    )
    parser.add_argument(
        "--address", required=False, help="Address of deployed contract to connect to"
    )
    if not transact:
        parser.add_argument(
            "--block-number",
            required=False,
            type=int,
            help="Call at the given block number, defaults to latest",
        )
        return
    parser.add_argument(
        "--sender", required=True, help="Path to keystore file for transaction sender"
    )
    parser.add_argument(
        "--password",
        required=False,
        help="Password to keystore file (if you do not provide it, you will be prompted for it)",
    )
    parser.add_argument(
        "--gas-price", default=None, help="Gas price at which to submit transaction"
    )
    parser.add_argument(
        "--max-fee-per-gas",
        default=None,
        help="Max fee per gas for EIP1559 transactions",
    )
    parser.add_argument(
        "--max-priority-fee-per-gas",
        default=None,
        help="Max priority fee per gas for EIP1559 transactions",
    )
    parser.add_argument(
        "--confirmations",
        type=int,
        default=None,
        help="Number of confirmations to await before considering a transaction completed",
    )
    parser.add_argument(
        "--nonce", type=int, default=None, help="Nonce for the transaction (optional)"
    )
    parser.add_argument(
        "--value", default=None, help="Value of the transaction in wei(optional)"
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")


def handle_deploy(args: argparse.Namespace) -> None:
    network.connect(args.network)
    transaction_config = get_transaction_config(args)
    contract = InventoryFacet(None)
    result = contract.deploy(transaction_config=transaction_config)
    print(result)
    if args.verbose:
        print(result.info())


def handle_verify_contract(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.verify_contract()
    print(result)


def handle_admin_terminus_info(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.admin_terminus_info(block_number=args.block_number)
    print(result)


def handle_assign_slot_to_subject_token_id(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.assign_slot_to_subject_token_id(
        to_subject_token_id=args.to_subject_token_id,
        slot_id=args.slot_id,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_create_slot(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.create_slot(
        unequippable=args.unequippable,
        slot_type=args.slot_type,
        slot_uri=args.slot_uri,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_equip(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.equip(
        subject_token_id=args.subject_token_id,
        slot=args.slot,
        item_type=args.item_type,
        item_address=args.item_address,
        item_token_id=args.item_token_id,
        amount=args.amount,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_get_equipped_item(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.get_equipped_item(
        subject_token_id=args.subject_token_id,
        slot=args.slot,
        block_number=args.block_number,
    )
    print(result)


def handle_get_slot_by_id(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.get_slot_by_id(
        subject_token_id=args.subject_token_id,
        slot_id=args.slot_id,
        block_number=args.block_number,
    )
    print(result)


def handle_get_slot_uri(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.get_slot_uri(slot_id=args.slot_id, block_number=args.block_number)
    print(result)


def handle_get_subject_token_slots(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.get_subject_token_slots(
        subject_token_id=args.subject_token_id, block_number=args.block_number
    )
    print(result)


def handle_init(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.init(
        admin_terminus_address=args.admin_terminus_address,
        admin_terminus_pool_id=args.admin_terminus_pool_id,
        contract_address=args.contract_address,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_mark_item_as_equippable_in_slot(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.mark_item_as_equippable_in_slot(
        slot=args.slot,
        item_type=args.item_type,
        item_address=args.item_address,
        item_pool_id=args.item_pool_id,
        max_amount=args.max_amount,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_max_amount_of_item_in_slot(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.max_amount_of_item_in_slot(
        slot=args.slot,
        item_type=args.item_type,
        item_address=args.item_address,
        item_pool_id=args.item_pool_id,
        block_number=args.block_number,
    )
    print(result)


def handle_num_slots(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.num_slots(block_number=args.block_number)
    print(result)


def handle_on_erc1155_batch_received(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.on_erc1155_batch_received(
        arg1=args.arg1,
        arg2=args.arg2,
        arg3=args.arg3,
        arg4=args.arg4,
        arg5=args.arg5,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_on_erc1155_received(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.on_erc1155_received(
        arg1=args.arg1,
        arg2=args.arg2,
        arg3=args.arg3,
        arg4=args.arg4,
        arg5=args.arg5,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_on_erc721_received(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.on_erc721_received(
        arg1=args.arg1,
        arg2=args.arg2,
        arg3=args.arg3,
        arg4=args.arg4,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_set_slot_uri(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.set_slot_uri(
        new_slot_uri=args.new_slot_uri,
        slot_id=args.slot_id,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_slot_is_unequippable(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.slot_is_unequippable(
        slot_id=args.slot_id, block_number=args.block_number
    )
    print(result)


def handle_subject(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.subject(block_number=args.block_number)
    print(result)


def handle_supports_interface(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    result = contract.supports_interface(
        interface_id=args.interface_id, block_number=args.block_number
    )
    print(result)


def handle_unequip(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = InventoryFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.unequip(
        subject_token_id=args.subject_token_id,
        slot=args.slot,
        unequip_all=args.unequip_all,
        amount=args.amount,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI for InventoryFacet")
    parser.set_defaults(func=lambda _: parser.print_help())
    subcommands = parser.add_subparsers()

    deploy_parser = subcommands.add_parser("deploy")
    add_default_arguments(deploy_parser, True)
    deploy_parser.set_defaults(func=handle_deploy)

    verify_contract_parser = subcommands.add_parser("verify-contract")
    add_default_arguments(verify_contract_parser, False)
    verify_contract_parser.set_defaults(func=handle_verify_contract)

    admin_terminus_info_parser = subcommands.add_parser("admin-terminus-info")
    add_default_arguments(admin_terminus_info_parser, False)
    admin_terminus_info_parser.set_defaults(func=handle_admin_terminus_info)

    assign_slot_to_subject_token_id_parser = subcommands.add_parser(
        "assign-slot-to-subject-token-id"
    )
    add_default_arguments(assign_slot_to_subject_token_id_parser, True)
    assign_slot_to_subject_token_id_parser.add_argument(
        "--to-subject-token-id", required=True, help="Type: uint256", type=int
    )
    assign_slot_to_subject_token_id_parser.add_argument(
        "--slot-id", required=True, help="Type: uint256", type=int
    )
    assign_slot_to_subject_token_id_parser.set_defaults(
        func=handle_assign_slot_to_subject_token_id
    )

    create_slot_parser = subcommands.add_parser("create-slot")
    add_default_arguments(create_slot_parser, True)
    create_slot_parser.add_argument(
        "--unequippable", required=True, help="Type: bool", type=boolean_argument_type
    )
    create_slot_parser.add_argument(
        "--slot-type", required=True, help="Type: uint256", type=int
    )
    create_slot_parser.add_argument(
        "--slot-uri", required=True, help="Type: string", type=str
    )
    create_slot_parser.set_defaults(func=handle_create_slot)

    equip_parser = subcommands.add_parser("equip")
    add_default_arguments(equip_parser, True)
    equip_parser.add_argument(
        "--subject-token-id", required=True, help="Type: uint256", type=int
    )
    equip_parser.add_argument("--slot", required=True, help="Type: uint256", type=int)
    equip_parser.add_argument(
        "--item-type", required=True, help="Type: uint256", type=int
    )
    equip_parser.add_argument("--item-address", required=True, help="Type: address")
    equip_parser.add_argument(
        "--item-token-id", required=True, help="Type: uint256", type=int
    )
    equip_parser.add_argument("--amount", required=True, help="Type: uint256", type=int)
    equip_parser.set_defaults(func=handle_equip)

    get_equipped_item_parser = subcommands.add_parser("get-equipped-item")
    add_default_arguments(get_equipped_item_parser, False)
    get_equipped_item_parser.add_argument(
        "--subject-token-id", required=True, help="Type: uint256", type=int
    )
    get_equipped_item_parser.add_argument(
        "--slot", required=True, help="Type: uint256", type=int
    )
    get_equipped_item_parser.set_defaults(func=handle_get_equipped_item)

    get_slot_by_id_parser = subcommands.add_parser("get-slot-by-id")
    add_default_arguments(get_slot_by_id_parser, False)
    get_slot_by_id_parser.add_argument(
        "--subject-token-id", required=True, help="Type: uint256", type=int
    )
    get_slot_by_id_parser.add_argument(
        "--slot-id", required=True, help="Type: uint256", type=int
    )
    get_slot_by_id_parser.set_defaults(func=handle_get_slot_by_id)

    get_slot_uri_parser = subcommands.add_parser("get-slot-uri")
    add_default_arguments(get_slot_uri_parser, False)
    get_slot_uri_parser.add_argument(
        "--slot-id", required=True, help="Type: uint256", type=int
    )
    get_slot_uri_parser.set_defaults(func=handle_get_slot_uri)

    get_subject_token_slots_parser = subcommands.add_parser("get-subject-token-slots")
    add_default_arguments(get_subject_token_slots_parser, False)
    get_subject_token_slots_parser.add_argument(
        "--subject-token-id", required=True, help="Type: uint256", type=int
    )
    get_subject_token_slots_parser.set_defaults(func=handle_get_subject_token_slots)

    init_parser = subcommands.add_parser("init")
    add_default_arguments(init_parser, True)
    init_parser.add_argument(
        "--admin-terminus-address", required=True, help="Type: address"
    )
    init_parser.add_argument(
        "--admin-terminus-pool-id", required=True, help="Type: uint256", type=int
    )
    init_parser.add_argument("--contract-address", required=True, help="Type: address")
    init_parser.set_defaults(func=handle_init)

    mark_item_as_equippable_in_slot_parser = subcommands.add_parser(
        "mark-item-as-equippable-in-slot"
    )
    add_default_arguments(mark_item_as_equippable_in_slot_parser, True)
    mark_item_as_equippable_in_slot_parser.add_argument(
        "--slot", required=True, help="Type: uint256", type=int
    )
    mark_item_as_equippable_in_slot_parser.add_argument(
        "--item-type", required=True, help="Type: uint256", type=int
    )
    mark_item_as_equippable_in_slot_parser.add_argument(
        "--item-address", required=True, help="Type: address"
    )
    mark_item_as_equippable_in_slot_parser.add_argument(
        "--item-pool-id", required=True, help="Type: uint256", type=int
    )
    mark_item_as_equippable_in_slot_parser.add_argument(
        "--max-amount", required=True, help="Type: uint256", type=int
    )
    mark_item_as_equippable_in_slot_parser.set_defaults(
        func=handle_mark_item_as_equippable_in_slot
    )

    max_amount_of_item_in_slot_parser = subcommands.add_parser(
        "max-amount-of-item-in-slot"
    )
    add_default_arguments(max_amount_of_item_in_slot_parser, False)
    max_amount_of_item_in_slot_parser.add_argument(
        "--slot", required=True, help="Type: uint256", type=int
    )
    max_amount_of_item_in_slot_parser.add_argument(
        "--item-type", required=True, help="Type: uint256", type=int
    )
    max_amount_of_item_in_slot_parser.add_argument(
        "--item-address", required=True, help="Type: address"
    )
    max_amount_of_item_in_slot_parser.add_argument(
        "--item-pool-id", required=True, help="Type: uint256", type=int
    )
    max_amount_of_item_in_slot_parser.set_defaults(
        func=handle_max_amount_of_item_in_slot
    )

    num_slots_parser = subcommands.add_parser("num-slots")
    add_default_arguments(num_slots_parser, False)
    num_slots_parser.set_defaults(func=handle_num_slots)

    on_erc1155_batch_received_parser = subcommands.add_parser(
        "on-erc1155-batch-received"
    )
    add_default_arguments(on_erc1155_batch_received_parser, True)
    on_erc1155_batch_received_parser.add_argument(
        "--arg1", required=True, help="Type: address"
    )
    on_erc1155_batch_received_parser.add_argument(
        "--arg2", required=True, help="Type: address"
    )
    on_erc1155_batch_received_parser.add_argument(
        "--arg3", required=True, help="Type: uint256[]", nargs="+"
    )
    on_erc1155_batch_received_parser.add_argument(
        "--arg4", required=True, help="Type: uint256[]", nargs="+"
    )
    on_erc1155_batch_received_parser.add_argument(
        "--arg5", required=True, help="Type: bytes", type=bytes_argument_type
    )
    on_erc1155_batch_received_parser.set_defaults(func=handle_on_erc1155_batch_received)

    on_erc1155_received_parser = subcommands.add_parser("on-erc1155-received")
    add_default_arguments(on_erc1155_received_parser, True)
    on_erc1155_received_parser.add_argument(
        "--arg1", required=True, help="Type: address"
    )
    on_erc1155_received_parser.add_argument(
        "--arg2", required=True, help="Type: address"
    )
    on_erc1155_received_parser.add_argument(
        "--arg3", required=True, help="Type: uint256", type=int
    )
    on_erc1155_received_parser.add_argument(
        "--arg4", required=True, help="Type: uint256", type=int
    )
    on_erc1155_received_parser.add_argument(
        "--arg5", required=True, help="Type: bytes", type=bytes_argument_type
    )
    on_erc1155_received_parser.set_defaults(func=handle_on_erc1155_received)

    on_erc721_received_parser = subcommands.add_parser("on-erc721-received")
    add_default_arguments(on_erc721_received_parser, True)
    on_erc721_received_parser.add_argument(
        "--arg1", required=True, help="Type: address"
    )
    on_erc721_received_parser.add_argument(
        "--arg2", required=True, help="Type: address"
    )
    on_erc721_received_parser.add_argument(
        "--arg3", required=True, help="Type: uint256", type=int
    )
    on_erc721_received_parser.add_argument(
        "--arg4", required=True, help="Type: bytes", type=bytes_argument_type
    )
    on_erc721_received_parser.set_defaults(func=handle_on_erc721_received)

    set_slot_uri_parser = subcommands.add_parser("set-slot-uri")
    add_default_arguments(set_slot_uri_parser, True)
    set_slot_uri_parser.add_argument(
        "--new-slot-uri", required=True, help="Type: string", type=str
    )
    set_slot_uri_parser.add_argument(
        "--slot-id", required=True, help="Type: uint256", type=int
    )
    set_slot_uri_parser.set_defaults(func=handle_set_slot_uri)

    slot_is_unequippable_parser = subcommands.add_parser("slot-is-unequippable")
    add_default_arguments(slot_is_unequippable_parser, False)
    slot_is_unequippable_parser.add_argument(
        "--slot-id", required=True, help="Type: uint256", type=int
    )
    slot_is_unequippable_parser.set_defaults(func=handle_slot_is_unequippable)

    subject_parser = subcommands.add_parser("subject")
    add_default_arguments(subject_parser, False)
    subject_parser.set_defaults(func=handle_subject)

    supports_interface_parser = subcommands.add_parser("supports-interface")
    add_default_arguments(supports_interface_parser, False)
    supports_interface_parser.add_argument(
        "--interface-id", required=True, help="Type: bytes4", type=bytes_argument_type
    )
    supports_interface_parser.set_defaults(func=handle_supports_interface)

    unequip_parser = subcommands.add_parser("unequip")
    add_default_arguments(unequip_parser, True)
    unequip_parser.add_argument(
        "--subject-token-id", required=True, help="Type: uint256", type=int
    )
    unequip_parser.add_argument("--slot", required=True, help="Type: uint256", type=int)
    unequip_parser.add_argument(
        "--unequip-all", required=True, help="Type: bool", type=boolean_argument_type
    )
    unequip_parser.add_argument(
        "--amount", required=True, help="Type: uint256", type=int
    )
    unequip_parser.set_defaults(func=handle_unequip)

    return parser


def main() -> None:
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
