import requests
import time
from datetime import datetime
import json
import sys
import sqlite3
import os

'''
number = 100
timestamp = 1422019499
url="https://ctftime.org/api/v1/events/?limit=100&start=1422019499&finish=1423029499"
#url = "https://ctftime.org/api/v1/events/?limit={number}&start={timestamp}&finish={timestamp}"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

response = requests.get(url, headers=headers)

print(response.content)
'''
total_ctftime = []
db_column = ["Alert", "Title", "StartTime", "FinishTime", "Duration", "Url", "Desc", "Or_id", "Or_name", "Event_id", "Ctf_id"]

def insert_ctftime(list_response): # list내부에 dict들
    add_count = 0
    conn = sqlite3.connect('ctftime.db')
    cur = conn.cursor()
    
    # ctf_id와 event_id를 이용하여 내부에 중복 여부 확인
    for response in list_response:
        event_id = response['id']
        ctf_id = response['ctf_id']
        
        cur.execute(f"SELECT Event_id,Ctf_id FROM CtfTime WHERE Ctf_id = {ctf_id} and Event_id = {event_id}")
        if len(list(cur)) == 0:
            # 크롤링 데이터 넣기
            Or = response['organizers'][0]
            
            Alert = "X"
            Title = response['title']
            StartTime = response['start']
            FinishTime = response['finish']
            Duration = response['duration'] # 가공 필요
            Duration = f"{Duration['days']} days - {Duration['hours']} hours"
            Url = response['url']
            Desc = response['description']
            Or_id = Or['id']
            Or_name = Or['name']
            Event_id = response['id']
            Ctf_id = response['ctf_id']
            
            cur.execute("INSERT INTO CtfTime VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", \
                (Alert, Title, StartTime, FinishTime, Duration, Url, Desc, Or_id, Or_name, Event_id, Ctf_id))
            conn.commit() # 이것 해야지 데이터가 입력됨
            add_count += 1
    print(f"[+] Insert Data - {add_count}")    
    conn.close()

def crawling_ctftime():
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
    #print_dict(list_response[0])
    
    return list_response

def print_dict(dict_file):
    list_key = list(dict_file.keys())
    for key in list_key:
        print(f"[{key}]")
        print(dict_file[key])
        print()

def load_DBData(conn):
    cur = conn.cursor()
    # index(int), alert(text), title(text), start(text), Finish(text), duration(text), url(text), Description(text), organiers_id(int), organier_name(text), id(int), ctf_id(int)
    
    # 내부 데이터 load
    cur.execute('select * from CtfTime')
    for row in cur:
        ctftime = list(row)
        total_ctftime.append(ctftime)

def init_CTFData(conn):
    # 테이블 생성
    #cur.execute("CREATE TABLE CtfTime (\
    #        Alert text, Title text, StartTime text, FinishTime text, Duration text, \
    #        Url text, Desc text, Or_id INTEGER, Or_name text, Event_id INTEGER, Ctf_id INTEGER);")
    
    # 테이블 내에 데이터 가져와서 저장
    load_DBData(conn)
    conn.close()

# (1) DB의 유무확인
# (1-1) DB를 생성 / (1-2) DB내부에 데이터 로딩
base_path = os.getcwd()
list_dir = os.listdir(base_path)
if not "ctftime.db" in list_dir:
    open("ctftime.db","w") # db파일 생성
    
conn = sqlite3.connect('ctftime.db')
init_CTFData(conn) # DB내에 ctftime데이터 로딩

# -----
list_response = crawling_ctftime()
insert_ctftime(list_response) # 중복이 없을 경우만 insert

# Next : alert를 기준으로 Discord봇에 웹훅