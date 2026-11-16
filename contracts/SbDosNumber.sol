// Benchmark candidate ported from smartbugs-curated: dataset/denial_of_service/dos_number.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbDosNumber {

    uint numElements = 0;
    uint[] array;

    function insertNnumbers(uint value,uint numbers) public {

        for(uint i=0;i<numbers;i++) {
            if(numElements == array.length) {
                array.push();
            }
            array[numElements++] = value;
        }
    }

    function clear() public {
        require(numElements>1500);
        numElements = 0;
    }

    function clearDOS() public {

        require(numElements>1500);
        array = new uint[](0);
        numElements = 0;
    }

    function getLengthArray() public view returns(uint) {
        return numElements;
    }

    function getRealLengthArray() public view returns(uint) {
        return array.length;
    }
}
