from node import Node
from node import FOLLOWER,CANDIDATE, LEADER
from flask import Flask, request, jsonify
import sys
import logging
app = Flask(__name__)


@app.route("/appendEntries", methods=['GET'])
def value_get():
    entries = request.json["entries"]
    reply = {"code": 'fail', 'entries': entries}
    if n.status == LEADER:
        result = n.handle_get(entries)
        if result:
            reply = {"code": "success", "entries": result}
    elif n.status == FOLLOWER:
        reply["entries"]["message"] = n.leader
        print(reply)
    return jsonify(reply)


@app.route("/appendEntries", methods=['PUT'])
def value_put():
    entries = request.json["entries"]
    reply = {"code": 'fail'}
     
    if n.status == LEADER:
        result = n.handle_put(entries)
        if result:
            reply = {"code": "success"}
    elif n.status == FOLLOWER:
        print("dfdsfvsfb",n.leader)
        entries["message"] = n.leader
        reply["entries"] = entries
    return jsonify(reply)


@app.route("/requestVote", methods=['POST'])
def requestVote():
    term = request.json["term"]
    commitIdx = request.json["commitIdx"]
    lastApplied = request.json["lastApplied"]
    choice, term = n.decide_vote(term, commitIdx, lastApplied)
    message = {"choice": choice, "term": term}
    return jsonify(message)


@app.route("/executeCmd", methods=['POST'])
def executeCmd():
    term, commitIdx = n.executeCmd_follower(request.json)
    message = {"term": term, "commitIdx": commitIdx}
    return jsonify(message)


log = logging.getLogger('werkzeug')
log.disabled = True

if __name__ == "__main__":
    if len(sys.argv) == 3:
        index = int(sys.argv[1])
        ip_list_file = sys.argv[2]
        ports= []
        with open(ip_list_file) as f:
            for ip in f:
                ports.append(ip.strip())
        my_ip = ports.pop(index)
        http, host, port = my_ip.split(':')
        n = Node(ports, my_ip)
        app.run(host="0.0.0.0", port=int(port), debug=False)