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
import "../libraries/LibDiamond.sol";
import "../libraries/LibInventory.sol";
import "../interfaces/IInventory.sol";

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
- [] Equip ERC20 tokens in eligible inventory slots
- [] Equip ERC721 tokens in eligible inventory slots
- [] Equip ERC1155 tokens in eligible inventory slots
- [ ] Unequip items from unequippable slots

Batch endpoints:
- [ ] Marking items as equippable
- [ ] Equipping items
- [ ] Unequipping items
 */
contract InventoryFacet is
    IInventory,
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

    // TODO: @ogarciarevett finish this
    // modifier onlySlotOwner(uint256 slotId) {
    //     // LibInventory.InventoryStorage storage istore = LibInventory.inventoryStorage();

    //     // // TODO: @ogarciarevett check if asking for the msg.sender will be required, if the user change the wallet could loose this relation
    //     // istore.SubjectSlots[msg.sender]

    //     // require(msg.sender);

    //     _;
    // }

    modifier requireValidItemType(uint256 itemType) {
        require(
            itemType == LibInventory.ERC20_ITEM_TYPE ||
                itemType == LibInventory.ERC721_ITEM_TYPE ||
                itemType == LibInventory.ERC1155_ITEM_TYPE,
            "InventoryFacet.requireValidItemType: Invalid item type"
        );
        _;
    }

    /**
    An Inventory must be initialized with:
    1. adminTerminusAddress: The address for the Terminus contract which hosts the Administrator badge.
    2. adminTerminusPoolId: The pool ID for the Administrator badge on that Terminus contract.
    3. contractAddress: The address of the ERC721 contract that the Inventory refers to.
     */
    function init(
        address adminTerminusAddress,
        uint256 adminTerminusPoolId,
        address contractAddress
    ) external {
        LibDiamond.enforceIsContractOwner();
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();
        istore.AdminTerminusAddress = adminTerminusAddress;
        istore.AdminTerminusPoolId = adminTerminusPoolId;
        istore.ContractERC721Address = contractAddress;

        emit AdministratorDesignated(adminTerminusAddress, adminTerminusPoolId);
        emit ContractAddressDesignated(contractAddress);
    }

    function adminTerminusInfo() external view returns (address, uint256) {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();
        return (istore.AdminTerminusAddress, istore.AdminTerminusPoolId);
    }

    function subject() external view returns (address) {
        return LibInventory.inventoryStorage().ContractERC721Address;
    }

    function createSlot(
        bool unequippable,
        uint256 slotType,
        string memory slotURI
    )
        external
        onlyAdmin
        returns (uint256)
    {
        require(slotType <= uint(LibInventory.SlotType.Trophies) && slotType >= uint(LibInventory.SlotType.Clothes));

        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        // Slots are 1-indexed!
        istore.NumSlots += 1;
        uint256 newSlot = istore.NumSlots;
        
        // save the slot type!
        istore.SlotData[newSlot] = LibInventory.Slot({
            slotType: LibInventory.SlotType(slotType),
            SlotURI: slotURI,
            SlotIsUnequippable: unequippable,
            SlotId: newSlot
        });

        emit SlotCreated(msg.sender, newSlot, unequippable);
        return newSlot;
    }

    function assignSlotToSubjectTokenId(uint256 toSubjectTokenId, uint256 slotId) external onlyAdmin {
        LibInventory.InventoryStorage storage istore = LibInventory.inventoryStorage();

        LibInventory.Slot memory slotData = istore.SlotData[slotId];

        istore.SubjectSlots[istore.ContractERC721Address][toSubjectTokenId].push(slotData);

        emit AssignSlotToSubjectTokenId(
            toSubjectTokenId,
            slotId
        );
    }

    function getSubjectTokenSlots(uint256 subjectTokenId) external view returns(LibInventory.Slot[] memory slots) {
        LibInventory.InventoryStorage storage istore = LibInventory.inventoryStorage();
        IERC721 subjectContract = IERC721(istore.ContractERC721Address);
        require(
            msg.sender == subjectContract.ownerOf(subjectTokenId),
            "InventoryFacet.getSubjectTokenSlots: Message sender is not owner of subject token"
        );
        return istore.SubjectSlots[istore.ContractERC721Address][subjectTokenId];
    }

    // COUNTER
    function numSlots() external view returns (uint256) {
        return LibInventory.inventoryStorage().NumSlots;
    }

    function getSlotById(uint256 subjectTokenId, uint slotId)
        external
        view
        // @TODO: @ogarciarevett add slotOwner modifier
        returns (LibInventory.Slot memory slot) {
        
        return LibInventory.inventoryStorage().SlotData[slotId];
    }
    
    function getSlotURI(uint256 slotId) external view returns (string memory) {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        return istore.SlotData[slotId].SlotURI;
    }

    // @TODO: @ogarciarevett add slotOwner modifier
    function setSlotUri(string memory newSlotURI, uint slotId) external diamondNonReentrant {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        LibInventory.Slot memory slot = istore.SlotData[slotId];
        slot.SlotURI = newSlotURI;
        emit NewSlotURI(slotId);
    }

    function slotIsUnequippable(uint256 slotId) external view returns (bool) {
        return LibInventory.inventoryStorage().SlotData[slotId].SlotIsUnequippable;
    }

    // TODO: @ogarciarevett remove this, is already in the Slot struct
    // function _slotIsUnequippable(uint256 slot) external view returns (bool) {
    //     return LibInventory.inventoryStorage().SlotIsUnequippable[slot];
    // }

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
            istore.SlotData[slot].SlotIsUnequippable,
            "InventoryFacet._unequip: That slot is not unequippable"
        );

        LibInventory.EquippedItem storage existingItem = istore.EquippedItems[
            istore.ContractERC721Address
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
                amount,
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
            delete istore.EquippedItems[istore.ContractERC721Address][
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
                amount == 1,
            "InventoryFacet.equip: amount can be other value than 1 only for ERC20 and ERC1155 items"
        );

        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        IERC721 subjectContract = IERC721(istore.ContractERC721Address);
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
            .EquippedItems[istore.ContractERC721Address][subjectTokenId][slot]
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

        istore.EquippedItems[istore.ContractERC721Address][subjectTokenId][
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

        IERC721 subjectContract = IERC721(istore.ContractERC721Address);
        require(
            msg.sender == subjectContract.ownerOf(subjectTokenId),
            "InventoryFacet.equip: Message sender is not owner of subject token"
        );

        _unequip(subjectTokenId, slot, unequipAll, amount);
    }

    function getEquippedItems(uint256 subjectTokenId, uint256 slot)
        external
        view
        returns (LibInventory.EquippedItem memory item)
    {
        LibInventory.InventoryStorage storage istore = LibInventory
            .inventoryStorage();

        LibInventory.EquippedItem memory equippedItem = istore.EquippedItems[
            istore.ContractERC721Address
        ][subjectTokenId][slot];

        return equippedItem;
    }
}
