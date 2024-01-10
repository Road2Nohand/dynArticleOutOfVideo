import os
import json
import boto3
from time import sleep
import logging
from datetime import datetime
from datetime import timedelta

# Konfiguration des Loggings
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

def parse_transcript(file_name, bucket_name):
    # Pfad zur JSON-Datei im S3 Bucket
    file_path = f"s3://{bucket_name}/{file_name}"

    # Lese die Datei aus S3
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    data = json.loads(obj['Body'].read().decode('utf-8'))

    # Parse-Logik
    transcripts = []
    cleaned_transcripts = []

    for entry in data.get('Transcript', []):
        if entry.get('ParticipantRole') == "AGENT":
            sentiment = entry.get("Sentiment")
            content = entry.get('Content')
            begin_offset_millis = entry.get('Items', [{}])[0].get('BeginOffsetMillis', 0)
            timestamp = str(timedelta(milliseconds=begin_offset_millis))[:7]
           
            # Fehlerbehandlung, falls AWS-Transcribe "null" für LoudnessScores oder Confidence zurückgibt
            loudness_scores = entry.get("LoudnessScores", [])
            confidences = [item.get("Confidence", "0.0") for item in entry.get("Items", [])]

            if loudness_scores:
                loudness_average = sum(loudness_scores) / len(loudness_scores)
            else:
                loudness_average = 0

            if confidences:
                confidence_average = sum(float(c) for c in confidences) / len(confidences)
            else:
                confidence_average = 0

            transcript_entry = {
                "timestamp": timestamp,
                "sentiment": sentiment,
                "loudness_avg": loudness_average,
                "confidence_avg": confidence_average,
                "content": content
            }
            transcripts.append(transcript_entry)
            
            # Rauschen aus dem Stadion rausfiltern
            if loudness_average >= 0.2 and confidence_average >= 0.2:
                cleaned_transcripts.append(transcript_entry)

    return transcripts, cleaned_transcripts

def handler(event, context):
    website_bucket_name = os.environ.get('WEBSITE_BUCKET_NAME')
    data_access_role_arn = os.environ.get('DATA_ACCESS_ROLE_ARN')
    video_bucket_name = os.environ.get('VIDEO_BUCKET_NAME')
    
    logger.info(f'Data Access Role ARN, die an Transcribe übergeben wird: {data_access_role_arn}')

    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = record['s3']['object']['key']
        logger.info(f"CallAnalytics-Function: {file_name} wurde in Bucket {bucket_name} hochgeladen!")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        job_name = f"{file_name.split('.')[0]}-{timestamp}"
        logger.info(f"Generierter CallAnalytics-Job-Name: {job_name}")
        file_uri = f"s3://{bucket_name}/{file_name}"

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

        while True:
            status = transcribe.get_call_analytics_job(CallAnalyticsJobName=job_name)
            job_status = status['CallAnalyticsJob']['CallAnalyticsJobStatus']
            logger.info(f"Aktueller Status des Call Analytics-Jobs '{job_name}': {job_status}")
            if job_status in ['COMPLETED', 'FAILED']:
                break
            sleep(5)
        
        if job_status == 'FAILED':
            failure_reason = status['CallAnalyticsJob']['FailureReason']
            logger.error(f"Call Analytics-Job '{job_name}' ist fehlgeschlagen. Grund: {failure_reason}")
        elif job_status == 'COMPLETED':
            logger.info(f"Call Analytics-Job '{job_name}' erfolgreich abgeschlossen.")

            # Ermitteln des Pfads der Ausgabedatei des Transcribe-Jobs
            transcript_bucket_name = 'dyn-bucket-for-static-article-website-dev'
            transcript_file_name = f"analytics/{job_name}.json"
            
            # Parsen der Transkription
            try:
                parsed_transcript, cleaned_transcript = parse_transcript(transcript_file_name, transcript_bucket_name)
                logger.info(f"Parsing der Transkription abgeschlossen.")
            except Exception as e:
                logger.error(f"Beim Parsen der Transkription ist ein Fehler aufgetreten: {e}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'Fehler beim Parsen der Transkription: {e}')
                }

            # Speichern der Ergebnisse im S3 Bucket
            parsed_output_file_name = transcript_file_name.replace('.json', '_transcript_parsed.json')
            cleaned_output_file_name = transcript_file_name.replace('.json', '_transcript_cleaned_from_noise.json')
            s3.put_object(Bucket=website_bucket_name, Key=parsed_output_file_name, Body=json.dumps(parsed_transcript))
            s3.put_object(Bucket=website_bucket_name, Key=cleaned_output_file_name, Body=json.dumps(cleaned_transcript))

    return {
        'statusCode': 200,
        'body': json.dumps('Call Analytics Transkription abgeschlossen und verarbeitet!')
    }