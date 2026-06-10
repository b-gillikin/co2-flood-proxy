import csv
import io
import os
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
DEFAULT_LOCATION = "Kerkrade"
UNIT_GROUP = "metric"
CONTENT_TYPE = "csv"
INCLUDE = "hours"
ELEMENTS = "name,datetime,datetimeEpoch,tempmax,tempmin,temp,dew,humidity,cloudcover,visibility,precip,precipprob,precipcover,preciptype,snow,snowdepth,windspeed,windspeedmean,windgust,winddir,pressure,solarradiation,solarenergy,uvindex,sunrise,sunset,moonphase,conditions,aquius,aqieur,aqielement,pm1,pm2p5,pm10,so1,no2,o3,co,cape,cin,latitude,longitude,timezone,description,stations,source"
MAX_DISTANCE = "25000"
DEFAULT_LOOKBACK_DAYS = 1
DEFAULT_TIMEZONE = "Europe/Amsterdam"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_save_folder() -> str:
    return os.getenv("SAVE_FOLDER", os.path.join(SCRIPT_DIR, "monthly_data"))


def get_location() -> str:
    return os.getenv("LOCATION", DEFAULT_LOCATION).strip() or DEFAULT_LOCATION


def get_hourly_api_key() -> str:
    api_key = os.getenv("HOURLY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("HOURLY_API_KEY is required.")
    return api_key


def safe_location_name(location: str) -> str:
    return location.replace(",", "_").replace(" ", "")


def month_file_path(folder: str, location: str, year: int, month: int) -> str:
    loc = safe_location_name(location)
    return os.path.join(folder, f"weather_{loc}_{year:04d}-{month:02d}.csv")


def build_url(location: str, api_key: str, start_date: date, end_date: date) -> str:
    return (
        f"{BASE_URL}{location}/{start_date.isoformat()}/{end_date.isoformat()}"
        f"?unitGroup={UNIT_GROUP}"
        f"&key={api_key}"
        f"&contentType={CONTENT_TYPE}"
        f"&include={INCLUDE}"
        f"&elements={ELEMENTS}"
        f"&maxDistance={MAX_DISTANCE}"
    )


def read_http_error_body(error: urllib.error.HTTPError) -> str:
    try:
        return error.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def parse_month(row: dict[str, str]) -> tuple[int, int]:
    dt = (row.get("datetime") or "").strip()
    if dt:
        candidates = (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        )
        for fmt in candidates:
            try:
                parsed = datetime.strptime(dt, fmt)
                return parsed.year, parsed.month
            except ValueError:
                continue

    epoch = (row.get("datetimeEpoch") or "").strip()
    if epoch:
        parsed = datetime.fromtimestamp(int(float(epoch)))
        return parsed.year, parsed.month

    raise ValueError("Row missing parseable datetime and datetimeEpoch.")


def row_key(row: dict[str, str]) -> str:
    epoch = (row.get("datetimeEpoch") or "").strip()
    if epoch:
        return f"epoch:{epoch}"
    return f"datetime:{(row.get('datetime') or '').strip()}"


def row_sort_key(row: dict[str, str]):
    epoch = (row.get("datetimeEpoch") or "").strip()
    if epoch:
        try:
            return (0, int(float(epoch)))
        except ValueError:
            pass
    return (1, (row.get("datetime") or "").strip())


def _parse_row_datetime(row: dict[str, str]) -> datetime | None:
    dt = (row.get("datetime") or "").strip()
    if not dt:
        return None
    # Accept ISO8601 variants (including timezone offsets) first.
    try:
        parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(ZoneInfo(DEFAULT_TIMEZONE)).replace(tzinfo=None)
        return parsed
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt, fmt)
        except ValueError:
            continue
    return None


def _is_future_row(row: dict[str, str], now_local_hour: datetime) -> bool:
    dt = _parse_row_datetime(row)
    if dt is not None:
        return dt > now_local_hour

    epoch_raw = (row.get("datetimeEpoch") or "").strip()
    if epoch_raw:
        try:
            return int(float(epoch_raw)) > int(datetime.now(timezone.utc).timestamp())
        except ValueError:
            return False
    return False


def read_csv_rows(path: str) -> tuple[list[str], list[dict[str, str]]]:
    if not os.path.exists(path):
        return [], []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, list(reader)


