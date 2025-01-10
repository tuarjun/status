import requests
import json
from time import gmtime, strftime, sleep
import concurrent.futures

output = {}

def output_logs():
    time = strftime("%Y-%m-%d %H:%M:%S +0000", gmtime())
    for i in output.keys():
        with open(f"logs/{i}_report.log","a") as f:
            f.write(time+", "+output[i]+"\n")        

    '''

    with open("logs/flashy_report.log","a") as f:
        f.write(time+", "+output["flashy"]+"\n")
    with open("logs/lorem_ipsum_report.log","a") as f:
        f.write(time+", "+output["Lorem ipsum"]+"\n")
    '''
        
def chk_resp(resp):
    if resp.status_code!=200:
       raise Exception("Backend")
    return resp

def login(URL,user,password):
    s = requests.Session()
    payload = { "query": "mutation ($username: String!, $password: String!, $token: String) {\n              login(username: $username, password: $password, token: $token) {\n                  id\n                  username\n                  name\n                  type\n              }\n            }","variables": { "username": user,"password":password ,"token": None,},}
    chk_resp(s.post(URL,json=payload))
    return s


def get_cstat(s,chall_id):
    payload = {"query":"query ($id: ID!) {\n          challenge(id: $id) {\n            isDeployable {\n              instance {\n                hasWebPage\n                isLive\n                isExternal\n                isShared\n                expiryTimestamp\n              }\n            }\n          }\n        }","variables":{"id":chall_id}}
    x = chk_resp(s.post(URL,json=payload))
    x = json.loads(x.text)["data"]["challenge"]
    if not x or not x["isDeployable"]:
        return [False,False]
    if x["isDeployable"]["instance"] and x["isDeployable"]["instance"]["isLive"]:
        return [True,True]
    else:
        return [True,False]

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


def chk_chall(s,id,name):
    result = "success"
    try:
        res = get_cstat(s,id)
        if res[0]:
            if res[1]:
                kill(s,id)
            deploy(s,id)
            tries = 0
            # Tries 30s (1minue) before moving on
            while tries<30:
                if get_cstat(s,id)[1]:
                    break
                tries += 5
                sleep(5)
            if not get_cstat(s,id)[1]:
                result="failed"
            kill(s,id)
        else:
            result="invalid"
    except:
        result = "failed"
        output["backend"] = "failed"
    return result

    
URL="https://synchrony.eng.run/api/graphql/"
user="statuscheckuser"
password="EtfLb4TUgfYx"
s = login(URL,user,password)

challs = get_challs(s)
#print(chk_chall(s,18,"meow"))


executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
futures = {}
for i in challs:
    id = i["id"]
    name = i["name"]
    print(id,name)
    future = executor.submit(chk_chall, s,id,name)
    futures[future] = id

for future in concurrent.futures.as_completed(futures):
    if future.result() == "invalid":
        continue
    for i in challs:
        if futures[future] == i["id"]:
            output[i["name"]] = future.result()
            break
if "backend" not in output.keys():        
    output["backend"] = "success"
output_logs()


    
'''
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
'''
