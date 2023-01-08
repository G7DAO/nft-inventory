// SPDX-License-Identifier: UNLICENSED

/**
 * Authors: Moonstream DAO (engineering@moonstream.to)
 * GitHub: https://github.com/G7DAO/contracts
 */

pragma solidity ^0.8.0;

import {TerminusPermissions} from "@moonstream/contracts/terminus/TerminusPermissions.sol";
import {DiamondReentrancyGuard} from "@moonstream-engine/contracts/diamond/security/DiamondReentrancyGuard.sol";
import "@openzeppelin-contracts/contracts/token/ERC1155/utils/ERC1155Holder.sol";
import "@openzeppelin-contracts/contracts/token/ERC721/utils/ERC721Holder.sol";
import "@openzeppelin-contracts/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin-contracts/contracts/token/ERC1155/IERC1155.sol";
import "../diamond/libraries/LibDiamond.sol";

/**
LibInventory defines the storage structure used by the Inventory contract as a facet for an EIP-2535 Diamond
proxy.
 */
library LibInventory {
    bytes32 constant STORAGE_POSITION =
        keccak256("g7dao.eth.storage.Inventory");

    uint256 constant ERC20_ITEM_TYPE = 20;
    uint256 constant ERC721_ITEM_TYPE = 721;
    uint256 constant ERC1155_ITEM_TYPE = 1155;

    struct InventoryStorage {
        address AdminTerminusAddress;
        uint256 AdminTerminusPoolId;
        address SubjectERC721Address;
        uint256 NumSlots;
        // Slot => Slot configuration bitmap
        // Currently, there are only two admissible configurations:
        // - 3 means that items can be unequipped from the slot
        // - 1 means that items cannot be unequipped from the slot
        // The intention is for these configurations to be a bitmap over all possible settings that can
        // be configured on a slot.
        // The first bit (2^0) is always active for created slots.
        // The 2 bit is active for slots from which items cannot be unequipped.
        mapping(uint256 => uint256) SlotConfigurations;
        // Slot => item type => item address => item pool ID => maximum equippable
        // For ERC20 and ERC721 tokens, item pool ID is assumed to be 0. No data will be stored under positive
        // item pool IDs.
        // Note that it is possible for the same contract to implement multiple of these ERCs (e.g. ERC20 and ERC721),
        // so this data structure actually makes sense.
        mapping(uint256 => mapping(uint256 => mapping(address => mapping(uint256 => uint256)))) SlotEligibleItems;
    }

    function inventoryStorage()
        internal
        pure
        returns (InventoryStorage storage istore)
    {
        bytes32 position = STORAGE_POSITION;
        assembly {
            istore.slot := position
        }
    }

    function isValidSlotConfiguration(uint256 configuration)
        internal
        pure
        returns (bool)
    {
        return configuration & 1 == 1 && configuration <= 3;
    }

    function isSlotConfigured(uint256 slot) internal view returns (bool) {
        return inventoryStorage().SlotConfigurations[slot] & 1 == 1;
    }

    function isSlotUnequippable(uint256 slot) internal view returns (bool) {
        return (inventoryStorage().SlotConfigurations[slot] >> 1) & 1 == 1;
    }
}

/**
InventoryFacet is a smart contract that can either be used standalone or as part of an EIP-2535 Diamond
proxy contract.

It implements an inventory system which can be layered onto any ERC721 contract.

For more details, please refer to the design document:
https://docs.google.com/document/d/1Oa9I9b7t46_ngYp-Pady5XKEDW8M2NE9rI0GBRACZBI/edit?usp=sharing

Admin flow:
- [x] Create inventory slots
- [x] Specify whether inventory slots are equippable or not on slot creation
- [x] Define tokens as equippable in inventory slots

Player flow:
- [ ] Equip ERC721 tokens in eligible inventory slots
- [ ] Equip ERC20 tokens in eligible inventory slots
- [ ] Equip ERC1155 tokens in eligible inventory slots
 */
