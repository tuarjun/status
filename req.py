import requests
import json
from time import gmtime, strftime

output = {}
output["backend"]=""
output["Lorem ipsum"]=""
output["flashy"]=""

def output_logs():
    time = strftime("%Y-%m-%d %H:%M:%S +0000", gmtime())
    with open("logs/backend_report.log","a") as f:
        f.write(time+", "+output["backend"]+"\n")
    with open("logs/flashy_report.log","a") as f:
        f.write(time+", "+output["flashy"]+"\n")
    with open("logs/lorem_ipsum_report.log","a") as f:
        f.write(time+", "+output["Lorem ipsum"]+"\n")

        
def chk_resp(resp):
    if resp.status_code!=200:
        for i in output.keys():
            output[i] = "failed"
        output_logs()
        exit(0)
    return resp

def login(URL,user,password):
    s = requests.Session()
    payload = { "query": "mutation ($username: String!, $password: String!, $token: String) {\n              login(username: $username, password: $password, token: $token) {\n                  id\n                  username\n                  name\n                  type\n              }\n            }","variables": { "username": user,"password":password ,"token": None,},}
    chk_resp(s.post(URL,json=payload))
    return s


def get_cstat(s,chall_id):
    payload = {"query":"query ($id: ID!) {\n          challenge(id: $id) {\n            isDeployable {\n              instance {\n                hasWebPage\n                isLive\n                isExternal\n                isShared\n                expiryTimestamp\n              }\n            }\n          }\n        }","variables":{"id":chall_id}}
    x = chk_resp(s.post(URL,json=payload))
    if json.loads(x.text)["data"]["challenge"]["isDeployable"]["instance"]:
        return True
    else:
        return False

# Check if challenge has instance first
def get_challs(s):
    pay_chall={"query":"query($keyword: String){\n                      contest{\n                          privateProperties{\n                              challenges(keyword: $keyword){\n                                   challenge{\n                                      value: id\n                                      label: name\n                                   }\n                              }\n                          }\n                      }\n                  }","variables":{"keyword":""}}
    x = chk_resp(s.post(URL,json=pay_chall))
    challs = json.loads(x.text)
    challs = challs["data"]["contest"]["privateProperties"]["challenges"]

    ret_chall = []
    for i in challs:
        tdict = {}
        tdict["id"] = i["challenge"]["value"]
        tdict["name"] = i["challenge"]["label"]
        ret_chall.append(tdict)
    
    return ret_chall

def deploy(s,id):
    payload = {"query":"mutation ($id: ID!){\n        spawnDeployment(challengeID: $id)\n      }","variables":{"id":id}}
    chk_resp(s.post(URL,json=payload))

def kill(s,id):
    payload = {"query":"mutation ($id: ID!){\n        terminateDeployment(challengeID: $id)\n      }","variables":{"id":id}}
    chk_resp(s.post(URL,json=payload))

URL="https://syfctf.eng.run/api/graphql/"
user="admin"
password="!nex#qJb*EG6dx"
s = login(URL,user,password)
 
challs = get_challs(s)
for i in challs:
    id = i["id"]
    name = i["name"]
    print(id,name)
    if(get_cstat(s,id)):
        kill(id)
    output[name] = "success"
    deploy(s,id)
    if(not get_cstat(s,id)):
        output[name] = "failed"
    kill(s,id)
    if(get_cstat(s,id)):
        output[name] = "failed"
output["backend"] = "success"
output_logs()
