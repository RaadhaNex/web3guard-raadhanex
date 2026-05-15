// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SaferToken {
    address public owner;
    mapping(address => uint256) public balanceOf;

    event Minted(address indexed to, uint256 amount);
    event Withdrawn(address indexed to, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function mint(address to, uint256 amount) public onlyOwner {
        require(to != address(0), "zero address");
        balanceOf[to] += amount;
        emit Minted(to, amount);
    }

    function withdraw(address payable to, uint256 amount) public onlyOwner {
        require(to != address(0), "zero address");
        (bool success,) = to.call{value: amount}("");
        require(success, "transfer failed");
        emit Withdrawn(to, amount);
    }
}
