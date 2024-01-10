import os
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
            Lasse alle anderen HTML-Tags, wie doctype, html, head, body und auch ein anfängliches ```html und endendes ``` weg. Hier ist die Transkription: \n \
            {data}"      
        }
    ]
)

# Extrahieren und Drucken des Inhalts der Antwort
response_content = chat_completion.choices[0].message.content

""" print(f"\nAntwort: {response_content}")

# Extrahieren und Drucken der Token-Informationen
completion_tokens = chat_completion.usage.completion_tokens
prompt_tokens = chat_completion.usage.prompt_tokens
total_tokens = chat_completion.usage.total_tokens
print(f"\nCompletion Tokens: {completion_tokens}, Prompt Tokens: {prompt_tokens}, Total Tokens: {total_tokens}") """