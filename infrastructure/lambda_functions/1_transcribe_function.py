import os
import json
import boto3
from time import sleep
import logging
from datetime import datetime
from datetime import timedelta
import urllib3

# Konfiguration des Loggings
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# OpenAI Lib testen
try:
    from openai import OpenAI
    # Einen Test-Print oder eine einfache Funktionsausführung durchführen
    client = OpenAI(api_key=os.environ.get("OPEN_AI_API_KEY"))
    logger.info(f"OpenAI erfolgreich importiert und OPEN_AI_API_KEY ausgelesen.")
except ImportError as e:
    # Loggen des Fehlers und ggf. Behandlung
    logger.error("Fehler beim Import von OpenAI: %s", e)


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

            # Loudness und confidence auf 3 Nachkomma-Stellen gerundet und Datensatz weiter zu verkleinern
            transcript_entry = {
                "timestamp": timestamp,
                "sentiment": sentiment,
                "loudness_avg": round(loudness_average, 3),
                "confidence_avg": round(confidence_average, 3),
                "content": content
            }
            transcripts.append(transcript_entry)
            
            # Rauschen aus dem Stadion rausfiltern
            if loudness_average >= 0.2 and confidence_average >= 0.2:
                cleaned_transcripts.append(transcript_entry)

    return transcripts, cleaned_transcripts


# Variable hinzufügen, um zu verfolgen, ob der Artikel bereits generiert wurde
article_generated = False

