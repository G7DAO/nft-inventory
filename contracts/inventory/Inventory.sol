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

    struct InventoryStorage {
        address AdminTerminusAddress;
        uint256 AdminTerminusPoolId;
        address SubjectERC721Address;
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
}
