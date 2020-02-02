pragma solidity 0.6.0;

contract DrugChain{
    
//basic datatypes for contract 
    struct Batch{
        uint id;
        string name;
        string secret;
        uint[] stops;
        uint status;
        bool exists;
    }
    
    struct Node{
        uint noBatches;
        bool exists;
        string name;
        uint level;
        address id;
        string lat;
        string lon;
        uint[] nodeBatches;
    }
    
    struct Stop{
        address nodeAddress;
        string timestamp;
    }

    
    
// global variables
    address public superuser;
    uint public nodeCount;
    uint public batchCount;
    uint public stopCount;
    uint[] public batchIds;
    address[] public nodeIds;
    
// mapping of objects
    mapping(uint => Batch) public batchMapping;
    mapping(address => Node ) public nodeMapping;
    mapping(uint => Stop) public stopMapping;
    mapping(address => bool) public adminMapping;
    
    constructor(address _owner) public{
        superuser = _owner;
        adminMapping[superuser] = true;
        nodeCount = 0;
        batchCount = 0;
    }
    
    
//Restrict function for superuserOnlyadmin use only 
    modifier superuserOnly()
    {
        require(
            msg.sender == superuser,
            "Sender not authorized."
        );
        _;
    }
    
    
        
//Restrict function for admin use only 
    modifier adminOnly()
    {
        require(
            adminMapping[msg.sender],
            "Sender not authorized."
        );
        _;
    }
    
    modifier nodeOnly(){
        require(
            nodeMapping[msg.sender].exists,
            "Not a node"
            );
            _;
    }
    
    
    function addAdmin(address _add) public superuserOnly(){
        adminMapping[_add] =true;
    }
    
    
    function addNode(string memory _name, uint _level, string memory _lat,string memory _lon,address _id) public adminOnly(){
        assert(nodeMapping[_id].exists == false);
        uint[] memory arr;
        nodeMapping[_id] = Node({name:_name, id: _id, level: _level, lat: _lat, lon: _lon, exists: true, noBatches: 0, nodeBatches:arr});
        nodeIds.push(_id);
        nodeCount += 1;
    }
    
    function addBatch(address _root, string memory _name, string memory _ts, string memory _secret) public adminOnly(){
        stopMapping[stopCount] =Stop({nodeAddress: _root, timestamp:_ts});
        uint[] memory _stops;
        batchMapping[batchCount] = Batch({id : batchCount, name: _name, secret: _secret,stops:_stops , status : 1, exists : true });
        batchMapping[batchCount].stops.push(stopCount);
        nodeMapping[_root].nodeBatches.push(batchCount);
        nodeMapping[_root].noBatches+=1;
        stopCount+=1;
        batchCount+=1;
        
    }
    
    function acceptBatch(uint _id, string memory _ts) public nodeOnly(){
        address _add = msg.sender;
        stopMapping[stopCount] =Stop({nodeAddress: _add, timestamp:_ts});
        batchMapping[_id].stops.push(stopCount);
        stopCount+=1;
    }
    
    function viewStops(uint _id) public view returns(uint[] memory){
        return batchMapping[_id].stops;
    }
    
    function nodeBatches(address _add) public view returns(uint[] memory){
        return nodeMapping[_add].nodeBatches;
        
    }
    
       
    
}
