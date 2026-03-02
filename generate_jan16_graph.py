import pandas as pd
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# -------------------------------
# GOOGLE SHEET CONFIG
# -------------------------------

SHEET_ID = "1Tb5_AMiqZQUDHSDy50Mg5MW5tRj1Utx7NDI_YU3RYeA"
SERVICE_ACCOUNT_FILE = "service_account.json"

# -------------------------------
# AUTHENTICATION
# -------------------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

df = pd.DataFrame(data)

# -------------------------------
# DATA CLEANING
# -------------------------------

# Ensure correct column names (change if needed)
df.columns = ["TIME", "Module", "Temperature", "Humidity"]

df["TIME"] = pd.to_datetime(df["TIME"], errors="coerce")

# -------------------------------
# FILTER ONLY 16 JAN 2026
# -------------------------------

jan16 = df[df["TIME"].dt.date == datetime(2026, 1, 16).date()]

# -------------------------------
# MODULE CORRECTION
# -------------------------------

module_mapping = {
    "Module_2": "Module_1",
    "Module_3": "Module_2",
    "Module_4": "Module_3"
}

jan16["Module"] = jan16["Module"].map(module_mapping)

# Remove rows where mapping failed
jan16 = jan16.dropna(subset=["Module"])

# -------------------------------
# PLOTTING
# -------------------------------

plt.figure(figsize=(14, 6))

for module in sorted(jan16["Module"].unique()):
    module_data = jan16[jan16["Module"] == module]
    plt.plot(
        module_data["TIME"],
        module_data["Temperature"],
        label=f"{module} Temp"
    )

plt.xlabel("Time")
plt.ylabel("Temperature")
plt.title("16 Jan 2026 Temperature Data - All Modules")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

# -------------------------------
# SAVE GRAPH
# -------------------------------

plt.savefig("static/jan16_static_graph.png")
plt.close()

print("✅ Graph saved to static/jan16_static_graph.png")
