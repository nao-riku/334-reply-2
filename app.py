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
world_rank = {}
load_res_yet = True

def get_result():
    global today_result, world_rank, load_res_yet
    load_res_yet = False
    r = requests.get(os.environ['URL2'])
    today_result = r.json()["result"]
    world_rank = r.json()["rank"]
    if today_result == {} or world_rank == {}:
        load_res_yet = True
    
def com(f, s):
    return (s - f).total_seconds() > 0
    
def com_t(f, s, t):
    return (s - f).total_seconds() >= 0 and (t - s).total_seconds() > 0


def get_stream():
    now = datetime.datetime.now()
    times = [
        datetime.datetime(now.year, now.month, now.day, 0, 0, 0),
        datetime.datetime(now.year, now.month, now.day, 2, 35, 40),
        datetime.datetime(now.year, now.month, now.day, 6, 35, 40),
        datetime.datetime(now.year, now.month, now.day, 10, 35, 40),
        datetime.datetime(now.year, now.month, now.day, 14, 35, 40),
        datetime.datetime(now.year, now.month, now.day, 18, 35, 40),
        datetime.datetime(now.year, now.month, now.day, 22, 35, 40),
        datetime.datetime(now.year, now.month, now.day + 1, 2, 35, 40),
        datetime.datetime(now.year, now.month, now.day + 1, 6, 35, 40)
    ]
    for num in range(7):
        if com_t(times[num], now, times[num + 1]):
            start_time = datetime.datetime(times[num + 1].year, times[num + 1].month, times[num + 1].day, times[num + 1].hour, times[num + 1].minute, times[num + 1].second + 2)
            end_time = times[num + 2]
    #start_time = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute + 1, 10)
                
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
    
        global oath, today_result, world_rank, load_res_yet
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
                                    elif "ランク" in tweet_text or "ランキング" in tweet_text:
                                        if com_t(r_start_time, t_time, r_end_time) and today_result != {} and world_rank != {}:
                                            key = str(json_response["data"]["author_id"])
                                            if key in world_rank:
                                                if world_rank[key][4] != world_rank[key][6]:
                                                    rep_text2 = "\n参考記録: " + world_rank[key][6]
                                                else:
                                                    rep_text2 = ""

                                                pt = float(world_rank[key][2])
                                                if pt < 500:
                                                    rank = "E"
                                                elif pt < 1000:
                                                    rank = "E+"
                                                elif pt < 1500:
                                                    rank = "D"
                                                elif pt < 2000:
                                                    rank = "D+"
                                                elif pt < 2500:
                                                    rank = "C"
                                                elif pt < 3000:
                                                    rank = "C+"
                                                elif pt < 3500:
                                                    rank = "B"
                                                elif pt < 4000:
                                                    rank = "B+"
                                                elif pt < 4500:
                                                    rank = "A"
                                                elif pt < 5000:
                                                    rank = "A+"
                                                elif pt < 5500:
                                                    rank = "S1"
                                                elif pt < 6000:
                                                    rank = "S2"
                                                elif pt < 6500:
                                                    rank = "S3"
                                                elif pt < 7000:
                                                    rank = "S4"
                                                elif pt < 7500:
                                                    rank = "S5"
                                                elif pt < 8000:
                                                    rank = "S6"
                                                elif pt < 8500:
                                                    rank = "S7"
                                                elif pt < 9000:
                                                    rank = "S8"
                                                elif pt < 9500:
                                                    rank = "S9"
                                                else:
                                                    rank = "RoR"
                                                    
                                                rep_text = json_response["includes"]["users"][0]["name"] + "\n\n級位: " + rank + "\n⠀最高pt: " + world_rank[key][2] + "\n⠀歴代: " + str(world_rank[key][3]) + " / " + world_rank["累計"][0] + "\n⠀現在pt: " + world_rank[key][4] + "\n⠀世界ランク: " + str(world_rank[key][5]) + " / " + world_rank["現在"][0] + rep_text2 +\
                                                "\n出場試合数: " + str(world_rank[key][7]) + "\n自己ベスト: " + world_rank[key][0] + " (" + str(world_rank[key][1]) + "回)\n戦績: 🥇×" + str(world_rank[key][8]) + " 🥈×" + str(world_rank[key][9]) + " 🥉×" + str(world_rank[key][10]) + " 📋×" + str(world_rank[key][11])
                                            else:
                                                rep_text = json_response["includes"]["users"][0]["name"] + "\n\n最高pt: -\n歴代: - / " + world_rank["累計"][0] + "\n現在pt: -\n世界ランク: - / " + world_rank["現在"][0] + "\n出場試合数: 0\n自己ベスト: -\n戦績: 🥇×0 🥈×0 🥉×0 📋×0"
                                        else:
                                            rep_text = "申し訳ありません\nランク照会可能時間はは3:34:30ごろ - 23:59:59となっております"
                                    else:
                                        if com_t(r_start_time, t_time, r_end_time) and today_result != {} and world_rank != {}:
                                            key = str(json_response["data"]["author_id"])
                                            if key in today_result:
                                                rep_text = today_result[key][1] + "\n\n" + start_str + "の334結果\nresult: +" + today_result[key][2] + " [sec]\nrank: " + today_result[key][0] + " / " + today_result["参加者数"][0]
                                            else:
                                                rep_text = json_response["includes"]["users"][0]["name"] + "\n\n" + start_str + "の334結果\nresult: DQ\nrank: DQ / " + today_result["参加者数"][0]
                                        else:
                                            rep_text = "申し訳ありません\nランク照会可能時間はは3:34:30ごろ - 23:59:59となっております"
							
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
                time.sleep(6)
                run+=1
                print("再接続します"+str(run)+"回目")
                print(datetime.datetime.now())
                    
            except Exception as e:
                # some other error occurred.. stop the loop
                print("Stopping loop because of un-handled error")
                print(traceback.format_exc())
                time.sleep(15)
                run+=1
                print("再接続します"+str(run)+"回目")
                print(datetime.datetime.now())
              
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
