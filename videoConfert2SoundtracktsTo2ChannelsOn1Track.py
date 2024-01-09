import subprocess

def convert_audio_tracks_to_stereo_and_merge_with_video(input_video_path, output_video_path):
    """
    Konvertiert zwei separate Audiospuren eines Videos in eine einzelne Stereospur,
    wobei die erste Spur auf den linken und die zweite Spur auf den rechten Kanal gelegt wird.
    Anschließend wird die neue Audiospur mit dem ursprünglichen Video kombiniert.
    """
    ffmpeg_path = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"  # Pfad zu ffmpeg

    # Befehl, um die Audiospuren zu einer Stereospur zu konvertieren und mit dem Video zu kombinieren
    command = [
        ffmpeg_path,
        "-i", input_video_path,
        "-filter_complex", "[0:a:0]pan=1c|c0=c0[left];[0:a:1]pan=1c|c0=c0[right];[left][right]amerge=inputs=2[aout]",
        "-map", "0:v",  # Behält das Video vom Input-File
        "-map", "[aout]",  # Nutzt die neu erstellte Stereospur
        "-c:v", "copy",  # Kopiert den Video-Codec
        "-ac", "2",  # Setzt die Anzahl der Audio-Kanäle auf 2 (Stereo)
        output_video_path
    ]

    # Führe den Befehl aus
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Pfad zur Eingabevideodatei
input_video_file = "BundesligaSpielmitZweiKommentatoren_reindexed.mp4"

# Pfad zur Ausgabevideodatei
output_video_file = "BundesligaSpiel_Stereo.mp4"

# Führe die Konvertierung und Zusammenführung aus
convert_audio_tracks_to_stereo_and_merge_with_video(input_video_file, output_video_file)
print("Konvertierung und Zusammenführung abgeschlossen.")