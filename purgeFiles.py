# this will traverse the tree, but backwards. 
# NOTE: This script WILL delete files that have a purge value less than their 'last-modified' date, in days.

# TODO: remove unnecessary / all(?) print statements
import requests
import argparse
from datetime import datetime, timezone
import time
import math
import sys

argParse = argparse.ArgumentParser(description='Arguments for Artifactory Purge')

argParse.add_argument('-p', '--production',
                    help='Set -p flag to explicitly run script on Artifactory Production server. Otherwise, runs on stage.',
                    action='store_true')

argParse.add_argument('-rt', '--reference-token',
                    help='Reference token created in Artifactory.',
                    required=True, action='store')

argParse.add_argument('-u', '--username',
                    help='Artifactory username.',
                    required=True, action='store')

argParse.add_argument('-r', '--repo',
                    help='Parent directory to begin purge. Defaults to wildcard "*" if not set.',
                    default='*',
                    action='store')

argParse.add_argument('--user_confirming_deletion',
                     help='This flag is required to actually perform deletions. If this flag is not explicitly set, no actual deletion will occur.',
                     action='store_true')

scriptArgs = argParse.parse_args()

AQL_USER = scriptArgs.username
AQL_TOK = scriptArgs.reference_token
deletionConfirmation = scriptArgs.user_confirming_deletion

# Assign server based on user input
if scriptArgs.production:
    ART_URL = "https://artifactory.domain.com/artifactory/"
else:
    ART_URL = "https://artifactory-stage.domain.com/artifactory/"

# Check user credentials
ping = "api/system/ping"
repoType = "api/repositories/"
AQL_AUTH_URL = ART_URL + ping
auth = (AQL_USER, AQL_TOK)

authUser = requests.get(AQL_AUTH_URL, auth=auth)
if not authUser.ok:
    print("Error authenticating user. Try again...")
    sys.exit(1)

headers = {"Content-Type": "text/plain"}

totalArtifacts = 0
deletedArtifacts = 0
wouldBeDeletedArtifacts = 0
pathPurgeDict = {}
todayDate = datetime.now()

# Function definitions
def summarizeFile(repo, path, name, days, purgeValue):
    print("\n======================================================================")
    print("======================================================================")
    print(f"Filename: {repo}{path}/{name}")
    
    print(f" - Repository: {repo}")
    print(f" - File Path: {path}")
    print(f" - File: {name}")

    print(f" - File deleted if {days} > {purgeValue}")
    
    print("--------------------------------------------------")

def daysOld(fileModifiedDate):
    dateDays = datetime.fromisoformat(fileModifiedDate)
    dtUtc = dateDays.astimezone(timezone.utc)

    currentUtc = datetime.now(timezone.utc)
    delta = dtUtc - currentUtc
    days = abs(delta.days)
    
    return days

def filePurge(repo, path, name, purgeValue, fileModifiedDate):
    # This is where the fun begins. 
    # if 'NEVER' is enccountered, the file will not be edited.
    if str(purgeValue).lower() == "never":
        return
    purgeURL = f'{ART_URL}api/storage/{repo}{path}/{name}'
    deleteURL = f'{ART_URL}{repo}{path}/{name}'
    fileRequest = requests.get(purgeURL, auth=auth)
    
    if fileRequest.status_code == 200:
        days = int(daysOld(fileModifiedDate))
        # all purge values are rounded UP to nearest whole number.
        purgeValue = int(math.ceil(float(purgeValue)))
        if days > purgeValue:
            if deletionConfirmation:
                summarizeFile(repo, path, name, days, purgeValue)
                # gone.
                purgeAction = requests.delete(deleteURL, auth=auth)
                global deletedArtifacts
                deletedArtifacts += 1
                if purgeAction.status_code == 204:
                    print(f"Purge successful. File {name} moved to trash bin.\n----------------------------------------------------------------------")
                    return
                    
                else:
                    print(f"Purge unsuccessful. File {name} has NOT been removed.")
            else:
                summarizeFile(repo, path, name, days, purgeValue)
                print(f"{name} not purged because the deletion flag was not set in initial query.\n----------------------------------------------------------------------")
                global wouldBeDeletedArtifacts
                wouldBeDeletedArtifacts += 1
                return
    else:
        print(f"{name} has been altered or no longer exists at {repo}{path}. ")

