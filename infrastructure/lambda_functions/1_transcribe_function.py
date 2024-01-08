import json

def handler(event, _):
    print("Received event: \n" + json.dumps(event))

    return {
        "statusCode": 200,
        "body": json.dumps("Hello from Transcribe-Function!")
    }