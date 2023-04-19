import sys, requests
def redirectToLeader(server_address, message):
    type = message["type"]
    while True:
        if type == "get":
            try:
                response = requests.get(server_address,json=message,timeout=10)
            except Exception as e:
                return e
        else:
            try:
                response = requests.put(server_address,json=message,timeout=10)
            except Exception as e:
                return e
        if response.status_code == 200 and "entries" in response.json():
            entries = response.json()["entries"]
            if "message" in entries:
                server_address = entries["message"] + "/appendEntries"
            else:
                break
        else:
            break
    return response.json()

def put(addr, key, value):
    server_address = addr + "/appendEntries"
    entries = {'key': key, 'value': value}
    message = {"type": "put", "entries": entries}
    print(redirectToLeader(server_address, message))

def get(addr, key):
    server_address = addr + "/appendEntries"
    entries = {'key': key}
    message = {"type": "get", "entries": entries}
    print(redirectToLeader(server_address, message))

if __name__ == "__main__":
    if len(sys.argv) == 3:
        addr = sys.argv[1]
        key = sys.argv[2]
        get(addr, key)
    elif len(sys.argv) == 4:
        addr = sys.argv[1]
        key = sys.argv[2]
        val = sys.argv[3]
        put(addr, key, val)
  