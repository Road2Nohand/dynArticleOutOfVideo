import json
from datetime import timedelta

# Pfad zur JSON-Datei
file_path = 'BundesligaSpiel1std37min.json'  # Ersetzen Sie dies mit dem tatsächlichen Dateipfad

# Output-Datei, ist der Name der Input Datei mit '_transcript_parsed.json' am Ende
out_file_path = file_path.replace('.json', '_transcript_parsed.json')
# Output-Datei für die bereinigte Version
cleaned_out_file_path = file_path.replace('.json', '_transcript_cleaned_from_noise.json')

# JSON-Datei laden
with open(file_path, 'r') as file:
    data = json.load(file)

# Liste für gespeicherte Transkripte erstellen
transcripts = []
cleaned_transcripts = []  # Für die bereinigte Version

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
        # Loudness-Scores und Confidences extrahieren
        loudness_scores = entry.get("LoudnessScores", [])
        confidences = [item.get("Confidence", "0.0") for item in entry.get("Items", [])]
        # Durchschnitt der Loudness-Scores berechnen
        loudness_average = sum(loudness_scores) / len(loudness_scores) if loudness_scores else None
        # Durchschnitt der Confidences berechnen
        confidence_average = sum(float(c) for c in confidences) / len(confidences) if confidences else None
        transcript_entry = {
            "timestamp": timestamp,
            "sentiment": sentiment,
            "loudness_avg": loudness_average,
            "confidence_avg": confidence_average,
            "content": content
        }
        transcripts.append(transcript_entry)
        
        # Überprüfen, ob sowohl Loudness- als auch Confidence-Durchschnitt größer oder gleich 0.2 sind
        if loudness_average is not None and confidence_average is not None and \
           loudness_average >= 0.2 and confidence_average >= 0.2:
            cleaned_transcripts.append(transcript_entry)

# Ergebnis als JSON-Datei speichern
with open(out_file_path, 'w') as output_file:
    json.dump(transcripts, output_file, indent=2)

# Ergebnis ausgeben
for transcript in transcripts:
    print(transcript)

# Bereinigte Version als JSON-Datei speichern
with open(cleaned_out_file_path, 'w') as cleaned_output_file:
    json.dump(cleaned_transcripts, cleaned_output_file, indent=2)
