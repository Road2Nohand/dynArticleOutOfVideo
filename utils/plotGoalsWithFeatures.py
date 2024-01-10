import matplotlib.pyplot as plt
import re
from datetime import datetime

# Funktion zum Extrahieren von Torinformationen aus dem Transkript mit Regex
def extract_goal_info_regex(transcript_data):
    goal_events = []

    # Regex pattern for "Tor" and "tor"
    goal_pattern = r'\bTor\b|\btor\b'

    for entry in transcript_data:
        content = entry['content']
        timestamp = entry['timestamp']
        sentiment = entry['sentiment']
        loudness = entry['loudness_avg']
        confidence = entry['confidence_avg']

        # Check for goal mentions using regex
        if re.search(goal_pattern, content):
            goal_events.append({'time': timestamp, 'content': content, 'sentiment': sentiment, 'loudness': loudness, 'confidence': confidence})

    return goal_events

goal_events_regex = extract_goal_info_regex(data)

# Funktion, um Zeitstempel in Minuten umzuwandeln
def timestamp_to_minutes(timestamp):
    time_parts = [int(part) for part in timestamp.split(':')]
    return time_parts[0] * 60 + time_parts[1] + time_parts[2] / 60

# Vorbereiten der Daten für das Plot
times_goals = [timestamp_to_minutes(event['time']) for event in goal_events_regex]
sentiments_goals = [event['sentiment'] for event in goal_events_regex]
texts_goals = [f"{event['content']}\nS: {event['sentiment']}\nL: {round(event['loudness'], 1)}\nC: {round(event['confidence'], 2)}" for event in goal_events_regex]

# Erstellen des Scatterplots
plt.figure(figsize=(15, 6))  # Anpassung der Plot-Breite
for i, event in enumerate(goal_events_regex):
    time = times_goals[i]
    plt.scatter(time, 1, color='blue', s=100, alpha=0.5)
    plt.text(time, 1, texts_goals[i], fontsize=8, ha='left', va='bottom', rotation=45)

# Anpassen des Plots
plt.title('Zeitliche Verteilung der Tore im Bundesliga-Spiel (mit Content)')
plt.xlabel('Spielzeit in Minuten')
plt.ylabel('Ereignisse')
plt.yticks([])
plt.xlim(0, 120)  # Einstellung der X-Achse auf 120 Minuten

# Anzeigen des Plots
plt.show()
