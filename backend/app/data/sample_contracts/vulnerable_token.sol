// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableToken {
    address public owner;
    mapping(address => uint256) public balanceOf;

    constructor() {
        owner = msg.sender;
    }

    function mint(address to, uint256 amount) public {
        balanceOf[to] += amount;
    }

    function withdraw(address payable to, uint256 amount) public {
        require(tx.origin == owner, "not owner");
        to.call{value: amount}("");
        balanceOf[msg.sender] -= amount;
    }

    function randomReward() public view returns (uint256) {
        return uint256(blockhash(block.number - 1)) + block.timestamp;
    }
}
