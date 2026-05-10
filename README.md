# Aviation Data Platform

#### Overview

This project is a cloud-based data pipeline built on AWS that ingests external API data, stores it in a structured data lake, and enables analytics through cataloging and querying services. It is designed to demonstrate practical data engineering skills including ingestion, transformation, orchestration concepts, and observability.

The system follows a serverless architecture and focuses on scalability, modularity, and maintainability using Infrastructure as Code.

## Architecture

The system is built around a simple event-driven data flow.

<img width="3385" height="576" alt="architecture-diagram" src="https://github.com/user-attachments/assets/1d1c8266-c0e5-4c9f-804b-39b5cf3e1c64" />

## Tech Stack

AWS Lambda for data ingestion
Amazon S3 for data lake storage
DynamoDB for pipeline execution logging
AWS Glue for metadata cataloging and schema discovery
Amazon Athena for querying structured data
CloudWatch for monitoring and observability
AWS CDK (TypeScript) for infrastructure as code
Python for Lambda implementation

##  Data Flow

Lambda function fetches weather data from an external API
Data is validated and written to S3 in a partitioned structure based on date
Each pipeline execution is logged in DynamoDB
CloudWatch captures logs and execution metrics
Glue Crawler scans S3 and updates the data catalog
Athena is used to query the processed data

## Key Features

Serverless data ingestion pipeline
Partitioned S3-based data lake design
Automated schema discovery using Glue Crawler
Execution tracking using DynamoDB
Monitoring and logging through CloudWatch
Retry logic implemented for API reliability
Infrastructure defined using AWS CDK

## Project Structure

aviation-data-platform/

├── bin/           CDK application entry point

├── lib/           Infrastructure stack definitions

├── lambda/        Data ingestion function

├── test/          Unit tests

├── cdk.json       CDK configuration

├── package.json   Dependencies and scripts


## Design Notes

The architecture is intentionally kept modular and cloud-native. The ingestion layer is fully serverless to allow scalability without infrastructure management overhead. Data is stored in a partitioned format in S3 to optimize query performance in Athena. Glue is used to maintain schema consistency and enable data discovery.

The design follows common data lake patterns used in modern cloud data platforms.

## Future Improvements
Introduce Apache Airflow for orchestration
Add Spark-based processing layer for large-scale transformations
Implement data quality framework (e.g., Great Expectations)
Integrate dbt or Snowflake for analytics modeling
Extend to near real-time ingestion using streaming services

## Author

Data & Analytics Engineer with experience in cloud data platforms, ETL pipeline design, and analytics engineering across AWS-based environments.
