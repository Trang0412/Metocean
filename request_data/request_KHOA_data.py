import requests
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd  # new import for CSV saving


def fetch_hourly_tide(
    service_key: str,
    base_url: str,
    obs_post_id: str,
    start_dt: str,
    end_dt: str,
    num_of_rows: int = 999,
    page_no: int = 1,
    response_type: str = "json",
) -> Dict[str, Any]:
    params = {
        "serviceKey": service_key,
        "obsPostId": obs_post_id,
        "startDt": start_dt,
        "endDt": end_dt,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "_type": response_type,
    }

    encoded_params = urllib.parse.urlencode(params, doseq=True)
    url = f"{base_url}?{encoded_params}"

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    if response_type.lower() == "json":
        data = resp.json()
    else:
        data = {"raw": resp.text}

    return data


def parse_hourly_tide_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Adjust keys according to actual API response.
    Example assumes:
      item["obsTime"]  -> observation time
      item["tideLevel"] -> tide height
    """
    try:
        items = data["response"]["body"]["items"]
    except (KeyError, TypeError):
        raise ValueError("Unexpected JSON structure or no data.")

    records = []
    for item in items:
        record = {
            "time": item.get("obsTime"),
            "tide": float(item.get("tideLevel")) if item.get("tideLevel") not in (None, "") else None,
            "obsPostId": item.get("obsPostId"),
        }
        records.append(record)

    return records


def save_tide_to_csv(records: List[Dict[str, Any]], filepath: str) -> None:
    """
    Save list of tide records (dicts) to a CSV file.
    """
    df = pd.DataFrame(records)
    # index=False to avoid the extra index column in the CSV.[web:23][web:25]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    SERVICE_KEY = "950fb465225d3909c46d9f7bac904b06f9ef1053d27c3b5ffd998425bf290dac"
    BASE_URL = "https://apis.data.go.kr/1192136/hourlyTide/GetHourlyTideApiService"
    OBS_POST_ID = "DT_0022"

    START_DT = "2024010100"
    END_DT = "2024010123"

    data = fetch_hourly_tide(
        service_key=SERVICE_KEY,
        base_url=BASE_URL,
        obs_post_id=OBS_POST_ID,
        start_dt=START_DT,
        end_dt=END_DT,
        num_of_rows=999,
        page_no=1,
        response_type="json",
    )

    tide_records = parse_hourly_tide_json(data)

    # choose your output CSV path
    output_csv = "D:\\InProbation\\Metocean\\Data\\Observations\\1hr_tide\\hourly_tide_20240101_DT_0022.csv"
    save_tide_to_csv(tide_records, output_csv)

    print(f"Saved {len(tide_records)} rows to {output_csv}")
