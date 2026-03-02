from flask import Flask, jsonify, request, send_file, render_template
import json
import os
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# ----------------------------------------------------------
# GOOGLE AUTH (Render-Safe) — DO NOT CHANGE
# ----------------------------------------------------------
def get_credentials():

    google_creds_b64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
    if not google_creds_b64:
        raise Exception("GOOGLE_CREDENTIALS_BASE64 missing!")

    import base64
    decoded = base64.b64decode(google_creds_b64).decode("utf-8")
    google_creds = json.loads(decoded)

    creds = service_account.Credentials.from_service_account_info(
        google_creds,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]
    )

    return creds


# ----------------------------------------------------------
# SHEET CONFIG
# ----------------------------------------------------------
SPREADSHEET_ID = "18jvq-xsOd6n4LL8dV-pRKFREANpFNlcptxAZbHlBylc"

# Expand range to A–E so Avg Hum is included
M1_RANGE = "Module_1!A2:E2"
M2_RANGE = "Module_2!A2:E2"


# ----------------------------------------------------------
# FETCH LIVE SENSOR DATA WITH CLEANING
# ----------------------------------------------------------
def fetch_sheet_data(sheet_range):
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_range
    ).execute()

    values = result.get("values", [])
    if not values:
        return {"current_temp": "-", "current_hum": "-", "avg_temp": "-", "avg_hum": "-"}

    row = values[0]

    # ---------------- CLEANING FUNCTION ----------------
    # Removes words, % symbols, timestamps etc.
    def clean(x):
        if not x:
            return "-"
        return (
            x.replace("Module_1", "")
             .replace("Module_2", "")
             .replace("Module_3", "")
             .replace("%", "")
             .replace("°C", "")
             .strip()
        )

    # ---------------- SAFE COLUMN EXTRACTION ----------------
    # row = [Timestamp, Current Temp, Current Hum, Avg Temp, Avg Hum]
    current_temp = clean(row[1] if len(row) > 1 else "-")
    current_hum  = clean(row[2] if len(row) > 2 else "-")
    avg_temp     = clean(row[3] if len(row) > 3 else "-")
    avg_hum      = clean(row[4] if len(row) > 4 else "-")

    return {
        "current_temp": current_temp,
        "current_hum": current_hum,
        "avg_temp": avg_temp,
        "avg_hum": avg_hum
    }


# ----------------------------------------------------------
# LIVE DATA API
# ----------------------------------------------------------
@app.route("/api/live-data")
def live_data():
    module1 = fetch_sheet_data(M1_RANGE)
    module2 = fetch_sheet_data(M2_RANGE)

    return jsonify({
        "modules": {
            "1": module1,
            "2": module2
        }
    })


# ----------------------------------------------------------
# GOOGLE DRIVE IMAGE FETCHER
# ----------------------------------------------------------
def fetch_drive_image(folder_id):

    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType contains 'image'",
        orderBy="createdTime desc",
        pageSize=1,
        fields="files(id,name)"
    ).execute()

    files = results.get("files", [])
    if not files:
        return None

    file_id = files[0]["id"]

    # Direct Google Drive download — Render safe
    request_file = service.files().get_media(fileId=file_id)
    raw_data = request_file.execute()

    return BytesIO(raw_data)


@app.route("/api/live-image")
def live_image():
    folder = request.args.get("folder")

    img = fetch_drive_image(folder)
    if img is None:
        return "No image", 404

    return send_file(img, mimetype="image/jpeg")


# ----------------------------------------------------------
# MAIN PAGE
# ----------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ----------------------------------------------------------
# SERVER START (Render uses $PORT)
# ----------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)