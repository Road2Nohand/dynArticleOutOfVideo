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



    # Test: Auf Video-Bucket zugreifen
    try:
        s3.list_objects(Bucket=video_bucket_name)  # Korrigierter Bucket-Name
        logger.info(f'Zugriff auf Video-Bucket "{video_bucket_name}" erfolgreich.')
        
        # Zusätzlicher Test: Ausgabe des Inhalts des Video-Buckets
        logger.info(f'Inhalt von Video-Bucket "{video_bucket_name}":')
        objects = s3.list_objects(Bucket=video_bucket_name)
        for obj in objects.get('Contents', []):
            logger.info(obj['Key'])
            
    except Exception as e:
        logger.error(f'Fehler beim Zugriff auf Video-Bucket "{video_bucket_name}": {str(e)}')

    # Test: Auf Website-Bucket zugreifen
    try:
        s3.list_objects(Bucket=website_bucket_name)
        logger.info(f'Zugriff auf Website-Bucket "{website_bucket_name}" erfolgreich.')
        
        # Zusätzlicher Test: Erstellen und Loggen einer "HelloWorld.txt" Datei im Website-Bucket
        s3.put_object(Bucket=website_bucket_name, Key='HelloWorld.txt', Body='Hello, World!')
        logger.info('Erstellung von "HelloWorld.txt" im Website-Bucket erfolgreich.')
        
    except Exception as e:
        logger.error(f'Fehler beim Zugriff auf Website-Bucket "{website_bucket_name}": {str(e)}')





    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = record['s3']['object']['key']

        logger.info(f"Transcribe-Function: {file_name} wurde in Bucket {bucket_name} hochgeladen!")

        # Generieren eines einzigartigen Job-Namens
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        job_name = f"{file_name.split('.')[0]}-{timestamp}"
        logger.info(f"Generierter Transkriptions-Job-Name: {job_name}")
        file_uri = f"s3://{bucket_name}/{file_name}"
        output_uri = f"s3://{website_bucket_name}"

        # Starten eines Transcription-Jobs mit Call Analytics
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': file_uri},
            MediaFormat='mp4',  # oder das entsprechende Format Ihrer Datei
            LanguageCode='de-DE',  # Setzt die Sprache auf Deutsch
            OutputBucketName=website_bucket_name,
            Settings={
                'ChannelIdentification': True,  # Aktiviert die automatische Kanalerkennung
                'ShowSpeakerLabels': True,  # Aktiviert die Sprechererkennung
                'MaxSpeakerLabels': 2  # Setzt die maximale Anzahl der Sprecher (angepasst an Ihr Szenario)
            }
        )

        # Warten, bis der Transkriptionsjob abgeschlossen ist
        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']
            logger.info(f"Aktueller Status des Transkriptionsjobs '{job_name}': {job_status}")
            if job_status in ['COMPLETED', 'FAILED']:
                break
            sleep(5)
        
        # Loggen des Jobstatus
        if job_status == 'FAILED':
            failure_reason = status['TranscriptionJob']['FailureReason']
            logger.error(f"Transkriptionsjob '{job_name}' ist fehlgeschlagen. Grund: {failure_reason}")
        elif job_status == 'COMPLETED':
            logger.info(f"Transkriptionsjob '{job_name}' erfolgreich abgeschlossen.")


    return {
        'statusCode': 200,
        'body': json.dumps('Call Analytics Transkription abgeschlossen!')
    }