import os
import json
import time
import urllib.request
import urllib.error
from datetime import date, datetime
import calendar

BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
DEFAULT_LOCATION = "Kerkrade"
UNIT_GROUP = "metric"
CONTENT_TYPE = "csv"
INCLUDE = "hours"
ELEMENTS = "name,datetime,datetimeEpoch,tempmax,tempmin,temp,dew,humidity,cloudcover,visibility,precip,precipprob,precipcover,preciptype,snow,snowdepth,windspeed,windspeedmean,windgust,winddir,pressure,solarradiation,solarenergy,uvindex,sunrise,sunset,moonphase,conditions,aquius,aqieur,aqielement,pm1,pm2p5,pm10,so1,no2,o3,co,cape,cin,latitude,longitude,timezone,description,stations,source"
MAX_DISTANCE = '25000'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
YEARS_BACK = 10
SLEEP_SECONDS_BETWEEN_CALLS = 1.0
MIN_BYTES_TO_TREAT_AS_VALID = 200


def load_api_keys():
    raw = os.getenv("API_KEYS", "").strip()
    if raw:
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        if keys:
            return keys
    return []


def get_save_folder():
    return os.getenv("SAVE_FOLDER", os.path.join(SCRIPT_DIR, "monthly_data"))

def get_location():
    return os.getenv("LOCATION", DEFAULT_LOCATION).strip() or DEFAULT_LOCATION

def safe_location_name(loc):
    return loc.replace(",", "_").replace(" ", "")

def month_start_end(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return (
        date(year, month, 1).isoformat(),
        date(year, month, last_day).isoformat(),
    )

def prev_month(year, month):
    month -= 1
    if month == 0:
        return year - 1, 12
    return year, month

def build_url(location, api_key, d1, d2):
    return (
        f"{BASE_URL}{location}/{d1}/{d2}"
        f"?unitGroup={UNIT_GROUP}"
        f"&key={api_key}"
        f"&contentType={CONTENT_TYPE}"
        f"&include={INCLUDE}"
        f"&elements={ELEMENTS}"
        f"&maxDistance={MAX_DISTANCE}"
    )

def read_http_error_body(e):
    try:
        return e.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

def load_state(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)

    today = date.today()
    return {
        "next_year": today.year,
        "next_month": today.month,
        "months_remaining": YEARS_BACK * 12,
    }

def save_state(path, state):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, path)

def month_file_path(folder, location, year, month):
    loc = safe_location_name(location)
    return os.path.join(folder, f"weather_{loc}_{year:04d}-{month:02d}.csv")

def main():
    api_keys = load_api_keys()
    if not api_keys:
        raise RuntimeError("No API keys configured. Set API_KEYS env var as comma-separated values.")

    save_folder = get_save_folder()
    location = get_location()
    os.makedirs(save_folder, exist_ok=True)
    state_path = os.path.join(save_folder, ".backfill_state.json")
    state = load_state(state_path)

    exhausted_keys = set()

    while state["months_remaining"] > 0 and len(exhausted_keys) < len(api_keys):

        y = state["next_year"]
        m = state["next_month"]
        out_path = month_file_path(save_folder, location, y, m)

        # Skip already downloaded months
        if os.path.exists(out_path) and os.path.getsize(out_path) >= MIN_BYTES_TO_TREAT_AS_VALID:
            y2, m2 = prev_month(y, m)
            state["next_year"], state["next_month"] = y2, m2
            state["months_remaining"] -= 1
            save_state(state_path, state)
            continue

        d1, d2 = month_start_end(y, m)
        success = False

        for idx, api_key in enumerate(api_keys):
            if idx in exhausted_keys:
                continue

            print(f"Trying {y:04d}-{m:02d} with key #{idx+1}")
            url = build_url(location, api_key, d1, d2)

            try:
                with urllib.request.urlopen(url) as resp:
                    csv_text = resp.read().decode("utf-8")

                tmp_path = out_path + ".part"
                with open(tmp_path, "w") as f:
                    f.write(csv_text)
                os.replace(tmp_path, out_path)

                print(f"SAVED {location} using key #{idx+1}")
                success = True
                break

            except urllib.error.HTTPError as e:
                body = read_http_error_body(e)

                if e.code == 429 and "daily cost" in body.lower():
                    print(f"Key #{idx+1} exhausted for today.")
                    exhausted_keys.add(idx)
                    continue

                print(f"HTTP Error {e.code}")
                raise

        if not success:
            print(f"All API keys exhausted. {datetime.now().strftime('%Y-%m-%d: %H:%M:%S')}")
            return

        # Advance month cursor
        y2, m2 = prev_month(y, m)
        state["next_year"], state["next_month"] = y2, m2
        state["months_remaining"] -= 1
        save_state(state_path, state)

        time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)

    if state["months_remaining"] == 0:
        print(f"DONE: Full 10-year backfill complete for {location}.")

if __name__ == "__main__":
    main()
