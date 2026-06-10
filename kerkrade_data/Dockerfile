FROM python:3.12-slim

WORKDIR /app

COPY monthly_pull.py /app/monthly_pull.py

# App writes to mounted Azure Files volume at /monthly_data.
ENV SAVE_FOLDER=/monthly_data

CMD ["python", "/app/monthly_pull.py"]
