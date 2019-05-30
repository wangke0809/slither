contract Greeter {
    /* Declare variable admin which will store an address */
    address public admin;

    /* this function is executed at initialization and sets the owner of the contract */
    constructor () {
        admin = msg.sender;
    }

    /* main function */
    function greet(bytes32 msg) returns (bytes32) {
        return msg;
    }
   
}
