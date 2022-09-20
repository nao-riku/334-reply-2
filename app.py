import sys
import requests
import os
import json
from requests_oauthlib import OAuth1Session
import time
import datetime
import traceback
import timeout_decorator

consumer_key = os.environ['CK']
consumer_secret = os.environ['CS']
access_token = os.environ['AT']
access_token_secret = os.environ['AS']
bearer_token_sub = os.environ['BT']

oath = OAuth1Session(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token_sub}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r

def get_rules():
    response = requests.get("https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth)
    if response.status_code != 200:
        raise Exception("Cannot get rules (HTTP {}): {}".format(response.status_code, response.text))
    #print(json.dumps(response.json()))
    return response.json()

def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None
    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post("https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth, json=payload)
    if response.status_code != 200:
        raise Exception("Cannot delete rules (HTTP {}): {}".format(response.status_code, response.text))
    #print(json.dumps(response.json()))

def set_rules(delete):
    rules = [{"value":"@Rank334"}]
    payload = {"add": rules}
    response = requests.post("https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth, json=payload)
    if response.status_code != 201:
        raise Exception("Cannot add rules (HTTP {}): {}".format(response.status_code, response.text))
    #print(json.dumps(response.json()))
	
def TweetId2Time(id):
    epoch = ((id >> 22) + 1288834974657) / 1000.0
    d = datetime.datetime.fromtimestamp(epoch)
    return d
    
def TimeToStr(d):
    stringTime = ""
    stringTime += '{0:02d}'.format(d.hour)
    stringTime += ':'
    stringTime += '{0:02d}'.format(d.minute)
    stringTime += ':'
    stringTime += '{0:02d}'.format(d.second)
    stringTime += '.'
    stringTime += '{0:03d}'.format(int(d.microsecond / 1000))
    return stringTime

today_result = {}
load_res_yet = True

def get_result():
    global today_result, load_res_yet
    load_res_yet = False
    r = requests.get(os.environ['URL2'])
    today_result = r.json()
    if today_result == {}:
        load_res_yet = True
    
def com(f, s):
    return (s - f).total_seconds() > 0
    
def com_t(f, s, t):
    return (s - f).total_seconds() >= 0 and (t - s).total_seconds() > 0


def get_stream():
    now = datetime.datetime.now()
    times = [
        datetime.datetime(now.year, now.month, now.day, 0, 0, 0),
        datetime.datetime(now.year, now.month, now.day, 2, 47, 40),
        datetime.datetime(now.year, now.month, now.day, 6, 47, 40),
        datetime.datetime(now.year, now.month, now.day, 10, 47, 40),
        datetime.datetime(now.year, now.month, now.day, 14, 47, 40),
        datetime.datetime(now.year, now.month, now.day, 18, 47, 40),
        datetime.datetime(now.year, now.month, now.day, 22, 47, 40),
        datetime.datetime(now.year, now.month, now.day + 1, 2, 47, 40),
        datetime.datetime(now.year, now.month, now.day + 1, 6, 47, 40)
    ]
    for num in range(7):
        if com_t(times[num], now, times[num + 1]):
            start_time = datetime.datetime(times[num + 1].year, times[num + 1].month, times[num + 1].day, times[num + 1].hour, times[num + 1].minute, times[num + 1].second + 1)
            end_time = times[num + 2]
                
    if start_time.hour != 2:
        get_result()
        
    time.sleep((start_time - datetime.datetime.now()).total_seconds())
    
    timeout = (end_time - datetime.datetime.now()).total_seconds()
    
    @timeout_decorator.timeout(timeout)
    def stream():
        nonlocal start_time, end_time
        
        #if com(datetime.datetime(now.year, now.month, now.day, 22, 47, 40), start_time):
        load_time = datetime.datetime(start_time.year, start_time.month, start_time.day, 3, 34, 30)
        r_start_time = load_time #datetime.datetime(start_time.year, start_time.month, start_time.day, 3, 35, 0)
        start_str = start_time.date().strftime('%Y/%m/%d')
        r_end_time = datetime.datetime(start_time.year, start_time.month, start_time.day + 1, 0, 0, 0)
    
        global oath, today_result, load_res_yet
        proxy_dict = {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"}
        run = 1

        while run:
            try:
                with requests.get("https://api.twitter.com/2/tweets/search/stream?tweet.fields=referenced_tweets&expansions=author_id&user.fields=name", auth=bearer_oauth, stream=True, timeout=timeout) as response:
                    if response.status_code != 200:
                        raise Exception("Cannot get stream (HTTP {}): {}".format(response.status_code, response.text))
                    for response_line in response.iter_lines():
                        if response_line:
                            json_response = json.loads(response_line)
                            tweet_id = json_response["data"]["id"]
                            t_time = TweetId2Time(int(tweet_id))
			
                            if com(load_time, t_time) and load_res_yet:
                                get_result()
				
                            if com_t(start_time, t_time, end_time):
                        
                                tweet_text = json_response["data"]["text"]
                                if ("@Rank334" in tweet_text or "@rank334" in tweet_text) and json_response["data"]["author_id"] != '1558892196069134337':
                                    reply_id = json_response["data"]["id"]
                                    rep_text = ""
						
                                    if 'referenced_tweets' in json_response["data"]:
                                        if json_response["data"]['referenced_tweets'][0]["type"] == "replied_to":
                                            orig_id = json_response["data"]['referenced_tweets'][0]["id"]
                                            orig_time = TweetId2Time(int(orig_id))
                                            rep_text = "ツイート時刻: " + TimeToStr(orig_time)
                                        else:
                                            continue
                                    else:
                                        if com_t(r_start_time, t_time, r_end_time) and today_result != {}:
                                            key = str(json_response["data"]["author_id"])
                                            if key in today_result:
                                                rep_text = today_result[key][1] + "\n\n" + start_str + "の334結果\nresult: +" + today_result[key][2] + " [sec]\nrank: " + today_result[key][0] + " / " + today_result["参加者数"][0]
                                            else:
                                                rep_text = json_response["includes"]["users"][0]["name"] + "\n\n" + start_str + "の334結果\nresult: DQ\nrank: DQ / " + today_result["参加者数"][0]
                                        else:
                                            continue
							
                                    params = {"text": rep_text, "reply": {"in_reply_to_tweet_id": reply_id}}
                                    response = oath.post("https://api.twitter.com/2/tweets", json = params)
                                    #print(response.headers["x-rate-limit-remaining"])
                                    if "status" in response.json():
                                        if response.json()["status"] == 429:
                                            response = oath.post("https://api.twitter.com/2/tweets", json = params, proxies = proxy_dict)
                                        

            except timeout_decorator.TimeoutError:
                print(start_time)
                print(end_time)
                print(datetime.datetime.now())
                run = 0

            except ChunkedEncodingError as chunkError:
                print(traceback.format_exc())
                time.sleep(6)
                continue
        
            except ConnectionError as e:
                print(traceback.format_exc())
                run+=1
                if run <10:
                    time.sleep(6)
                    print("再接続します",run+"回目")
                    continue
                else:
                    run=0
            except Exception as e:
                # some other error occurred.. stop the loop
                print("Stopping loop because of un-handled error")
                print(traceback.format_exc())
                run+=1
                if run <5:
                    time.sleep(6)
                    print("再接続します",run+"回目")
                    continue
                else:
                    run=0
              
    stream()
    
	    
class ChunkedEncodingError(Exception):
    pass


def main():
    #rules = get_rules()
    #delete = delete_all_rules(rules)
    #set = set_rules(delete)
    get_stream()

 
if __name__ == "__main__":
    main()
