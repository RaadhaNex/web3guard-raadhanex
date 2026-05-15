// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract UpgradeableInitRisk {
    address public owner;
    address public implementation;

    function initialize(address newOwner) public {
        owner = newOwner;
    }

    function upgradeTo(address newImplementation) public {
        implementation = newImplementation;
    }
}
