# Raft-Consensus-Algorithm

Refer this paper: [raft.pdf](https://github.com/VARUNvk1729/Raft-Consensus-Algorithm/files/11268629/raft.pdf)
 
This is a simple implementation of the Raft consensus algorithm in Python. The implementation covers the following tasks:
 
1. Leader Election
In this task, X number of nodes are set up, where each node initially starts as a follower with a random timer (between 1500-3000ms). When the timer expires, the node becomes a candidate and requests votes from all other nodes. If a candidate receives the majority of the votes, it becomes a leader and sends a heartbeat to all nodes. The paper provides detailed technical information.
 
2. Append Entries
Once a leader is elected, it can start servicing client requests. Each client request contains a command to be executed. The leader appends the command to its log as a new entry and then sends appendEntries in parallel to each of the other servers/nodes to replicate the log entry.
 
For this task, a client (such as Postman) calls the leader's /executeCommand, which adds the command to the log entry at that checkpoint. The leader then sends the log to all other nodes.
 
Example:
 
Let's say there are four nodes, and node 1 is the leader. When node 1 receives the executeCommand request from the client, it adds the command to the log entry and sends the log to all other nodes.
 
![image](https://user-images.githubusercontent.com/76661061/232969338-c78349bc-40eb-45b8-a4c2-90a7f6500e70.png)
 
 
TO DO:
 
3. Node Recovery
If a node crashes and then rejoins the network, it needs to catch up on the existing logs of the other nodes. In this task, you need to add logic where a new node catches up with the existing node's log entries.
 
Please refer to the paper for more details on the Raft consensus algorithm.
 
If you notice any grammatical errors, please feel free to correct them to make this README more readable.
