import unittest

from brownie import accounts, network, web3 as web3_client, ZERO_ADDRESS
from brownie.exceptions import VirtualMachineError
from brownie.network import chain
from moonworm.watch import _fetch_events_chunk

from . import InventoryFacet, MockERC20, MockERC721, MockTerminus, inventory_events
from .core import inventory_gogogo

MAX_UINT = 2**256 - 1


class InventoryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            network.connect()
        except:
            pass

        cls.owner = accounts[0]
        cls.owner_tx_config = {"from": cls.owner}

        cls.admin = accounts[1]
        cls.player = accounts[2]
        cls.random_person = accounts[3]

        cls.nft = MockERC721.MockERC721(None)
        cls.nft.deploy(cls.owner_tx_config)

        cls.terminus = MockTerminus.MockTerminus(None)
        cls.terminus.deploy(cls.owner_tx_config)

        cls.payment_token = MockERC20.MockERC20(None)
        cls.payment_token.deploy("lol", "lol", cls.owner_tx_config)

        cls.terminus.set_payment_token(cls.payment_token.address, cls.owner_tx_config)
        cls.terminus.set_pool_base_price(1, cls.owner_tx_config)

        cls.payment_token.mint(cls.owner.address, 999999, cls.owner_tx_config)

        cls.payment_token.approve(cls.terminus.address, MAX_UINT, cls.owner_tx_config)

        cls.terminus.create_pool_v1(1, False, True, cls.owner_tx_config)
        cls.admin_terminus_pool_id = cls.terminus.total_pools()

        # Mint admin badge to administrator account
        cls.terminus.mint(
            cls.admin.address, cls.admin_terminus_pool_id, 1, "", cls.owner_tx_config
        )

        cls.predeployment_block = len(chain)
        cls.deployed_contracts = inventory_gogogo(
            cls.terminus.address,
            cls.admin_terminus_pool_id,
            cls.nft.address,
            cls.owner_tx_config,
        )
        cls.postdeployment_block = len(chain)
        cls.inventory = InventoryFacet.InventoryFacet(
            cls.deployed_contracts["contracts"]["Diamond"]
        )


class InventorySetupTests(InventoryTestCase):
    def test_admin_terminus_info(self):
        terminus_info = self.inventory.admin_terminus_info()
        self.assertEqual(terminus_info[0], self.terminus.address)
        self.assertEqual(terminus_info[1], self.admin_terminus_pool_id)

    def test_administrator_designated_event(self):
        administrator_designated_events = _fetch_events_chunk(
            web3_client,
            inventory_events.ADMINISTRATOR_DESIGNATED_ABI,
            self.predeployment_block,
            self.postdeployment_block,
        )
        self.assertEqual(len(administrator_designated_events), 1)

        self.assertEqual(
            administrator_designated_events[0]["args"]["adminTerminusAddress"],
            self.terminus.address,
        )
        self.assertEqual(
            administrator_designated_events[0]["args"]["adminTerminusPoolId"],
            self.admin_terminus_pool_id,
        )

    def test_subject_erc721_address(self):
        self.assertEqual(self.inventory.subject(), self.nft.address)

    def test_subject_designated_event(self):
        subject_designated_events = _fetch_events_chunk(
            web3_client,
            inventory_events.SUBJECT_DESIGNATED_ABI,
            self.predeployment_block,
            self.postdeployment_block,
        )
        self.assertEqual(len(subject_designated_events), 1)

        self.assertEqual(
            subject_designated_events[0]["args"]["subjectAddress"],
            self.nft.address,
        )


