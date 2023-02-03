// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface IDiamond {
    fallback() external payable;

    receive() external payable;
}