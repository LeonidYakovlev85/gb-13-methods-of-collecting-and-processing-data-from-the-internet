import requests
import json

headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/91.0.4472.164 '
                  'Safari/537.36 OPR/77.0.4054.277',
    'Accept': 'application/vnd.github.v3+json'
}

user = 'LeonidYakovlev85'
url = f'https://api.github.com/users/{user}/repos'
request = requests.get(url, headers=headers)
data = json.loads(request.text)

with open('13.01.99_hw_01_data_file.json', 'w') as writable_file:
    json.dump(data, writable_file)

with open('13.01.99_hw_01_data_file.json', 'r') as readable_file:
    data = json.load(readable_file)

for repo in data:
    print(repo['name'])
