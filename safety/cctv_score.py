import requests

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def cctv_score(route):
    try:
        points = route[::20]
        total = 0

        for lon, lat in points:
            query = f"""
            [out:json];
            node(around:80,{lat},{lon})["man_made"="surveillance"];
            out count;
            """

            res = requests.post(OVERPASS_URL, data=query, timeout=20)

            if res.status_code != 200 or not res.text.strip():
                continue

            data = res.json()
            total += int(data["elements"][0]["tags"]["total"])

        density = total / max(len(points), 1)
        return min(density / 5, 1.0)

    except Exception as e:
        print("CCTV API failed:", e)
        return 0.4

