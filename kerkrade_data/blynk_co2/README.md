# Blynk CO2 Stream

This folder contains the Blynk CO2 streaming collector integrated into this project.

## Files

- `iot_stream.py`: pulls current values from Blynk and appends one row.
- `pin-mapping.json`: pin-to-column mapping.
- `streaming_data.csv`: append-only CSV output.
- `streaming_data.parquet`: append-only Parquet output.
- `requirements.txt`: dependencies for this submodule only.

## Usage

```bash
cd blynk_co2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BLYNK_BASE_TOKEN="your-base-token"
python iot_stream.py
```
