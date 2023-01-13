// SPDX-License-Identifier: UNLICENSED

/**
 * Authors: Moonstream DAO (engineering@moonstream.to)
 * GitHub: https://github.com/G7DAO/contracts
 */

pragma solidity 0.8.17;

import {TerminusPermissions} from "@moonstream/contracts/terminus/TerminusPermissions.sol";
import {DiamondReentrancyGuard} from "@moonstream-engine/contracts/diamond/security/DiamondReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC1155/utils/ERC1155Holder.sol";
import "@openzeppelin/contracts/token/ERC721/utils/ERC721Holder.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC1155/IERC1155.sol";
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

    // EquippedItem represents an item equipped in a specific inventory slot for a specific ERC721 token.
    struct EquippedItem {
        uint256 ItemType;
        address ItemAddress;
        uint256 ItemTokenId;
        uint256 Amount;
    }

    struct InventoryStorage {
        address adminTerminusAddress;
        uint256 adminTerminusPoolId;
        address subjectERC721Address;
        uint256 NumSlots;
        // Slot => true if items can be unequipped from that slot and false otherwise
        mapping(uint256 => bool) slotIsUnequippable;
        // Slot => item type => item address => item pool ID => maximum equippable
        // For ERC20 and ERC721 tokens, item pool ID is assumed to be 0. No data will be stored under positive
        // item pool IDs.
        //
        // NOTE: It is possible for the same contract to implement multiple of these ERCs (e.g. ERC20 and ERC721),
        // so this data structure actually makes sense.
        mapping(uint256 => mapping(uint256 => mapping(address => mapping(uint256 => uint256)))) slotEligibleItems;
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
        mapping(address => mapping(uint256 => mapping(uint256 => EquippedItem))) equippedItems;
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

    modifier requireValidItemType(uint256 itemType) {
        require(
            itemType == LibInventory.ERC20_ITEM_TYPE ||
                itemType == LibInventory.ERC721_ITEM_TYPE ||
                itemType == LibInventory.ERC1155_ITEM_TYPE,
            "InventoryFacet.requireValidItemType: Invalid item type"
        );
        _;
    }

    event AdministratorDesignated(
        address indexed adminTerminusAddress,
        uint256 indexed adminTerminusPoolId
    );

    event SubjectDesignated(address indexed subjectAddress);

    event SlotCreated(address indexed creator, uint256 slot, bool unequippable);

    event ItemMarkedAsEquippableInSlot(
        uint256 indexed slot,
        uint256 indexed itemType,
        address indexed itemAddress,
        uint256 itemPoolId,
        uint256 maxAmount
    );

    event ItemEquipped(
        uint256 indexed subjectTokenId,
        uint256 indexed slot,
        uint256 itemType,
        address indexed itemAddress,
        uint256 itemTokenId,
        uint256 amount,
        address equippedBy
    );

    event ItemUnequipped(
        uint256 indexed subjectTokenId,
        uint256 indexed slot,
        uint256 itemType,
        address indexed itemAddress,
        uint256 itemTokenId,
        uint256 amount,
        address unequippedBy
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

    function createSlot(bool unequippable)
        external
        onlyAdmin
        returns (uint256)
    {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        // Slots are 1-indexed!
        istore.NumSlots += 1;
        uint256 newSlot = istore.NumSlots;
        istore.SlotIsUnequippable[newSlot] = unequippable;

        emit SlotCreated(msg.sender, newSlot, unequippable);
        return newSlot;
    }

    function numSlots() external view returns (uint256) {
        return LibInventory.inventoryStorage().NumSlots;
    }

    function slotIsUnequippable(uint256 slot) external view returns (bool) {
        return LibInventory.inventoryStorage().SlotIsUnequippable[slot];
    }

    function markItemAsEquippableInSlot(
        uint256 slot,
        uint256 itemType,
        address itemAddress,
        uint256 itemPoolId,
        uint256 maxAmount
    ) external onlyAdmin requireValidItemType(itemType) {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

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

    function _unequip(
        uint256 subjectTokenId,
        uint256 slot,
        bool unequipAll,
        uint256 amount
    ) internal {
        require(
            !unequipAll || amount == 0,
            "InventoryFacet._unequip: Set amount to 0 if you are unequipping all instances of the item in that slot"
        );

        require(
            unequipAll || amount > 0,
            "InventoryFacet._unequip: Since you are not unequipping all instances of the item in that slot, you must specify how many instances you want to unequip"
        );

        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        require(
            istore.SlotIsUnequippable[slot],
            "InventoryFacet._unequip: That slot is not unequippable"
        );

        LibInventory.EquippedItem storage existingItem = istore.EquippedItems[
            istore.SubjectERC721Address
        ][subjectTokenId][slot];

        if (unequipAll) {
            amount = existingItem.Amount;
        }

        require(
            amount <= existingItem.Amount,
            "InventoryFacet._unequip: Attempting to unequip too many items from the slot"
        );

        if (existingItem.ItemType == 20) {
            IERC20 erc20Contract = IERC20(existingItem.ItemAddress);
            bool transferSuccess = erc20Contract.transfer(msg.sender, amount);
            require(
                transferSuccess,
                "InventoryFacet._unequip: Error unequipping ERC20 item - transfer was unsuccessful"
            );
        } else if (existingItem.ItemType == 721 && amount > 0) {
            IERC721 erc721Contract = IERC721(existingItem.ItemAddress);
            erc721Contract.safeTransferFrom(
                address(this),
                msg.sender,
                existingItem.ItemTokenId
            );
        } else if (existingItem.ItemType == 1155) {
            IERC1155 erc1155Contract = IERC1155(existingItem.ItemAddress);
            erc1155Contract.safeTransferFrom(
                address(this),
                msg.sender,
                existingItem.ItemTokenId,
                existingItem.Amount,
                ""
            );
        }

        emit ItemUnequipped(
            subjectTokenId,
            slot,
            existingItem.ItemType,
            existingItem.ItemAddress,
            existingItem.ItemTokenId,
            amount,
            msg.sender
        );

        existingItem.Amount -= amount;
        if (existingItem.Amount == 0) {
            delete istore.EquippedItems[istore.SubjectERC721Address][
                subjectTokenId
            ][slot];
        }
    }

    function equip(
        uint256 subjectTokenId,
        uint256 slot,
        uint256 itemType,
        address itemAddress,
        uint256 itemTokenId,
        uint256 amount
    ) external requireValidItemType(itemType) diamondNonReentrant {
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

        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        IERC721 subjectContract = IERC721(istore.SubjectERC721Address);
        require(
            msg.sender == subjectContract.ownerOf(subjectTokenId),
            "InventoryFacet.equip: Message sender is not owner of subject token"
        );

        // TODO(zomglings): Although this does the job, it is not gas-efficient if the caller is
        // increasing the amount of an existing token in the given slot. To increase gas-efficiency,
        // we could add more complex logic here to handle that situation by only equipping the difference
        // between the existing amount of the token and the target amount.
        if (
            istore
            .EquippedItems[istore.SubjectERC721Address][subjectTokenId][slot]
                .ItemType != 0
        ) {
            _unequip(subjectTokenId, slot, true, 0);
        }

        require(
            // Note the if statement when accessing the itemPoolId key in the SlotEligibleItems mapping.
            // That field is only relevant for ERC1155 tokens. For ERC20 and ERC721 tokens, the capacity
            // is set under the 0 key in that position.
            // Using itemTokenId as the key in that position would incorrectly yield a value of 0 for
            // ERC721 tokens.
            istore.SlotEligibleItems[slot][itemType][itemAddress][
                itemType == 1155 ? itemTokenId : 0
            ] >= amount,
            "InventoryFacet.equip: You can not equip those many instances of that item into the given slot"
        );

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
        } else if (itemType == LibInventory.ERC721_ITEM_TYPE) {
            IERC721 erc721Contract = IERC721(itemAddress);
            require(
                msg.sender == erc721Contract.ownerOf(itemTokenId),
                "InventoryFacet.equip: Message sender cannot equip an item that they do not own"
            );
            erc721Contract.safeTransferFrom(
                msg.sender,
                address(this),
                itemTokenId
            );
        } else if (itemType == LibInventory.ERC1155_ITEM_TYPE) {
            IERC1155 erc1155Contract = IERC1155(itemAddress);
            require(
                erc1155Contract.balanceOf(msg.sender, itemTokenId) >= amount,
                "InventoryFacet.equip: Message sender does not own enough of that item to equip"
            );
            erc1155Contract.safeTransferFrom(
                msg.sender,
                address(this),
                itemTokenId,
                amount,
                ""
            );
        }

        emit ItemEquipped(
            subjectTokenId,
            slot,
            itemType,
            itemAddress,
            itemTokenId,
            amount,
            msg.sender
        );

        istore.EquippedItems[istore.SubjectERC721Address][subjectTokenId][
                slot
            ] = LibInventory.EquippedItem({
            ItemType: itemType,
            ItemAddress: itemAddress,
            ItemTokenId: itemTokenId,
            Amount: amount
        });
    }

    function unequip(
        uint256 subjectTokenId,
        uint256 slot,
        bool unequipAll,
        uint256 amount
    ) external diamondNonReentrant {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        IERC721 subjectContract = IERC721(istore.SubjectERC721Address);
        require(
            msg.sender == subjectContract.ownerOf(subjectTokenId),
            "InventoryFacet.equip: Message sender is not owner of subject token"
        );

        _unequip(subjectTokenId, slot, unequipAll, amount);
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
