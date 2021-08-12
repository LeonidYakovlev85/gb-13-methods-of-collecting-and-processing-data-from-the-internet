import requests
import json

headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/91.0.4472.164 '
                  'Safari/537.36 OPR/77.0.4054.277'
}

method = 'users.get'
params = (
    'user_ids=210700286, leonidyakovlev85&'
    'fields=bdate'
)
access_token = 'YOUR_TOKEN'  # Ваш ключ доступа
version = '5.131'

url = f'https://api.vk.com/method/{method}?{params}&access_token={access_token}&v={version}'

request = requests.get(url, headers=headers)
data = json.loads(request.text)

with open('13.01.99_hw_02_data_file.json', 'w') as writable_file:
    json.dump(data, writable_file)
