import requests
import time
from datetime import datetime
import json
import sys

'''
number = 100
timestamp = 1422019499
url="https://ctftime.org/api/v1/events/?limit=100&start=1422019499&finish=1423029499"
#url = "https://ctftime.org/api/v1/events/?limit={number}&start={timestamp}&finish={timestamp}"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

response = requests.get(url, headers=headers)

print(response.content)
'''
timestamp = time.time()
datetimes = str(datetime.fromtimestamp(timestamp))

number = 100
end_time = timestamp+1010000
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
url = "https://ctftime.org/api/v1/events/?limit={number}&start={timestamp}&finish={end_time}"

responses = requests.get(url, headers=headers)
response = responses.content.decode('utf-8')[1:-1]

list_response = list()
list_count = [0,0]
dict_str = ""
for s in response:
    if s == "{":
        list_count[0] += 1
    if s == "}":
        list_count[1] += 1
    
    dict_str += s
    
    if list_count[0] == list_count[1]:
        if dict_str == ",":
            dict_str = ""
            continue
        elif dict_str == " ":
            dict_str = ""
            continue
        
        list_response.append(dict_str)
        dict_str = ""
# json변환 완료
for i in range(len(list_response)):
    list_response[i] = json.loads(list_response[i])