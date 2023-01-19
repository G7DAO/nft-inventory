// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../libraries/LibInventory.sol";


interface IInventory {

    event AdministratorDesignated(
        address indexed adminTerminusAddress,
        uint256 indexed adminTerminusPoolId
    );

    event ContractAddressDesignated(address indexed contractAddress);

    event SlotCreated(address indexed creator, uint256 slot, bool unequippable);

    event ItemMarkedAsEquippableInSlot(
        uint256 indexed slot,
        uint256 indexed itemType,
        address indexed itemAddress,
        uint256 itemPoolId,
        uint256 maxAmount
    );

    event AssignSlotToSubjectTokenId(uint indexed toSubjectTokenId, uint256 indexed slotId);

    event NewSlotURI(uint indexed slotId);

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

    function init(
        address adminTerminusAddress,
        uint256 adminTerminusPoolId,
        address subjectAddress
    ) external;

    function adminTerminusInfo() external view returns (address, uint256);

    function subject() external view returns (address);

    function createSlot(bool unequippable, uint256 slotType, string memory slotURI)
        external returns (uint256);

    function numSlots() external view returns (uint256);

    function slotIsUnequippable(uint256 slotId) external view returns (bool);

    function markItemAsEquippableInSlot(
        uint256 slot,
        uint256 itemType,
        address itemAddress,
        uint256 itemPoolId,
        uint256 maxAmount
    ) external;

    function maxAmountOfItemInSlot(
        uint256 slot,
        uint256 itemType,
        address itemAddress,
        uint256 itemPoolId
    ) external view returns (uint256);

    function equip(
        uint256 subjectTokenId,
        uint256 slot,
        uint256 itemType,
        address itemAddress,
        uint256 itemTokenId,
        uint256 amount
    ) external;

    function unequip(
        uint256 subjectTokenId,
        uint256 slot,
        bool unequipAll,
        uint256 amount
    ) external;

    function getEquippedItems(uint256 subjectTokenId, uint256 slot)
        external
        view
        returns (LibInventory.EquippedItem memory item);

    function getSlotById(uint256 subjectTokenId, uint slotId)
        external
        view
        returns (LibInventory.Slot memory slots);

    function getSubjectTokenSlots(uint256 subjectTokenId)
        external
        view
        returns(LibInventory.Slot[] memory slot);
    
    function assignSlotToSubjectTokenId(uint256 toSubjectTokenId, uint256 slotId) external;

    function getSlotURI(uint256 slotId) external view returns (string memory);
}