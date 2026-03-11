import os
import time
import requests
import pandas as pd
from datetime import datetime

# ==============================
# USER SETTINGS
# ==============================
service_key = "950fb465225d3909c46d9f7bac904b06f9ef1053d27c3b5ffd998425bf290dac"   # 일반 인증키 (NOT encoded)
path_save = r"D:\InProbation\Metocean\Data\Observations\1hr_tide"

stn_id = "DT_0022"          
# stn_name = "성산포"

start_year = 2000
end_year = 2026
# end_year = datetime.now().year - 1

#base_url = "http://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"
base_url = "https://apis.data.go.kr/1192136/hourlyTide/GetHourlyTideApiService"
num_of_rows = 999

os.makedirs(path_save, exist_ok=True)

# ==============================
# FUNCTION: DOWNLOAD ONE YEAR
# ==============================
def get_year_data(year):
    all_rows = []
    page = 1

    while True:
        params = {
            "serviceKey": service_key,
            "dataType": "JSON",
            "dateCd": "HR",
            "startDt": f"{year}0101",
            "startHh": "00",
            "endDt": f"{year}1231",
            "endHh": "23",
            "obsCode": stn_id,
            "numOfRows": num_of_rows,
            "pageNo": page
        }

        r = requests.get(base_url, params=params)
        r.raise_for_status()
        data = r.json()

        if data["response"]["header"]["resultCode"] != "00":
            return None

        body = data["response"]["body"]
        items = body.get("items")

        if items is None:
            break

        items = items.get("item", [])
        if not items:
            break

        all_rows.extend(items)

        if len(all_rows) >= body["totalCount"]:
            break

        page += 1
        time.sleep(0.15)   # avoid rate limit

    if not all_rows:
        return None

    return pd.DataFrame(all_rows)

# ==============================
# MAIN LOOP (YEARLY SAVE)
# ==============================
for year in range(start_year, end_year + 1):
    print(f"Processing {year}...")

    try:
        df = get_year_data(year)

        if df is None:
            print("  → No data")
            continue

        # optional: convert time column
        df["tm"] = pd.to_datetime(df["tm"])

        out_file = os.path.join(
            path_save,
            f"{stn_id}_{year}.xlsx"
        )

        df.to_excel(out_file, index=False)
        print(f"  ✔ Saved: {out_file}")

    except Exception as e:
        print(f"  ✖ Error in {year}: {e}")