contract InventoryFacet is
    ERC721Holder,
    ERC1155Holder,
    TerminusPermissions,
    DiamondReentrancyGuard
{
    modifier onlyAdmin() {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();
        require(
            _holdsPoolToken(
                istore.AdminTerminusAddress,
                istore.AdminTerminusPoolId,
                1
            ),
            "InventoryFacet.onlyAdmin: The address is not an authorized administrator"
        );
        _;
    }

    event AdministratorDesignated(
        address indexed adminTerminusAddress,
        uint256 indexed adminTerminusPoolId
    );

    event SubjectDesignated(address indexed subjectAddress);

    event InventorySlotCreated(
        address indexed creator,
        uint256 slot,
        uint256 slotConfiguration
    );

    event ItemMarkedAsEquippableInSlot(
        uint256 indexed slot,
        uint256 indexed itemType,
        address indexed itemAddress,
        uint256 itemPoolId,
        uint256 maxAmount
    );

    /**
    An Inventory must be initialized with:
    1. adminTerminusAddress: The address for the Terminus contract which hosts the Administrator badge.
    2. adminTerminusPoolId: The pool ID for the Administrator badge on that Terminus contract.
    3. subjectAddress: The address of the ERC721 contract that the Inventory refers to.
     */
    function init(
        address adminTerminusAddress,
        uint256 adminTerminusPoolId,
        address subjectAddress
    ) external {
        LibDiamond.enforceIsContractOwner();
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();
        istore.AdminTerminusAddress = adminTerminusAddress;
        istore.AdminTerminusPoolId = adminTerminusPoolId;
        istore.SubjectERC721Address = subjectAddress;

        emit AdministratorDesignated(adminTerminusAddress, adminTerminusPoolId);
        emit SubjectDesignated(subjectAddress);
    }

    function adminTerminusInfo() external view returns (address, uint256) {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();
        return (istore.AdminTerminusAddress, istore.AdminTerminusPoolId);
    }

    function subject() external view returns (address) {
        return LibInventory.inventoryStorage().SubjectERC721Address;
    }

    function createSlot(uint256 configuration)
        external
        onlyAdmin
        returns (uint256)
    {
        require(
            LibInventory.isValidSlotConfiguration(configuration),
            "InventoryFacet.createSlot: Invalid slot configuration"
        );
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        uint256 newSlot = istore.NumSlots++;
        istore.SlotConfigurations[newSlot] = configuration;

        emit InventorySlotCreated(msg.sender, newSlot, configuration);
        return newSlot;
    }

    function numSlots() external view returns (uint256) {
        return LibInventory.inventoryStorage().NumSlots;
    }

    function getSlotConfiguration(uint256 slot)
        external
        view
        returns (uint256)
    {
        return LibInventory.inventoryStorage().SlotConfigurations[slot];
    }

    function markItemAsEquippableInSlot(
        uint256 slot,
        uint256 itemType,
        address itemAddress,
        uint256 itemPoolId,
        uint256 maxAmount
    ) external onlyAdmin {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        require(
            itemType == LibInventory.ERC20_ITEM_TYPE ||
                itemType == LibInventory.ERC721_ITEM_TYPE ||
                itemType == LibInventory.ERC1155_ITEM_TYPE,
            "InventoryFacet.markItemAsEquippableInSlot: Invalid item type"
        );
        require(
            itemType == LibInventory.ERC1155_ITEM_TYPE || itemPoolId == 0,
            "InventoryFacet.markItemAsEquippableInSlot: Pool ID can only be non-zero for items from ERC1155 contracts"
        );
        require(
            itemType != LibInventory.ERC721_ITEM_TYPE || maxAmount <= 1,
            "InventoryFacet.markItemAsEquippableInSlot: maxAmount should be at most 1 for items from ERC721 contracts"
        );

        // NOTE: We do not perform any check on the previously registered maxAmount for the item.
        // This gives administrators some flexibility in marking items as no longer eligible for slots.
        // But any player who has already equipped items in a slot before a change in maxAmount will
        // not be subject to the new limitation. This is something administrators will have to factor
        // into their game design.
        istore.SlotEligibleItems[slot][itemType][itemAddress][
            itemPoolId
        ] = maxAmount;

        emit ItemMarkedAsEquippableInSlot(
            slot,
            itemType,
            itemAddress,
            itemPoolId,
            maxAmount
        );
    }

    function maxAmountOfItemInSlot(
        uint256 slot,
        uint256 itemType,
        address itemAddress,
        uint256 itemPoolId
    ) external view returns (uint256) {
        return
            LibInventory.inventoryStorage().SlotEligibleItems[slot][itemType][
                itemAddress
            ][itemPoolId];
    }
}
