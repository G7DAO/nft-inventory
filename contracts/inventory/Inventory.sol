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
    uint256 constant UNEQUIP_ITEM_TYPE = 0;

    // EquippedItem represents an item equipped in a specific inventory slot for a specific ERC721 token.
    struct EquippedItem {
        uint256 ItemType;
        address ItemAddress;
        uint256 ItemTokenId;
        uint256 Amount;
    }

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
        //
        // NOTE: It is possible for the same contract to implement multiple of these ERCs (e.g. ERC20 and ERC721),
        // so this data structure actually makes sense.
        mapping(uint256 => mapping(uint256 => mapping(address => mapping(uint256 => uint256)))) SlotEligibleItems;
        // Subject contract address => subject token ID => slot => EquippedItem
        // Item type and Pool ID on EquippedItem have the same constraints as they do elsewhere (e.g. in SlotEligibleItems).
        //
        // NOTE: We have added the subject contract address as the first mapping key as a defense against
        // future modifications which may allow administrators to modify the subject contract address.
        // If such a modification were made, it could make it possible for a bad actor administrator
        // to change the address of the subject token to the address to an ERC721 contract they control
        // and drain all items from every subject token's inventory.
        // If this contract is deployed as a Diamond proxy, the owner of the Diamond can pretty much
        // do whatever they want in any case, but adding the subject contract address as a key protects
        // users of non-Diamond deployments even under small variants of the current implementation.
        // It also offers *some* protection to users of Diamond deployments of the Inventory.
        mapping(address => mapping(uint256 => mapping(uint256 => EquippedItem))) EquippedItems;
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
- [ ] Equip ERC20 tokens in eligible inventory slots
- [ ] Equip ERC721 tokens in eligible inventory slots
- [ ] Equip ERC1155 tokens in eligible inventory slots
- [ ] Unequip items from unequippable slots

Batch endpoints:
- [ ] Marking items as equippable
- [ ] Equipping items
- [ ] Unequipping items
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

    function equip(
        uint256 subjectTokenId,
        uint256 slot,
        uint256 itemType,
        address itemAddress,
        uint256 itemTokenId,
        uint256 amount
    ) external {
        require(
            itemType == LibInventory.ERC20_ITEM_TYPE ||
                itemType == LibInventory.ERC721_ITEM_TYPE ||
                itemType == LibInventory.ERC1155_ITEM_TYPE ||
                itemType == LibInventory.UNEQUIP_ITEM_TYPE,
            "InventoryFacet.equip: Invalid item type"
        );
        require(
            itemType == LibInventory.ERC721_ITEM_TYPE ||
                itemType == LibInventory.ERC1155_ITEM_TYPE ||
                itemTokenId == 0,
            "InventoryFacet.equip: itemTokenId can only be non-zero for ERC721 or ERC1155 items"
        );
        require(
            itemType == LibInventory.ERC20_ITEM_TYPE ||
                itemType == LibInventory.ERC1155_ITEM_TYPE ||
                amount <= 1,
            "InventoryFacet.equip: amount can exceed 1 only for ERC20 and ERC1155 items"
        );
        require(
            itemType != LibInventory.UNEQUIP_ITEM_TYPE || amount == 0,
            "InventoryFacet.equip: amout should be 0 if you are unequipping an item"
        );

        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        IERC721 subjectContract = IERC721(istore.SubjectERC721Address);
        require(
            msg.sender == subjectContract.ownerOf(subjectTokenId),
            "InventoryFacet.equip: Message sender is not owner of subject token"
        );

        LibInventory.EquippedItem memory existingItem = istore.EquippedItems[
            istore.SubjectERC721Address
        ][subjectTokenId][slot];

        // TODO(zomglings): To set things up, we will only test equipping workflow. To make it
        // so that tokens cannot be unequipped, we require that the existingItem.ItemType be zero.
        // We will turn this off when we add support for unequipping items from unequippable slots
        // and when we want to add support for reupping items of the same already equipped type into
        // a slot.
        require(
            existingItem.ItemType == 0,
            "InventoryFacet.equip: This is a temporary restriction that no item can already be equipped in the given slot"
        );

        // TODO(zomglings): When we support reupping items, we will need to modify the amount in the check
        // below to amount + existingItem.amount.
        require(
            itemType == LibInventory.UNEQUIP_ITEM_TYPE ||
                istore.SlotEligibleItems[slot][itemType][itemAddress][
                    itemTokenId
                ] >=
                amount,
            "InventoryFacet.equip: You can not equip those many instances of that item into the given slot"
        );

        // TODO(zomglings): Add case here when we need to support unequipping.
        if (itemType == LibInventory.ERC20_ITEM_TYPE) {
            IERC20 erc20Contract = IERC20(itemAddress);
            bool erc20TransferSuccess = erc20Contract.transferFrom(
                msg.sender,
                address(this),
                amount
            );
            require(
                erc20TransferSuccess,
                "InventoryFacet.equip: Error equipping ERC20 item - transfer was unsuccessful"
            );
        }

        istore.EquippedItems[istore.SubjectERC721Address][subjectTokenId][
                slot
            ] = LibInventory.EquippedItem({
            ItemType: itemType,
            ItemAddress: itemAddress,
            ItemTokenId: itemTokenId,
            Amount: amount
        });
    }

    function equipped(uint256 subjectTokenId, uint256 slot)
        external
        view
        returns (LibInventory.EquippedItem memory item)
    {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        LibInventory.EquippedItem memory equippedItem = istore.EquippedItems[
            istore.SubjectERC721Address
        ][subjectTokenId][slot];

        return equippedItem;
    }
}
