import json
import matplotlib.pyplot as plt
import re
from datetime import datetime

def timestamp_to_minutes(timestamp):
    """Converts a timestamp in the format hh:mm:ss to minutes."""
    time_parts = [int(part) for part in timestamp.split(':')]
    return time_parts[0] * 60 + time_parts[1] + time_parts[2] / 60

# Pfad zur JSON-Datei
file_path = '/mnt/data/BundesligaSpiel1std37min_transcript_cleaned_from_noise.json'  # Ersetzen Sie dies mit dem tatsächlichen Dateipfad

# JSON-Datei laden
with open(file_path, 'r') as file:
    data = json.load(file)

# Funktion zum Extrahieren der Karten-Informationen mit Regex
def extract_card_info_regex(transcript_data):
    card_events = []

    # Regex patterns for red and yellow cards
    red_card_pattern = r'\bRote Karte\b|\brote Karte\b|\brote karte\b'
    yellow_card_pattern = r'\bGelbe Karte\b|\bgelbe Karte\b|\bgelbe karte\b'

    for entry in transcript_data:
        content = entry['content']
        timestamp = entry['timestamp']
        sentiment = entry['sentiment']
        loudness = entry['loudness_avg']
        confidence = entry['confidence_avg']

        # Check for red card mentions using regex
        if re.search(red_card_pattern, content):
            card_events.append({'time': timestamp, 'type': 'Red Card', 'content': content, 'sentiment': sentiment, 'loudness': loudness, 'confidence': confidence})
        
        # Check for yellow card mentions using regex
        if re.search(yellow_card_pattern, content):
            card_events.append({'time': timestamp, 'type': 'Yellow Card', 'content': content, 'sentiment': sentiment, 'loudness': loudness, 'confidence': confidence})

    return card_events

card_events_regex = extract_card_info_regex(data)

# Erstellen des Scatterplots
plt.figure(figsize=(15, 6))
for event in card_events_regex:
    time = timestamp_to_minutes(event['time'])
    color = 'red' if event['type'] == 'Red Card' else 'yellow'
    plt.scatter(time, 1, color=color, s=100, alpha=0.5)
    plt.text(time, 1, event['content'] + f"\nS: {event['sentiment']}\nL: {round(event['loudness'], 1)}\nC: {round(event['confidence'], 2)}", 
             fontsize=8, ha='left', va='bottom', rotation=45)

# Anpassen des Plots
plt.title('Zeitliche Verteilung der Karten im Bundesliga-Spiel (mit Content)')
plt.xlabel('Spielzeit in Minuten')
plt.ylabel('Karten')
plt.yticks([])
plt.grid(axis='x')

# Hinzufügen einer Legende
red_patch = mpatches.Patch(color='red', label='Rote Karte')
yellow_patch = mpatches.Patch(color='yellow', label='Gelbe Karte')
plt.legend(handles=[red_patch, yellow_patch])

# Anzeigen des Plots
plt.show()
