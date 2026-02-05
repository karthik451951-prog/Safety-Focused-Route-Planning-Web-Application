from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests, csv, os, smtplib
from email.mime.text import MIMEText

from safety.safety_model import evaluate_route   # ✅ time-aware logic inside

app = Flask(__name__)
CORS(app)

TOMTOM_API_KEY = "UBO6wySTq3DUsyHBzJE6UbYbDXNjxcro"
FAST2SMS_API_KEY = "Sun4bv2Ejzkf5pOJq61aXRYtUQKg3oBDCHLPeiTAVWcdy9h78rmIe6sbpZKG0lQg7NPcawMXR3t5JkiT"

EMAIL_ADDRESS = "foodorderingg14@gmail.com"
EMAIL_PASSWORD = "vgyu hpks cboq elii"

CONTACTS_FILE = "emergency_contacts.csv"
emergency_contacts = []


# ================= LOAD CONTACTS =================

def load_contacts():
    global emergency_contacts
    emergency_contacts = []

    if not os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "phone", "email"])

    with open(CONTACTS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            emergency_contacts.append(row)

    print("Loaded contacts:", emergency_contacts)

load_contacts()


# ================= HOME =================

@app.route("/")
def index():
    return render_template("index.html")


# ================= ROUTING (OSRM) =================

def get_routes(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
    params = {"overview": "full", "geometries": "geojson", "alternatives": "true"}

    res = requests.get(url, params=params, timeout=20)
    data = res.json()

    routes = []
    for r in data.get("routes", []):
        routes.append({
            "geometry": r["geometry"],
            "properties": {
                "segments": [{
                    "distance": r["distance"],
                    "duration": r["duration"]
                }]
            }
        })
    return routes


# ================= SAFE ROUTE =================

@app.route("/safe-route", methods=["POST"])
def safe_route():
    data = request.json
    start = data.get("start")
    end = data.get("end")

    print("\nREQUEST:", data)

    routes = get_routes(start, end)
    analyzed = []

    for i, r in enumerate(routes):
        coords = r["geometry"]["coordinates"]
        seg = r["properties"]["segments"][0]

        # ✅ time-aware safety is computed inside this
        safety = evaluate_route(coords, TOMTOM_API_KEY)

        analyzed.append({
            "id": i,
            "coordinates": coords,
            "distance": round(seg["distance"]/1000, 2),
            "duration": round(seg["duration"]/60, 2),
            "safety": safety
        })

    print("ROUTES FOUND:", len(analyzed))

    # sort by highest safety
    sorted_routes = sorted(analyzed, key=lambda x: x["safety"]["final"], reverse=True)

    # ================= TERMINAL OUTPUT =================
    for idx, r in enumerate(sorted_routes):
        s = r["safety"]

        print("\n------------------------------")
        print(f"--- ROUTE {idx+1} ---")
        print("Time Category :", s.get("time_category"))
        print("Distance (km) :", r["distance"])
        print("Duration (m)  :", r["duration"])
        print("Crime score   :", s["crime"])
        print("CCTV score    :", s["cctv"])
        print("Infra score   :", s["infra"])
        print("Traffic score :", s["traffic"])
        print("FINAL SAFETY  :", s["final"])

    safest = sorted_routes[0]
    moderate = sorted_routes[1] if len(sorted_routes) > 1 else None

    return jsonify({"safest": safest, "moderate": moderate})


# ================= SAVE CONTACT =================

@app.route("/save-contact", methods=["POST"])
def save_contact():
    data = request.json

    emergency_contacts.append(data)

    with open(CONTACTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([data["name"], data["phone"], data["email"]])

    return jsonify({"status": "saved"})


# ================= FAST2SMS =================

def send_sms(phone, message):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "numbers": phone
    }
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    requests.post(url, json=payload, headers=headers)


# ================= EMAIL =================

def send_email(to_email, message):
    msg = MIMEText(message)
    msg["Subject"] = "🚨 SOS Emergency Alert"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
    server.quit()


# ================= SOS =================

@app.route("/sos", methods=["POST"])
def sos():
    data = request.json
    lat = data["lat"]
    lng = data["lng"]

    link = f"https://maps.google.com/?q={lat},{lng}"

    message = f"""🚨 EMERGENCY ALERT

Rishi needs immediate help.

Live location:
{link}
"""

    for c in emergency_contacts:
        try:
            send_sms(c["phone"], message)
            send_email(c["email"], message)
        except Exception as e:
            print("Failed for:", c, e)

    return jsonify({"status": "sent"})


# ================= MAIN =================

if __name__ == "__main__":
    app.run(debug=True)
