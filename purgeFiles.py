# this will traverse the tree, but backwards. 
# NOTE: This script WILL delete files that have a purge value less than their 'last-modified' date, in days.

# TODO: Make deploy changes
import requests
import argparse
from datetime import datetime, timezone, timedelta
import time
import math
import sys
import tempfile
import os
from smtplib import SMTP
from email.mime.text import MIMEText

# obtain file from argument
argParse = argparse.ArgumentParser(description='Arguments for Artifactory Purge')

argParse.add_argument('-l', '--logpath',
                    help='File path to write a report of deleted files.',
                    action='store',
                    required=True)

argParse.add_argument('-p', '--production',
                    help='Set -p flag to explicitly run script on Artifactory Production server. Otherwise, runs on stage.',
                    action='store_true')

argParse.add_argument('--user_confirming_deletion',
                     help='This flag is required to actually perform deletions. If this flag is not explicitly set, no actual deletion will occur.',
                     action='store_true')

argParse.add_argument('-rt', '--reference-token',
                    help='Reference token created in Artifactory.',
                    action='store',
                    required=True)

argParse.add_argument('-u', '--username',
                    help='Artifactory username.',
                    action='store',
                    required=True)

# setting arguments
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
totalFreedStorageSpace = 0
pathPurgeDict = {}
ownershipDict = {}
emailDictionary = {}
tempDirectory = tempfile.gettempdir() + "/myTmpDire"
todayDate = datetime.now()
senderEmail = "devops@domain.com"

# TODO: change this to 'devops'
defaultReceiverEmail = "devops@domain.com"
multiplePurges = False

# create log file with current date&time
fileNameDate = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

if scriptArgs.logpath[-1] != "/":
    scriptArgs.logpath += "/"

# checks if provided path is valid, if not, uses a default 'temp' directory
if os.path.isdir(scriptArgs.logpath):
    print(f"Writing to `{scriptArgs.logpath}`...")
    scriptArgs.logpath = scriptArgs.logpath + "artifactory_purge_" + str(fileNameDate) + ".log"
    fileWrite = open(scriptArgs.logpath, "x")
else:
    print(f"BAD file path. Writing to default path `{tempDirectory}`...")
    try:
        os.makedirs(tempDirectory)
    except FileExistsError:
        print("File path already exists!")
    except Exception as e:
        print(f"Unknown error: {e}") 
    scriptArgs.logpath = tempDirectory + "/" + "artifactory_purge_" + str(fileNameDate) + ".log"
    fileWrite = open(scriptArgs.logpath, "x")

# Function definitions
def timerConvert(runtime):
    runtime = math.ceil(runtime)
    parts = []

    hours = runtime // 3600
    if hours:
        parts.append(f"{hours}hr{'s' if hours != 1 else ''}")
    runtime %= 3600

    minutes = runtime // 60
    if minutes:
        parts.append(f"{minutes}min{'s' if minutes != 1 else ''}")
    runtime %= 60

    if runtime or not parts:
        parts.append(f"{runtime}s")
    return ', '.join(parts)

def repoEmailSend(sender, receiver, htmlContent):
    print("Sending email...")
    htmlContent += f"""
    <html>
        <body>
            <p>have more than one <b>PURGE</b> property defined on it. Please remove all but one <b>PURGE</b> property on the listed path(s). No file cleanup will be performed until the properties are corrected to reflect the actual retention period desired. </p>    
            <p>The proper name for the property is "<b>PURGE</b>" and a <i>single</i> positive integer as the value representing the days to retain artifacts until they are removed. Properties are case-sensitive and more than one can be defined with the same spelling, so please ensure there is only one defined in all uppercase letters.</p>
            <p>Contact <a href="mailto:devops@domain.com">devops@domain.com</a> if you have any questions.</p>
        </body>
    </html>
    """
    
    subject = 'Artifactory Purge Property Error Summary'
    
    errorMessage = MIMEText(htmlContent, 'html')
    errorMessage['Subject'] = subject
    errorMessage['From'] = sender
    errorMessage['To'] = receiver

    try:
        smtp = SMTP('smtp.domain.com', 25)
        smtp.sendmail(sender, receiver, errorMessage.as_string())
        smtp.quit()
    except Exception as e:
        print(f"Unknown error found: {e}")

def appendBadPurgeEmail(path):
    htmlContent = f"""
        <html>
            <body>
                <p><li><a href="https://artifactory-stage.domain.com/ui/repos/tree/Properties/{path}">{path}</a></li>         
                </p>
            </body>
        </html>
    """
    return htmlContent   

