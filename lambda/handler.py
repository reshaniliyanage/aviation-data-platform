import json
import os
import logging
import datetime
import time

import boto3
import requests
from botocore.exceptions import ClientError

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
cloudwatch = boto3.client("cloudwatch")

# API
API_URL = "https://api.open-meteo.com/v1/forecast?latitude=60.1699&longitude=24.9384&current_weather=true"


# Config loader
def get_config(event):
    event = event or {}

    bucket = event.get("bucket") or os.environ.get("BUCKET_NAME")
    table_name = event.get("table") or os.environ.get("TABLE_NAME")

    if not bucket or not table_name:
        raise ValueError("Missing BUCKET_NAME or TABLE_NAME")

    return bucket, table_name


# Metrics helper
def put_metric(name, value):
    cloudwatch.put_metric_data(
        Namespace="AviationPipeline",
        MetricData=[
            {
                "MetricName": name,
                "Value": value,
                "Unit": "Count"
            }
        ]
    )


# Retry with exponential backoff
def fetch_with_retry(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "aviation-data-pipeline/1.0"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning({
                "event": "api_retry",
                "attempt": attempt + 1,
                "error": str(e)
            })
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                raise


# Validation
def validate_weather(data):
    if "current_weather" not in data:
        raise ValueError("Invalid API response")
    return True


def main(event, context):
    now = datetime.datetime.utcnow()
    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    start_time = time.time()

    try:
        bucket, table_name = get_config(event)
        table = dynamodb.Table(table_name)

        logger.info({"event": "start", "run_id": run_id})

        # Fetch + validate
        data = fetch_with_retry(API_URL)
        validate_weather(data)

        # Partitioned path
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")

        key = f"weather/year={year}/month={month}/day={day}/weather_{run_id}.json"

        # Upload
        # Flatten weather payload
        weather = data["current_weather"]

        record = {
            "timestamp": weather["time"],
            "temperature": weather["temperature"],
            "windspeed": weather["windspeed"],
            "winddirection": weather["winddirection"],
            "weathercode": weather["weathercode"],
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "year": year,
            "month": month,
            "day": day
        }

        # Upload flattened record
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(record),
            ContentType="application/json",
            Metadata={"run_id": run_id}
        )

        # DynamoDB log
        table.put_item(
            Item={
                "run_id": run_id,
                "status": "SUCCESS",
                "s3_path": f"s3://{bucket}/{key}",
                "timestamp": now.isoformat()
            }
        )

        # Metrics
        put_metric("SuccessfulRuns", 1)
        duration = time.time() - start_time

        cloudwatch.put_metric_data(
            Namespace="AviationPipeline",
            MetricData=[
                {"MetricName": "ExecutionTime", "Value": duration, "Unit": "Seconds"}
            ]
        )

        logger.info({"event": "success", "run_id": run_id})

        return {
            "statusCode": 200,
            "body": json.dumps({"run_id": run_id})
        }

    except Exception as e:
        logger.error({"event": "failure", "run_id": run_id, "error": str(e)})

        put_metric("FailedRuns", 1)

        try:
            _, table_name = get_config(event)
            table = dynamodb.Table(table_name)

            table.put_item(
                Item={
                    "run_id": run_id,
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": now.isoformat()
                }
            )
        except ClientError:
            logger.error("DynamoDB logging failed")

        raise