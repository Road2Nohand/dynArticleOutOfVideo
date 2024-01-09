import os
import json
import boto3
from time import sleep

def handler(event, context):
    s3 = boto3.client('s3')
    transcribe = boto3.client('transcribe')

    # Terraform Umgebungsvariablen auslesen
    website_bucket_name = os.environ.get('WEBSITE_BUCKET_PATH')
    data_access_role_arn = os.environ.get('DATA_ACCESS_ROLE_ARN')

    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = record['s3']['object']['key']

        print(f"Transcribe-Function: {file_name} wurde in bucket {bucket_name} hochgeladen!")

        job_name = file_name.split('.')[0]
        file_uri = f"s3://{bucket_name}/{file_name}"
        output_uri = f"s3://{website_bucket_name}"

        # Starten eines Transcription-Jobs mit Call Analytics
        transcribe.start_call_analytics_job(
            CallAnalyticsJobName=job_name,
            Media={'MediaFileUri': file_uri},
            OutputLocation=output_uri,
            DataAccessRoleArn=data_access_role_arn,
            ChannelDefinitions=[
                {'ChannelId': 0, 'ParticipantRole': 'AGENT'},
                {'ChannelId': 1, 'ParticipantRole': 'CUSTOMER'}
            ] # Call Analytics benötigt die Angabe der Channel-Definitionen, die müssen min 2 sein, man müsste die .mp4 vorher genau definieren, deswegen faken wir hier 2 Kanäle
        )

        # Warten, bis der Transkriptionsjob abgeschlossen ist
        while True:
            status = transcribe.get_call_analytics_job(CallAnalyticsJobName=job_name)
            job_status = status['CallAnalyticsJob']['CallAnalyticsJobStatus']
            print(f"Aktueller Status des Transkriptionsjobs '{job_name}': {job_status}")
            if job_status in ['COMPLETED', 'FAILED']:
                break
            sleep(5)

        # Loggen des Fehlschlagens des Transkriptionsjobs
        if job_status == 'FAILED':
            failure_reason = status['CallAnalyticsJob']['FailureReason']
            print(f"Transkriptionsjob '{job_name}' ist fehlgeschlagen. Grund: {failure_reason}")

        # Transkriptionsergebnis und Analyse abrufen, wenn erfolgreich
        elif job_status == 'COMPLETED':
            transcription_file_uri = status['CallAnalyticsJob']['Transcript']['TranscriptFileUri']
            transcription_response = s3.get_object(Bucket=bucket_name, Key=transcription_file_uri)
            transcription_content = json.loads(transcription_response['Body'].read().decode('utf-8'))

            print(transcription_content)

    return {
        'statusCode': 200,
        'body': json.dumps('Call Analytics Transkription abgeschlossen!')
    }
