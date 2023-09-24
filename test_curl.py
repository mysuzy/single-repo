import requests

baseId = 'fuckingla'
tableIdOrName='house'

headers= {'Authorization': 'Bearer patqmwV7hrU86hqYI.27fd1e12ce830b4306ac7bf5658fcb1929804783df1d4c3a0b579110e22a6b78'}

response = requests.get(f"https://api.airtable.com/v0/{baseId}/{tableIdOrName}",headers=headers)
print(response.json())