def write_csv_rows(path: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    tmp_path = path + ".part"
    with open(tmp_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp_path, path)


def fetch_hourly_rows(location: str, api_key: str, lookback_days: int) -> tuple[list[str], list[dict[str, str]]]:
    today = date.today()
    start_date = today - timedelta(days=lookback_days)
    url = build_url(location, api_key, start_date, today)
    print(f"Pulling hourly data for {location}: {start_date} -> {today}")

    try:
        with urllib.request.urlopen(url) as resp:
            csv_text = resp.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        body = read_http_error_body(error)
        raise RuntimeError(f"HTTP {error.code}: {body}") from error

    reader = csv.DictReader(io.StringIO(csv_text))
    fieldnames = list(reader.fieldnames or [])
    rows = list(reader)
    if not fieldnames or not rows:
        raise RuntimeError("No hourly rows returned by API.")

    # Visual Crossing includes forecast rows for future hours in the current day.
    # Keep only the single latest observed row so each run appends one hour at a time.
    tz_name = os.getenv("HOURLY_TIMEZONE", DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE
    now_local_hour = datetime.now(ZoneInfo(tz_name)).replace(minute=0, second=0, microsecond=0, tzinfo=None)
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    observed_rows: list[dict[str, str]] = []
    dropped_future = 0
    for row in rows:
        row_dt = _parse_row_datetime(row)
        if row_dt is not None:
            if row_dt > now_local_hour:
                dropped_future += 1
                continue
            observed_rows.append(row)
            continue

        epoch_raw = (row.get("datetimeEpoch") or "").strip()
        if epoch_raw:
            try:
                row_epoch = int(float(epoch_raw))
            except ValueError:
                continue
            if row_epoch > now_epoch:
                dropped_future += 1
                continue
            observed_rows.append(row)
            continue

        # If neither datetime nor datetimeEpoch is parseable, skip row.
        continue

    if not observed_rows:
        print("No observed hourly rows returned by API; skipping this run.")
        return fieldnames, []

    latest_row = max(observed_rows, key=row_sort_key)
    if dropped_future:
        print(f"Dropped {dropped_future} future forecast rows from hourly pull.")
    print(f"Selected one observed hourly row: {latest_row.get('datetime', '')}")

    return fieldnames, [latest_row]


def merge_into_month_file(path: str, incoming_fieldnames: list[str], incoming_rows: list[dict[str, str]]) -> None:
    existing_fieldnames, existing_rows = read_csv_rows(path)
    tz_name = os.getenv("HOURLY_TIMEZONE", DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE
    now_local_hour = datetime.now(ZoneInfo(tz_name)).replace(minute=0, second=0, microsecond=0, tzinfo=None)
    existing_rows = [r for r in existing_rows if not _is_future_row(r, now_local_hour)]
    fieldnames = incoming_fieldnames or existing_fieldnames
    if not fieldnames:
        raise RuntimeError("No CSV header available to write merged file.")

    merged_by_key: dict[str, dict[str, str]] = {}
    for row in existing_rows:
        merged_by_key[row_key(row)] = row
    for row in incoming_rows:
        merged_by_key[row_key(row)] = row

    merged_rows = sorted(merged_by_key.values(), key=row_sort_key)
    write_csv_rows(path, fieldnames, merged_rows)
    print(f"UPDATED {os.path.basename(path)} (+{len(incoming_rows)} rows, total={len(merged_rows)})")


def main() -> None:
    save_folder = get_save_folder()
    location = get_location()
    api_key = get_hourly_api_key()
    lookback_days = int(os.getenv("HOURLY_LOOKBACK_DAYS", str(DEFAULT_LOOKBACK_DAYS)))

    os.makedirs(save_folder, exist_ok=True)
    fieldnames, rows = fetch_hourly_rows(location, api_key, lookback_days)

    if not rows:
        return

    rows_by_month: dict[tuple[int, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        year, month = parse_month(row)
        rows_by_month[(year, month)].append(row)

    for (year, month), month_rows in sorted(rows_by_month.items()):
        out_path = month_file_path(save_folder, location, year, month)
        merge_into_month_file(out_path, fieldnames, month_rows)


if __name__ == "__main__":
    main()