def reverseTraverse(repo, path, name, date):
    path = '/' + path
    backPath = path + '/' + name
    purgeFound = False

    currentLeafPath = repo + path
    dictPath = repo + backPath
    
    while not purgeFound:  
        dictPath = repo + backPath
        if pathPurgeDict.get(dictPath) == "NA":
            pass
                    
        elif pathPurgeDict.get(dictPath):
            fullPath = currentLeafPath + '/' + name
            purgeFound = True

            # ensures file-based purge values are not inherited
            if fullPath != dictPath:
                pathPurgeDict[currentLeafPath] = pathPurgeDict[dictPath]
                
            # purge action
            filePurge(repo, path, name, pathPurgeDict[dictPath], date)
            purgeFound = True
            
        elif not pathPurgeDict.get(dictPath):
            pathPurgeDict[dictPath] = "NA"

        backPath = backPath.rstrip('/')
        index = backPath.rfind('/')
        if index == -1:
            return
        else:
            backPath = backPath[:index]

def addPurgeToDictionary(item, propertyArray):
    purgeValueArray = []
    dictPath = ''
    for k in propertyArray:
        if k['key'].lower() == "purge":
            # handling parent directories, and the '.' oddity.
            if item['path'][0] == '.':
                dictPath = item['repo'] + '/' + item['name']
            else:
                dictPath = item['repo'] + '/' + item['path'] + '/' + item['name']

            # 'never' shouldn't be an array. that always takes priority. 
            # if 'never' is found, it is set, and we move on to the next artifact.
            if k['value'].lower() == "never":
                pathPurgeDict[dictPath] = k['value']
                return

            # handles purge values like 'Four days' or '5 hours'
            try:   
                purgeValueArray.append(abs(int(k['value'])))
            except Exception:
                continue
    if purgeValueArray:
        pathPurgeDict[dictPath] = int(max(purgeValueArray))

def getEachFile(path, repo):
    fileQuery = f'''items.find({{
        "repo": "{repo}",
        "path": {{"$match": "{path}"}},
        "type": "file"
    }}).include("@*")'''    
    aqlUrl = f"{ART_URL}/api/search/aql"
    aqlReq = requests.post(aqlUrl, data=fileQuery, headers=headers, auth=auth)
    if aqlReq.ok:
        aqlResult = aqlReq.json()
        for item in aqlResult.get('results', []):
            testpath = item['repo'] + item['path']
            propCheck = item.get('properties', {})
            
            if propCheck:
                addPurgeToDictionary(item, propCheck)
            fileName = item['name']
            filePath = item['path']
            lastModified = item['modified']
            
            reverseTraverse(repo, filePath, fileName, lastModified)
            global totalArtifacts
            totalArtifacts += 1
                        
def get_all_info(repo):
    print(f"\nCalling `get_all_info() on {repo}`")
    print("Starting initial query...")
    dirQuery = f'''items.find({{
        "repo": {{"$match": "{repo}"}},
        "type": "folder"
        }}).include("@*")'''    
    
    aqlUrl = f"{ART_URL}/api/search/aql"
    aqlReq = requests.post(aqlUrl, data=dirQuery, headers=headers, auth=auth)

    if aqlReq.ok:
        aqlResult = aqlReq.json()     
        for item in aqlResult.get('results', []):          
            propCheck = item.get('properties', {})
            if propCheck:  
                addPurgeToDictionary(item, propCheck)
            
            passRepo = item['repo']
            passPath = item['path'] + '/' + item['name']            
            getEachFile(passPath, passRepo)
    else:
        print("\n" + "-"*75)
        errorMessage = "Could not make a successful query. Check one of the following: \n  - Username\n  - Reference Token\n  - Query syntax\n"
        print(errorMessage)

# TODO: remove in final deployment
if scriptArgs.production and scriptArgs.user_confirming_deletion:
    userDoubleCheck = input(f"NOTE: This script will delete outdated files marked for deletion on PROD SERVER because you explicitly defined the deletion flag. Press [ENTER] to confirm...")

start = round(time.time(), 2)
path='*'

# check for 'repo type' and 'package type'
typeUrl = ART_URL + repoType

repoTypeReq = requests.get(typeUrl, auth=auth)
if repoTypeReq.status_code == 200:
    for item in repoTypeReq.json():
        if item['type'] == "LOCAL" and item['packageType'] == "Generic":
            get_all_info(item['key'])

print("\n-----------------------------------")
print(f"Total artifacts scanned: {totalArtifacts}")
print(f"Deleted artifacts: {deletedArtifacts}")
end = round(time.time(), 2)
print(f"Purge Time: {end-start} seconds")

if not scriptArgs.user_confirming_deletion:
    print(f"This would have removed {wouldBeDeletedArtifacts} artifacts if the deletion flag was set.")
    print("\n* Use '--user_confirming_deletion' to prompt script to delete files.")
