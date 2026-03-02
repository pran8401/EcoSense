import io
import pandas as pd
from flask import Flask, send_file, render_template, request, abort, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

SERVICE_ACCOUNT_FILE = "service_account.json"

# Drive folders
DRIVE_FOLDER_M1 = "1YvNkyQUa3cANtHr1roleh0cYdqn3yC4K"
DRIVE_FOLDER_M2 = "1JHvGs6RtaeaDzwthXgSnBpkxytVMFciO"

# Module Google Sheet URLs
MODULE_1_URL = "https://docs.google.com/spreadsheets/d/18jvq-xsOd6n4LL8dV-pRKFREANpFNlcptxAZbHlBylc/gviz/tq?tqx=out:csv&gid=0"
MODULE_2_URL = "https://docs.google.com/spreadsheets/d/18jvq-xsOd6n4LL8dV-pRKFREANpFNlcptxAZbHlBylc/gviz/tq?tqx=out:csv&gid=42078347"


# ================= GOOGLE AUTH ==================

def get_credentials():
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )


def drive_service():
    return build("drive", "v3", credentials=get_credentials())


# ================= DRIVE IMAGE FETCH ==================

def get_latest_image(folder_id):
    service = drive_service()

    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType contains 'image'",
        orderBy="createdTime desc",
        pageSize=1,
        fields="files(id,name)"
    ).execute()

    files = results.get("files", [])
    if not files:
        abort(404, "No images found")

    data = service.files().get_media(fileId=files[0]["id"]).execute()
    return io.BytesIO(data)


# ================= LOAD MODULE SHEETS ==================

def load_module(url):
    df = pd.read_csv(url)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])
    df["DATE_ONLY"] = df["Timestamp"].dt.strftime("%Y-%m-%d")
    return df


# ================= LIVE API ==================

@app.route("/api/live-data")
def api_live():

    df1 = load_module(MODULE_1_URL)
    df2 = load_module(MODULE_2_URL)

    today1 = df1["DATE_ONLY"].max()
    today2 = df2["DATE_ONLY"].max()

    d1 = df1[df1["DATE_ONLY"] == today1]
    d2 = df2[df2["DATE_ONLY"] == today2]

    last1 = d1.sort_values("Timestamp").iloc[-1]
    last2 = d2.sort_values("Timestamp").iloc[-1]

    return jsonify({
        "modules": {
            "1": {
                "current_temp": last1["Temperature"],
                "current_hum": last1["Humidity"],
                "avg_temp": round(d1["Temperature"].mean(), 2),
                "avg_hum": round(d1["Humidity"].mean(), 2)
            },
            "2": {
                "current_temp": last2["Temperature"],
                "current_hum": last2["Humidity"],
                "avg_temp": round(d2["Temperature"].mean(), 2),
                "avg_hum": round(d2["Humidity"].mean(), 2)
            }
        }
    })


@app.route("/api/live-image")
def api_image():

    folder = request.args.get("folder")

    if folder == DRIVE_FOLDER_M1:
        img = get_latest_image(DRIVE_FOLDER_M1)

    elif folder == DRIVE_FOLDER_M2:
        img = get_latest_image(DRIVE_FOLDER_M2)

    else:
        abort(400, "Invalid folder")

    return send_file(img, mimetype="image/jpeg")


# ================= MAIN ROUTE ==================

@app.route("/")
def home():
    return render_template("index.html")


# ================= RUN ==================

if __name__ == "__main__":
    app.run(debug=True)