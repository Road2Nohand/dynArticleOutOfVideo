import os
import subprocess

def compress_video(input_path, output_path, target_size_mb):
    """
    Komprimiert das Video auf die angegebene Zielgröße in Megabyte, behält aber alle Audiospuren unverändert.
    """
    # Pfad zur ffmpeg.exe-Datei
    ffmpeg_path = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"

    # Befehl zum Komprimieren des Videos mit ffmpeg
    command = [
        ffmpeg_path,  # Pfad zur ffmpeg.exe-Datei
        "-i", input_path,  # Eingabedatei
        "-c:v", "libx264",  # Videocodec
        "-b:v", f"{target_size_mb}M",  # Zielgröße für das Video in Megabyte
        "-c:a", "copy",  # Kopiere alle Audiospuren unverändert
        "-map", "0",  # Behalte alle Streams aus der Eingabedatei bei
        output_path  # Ausgabedatei
    ]

    # Führe den ffmpeg-Befehl aus
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Pfad zur hochgeladenen Datei
input_file = "BundesligaSpielmitZweiKommentatoren.mp4"

# Zielgröße in Megabyte
target_size_mb = 0.5  # Gewünschte Dateigröße in Megabyte

# Erstellen Sie den Ausgabepfad für die komprimierte Videodatei
output_file = os.path.splitext(input_file)[0] + "_compressed.mp4"

# Komprimieren Sie das Video und behalten Sie alle Audiospuren unverändert
compress_video(input_file, output_file, target_size_mb)