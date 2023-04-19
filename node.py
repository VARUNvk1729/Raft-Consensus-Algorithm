import threading
import time
import helper
from config import cfg

FOLLOWER = 0
CANDIDATE = 1
LEADER = 2


class Node():
    def __init__(self, fellow, my_ip):
        self.addr = my_ip
        self.fellow = fellow
        self.lock = threading.Lock()
        self.DB = {}
        self.log = []
        self.lastApplied = None
        self.term = 0
        self.status = FOLLOWER
        self.majority = ((len(self.fellow) + 1) // 2) + 1
        self.voteCount = 0
        self.commitIdx = 0
        self.timeout_thread = None
        self.init_timeout()

    def incrementVote(self):
        self.voteCount += 1
        if self.voteCount >= self.majority:
            print(f"{self.addr} becomes the leader of term {self.term}")
            self.status = LEADER
            self.startexecuteCmd()

    def startElection(self):
        self.term += 1
        self.voteCount = 0
        self.status = CANDIDATE
        self.init_timeout()
        self.incrementVote()
        self.send_vote_req()

    def send_vote_req(self):
        for voter in self.fellow:
            threading.Thread(target=self.ask_for_vote,args=(voter, self.term)).start()

    def ask_for_vote(self, voter, term):
        message = {
            "term": term,
            "commitIdx": self.commitIdx,
            "lastApplied": self.lastApplied
        }
        route = "requestVote"
        while self.status == CANDIDATE and self.term == term:
            reply = helper.send(voter, route, message)
            if reply:
                choice = reply.json()["choice"]
                # print(f"RECEIVED VOTE {choice} from {voter}")
                if choice and self.status == CANDIDATE:
                    self.incrementVote()
                elif not choice:
                    term = reply.json()["term"]
                    if term > self.term:
                        self.term = term
                        self.status = FOLLOWER
                break

    def decide_vote(self, term, commitIdx, lastApplied):
        if self.term < term and self.commitIdx <= commitIdx and (lastApplied or (self.lastApplied == lastApplied)):
            self.reset_timeout()
            self.term = term
            return True, self.term
        else:
            return False, self.term

    def startexecuteCmd(self):
        print("Starting HEARTBEAT")
        if self.lastApplied:
            self.handle_put(self.lastApplied)

        for each in self.fellow:
            t = threading.Thread(target=self.send_executeCmd, args=(each, ))
            t.start()

    def update_follower_commitIdx(self, follower):
        route = "executeCmd"
        first_message = {"term": self.term, "addr": self.addr}
        second_message = {
            "term": self.term,
            "addr": self.addr,
            "action": "commit",
            "entries": self.log[-1]
        }
        reply = helper.send(follower, route, first_message)
        if reply and reply.json()["commitIdx"] < self.commitIdx:
            reply = helper.send(follower, route, second_message)

    def send_executeCmd(self, follower):
        if self.log:
            self.update_follower_commitIdx(follower)

        route = "executeCmd"
        message = {"term": self.term, "addr": self.addr}
        while self.status == LEADER:
            start = time.time()
            reply = helper.send(follower, route, message)
            if reply:
                self.executeCmd_reply_handler(reply.json()["term"],reply.json()["commitIdx"])
            delta = time.time() - start
            time.sleep((cfg.HB_TIME - delta) / 1000)

    def executeCmd_reply_handler(self, term, commitIdx):
        if term > self.term:
            self.term = term
            self.status = FOLLOWER
            self.init_timeout()

    def reset_timeout(self):
        self.election_time = time.time() + helper.random_timeout()

    def executeCmd_follower(self, msg):
        term = msg["term"]
        if self.term <= term:
            self.leader = msg["addr"]
            self.reset_timeout()
            if self.status == CANDIDATE:
                self.status = FOLLOWER
            elif self.status == LEADER:
                self.status = FOLLOWER
                self.init_timeout()
            if self.term < term:
                self.term = term
            if "action" in msg:
                print("received action", msg)
                action = msg["action"]
                if action == "log":
                    entries = msg["entries"]
                    self.lastApplied = entries
                elif self.commitIdx <= msg["commitIdx"]:
                    if not self.lastApplied:
                        self.lastApplied = msg["entries"]
                    self.commit()
        print("received heartbeat from leader:", msg["addr"])
        return self.term, self.commitIdx

    def init_timeout(self):
        self.reset_timeout()
        if self.timeout_thread and self.timeout_thread.is_alive():
            return
        self.timeout_thread = threading.Thread(target=self.timeout_loop)
        self.timeout_thread.start()

    def timeout_loop(self):
        while self.status != LEADER:
            delta = self.election_time - time.time()
            if delta < 0:
                self.startElection()
            else:
                time.sleep(delta)

    def handle_get(self, entries):
        print("getting", entries)
        key = entries["key"]
        if key in self.DB:
            entries["value"] = self.DB[key]
            return entries
        else:
            return None

    def spread_update(self, message, confirmations=None, lock=None):
        for i, each in enumerate(self.fellow):
            r = helper.send(each, "executeCmd", message)
            if r and confirmations:
                # print(f" - - {message['action']} by {each}")
                confirmations[i] = True
        if lock:
            lock.release()

    def handle_put(self, entries):
        print("putting", entries)
        self.lock.acquire()
        self.lastApplied = entries
        waited = 0
        log_message = {
            "term": self.term,
            "addr": self.addr,
            "entries": entries,
            "action": "log",
            "commitIdx": self.commitIdx
        }
        log_confirmations = [False] * len(self.fellow)
        threading.Thread(target=self.spread_update,args=(log_message, log_confirmations)).start()
        while sum(log_confirmations) + 1 < self.majority:
            waited += 0.0005
            time.sleep(0.0005)
            if waited > cfg.MAX_LOG_WAIT / 1000:
                print(f"waited {cfg.MAX_LOG_WAIT} ms, update rejected:")
                self.lock.release()
                return False
        commit_message = {
            "term": self.term,
            "addr": self.addr,
            "entries": entries,
            "action": "commit",
            "commitIdx": self.commitIdx
        }
        self.commit()
        threading.Thread(target=self.spread_update,args=(commit_message, None, self.lock)).start()
        print("Sending message to all peers")
        return True

    def commit(self):
        self.commitIdx += 1
        self.log.append(self.lastApplied)
        key = self.lastApplied["key"]
        value = self.lastApplied["value"]
        self.DB[key] = value
        self.lastApplied = None
