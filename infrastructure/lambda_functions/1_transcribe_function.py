import json

def handler(event, context):
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = record['s3']['object']['key']
        print(f"Transcribe-Function: Eine Datei wurde hochgeladen: {file_name} im Bucket: {bucket_name}")
        # weitere Logik ...

    return {
        "statusCode": 200,
        "body": json.dumps("Hello from Transcribe-Function!")
    }