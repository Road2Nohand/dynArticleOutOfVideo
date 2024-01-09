import os
import json
import boto3
from time import sleep
import logging
from datetime import datetime

# Konfiguration des Loggings
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    s3 = boto3.client('s3')
    transcribe = boto3.client('transcribe')

    # Terraform Umgebungsvariablen auslesen
    website_bucket_name = os.environ.get('WEBSITE_BUCKET_NAME')
    data_access_role_arn = os.environ.get('DATA_ACCESS_ROLE_ARN')
    video_bucket_name = os.environ.get('VIDEO_BUCKET_NAME')
    
    # Protokollieren der ARN, die an die Transcribe-Funktion übergeben wird
    logger.info(f'Data Access Role ARN, die an Transcribe übergeben wird: {data_access_role_arn}')

    # Zugriff auf Buckets testen (Code unverändert)

    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = record['s3']['object']['key']

        logger.info(f"CallAnalytics-Function: {file_name} wurde in Bucket {bucket_name} hochgeladen!")

        # Generieren eines einzigartigen Job-Namens
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        job_name = f"{file_name.split('.')[0]}-{timestamp}"
        logger.info(f"Generierter CallAnalytics-Job-Name: {job_name}")
        file_uri = f"s3://{bucket_name}/{file_name}"

        # Starten eines Call Analytics-Jobs
        transcribe.start_call_analytics_job(
            CallAnalyticsJobName=job_name,
            Media={'MediaFileUri': file_uri},
            OutputLocation=f"s3://{website_bucket_name}",
            DataAccessRoleArn=data_access_role_arn,
            ChannelDefinitions=[
                {
                    'ChannelId': 0,
                    'ParticipantRole': 'AGENT'
                },
                {
                    'ChannelId': 1,
                    'ParticipantRole': 'CUSTOMER'
                }
            ]
        )

        # Warten, bis der Call Analytics-Job abgeschlossen ist
        while True:
            status = transcribe.get_call_analytics_job(CallAnalyticsJobName=job_name)
            job_status = status['CallAnalyticsJob']['CallAnalyticsJobStatus']
            logger.info(f"Aktueller Status des Call Analytics-Jobs '{job_name}': {job_status}")
            if job_status in ['COMPLETED', 'FAILED']:
                break
            sleep(5)
        
        # Loggen des Jobstatus
        if job_status == 'FAILED':
            failure_reason = status['CallAnalyticsJob']['FailureReason']
            logger.error(f"Call Analytics-Job '{job_name}' ist fehlgeschlagen. Grund: {failure_reason}")
        elif job_status == 'COMPLETED':
            logger.info(f"Call Analytics-Job '{job_name}' erfolgreich abgeschlossen.")

    return {
        'statusCode': 200,
        'body': json.dumps('Call Analytics Transkription abgeschlossen!')
    }
