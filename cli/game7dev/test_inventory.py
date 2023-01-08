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
