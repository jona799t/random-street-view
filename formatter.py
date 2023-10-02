import json

map = [json.loads(location) for location in open("map.json").readlines()]
open("map_ready.json", "w").write(json.dumps(map))