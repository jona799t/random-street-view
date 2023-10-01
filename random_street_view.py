import os
import random
import sys

import requests
import shapefile  # pip install pyshp

# Determine if a point is inside a given polygon or not
# Polygon is a list of (x,y) pairs.
# http://www.ariel.com.au/a/python-point-int-poly.html
def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


shape_file = "TM_WORLD_BORDERS-0.3.shp"
if not os.path.exists(shape_file):
    sys.exit(
        f"Cannot find {shape_file}. Please download it from "
        "http://thematicmapping.org/downloads/world_borders.php and try again."
    )

sf = shapefile.Reader(shape_file, encoding="latin1")
shapes = sf.shapes()

def empty(msg):
    pass

def search(country, images_wanted=100, pitch=0, zoom=0, logger=empty): #ISO 3166-1 Alpha-3 Country Code
    for i, record in enumerate(sf.records()):
        if record[2] == country.upper():
            min_lng = shapes[i].bbox[0]
            min_lat = shapes[i].bbox[1]
            max_lng = shapes[i].bbox[2]
            max_lat = shapes[i].bbox[3]
            borders = shapes[i].points
            break

    attempts, country_hits, imagery_hits, imagery_unofficial, imagery_misses = 0, 0, 0, 0, 0

    locations = []
    panoIds = []
    try:
        while imagery_hits < images_wanted:
            logger({"code": "msg", "msg": f"[{country}]: {imagery_hits}/{images_wanted}"})

            attempts += 1
            rand_lat = random.uniform(min_lat, max_lat)
            rand_lng = random.uniform(min_lng, max_lng)
            # Is (lat,lon) inside borders?
            if point_inside_polygon(rand_lng, rand_lat, borders):
                country_hits += 1

                resp = requests.post("https://maps.googleapis.com/$rpc/google.internal.maps.mapsjs.v1.MapsJsInternalService/SingleImageSearch", headers={"Content-Type": "application/json+protobuf"}, data=f'[["apiv3",null,null,null,"US",null,null,null,null,null,[[0]]],[[null,null,{rand_lat},{rand_lng}],{500}],[null,["en","DK"],null,null,null,null,null,null,[2],null,[[[2,1,2],[3,1,2],[10,1,2]]]],[[1,2,3,4,8,6]]]').json()
                if len(resp) == 1:
                    imagery_misses += 1
                    continue

                imagery_hits += 1
                
                if "Images may be subject to copyright." not in str(resp):
                    location = {"lat": resp[1][5][0][1][0][2], "lng": resp[1][5][0][1][0][3], "panoId": resp[1][1][1], "heading": round(resp[1][5][0][6][0][1][3]), "pitch": pitch, "zoom": zoom}

                    if location["panoId"] not in panoIds:
                        logger({"code": "new_location", "location": location})
                        panoIds.append(location["panoId"])
                        locations.append(location)
                    
                #try:
                #    location = {"lat": resp[1][5][0][1][0][2], "lng": resp[1][5][0][1][0][3], "panoId": resp[1][1][1], "heading": round(resp[1][5][0][6][0][1][3]), "pitch": pitch, "zoom": zoom}

                #    if location["panoId"] not in panoIds:
                #        logger({"code": "new_location", "location": location})
                #        panoIds.append(location["panoId"])
                #        locations.append(location)
                #except IndexError:
                #    imagery_unofficial += 1
    except KeyboardInterrupt:
        pass

    logger({"code": "done", "result": locations})
    return locations, {"attempts": attempts, "country_hits": country_hits, "imagery_misses": imagery_misses, "imagery_hits": imagery_hits, "imagery_unofficial": imagery_unofficial}
