import json
from datetime import timedelta
import matplotlib.pyplot as plt
import re

def timestamp_to_minutes(timestamp):
    """Converts a timestamp in the format hh:mm:ss to minutes"""
    time = timestamp.split(':')
    return int(time[0]) * 60 + int(time[1]) + int(time[2]) / 60

# Pfad zur JSON-Datei
file_path = 'BundesligaSpiel1std37min_transcript_parsed.json'  # Ersetzen Sie dies mit dem tatsächlichen Dateipfad

# JSON-Datei laden
with open(file_path, 'r') as file:
    data = json.load(file)

# Funktion zum Extrahieren der Karten-Informationen
def extract_card_info(transcript_data):
    card_events = []

    for entry in transcript_data:
        # Überprüfen, ob der Inhalt "Rote Karte" oder "Gelbe Karte" enthält
        if "Rote Karte" in entry['content']:
            card_events.append({'time': entry['timestamp'], 'type': 'Red Card'})
        elif "Gelbe Karte" in entry['content']:
            card_events.append({'time': entry['timestamp'], 'type': 'Yellow Card'})

    return card_events

# Updating the function to use regex for card detection and to include the content
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

plt.figure(figsize=(15, 6))
for event in card_events_regex:
    time = timestamp_to_minutes(event['time'])
    color = 'red' if event['type'] == 'Red Card' else 'yellow'
    plt.scatter(time, 1, color=color, s=100, alpha=0.5)
    plt.text(time, 1, event['content'] + f"\nS: {event['sentiment']}\nL: {round(event['loudness'], 1)}\nC: {round(event['confidence'], 2)}", 
             fontsize=8, ha='left', va='bottom', rotation=45)

# Customizing the plot
plt.title('Zeitliche Verteilung der Karten im Bundesliga-Spiel (mit Content)')
plt.xlabel('Spielzeit in Minuten')
plt.ylabel('Karten')
plt.yticks([])
plt.grid(axis='x')

# Adding legend
plt.legend(handles=[red_patch, yellow_patch])

# Show the plot
plt.show()