def handler(event, context):
    global article_generated

    website_bucket_name = os.environ.get('WEBSITE_BUCKET_NAME')
    data_access_role_arn = os.environ.get('DATA_ACCESS_ROLE_ARN')
    
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

        progress_created = False
        while True:
            status = transcribe.get_call_analytics_job(CallAnalyticsJobName=job_name)
            job_status = status['CallAnalyticsJob']['CallAnalyticsJobStatus']
            logger.info(f"Aktueller Status des Call Analytics-Jobs '{job_name}': {job_status}")
            if job_status in ['COMPLETED', 'FAILED']:
                break
            else:
                if not progress_created:
                    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                    s3.put_object(Bucket=website_bucket_name, Key='analytics/PROGRESS.txt', Body=f'gestartet um {timestamp}...')
                    logger.info("PROGRESS.txt im S3 Bucket erstellt.")
                    progress_created = True
            sleep(5) # to poll AWS Transcription Progress
        
        if job_status == 'FAILED':
            failure_reason = status['CallAnalyticsJob']['FailureReason']
            logger.error(f"Call Analytics-Job '{job_name}' ist fehlgeschlagen. Grund: {failure_reason}")
            s3.put_object(Bucket=website_bucket_name, Key='analytics/PROGRESS.txt', Body=f'Trankskription fehlgeschlagen: \n {failure_reason}')

        elif job_status == 'COMPLETED':
            logger.info(f"Call Analytics-Job '{job_name}' erfolgreich abgeschlossen.")
            # aktueller timestmamp für PROGRESS.txt
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            s3.put_object(Bucket=website_bucket_name, Key='analytics/PROGRESS.txt', Body=f'Transkription abgeschlossen um \n {timestamp} \n Generiere Artikel und Thumbnail...')
            logger.info(f"Transkription abgeschlossen um {timestamp}.")

            # Ermitteln des Pfads der Ausgabedatei des Transcribe-Jobs
            transcript_bucket_name = 'dyn-bucket-for-static-article-website-dev'
            transcript_file_name = f"analytics/{job_name}.json"
            
            if not article_generated:
                # Parsen der Transkription
                try:
                    parsed_transcript, cleaned_transcript = parse_transcript(transcript_file_name, transcript_bucket_name)
                    logger.info(f"Parsing der Transkription abgeschlossen.")                    

                    # Speichern der Ergebnisse im S3 Bucket
                    s3.put_object(Bucket=website_bucket_name, Key="analytics/transcript_parsed.json", Body=json.dumps(parsed_transcript))
                    s3.put_object(Bucket=website_bucket_name, Key="analytics/transcript_cleaned_from_noise.json", Body=json.dumps(cleaned_transcript))

                    try:
                        # Generieren des Artikels mit GPT-4 Turbo und 128k Context-Length, da 1std.37min Transkription, selbst geparsed, bereits 28k Tokens hatte.
                        # Und möglichst viel historisches Wissen in den Artikel einfließen soll.
                        logger.info(f"Generiere Artikel mit GPT-4 Turbo.")

                        data = json.dumps(cleaned_transcript)  # Konvertieren der bereinigten Transkription in einen String
                        chat_completion = client.chat.completions.create(
                            model="gpt-4-1106-preview",
                            messages=[
                                {
                                    "role": "user",
                                    "content": \
                                    f"Basierend auf der folgenden Transkription eines Fußballspiels, erstelle bitte einen spannenden und kurzen Fußballartikel, \
                                    wie er in einem Sportmagazin stehen könnte. Der Artikel soll einen reißerischen Titel haben und den Leser in Spannung halten. \
                                    Bitte korrigiere auch falsch transkribierte Spielernamen mit deinem historischen Wissen. Gib mir die Antwort ausschließlich als HTML-Code, \
                                    bestehend nur aus einer h1-Überschrift für den Titel und p-Tags für die Absätze des Artikels. Verwende <br>-Tags für Zeilenumbrüche innerhalb der Absätze. \
                                    Lasse alle anderen HTML-Tags, wie doctype, html, head, body und auch ein anfängliches ```html und ein endendes ``` weg. Hier ist die Transkription: \n \
                                    {data}"
                                }
                            ]
                        )
                        article = chat_completion.choices[0].message.content  # Erhalten des HTML-Inhalts
                        print(f"Anz. Input Tokens: {chat_completion.usage.prompt_tokens}")
                        print(f"Anz. Output Tokens: {chat_completion.usage.completion_tokens}")
                        # Speichern des HTML-Artikels im S3 Bucket
                        s3.put_object(Bucket=website_bucket_name, Key='analytics/article.html', Body=article)
                        logger.info("Artikel im S3 Bucket gespeichert.")
                        article_generated = True

                    except Exception as e:
                        logger.error(f"Fehler beim Generieren des Artikels mit GPT-4 Turbo: {e}")
                        return {
                            'statusCode': 500,
                            'body': json.dumps(f'Fehler beim Generieren des Artikels mit GPT-4 Turbo: {e}')
                        }

                    


                    # Generieren des Thumbnails mit DALL-E
                    try:
                        image_generation = client.images.generate(
                        model="dall-e-3",
                        prompt=(
                            "Basierend auf der folgenden Artikel eines Fußballspiels, erstelle bitte ein lebendiges und dynamisches Bild, das ein Fußballspiel darstellt. \n"
                            "Die Szene sollte die Spannung und Energie des Spiels einfangen, \n"
                            "mit zwei Teams inmitten der Aktion und die Spieler inmitten des Fußballfeldes auf dem das Spiel stattgefunden haben könnte. \n"
                            "Die Spieler tragen die Trikots ihres jeweiligen Teams. Versuche auch die Logos der Teams zu representieren. Das Stadion ist voll mit begeisterten Fans, was für eine lebhafte Atmosphäre sorgt. \n"
                            "Dieses Bild sollte die Begeisterung und Leidenschaft des Fußballs vermitteln und ist perfekt als Thumbnail für einen Artikel über ein Fußballspiel geeignet. \n"
                            "Das Bild soll zudem photorealistisch sein!\n"
                            f"{article}"
                            ),
                        size="1024x1024",
                        quality="standard",
                        n=1,
                        )
                    except Exception as e:
                        logger.error(f"Fehler beim Generieren des Thumbnails mit DALL-E: {e}")
                        return {
                            'statusCode': 500,
                            'body': json.dumps(f'Fehler beim Generieren des Thumbnails mit DALL-E: {e}')
                        }

                    image_url = image_generation.data[0].url
                    print(image_url)
                    http = urllib3.PoolManager()
                    response = http.request('GET', image_url)
                    
                    if response.status == 200:
                        # Speichern der Datei im /tmp Verzeichnis
                        temp_file_path = "/tmp/thumbnail.png"
                        with open(temp_file_path, "wb") as file:
                            file.write(response.data)
                        print("Bild erfolgreich gespeichert als /tmp/thumbnail.png")
                    
                        # Hochladen der Datei von /tmp zum S3 Bucket
                        try:
                            s3.upload_file(temp_file_path, website_bucket_name, "analytics/thumbnail.png")
                            logger.info("Thumbnail im S3 Bucket gespeichert.")
                        except Exception as e:
                            logger.error(f"Fehler beim Hochladen des Thumbnails in den S3 Bucket: {e}")
                            return {
                                'statusCode': 500,
                                'body': json.dumps(f'Fehler beim Hochladen des Thumbnails: {e}')
                            }
                    else:
                        print("Fehler beim Herunterladen des Bildes")

                except Exception as e:
                    logger.error(f"Beim Parsen der Transkription ist ein Fehler aufgetreten: {e}")
                    return {
                        'statusCode': 500,
                        'body': json.dumps(f'Fehler beim Parsen der Transkription: {e}')
                    }
                
                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                s3.put_object(Bucket=website_bucket_name, Key='analytics/PROGRESS.txt', Body=f'Transkription und Generierung des \n Artikels und Thumbnails um {timestamp} erfolgreich.')

                # Speichern des Thumbnails im S3 Bucket
                s3.upload_file("thumbnail.png", website_bucket_name, "analytics/thumbnail.png")
                logger.info("Thumbnail im S3 Bucket gespeichert.")

                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                s3.put_object(Bucket=website_bucket_name, Key='analytics/PROGRESS.txt', Body=f'Transkription, Article und Thumbnail erfolgreich inferiert um {timestamp}!')

    return {
        'statusCode': 200,
        'body': json.dumps('Call Analytics Transkription abgeschlossen und verarbeitet!')
    }