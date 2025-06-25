import requests as r
import json as j

ART_USER = "your_username"
ART_TOK = "your_reference_token"

ART_URL = "https://artifactory.yourdomain.com/artifactory"

auth = (ART_USER, ART_TOK)
headers = {"Content-Type": "text/plain"}

# Function definitions
def getEachFile(path, repo):
    fileQuery = f'''items.find({{
        "repo": "{repo}",
        "path": {{"$match": "{path}"}}
    }})'''         
    aqlUrl = f"{ART_URL}/api/search/aql"
    aqlReq = r.post(aqlUrl, data=fileQuery, headers=headers, auth=auth)
    if aqlReq.ok:
        aqlResult = aqlReq.json()
        for item in aqlResult.get('results', []):
            fileName = item['name']
            print(" - " + fileName)

def get_all_info(repo, path):
    dirQuery = f'''items.find({{
        "repo": {{"$match": "{repo}"}},
        "path": {{"$match": "{path}"}},
        "type": {{"$eq": "folder"}}
        }}).include("@*")'''    
    
    aqlUrl = f"{ART_URL}/api/search/aql"
    aqlReq = r.post(aqlUrl, data=dirQuery, headers=headers, auth=auth)

    print(f"Url: {aqlUrl}")

    if aqlReq.ok:
        aqlResult = aqlReq.json()
        for item in aqlResult.get('results', []):
            baseFolder = item['repo'] + '/' + item['path'] + '/' + item['name']
            print('\n' + baseFolder) 
            
            passRepo = item['repo']
            passPath = item['path'] + '/' + item['name']
            getEachFile(passPath, passRepo)
    else:
        print("\n" + "-"*75)
        print("Could not make a successful query. Check one of the following: ")
        print("  - Username")
        print("  - Reference Token")
        print("  - Query syntax")
    print("\n")  

repo = str(input("Enter parent repo: "))
path = str(input("Enter path: "))

get_all_info(repo, path)
