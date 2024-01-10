$jsonContent = Get-Content 'BundesligaSpiel1std37min.json' | ConvertFrom-Json

# Erstellung eines Objekts für jeden AGENT-Transkript-Eintrag mit Content und Sentiment als Text
$agentDetails = $jsonContent.Transcript | Where-Object { $_.ParticipantRole -eq "AGENT" } | ForEach-Object {
    $content = $_.Content
    $sentimentText = $_.Sentiment

    # Erstellung eines benutzerdefinierten Objekts für jede Ausgabe
    [PSCustomObject]@{
        Content = $content
        SentimentText = $sentimentText
    }
}

# Ausgabe der Details als Objekt
$agentDetails