def summarizeFile(repo, path, name, objectDaysOld, purgeValue, fileReport):
    print("\n======================================================================")
    fileReport.write("\n======================================================================")
    print("======================================================================")
    fileReport.write("\n======================================================================")
    
    print(f"File path: {repo}{path}/{name}")
    
    fileReport.write(f"\nFile path: {repo}{path}/{name}")

    print(f" - File age: {objectDaysOld}")
    print(f" - Retention days: {purgeValue}")

    fileReport.write(f"\n - File age: {objectDaysOld}")
    fileReport.write(f"\n - Retention days: {purgeValue}")
    
    print("--------------------------------------------------")
    fileReport.write(f"\n--------------------------------------------------\n")

def daysOld(fileModifiedDate):
    dateDays = datetime.fromisoformat(fileModifiedDate)
    dtUtc = dateDays.astimezone(timezone.utc)

    currentUtc = datetime.now(timezone.utc)
    delta = dtUtc - currentUtc
    daysOld = abs(delta.days)
    
    return daysOld

def filePurge(repo, path, name, purgeValue, fileModifiedDate, fileReport):
    # This is where the fun begins. 
    # if 'NEVER' is enccountered, the file will not be edited.
    if str(purgeValue).lower() == "never":
        return
    purgeURL = f'{ART_URL}api/storage/{repo}{path}/{name}'
    deleteURL = f'{ART_URL}{repo}{path}/{name}'
    fileRequest = requests.get(purgeURL, auth=auth)
    #if fileRequest.status_code == 200:
    objectDaysOld = int(daysOld(fileModifiedDate))
    # all purge values are rounded UP to nearest whole number.
    purgeValue = int(math.ceil(float(purgeValue)))
    if objectDaysOld > purgeValue:
        summarizeFile(repo, path, name, objectDaysOld, purgeValue, fileReport)
        if scriptArgs.user_confirming_deletion:
            # gone.
            purgeAction = requests.delete(deleteURL, auth=auth)
            global deletedArtifacts
            deletedArtifacts += 1
            if purgeAction.status_code == 204:
                print(f"Purge successful. File {name} moved to trash bin.\n----------------------------------------------------------------------")
                fileReport.write(f"Purge successful. File {name} moved to trash bin.\n----------------------------------------------------------------------")
                return
                    
            else:
                print(f"Purge unsuccessful. File {name} has NOT been removed.")
                fileReport.write(f"Purge unsuccessful. File {name} has NOT been removed.")
        else:
            print(f"{name} not purged because the deletion flag was not set in initial query.\n----------------------------------------------------------------------")
            global wouldBeDeletedArtifacts
            wouldBeDeletedArtifacts += 1
            return
   # else:
     #   print(f"{name} has been altered or no longer exists at {repo}{path}. ")

def reverseTraverse(repo, path, name, date, fileReport):
    path = '/' + path
    backPath = path + '/' + name
    purgeFound = False

    currentLeafPath = repo + path
    
    while not purgeFound: 
        dictPath = repo + backPath
        if pathPurgeDict.get(dictPath) == "NA":
            pass
                    
        elif isinstance(pathPurgeDict.get(dictPath), int):
            fullPath = currentLeafPath + '/' + name

            # ensures file-based purge values are not inherited
            if fullPath != dictPath:
                pathPurgeDict[currentLeafPath] = pathPurgeDict[dictPath]
                
            # purge action
            filePurge(repo, path, name, pathPurgeDict[dictPath], date, fileReport)
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
    hasRepoAdmin = False
    for k in propertyArray:
        if k['key'].lower() == "repo_admin":
            ownershipDict[item['repo']] = k['value']
            emailDictionary[k['value']] = f"""
                        <html>
                            <body>
                                <p>The following artifacts:</p>
                            </body>
                        </html>
                        """
            hasRepoAdmin = True
        elif k['key'].lower() == "purge":
            # handling parent directories, and the '.' oddity.
            if item['path'] == "" and item['name'] == "":
                dictPath = item['repo']
            elif item['path'][0] == '.':
                dictPath = item['repo'] + '/' + item['name']
            else:
                dictPath = item['repo'] + '/' + item['path'] + '/' + item['name']

            # 'never' shouldn't be an array. that always takes priority. 
            # if 'never' is found, it is set, and we move on to the next artifact.
            if k['value'].lower() == "never":
                pathPurgeDict[dictPath] = k['value']
                return

            # handles purge values like 'Four days' or '5 hours'
            # thought for future versions - also including an email that alerts if any values like this exist?
            try:   
                purgeValueArray.append(abs(int(k['value'])))
            except Exception:
                continue
    # Checks if a repo admin exists AND if the object has been created. 
    # Otherwise, it overwrites the value for every single object. 
    if not hasRepoAdmin and not emailDictionary.get(ownershipDict.get(item['repo'])):
        ownershipDict[item['repo']] = defaultReceiverEmail
        emailDictionary[defaultReceiverEmail] = f"""
                        <html>
                            <body>
                                <p>The following artifacts:</p>
                            </body>
                        </html>
                        """
    if purgeValueArray:
        if len(purgeValueArray) > 1:
            emailDictionary[ownershipDict[item['repo']]] += appendBadPurgeEmail(dictPath)
            global multiplePurges
            multiplePurges = True
        else:
            pathPurgeDict[dictPath] = int(max(purgeValueArray))

