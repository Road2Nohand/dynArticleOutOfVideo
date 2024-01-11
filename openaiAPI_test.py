import os
import requests
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPEN_AI_API_KEY"),
)

# Öffne die Datei BundesligaSpiel1std37min_transcript_parsed.json
with open("BundesligaSpiel1std37min_transcript_parsed.json") as f:
    data = f.read()


chat_completion = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=[
        {
            "role": "user",
            "content": \
            f"Basierend auf der folgenden Transkription eines Fußballspiels, erstelle bitte einen spannenden und kurzen Fußballartikel, \
            wie er in einem Sportmagazin stehen könnte. Der Artikel soll einen reißerischen Titel haben und den Leser in Spannung halten. \
            Bitte korrigiere auch falsch transkribierte Spielernamen mit deinem historischen Wissen. Gib mir die Antwort ausschließlich als HTML-Code, \
            bestehend nur aus einer h1-Überschrift für den Titel und p-Tags für die Absätze des Artikels. Verwende <br>-Tags für Zeilenumbrüche innerhalb der Absätze. \
            Lasse alle anderen HTML-Tags, wie doctype, html, head, body und auch ein anfängliches ```html und ein endendes ``` weg. Hier ist die Transkription: \n \
            {data}"      
        }
    ]
)

# Extrahieren und Drucken des Inhalts der Antwort
article = chat_completion.choices[0].message.content

# Extrahieren Sie die Token-Information aus der Antwort
print(f"Anzahl der Tokens für die Eingabe: {chat_completion.usage.prompt_tokens}")
print(f"Anzahl der Tokens für die Ausgabe: {chat_completion.usage.completion_tokens}")

image_generation = client.images.generate(
    model="dall-e-3",
    prompt=(
        "Basierend auf der folgenden Artikel eines Fußballspiels, erstelle bitte ein lebendiges und dynamisches Bild, das ein Fußballspiel darstellt. \n"
        "Die Szene sollte die Spannung und Energie des Spiels einfangen, \n"
        "mit zwei Teams inmitten der Aktion und die Spieler inmitten des Fußballfeldes auf dem das Spiel stattgefunden haben könnte. \n"
        "Die Spieler tragen die Trikots ihres jeweiligen Teams. Versuche auch die Logos der Teams zu representieren. Das Stadion ist voll mit begeisterten Fans, was für eine lebhafte Atmosphäre sorgt. \n"
        "Dieses Bild sollte die Begeisterung und Leidenschaft des Fußballs vermitteln und ist perfekt als Thumbnail für einen Artikel über ein Fußballspiel geeignet. \n"
        "Das Bild soll zudem photorealistisch sein!\n"
        f"{article}"
    ),
    size="1024x1024",
    quality="hd",
    n=1,
)

image_url = image_generation.data[0].url
response = requests.get(image_url)
if response.status_code == 200:
    with open("fussballspiel_thumbnail.png", "wb") as file:
        file.write(response.content)
    print("Bild erfolgreich gespeichert als fussballspiel_thumbnail.png")
else:
    print("Fehler beim Herunterladen des Bildes")