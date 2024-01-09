import os
import json
import boto3
from time import sleep

def handler(event, context):
    s3 = boto3.client('s3')
    transcribe = boto3.client('transcribe')

    # Terraform Umgebungsvariablen auslesen
    website_bucket_path = os.environ.get('WEBSITE_BUCKET_PATH')
    data_access_role_arn = os.environ.get('DATA_ACCESS_ROLE_ARN')

    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = record['s3']['object']['key']

        print(f"Transcribe-Function: {file_name} wurde in bucket {bucket_name} hochgeladen!")

        job_name = file_name.split('.')[0]
        file_uri = f"s3://{bucket_name}/{file_name}"

        # Starten eines Transcription-Jobs mit Call Analytics
        transcribe.start_call_analytics_job(
            CallAnalyticsJobName=job_name,
            Media={'MediaFileUri': file_uri},
            OutputLocation=website_bucket_path,
            DataAccessRoleArn=data_access_role_arn,
            Settings={
                # Hier können spezifische Einstellungen für Call Analytics angepasst werden
            }
        )

        # Warten, bis der Transkriptionsjob abgeschlossen ist
        while True:
            status = transcribe.get_call_analytics_job(CallAnalyticsJobName=job_name)
            if status['CallAnalyticsJob']['CallAnalyticsJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            sleep(5)

        # Transkriptionsergebnis und Analyse abrufen
        if status['CallAnalyticsJob']['CallAnalyticsJobStatus'] == 'COMPLETED':
            transcription_file_uri = status['CallAnalyticsJob']['Transcript']['TranscriptFileUri']
            transcription_response = s3.get_object(Bucket=bucket_name, Key=transcription_file_uri)
            transcription_content = json.loads(transcription_response['Body'].read().decode('utf-8'))

            print(transcription_content)

    return {
        'statusCode': 200,
        'body': json.dumps('Call Analytics Transkription abgeschlossen!')
    }
