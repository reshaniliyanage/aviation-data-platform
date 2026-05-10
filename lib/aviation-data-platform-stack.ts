import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as glue from 'aws-cdk-lib/aws-glue';
import * as iam from 'aws-cdk-lib/aws-iam';

export class AviationDataPlatformStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 Data Lake
    const dataLake = new s3.Bucket(this, 'AviationDataLake', {
      bucketName: 'aviation-data-lake-dev',
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // DynamoDB Logs Table
    const logsTable = new dynamodb.Table(this, 'PipelineLogs', {
      tableName: 'aviation-pipeline-logs',
      partitionKey: { name: 'run_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // Lambda Ingestion Function
    const ingestionLambda = new lambda.Function(this, 'IngestionLambda', {
      functionName: 'aviation-ingestion-lambda',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.main',
      code: lambda.Code.fromAsset('lambda'),
      environment: {
        BUCKET_NAME: dataLake.bucketName,
        TABLE_NAME: logsTable.tableName,
      },
    });

    dataLake.grantWrite(ingestionLambda);
    logsTable.grantWriteData(ingestionLambda);

    ingestionLambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['cloudwatch:PutMetricData'],
        resources: ['*'],
      })
    );

    // Glue Database
    const glueDatabase = new glue.CfnDatabase(this, 'GlueDatabase', {
      catalogId: this.account,
      databaseInput: {
        name: 'aviation_raw',
      },
    });

    // Glue Crawler Role
    const crawlerRole = new iam.Role(this, 'GlueCrawlerRole', {
      assumedBy: new iam.ServicePrincipal('glue.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AWSGlueServiceRole'
        ),
      ],
    });

    dataLake.grantRead(crawlerRole);

    // Glue Crawler
    new glue.CfnCrawler(this, 'WeatherCrawler', {
      name: 'aviation-weather-crawler',
      role: crawlerRole.roleArn,
      databaseName: glueDatabase.ref,

      targets: {
        s3Targets: [
          {
            path: `s3://${dataLake.bucketName}/weather/`,
          },
        ],
      },

      schedule: {
        scheduleExpression: 'cron(45 16 * * ? *)',
      },

      schemaChangePolicy: {
        updateBehavior: 'UPDATE_IN_DATABASE',
        deleteBehavior: 'LOG',
      },
    });
  }
}