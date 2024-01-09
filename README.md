# Sports Video to Article

Task 1:

* Create a **working prototype** that automatically creates an article out of video Content (using AWS Services)
  * The Article should contain text and a relevant picture to the article.
  * Use IaC only

Task 2:

* Create **a concept** for synchronizing sport event data (goal, yellow card, red card, etc.) **with video data**
  * **How do you approach setting up IAM roles for a new AWS project**
    * "Ich würde die IAM-Rollen für das neue AWS-Projekt unter Verwendung von Infrastructure as Code definieren. Mit Hilfe von Terraform würde ich die Rollen erstellen, dabei die notwendigen Berechtigungen und Best Practices für Sicherheit berücksichtigen. Die Rollen würden logisch organisiert, vererbt und regelmäßig überprüft werden, um sicherzustellen, dass sie den Sicherheitsrichtlinien entsprechen. Die Dokumentation der Rollen und Berechtigungen wäre ebenfalls ein wichtiger Bestandteil, um Transparenz und Audits zu ermöglichen."
    * Ich würde IaC nutzen um Tags zu setzen, wodurch Alerts, Billing und Rollen pro Env gesteuert werden können
    * Rollen für temproräre oder externe Berechtigungen, Gruppen für Batches an statischen Berechtigungen
    * Anstatt PW Rotationen würde ich evtl. direkt auf MFA zugreifen, AWS unterstützt z.B. Auth Apps und Yubi-Keys, ein Hybrid wäre praktikabel und sicher.
      Hier muss man ein geeignetes Mittel zwischen Convenience und Praktikabilität finden.
  * **What factors influence your choice of AWS services for a project?**
    * Hier gibt es gesonderte KI Aspekte wie Haluzination (Sicherheit der Inferenz), Kosten (Größe, Quantisierung, Lizenz), Geschwindigkeit (Inferenz)
      LTS und Vergleich zu OpenSource Lösungen, Inhouse Hardware/Zeit (reicht es für eigenes Training)
    * Kosten/Durchsatz, Sicherheit im Allgemeinen, LTS (noch zu "beta"?), Migration zu anderen Clouds?, Popularität im Entwickler-Markt, time-to-market,
      Integration mit bestehenden legacy Systemen?, Skalierbarkeit, Tech die schnelle Prototypen-Entw. ermöglichen veringern auch die time-to markt weil
      man schneller Kunden Feedback bekommt / Agilität.
  * **Highlight key considerations in your choice of technology like costs, realiability, time-to-market.**

## Task 1 - Solution

### Tech Stack

1. **AWS Lambda Functions:**

   * Verwende Lambda Functions für die Ausführung des Codes, der das Video analysiert und den Artikel generiert. Lambda ermöglicht eine serverlose Architektur, die einfach zu skalieren ist.
2. **AWS S3:**

   * Lade die Videos in einen Amazon S3-Bucket hoch. Dies dient als zentraler Speicherort für deine Videodateien.
3. **AWS Transcribe:**

   * Nutze den AWS Transcribe Service, um den gesprochenen Inhalt des Videos in Text umzuwandeln. Dieser Service ist in der Lage, automatisch Sprache zu transkribieren und könnte daher für die Texterstellung des Artikels verwendet werden.
   * Alternativ zu Transcribe: **AWS Recognition** (für Bild und Video analysen)
4. **AWS Comprehend:**

   * Verwende AWS Comprehend, um wichtige Informationen aus dem transkribierten Text zu extrahieren. Dies könnte Schlüsselwörter, Themen oder Stimmungen umfassen.
5. **AWS Lambda (Bildverarbeitung):**

   * Implementiere eine weitere Lambda-Funktion, die ein passendes Bild zum Artikel auswählt. Dies könnte mithilfe von AWS Rekognition geschehen, indem Gesichtserkennung oder Objekterkennung verwendet wird.
6. **AWS S3 (Bildspeicher):**

   * Speichere das ausgewählte Bild in einem anderen S3-Bucket, der als Speicherort für Bilder dient.
7. **AWS EventBridge:**

   * Verbinde die Lambda-Funktionen und S3-Ereignisse mithilfe von AWS EventBridge. Dies ermöglicht eine automatische Ausführung deiner Funktionen, wenn ein neues Video hochgeladen wird.
8. AWS CloudFront (optional):

   * Für die Bereistellung der S3 URLs mit Artikel
9. **AWS DynamoDB** (optional):

   * Speichere die Daten/Meta-Daten der Artikel in einer DynamoDB-Tabelle, um den Status der Verarbeitung und andere relevante Informationen zu verfolgen.
10. **AWS Elemental MediaConvert** (optional):

    * Nutze AWS Elemental MediaConvert, um das Video in verschiedene Formate zu konvertieren. Dies könnte helfen, die Kompatibilität mit verschiedenen Videoquellen zu verbessern.

### Lernzeitplan:

1. **Tag 1-2: Grundlagen von Lambda und EventBridge mit Terraform**:
   * Erlerne die Grundlagen von Terraform für das Erstellen von S3 Buckets und Lambda Functions
   * Erforsche die Grundlagen von Lambda und EventBridge.
   * Setze eine einfache Lambda-Funktion mit Terraform auf, die auf ein Event reagiert.
2. **Tag 3-4: Lambda, Transcribe und S3:**
   * Lerne die Grundlagen von AWS Lambda und AWS Transcribe.
   * Integriere Lambda-Funktionen für die Transkribierung.
   * Arbeite mit S3, um Ressourcen zu speichern.
3. **Tag 5-6: Comprehend (Bildanalyse) und erweiterte Konfiguration:**
   * Implementiere AWS Comprehend für die Bildanalyse.
   * Erweitere die Step Function, um den gesamten Ablauf zu orchestrieren.
4. **Tag 7-8: Feinabstimmung, Tests und Dokumentation:**
   * Führe Tests durch und optimiere den Code.
   * Dokumentiere den Arbeitsablauf und die Konfigurationen.
