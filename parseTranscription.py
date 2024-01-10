import json
from datetime import timedelta

# Pfad zur JSON-Datei
file_path = 'BundesligaSpiel1std37min.json' # Ersetzen Sie dies mit dem tatsächlichen Dateipfad

# JSON-Datei laden
with open(file_path, 'r') as file:
    data = json.load(file)

# Liste für gespeicherte Transkripte erstellen
transcripts = []

# Durch alle Transkripte gehen
for entry in data.get('Transcript', []):
    # Überprüfen ob die ParticipantRole "AGENT" ist
    if entry.get('ParticipantRole') == "AGENT":
        sentiment = entry.get("Sentiment")
        content = entry.get('Content')
        # Beginn-Zeitstempel aus dem ersten Item extrahieren
        begin_offset_millis = entry.get('Items', [{}])[0].get('BeginOffsetMillis', 0)
        # Timestamp in ein lesbares Format umwandeln (hh:mm:ss)
        timestamp = str(timedelta(milliseconds=begin_offset_millis))
        # timestamp nur die ersten 7 Zeichen (hh:mm:ss) behalten
        timestamp = timestamp[:7]
        transcripts.append(f"{timestamp} Sentiment: {sentiment} Content: {content}")

# Ergebnis ausgeben
for transcript in transcripts:
    print(transcript)
