import subprocess
import json
import os

def extract_video_info(video_path):
    """
    Extrahiert Informationen über das Video, insbesondere über die Audiospuren und den Video-Codec.
    """
    ffprobe_path = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"  # Pfad zu ffprobe

    # Befehl, um Informationen über das Video zu extrahieren
    command = [
        ffprobe_path,
        "-v", "error",  # Unterdrückt Warnungen
        "-show_entries", "stream=index,codec_type,codec_name,channels",  # Gibt spezifische Stream-Informationen aus
        "-of", "json",  # Format der Ausgabe als JSON
        video_path
    ]

    # Führe den Befehl aus und erfasse die Ausgabe
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout

    # Parse die JSON-Ausgabe
    try:
        info = json.loads(output)
        return info
    except json.JSONDecodeError:
        print("Fehler beim Parsen der Video-Informationen.")
        return None

# Pfad zur Videodatei
video_file = "BundesligaSpielmitZweiKommentatoren_reindexed.mp4"

# Extrahieren der Video-Informationen
video_info = extract_video_info(video_file)

# Ausgabe der extrahierten Informationen
if video_info:
    print(json.dumps(video_info, indent=4))
else:
    print("Keine Informationen verfügbar.")


# um Video und Audio INdex zu drehen:
#    & "C:\Program Files\ffmpeg\bin\ffmpeg.exe" -i BundesligaSpielmitZweiKommentatoren_compressed.mp4 -map 0:a:0 -map 0:a:1 -map 0:v -c copy BundesligaSpielmitZweiKommentatoren_reindexed.mp4