def getEachFile(path, repo, fileReport):
    # repo/oneFolderPath/file.ext were not getting flagged due to path having './'. 
    # ./ is the death of me. it's a folder. not an executable. thanks artifactory.
    if path[0:2] == "./":
        path = path[2:]
    
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
            propCheck = item.get('properties', {})
            
            if propCheck:
                addPurgeToDictionary(item, propCheck)
            fileName = item['name']
            filePath = item['path']
            lastModified = item['modified']
            
            reverseTraverse(repo, filePath, fileName, lastModified, fileReport)
            global totalArtifacts
            totalArtifacts += 1
                        
def get_all_info(repo, fileReport):
    print(f"\nCalling `get_all_info()` on {repo}")
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
            getEachFile(passPath, passRepo, fileReport)
    else:
        print("\n" + "-"*75)
        errorMessage = "Could not make a successful query. Check one of the following: \n  - Username\n  - Reference Token\n  - Query syntax\n"
        print(errorMessage)

# need separate check for parent repository
def parentProperties(name):
    parentPropQuery = f'''items.find({{
        "repo": "{name}",
        "path": ".",
        "name": ".",
        "type": "folder"
        }}).include("@*")''' 
    propUrl = ART_URL + "api/search/aql"
   # print(propUrl)
    propReq = requests.post(propUrl, data=parentPropQuery, headers=headers, auth=auth)
    if propReq.ok:
        propJson = propReq.json()
        for item in propJson.get('results', []):
            propArray = item.get('properties', {})
            if propArray:
                item['path'] = item['name'] = ""
                addPurgeToDictionary(item, propArray)


def main():
    # TODO: remove in final deployment
    if scriptArgs.production and scriptArgs.user_confirming_deletion:
        userDoubleCheck = input(f"NOTE: This script will delete outdated files marked for deletion on PROD SERVER because you explicitly defined the deletion flag. Press [ENTER] to confirm...")

    start = round(time.time(), 2)

    # check for 'repo type' and 'package type'
    typeUrl = ART_URL + repoType

    repoTypeReq = requests.get(typeUrl, auth=auth)
    if repoTypeReq.status_code == 200:
        for item in repoTypeReq.json():
            if item['type'] == "LOCAL" and item['packageType'] == "Generic":
                parentProperties(item['key'])
                get_all_info(item['key'], fileWrite)
                
                repoOwnerEmail = ownershipDict.get(item['key'])
                if scriptArgs.user_confirming_deletion:
                    if repoOwnerEmail and multiplePurges:
                        repoEmailSend(senderEmail, ownershipDict[item['key']], emailDictionary[ownershipDict[item['key']]])
                    elif not repoOwnerEmail and multiplePurges:
                        repoEmailSend(senderEmail, defaultReceiverEmail, ownershipDict[item['key']], emailDictionary[ownershipDict[item['key']]])
                    multiplePurges = False
                
    fileWrite.write(f"\n\nTotal artifacts scanned: {totalArtifacts}")

    fileWrite.write(f"\nDeleted artifacts: {deletedArtifacts}\n")

    if not scriptArgs.user_confirming_deletion:   
        fileWrite.write("\n -- Deletion flag NOT set. None of these files were removed.\n")

    end = round(time.time(), 2)
    runtime = end-start
    runtime = math.ceil(runtime)
    runtime = timedelta(seconds=runtime)
    fileWrite.write(f"\nPurge Time: {runtime}\n")
    print("Finished running.")

    fileWrite.close()
    print("File closed.")

if __name__ == "__main__":
    main()
