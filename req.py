import requests
import json
from time import gmtime, strftime, sleep, localtime, tzset
import concurrent.futures
import os
import subprocess

        
def chk_resp(resp):
    if resp.status_code!=200:
       raise Exception("Backend")
    return resp

def login(URL,user,password):
    s = requests.Session()
    payload = { "query": "mutation ($username: String!, $password: String!, $token: String) {\n              login(username: $username, password: $password, token: $token) {\n                  id\n                  username\n                  name\n                  type\n              }\n            }","variables": { "username": user,"password":password ,"token": None,},}
    chk_resp(s.post(URL,json=payload))
    return s



def contest_stats(s):
    payload = {"query":"query {contentStats \nprofile:me {\n    id\n    name\n    username\n    team { id }\n    type\n    avatarID\n    avatarURL\n    preferDarkTheme\n    contestant{\n      id\n      score {\n        rank\n        points\n        flagsSubmitted\n      }\n    }\n    permissions {\n        viewAdminPanel\n    }\n} \nproperties: contest {\n    name\n    platformMode\n    startTimestamp\n    endTimestamp\n    isFrozen\n    isPaused\n    lockProfile\n    captchaConfig {\n      siteKey\n      provider\n    }\n    virtualDeskGroups {\n      name\n      nodeGroupID\n    }\n    isAcceptingRegistrations\n    googleAnalyticsTrackingID\n    footerMenu\n    allowTeams\n    allowIndividuals\n    allowedChallengeModes\n    styling {\n        lightLogoURL\n        colorLogoURL\n        iconURL\n        defaultTheme\n        disableThemeSwitching\n        customCSS\n        customHeadHTML\n        customFooterHTML\n        hideTrabodaBranding\n        darkTheme {\n            text\n            background\n            primary\n            secondary\n        }\n        lightTheme {\n            text\n            background\n            primary\n            secondary\n        }\n        footer {\n          copyrightText\n          socialLinks {\n            label\n            url\n          }\n        }\n    }\n    permissions {\n      can {\n        manage\n        viewChallenges\n        viewScoreboard\n        viewNotices\n        viewProfiles\n        viewAnalytics\n        viewSubmissions\n        viewSettings\n        viewTeams\n        viewUsers\n        viewLogs\n        viewRoles\n        register\n        manage\n      }\n    }\n    scoring {\n        filters\n        searchEnabled\n        headerGraph\n    }\n    contestantConfig{\n      affiliationLabel\n    }\n    privacyConfig {\n        showCookieBanner\n        consentText\n    }\n    securityConfig{\n        minimumPasswordLength\n        passwordShouldContain\n    }\n}}","variables":{}}
    x = chk_resp(s.post(URL,json=payload))
    x = json.loads(x.text)
    y = x["data"]["contentStats"]
    ret = {}
    keys = {"Total Challenges":"challenges","Total Registered Teams":"teams","Total Registered Users":"users","Current Total Submissions":"flag_submissions","Current Running Instances":"instances"}
    for i in keys.keys():
        ret[i] = y[keys[i]]

    keys = {"Start Time":"startTimestamp","End Time":"endTimestamp"}
    y = x["data"]["properties"]
    for i in keys.keys():
        ret[i] = y[keys[i]]
    return ret




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
            # Tries 60s (1minue) before moving on
            while tries<120:
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

tel_msg = ""
def li_insert(html,key,value):
    global tel_msg
    tel_msg += key+":"+value+"\n"
    key = key+":"
    idx = html.find(key)
    idx += len(key)
    html = html[:idx] +" "+ value + html[idx:]
    return html

URL="https://hackathon.dsci.in/api/graphql/"
user="adminadmin"
password="adminiswrong"

html = []    


with open(f"index.html.template","r") as f:
    html = f.read()

os.environ['TZ'] = "Asia/Kolkata"
tzset()
checktime = strftime("%Y-%m-%d %H:%M:%S +0530", localtime())
html = li_insert(html,"Last Checked",checktime)
url_real = URL[:URL.find("/api")]
#url_real = "<a href=\""+url_real+"\">"+url_real+"</a>"
html = li_insert(html,"Instance URL",url_real)

challs = {}
try:
    s = login(URL,user,password)
    stats = contest_stats(s)

    for i in stats.keys():
        html = li_insert(html,i,str(stats[i]))
    challs = get_challs(s)    
except Exception as ex:
    html = li_insert(html,"System Status","Backend DOWN")
    html = li_insert(html,"Backend","DOWN")
    subprocess.run(["./tel_send.sh",tel_msg])

output = {}

executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
futures = {}
for i in challs:
    id = i["id"]
    name = i["name"]

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
    html = li_insert(html,"Backend","UP")
    if any([output[i]!="success" for i in output]):
        html = li_insert(html,"System Status","Deployment DOWN")
        down_names = []
        for i in output:
            if output[i]!="success":
                down_names.append(i)

        html = li_insert(html,"Down Challenges",str(len(down_names)))

        idx = html.find("</body>")
        html_pre = html[:idx]
        html_post = html[idx:]

        html_pre += "<h2>Down Challenges</h2>\n"
        html_pre += "<ul>\n"
        for i in down_names:
            html_pre += "<li>"+i+"</li>\n"
        html_pre += "</ul>\n"

        html = html_pre + html_post

        subprocess.run(["./tel_send.sh",tel_msg])
    else:
        html = li_insert(html,"System Status","UP")
        html = li_insert(html,"Down Challenges","0")
        
else:
    html = li_insert(html,"System Status","Backend DOWN")
    html = li_insert(html,"Backend","DOWN")
    subprocess.run(["./tel_send.sh",tel_msg])
    del output["backend"]

print(html)
