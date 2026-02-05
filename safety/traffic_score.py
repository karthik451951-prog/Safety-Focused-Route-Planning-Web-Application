import requests

def traffic_score(route, api_key):
    try:
        lon, lat = route[len(route)//2]

        url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        params = {
            "point": f"{lat},{lon}",
            "key": api_key
        }

        res = requests.get(url, params=params, timeout=10)

        if res.status_code != 200:
            print("TomTom error:", res.text)
            return 0.5

        data = res.json()

        flow = data.get("flowSegmentData")
        if not flow:
            return 0.5

        current = flow.get("currentSpeed", 1)
        free = flow.get("freeFlowSpeed", 1)

        congestion = 1 - (current / free)
        return round(1 - congestion, 3)

    except Exception as e:
        print("Traffic API failed:", e)
        return 0.5
