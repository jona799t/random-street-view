import random_street_view
from countries import countries
from threading import Thread
import json

try:
    map = open("map.json").readlines()
    panoIds = [json.loads(location)["panoId"] for location in map] # Dårlig måde at gøre det på
except FileNotFoundError:
    open("map.json", "w").write("")
    panoIds = []

def logger(msg):
    if msg["code"] == "new_location":
        if msg["location"]["panoId"] not in panoIds:
            print("New location:", msg["location"])
            open("map.json", "a").write(json.dumps(msg["location"]) + "\n")
    elif msg["code"] == "msg":
        pass
        #print(msg["msg"])
    elif msg["code"] == "done":
        pass
        #print(msg["result"])

threads = []
for _ in range(20): # Amount of workers per country
    for country in countries:
        #random_street_view.search(country, 1, 0, 0, logger)
        thread = Thread(target=random_street_view.search, args=[country, float("INF"), 0, 0, logger])
        thread.start()
        threads.append(thread)

for thread in threads:
    thread.join()