class AdminFlowTests(InventoryTestCase):
    def test_admin_can_create_nonunequippable_slot(self):
        slot_configuration = 1

        num_slots_0 = self.inventory.num_slots()
        tx_receipt = self.inventory.create_slot(
            slot_configuration, {"from": self.admin}
        )
        num_slots_1 = self.inventory.num_slots()

        self.assertEqual(num_slots_1, num_slots_0 + 1)
        self.assertEqual(
            self.inventory.get_slot_configuration(num_slots_0), slot_configuration
        )

        inventory_slot_created_events = _fetch_events_chunk(
            web3_client,
            inventory_events.INVENTORY_SLOT_CREATED_ABI,
            tx_receipt.block_number,
            tx_receipt.block_number,
        )

        self.assertEqual(len(inventory_slot_created_events), 1)
        self.assertEqual(
            inventory_slot_created_events[0]["args"]["creator"],
            self.admin.address,
        )
        self.assertEqual(
            inventory_slot_created_events[0]["args"]["slot"],
            num_slots_0,
        )
        self.assertEqual(
            inventory_slot_created_events[0]["args"]["slotConfiguration"],
            slot_configuration,
        )

    def test_admin_can_create_unequippable_slot(self):
        slot_configuration = 3

        num_slots_0 = self.inventory.num_slots()
        tx_receipt = self.inventory.create_slot(
            slot_configuration, {"from": self.admin}
        )
        num_slots_1 = self.inventory.num_slots()

        self.assertEqual(num_slots_1, num_slots_0 + 1)
        self.assertEqual(
            self.inventory.get_slot_configuration(num_slots_0), slot_configuration
        )

        inventory_slot_created_events = _fetch_events_chunk(
            web3_client,
            inventory_events.INVENTORY_SLOT_CREATED_ABI,
            tx_receipt.block_number,
            tx_receipt.block_number,
        )

        self.assertEqual(len(inventory_slot_created_events), 1)
        self.assertEqual(
            inventory_slot_created_events[0]["args"]["creator"],
            self.admin.address,
        )
        self.assertEqual(
            inventory_slot_created_events[0]["args"]["slot"],
            num_slots_0,
        )
        self.assertEqual(
            inventory_slot_created_events[0]["args"]["slotConfiguration"],
            slot_configuration,
        )

    def test_admin_cannot_create_slot_with_invalid_configuration(self):
        slot_configuration = 2

        num_slots_0 = self.inventory.num_slots()
        with self.assertRaises(VirtualMachineError):
            self.inventory.create_slot(slot_configuration, {"from": self.admin})
        num_slots_1 = self.inventory.num_slots()

        self.assertEqual(num_slots_1, num_slots_0)

    def test_nonadmin_cannot_create_slot(self):
        slot_configuration = 1

        num_slots_0 = self.inventory.num_slots()
        with self.assertRaises(VirtualMachineError):
            self.inventory.create_slot(slot_configuration, {"from": self.player})
        num_slots_1 = self.inventory.num_slots()

        self.assertEqual(num_slots_1, num_slots_0)

    def test_admin_cannot_mark_contracts_with_invalid_type_as_eligible_for_slots(
        self,
    ):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        invalid_type = 0

        with self.assertRaises(VirtualMachineError):
            self.inventory.mark_item_as_equippable_in_slot(
                slot,
                invalid_type,
                self.payment_token.address,
                0,
                MAX_UINT,
                {"from": self.admin},
            )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, invalid_type, self.payment_token.address, 0
            ),
            0,
        )

    def test_admin_can_mark_erc20_tokens_as_eligible_for_slots(self):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        erc20_type = 20

        tx_receipt = self.inventory.mark_item_as_equippable_in_slot(
            slot,
            erc20_type,
            self.payment_token.address,
            0,
            MAX_UINT,
            {"from": self.admin},
        )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc20_type, self.payment_token.address, 0
            ),
            MAX_UINT,
        )

        item_marked_as_equippable_in_slot_events = _fetch_events_chunk(
            web3_client,
            inventory_events.ITEM_MARKED_AS_EQUIPPABLE_IN_SLOT_ABI,
            tx_receipt.block_number,
            tx_receipt.block_number,
        )

        self.assertEqual(len(item_marked_as_equippable_in_slot_events), 1)
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["slot"],
            slot,
        )
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["itemType"],
            erc20_type,
        )
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["itemAddress"],
            self.payment_token.address,
        )
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["itemPoolId"],
            0,
        )
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["maxAmount"],
            MAX_UINT,
        )

    def test_nonadmin_cannot_mark_erc20_tokens_as_eligible_for_slots(self):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        erc20_type = 20

        with self.assertRaises(VirtualMachineError):
            self.inventory.mark_item_as_equippable_in_slot(
                slot,
                erc20_type,
                self.payment_token.address,
                0,
                MAX_UINT,
                {"from": self.player},
            )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc20_type, self.payment_token.address, 0
            ),
            0,
        )

    def test_admin_cannot_mark_erc20_tokens_as_eligible_for_slots_if_pool_id_is_nonzero(
        self,
    ):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        erc20_type = 20

        with self.assertRaises(VirtualMachineError):
            self.inventory.mark_item_as_equippable_in_slot(
                slot,
                erc20_type,
                self.payment_token.address,
                1,
                MAX_UINT,
                {"from": self.admin},
            )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc20_type, self.payment_token.address, 1
            ),
            0,
        )

    def test_admin_can_mark_erc721_tokens_as_eligible_for_slots(self):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        erc721_type = 721

        tx_receipt = self.inventory.mark_item_as_equippable_in_slot(
            slot,
            erc721_type,
            self.nft.address,
            0,
            1,
            {"from": self.admin},
        )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc721_type, self.nft.address, 0
            ),
            1,
        )

        item_marked_as_equippable_in_slot_events = _fetch_events_chunk(
            web3_client,
            inventory_events.ITEM_MARKED_AS_EQUIPPABLE_IN_SLOT_ABI,
            tx_receipt.block_number,
            tx_receipt.block_number,
        )

        self.assertEqual(len(item_marked_as_equippable_in_slot_events), 1)
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["slot"],
            slot,
        )
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["itemType"],
            erc721_type,
        )
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["itemAddress"],
            self.nft.address,
        )
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["itemPoolId"],
            0,
        )
        self.assertEqual(
            item_marked_as_equippable_in_slot_events[0]["args"]["maxAmount"],
            1,
        )

    def test_nonadmin_cannot_mark_erc721_tokens_as_eligible_for_slots(self):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        erc721_type = 721

        with self.assertRaises(VirtualMachineError):
            self.inventory.mark_item_as_equippable_in_slot(
                slot,
                erc721_type,
                self.payment_token.address,
                0,
                1,
                {"from": self.player},
            )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc721_type, self.payment_token.address, 0
            ),
            0,
        )

    def test_admin_cannot_mark_erc721_tokens_as_eligible_for_slots_if_pool_id_is_nonzero(
        self,
    ):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        erc721_type = 721

        with self.assertRaises(VirtualMachineError):
            self.inventory.mark_item_as_equippable_in_slot(
                slot,
                erc721_type,
                self.payment_token.address,
                1,
                1,
                {"from": self.admin},
            )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc721_type, self.payment_token.address, 1
            ),
            0,
        )

    def test_admin_cannot_mark_erc721_tokens_as_eligible_for_slots_with_max_amount_greater_than_1(
        self,
    ):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        erc721_type = 721

        with self.assertRaises(VirtualMachineError):
            self.inventory.mark_item_as_equippable_in_slot(
                slot,
                erc721_type,
                self.payment_token.address,
                0,
                2,
                {"from": self.admin},
            )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc721_type, self.payment_token.address, 0
            ),
            0,
        )

    def test_admin_can_mark_erc721_tokens_as_eligible_for_slots_with_max_amount_1_then_0(
        self,
    ):
        slot_configuration = 3
        self.inventory.create_slot(slot_configuration, {"from": self.admin})
        slot = self.inventory.num_slots()

        erc721_type = 721

        tx_receipt_0 = self.inventory.mark_item_as_equippable_in_slot(
            slot,
            erc721_type,
            self.nft.address,
            0,
            1,
            {"from": self.admin},
        )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc721_type, self.nft.address, 0
            ),
            1,
        )

        tx_receipt_1 = self.inventory.mark_item_as_equippable_in_slot(
            slot,
            erc721_type,
            self.nft.address,
            0,
            0,
            {"from": self.admin},
        )

        self.assertEqual(
            self.inventory.max_amount_of_item_in_slot(
                slot, erc721_type, self.nft.address, 0
            ),
            0,
        )

        item_marked_as_equippable_in_slot_events = _fetch_events_chunk(
            web3_client,
            inventory_events.ITEM_MARKED_AS_EQUIPPABLE_IN_SLOT_ABI,
            tx_receipt_0.block_number,
            tx_receipt_1.block_number,
        )

        self.assertEqual(len(item_marked_as_equippable_in_slot_events), 2)
        for i, event in enumerate(item_marked_as_equippable_in_slot_events):
            self.assertEqual(
                event["args"]["slot"],
                slot,
            )
            self.assertEqual(
                event["args"]["itemType"],
                erc721_type,
            )
            self.assertEqual(
                event["args"]["itemAddress"],
                self.nft.address,
            )
            self.assertEqual(
                event["args"]["itemPoolId"],
                0,
            )
            self.assertEqual(
                event["args"]["maxAmount"],
                1 - i,
            )
