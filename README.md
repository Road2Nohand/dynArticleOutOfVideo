# SportsVideo-to-Article-to-Thumbnail

## Projektübersicht
Dieses Projekt entwickelt einen Prototypen, der automatisch aus Sportvideoinhalten Artikel erstellt. Dabei wird ausschließlich auf Infrastructure as Code (IaC) unter Verwendung von AWS-Diensten gesetzt.

## Hauptaufgaben

### Task 1: Prototypentwicklung
Erstellung eines Prototyps, der automatisch Artikel aus Sportvideos generiert. Jeder Artikel soll Text und ein relevantes Bild enthalten.

### Task 2: Konzeptentwicklung
Entwicklung eines Konzepts zur Synchronisierung von Sportereignisdaten (z.B. Tore, Karten) mit Videodaten. Dies beinhaltet die Einrichtung von IAM-Rollen und die Auswahl von AWS-Diensten unter Berücksichtigung von KI-Aspekten, Kosten und Sicherheit.

## Infrastruktur und Konfiguration

### Terraform-Infrastruktur (Verzeichnis: `infrastructure`)

#### Hauptkonfiguration (`main.tf`)
Konfiguriert den AWS-Provider und definiert die Terraform-Backend-Einstellungen sowie die erforderlichen AWS-Ressourcen wie S3 Buckets, IAM Rollen und Policies, und Lambda-Funktionen.

#### Variablendefinitionen
Definiert Variablen für Bucket-Namen und andere wiederverwendbare Konfigurationselemente.

#### S3 Buckets
Konfiguration der S3 Buckets für die Speicherung von Website-Daten und Videomaterial.

#### IAM Rollen und Policies
Definiert Rollen und Policies für den Zugriff auf AWS-Dienste und Ressourcen.

#### Lambda-Funktionen
Lambda-Funktionen zur Verarbeitung von Videos und Erstellung von Transkripten.

### GitHub Actions Workflow (Verzeichnis: `.github/workflows`)

#### Terraform CI/CD Workflow (`terraform-ci-workflow.yml`)
Definiert einen Workflow für Continuous Integration und Deployment mit Terraform auf GitHub Actions. Dieser Workflow beinhaltet Schritte für das Einrichten von AWS-Zugangsdaten, Initialisierung und Anwendung von Terraform sowie das Hochladen von Inhalten auf S3.

## Lambda-Funktionen (Verzeichnis: `infrastructure/lambda_functions`)

### Transkriptionsfunktion (`1_transcribe_function.py`)
Eine Python-Funktion, die AWS Transcribe verwendet, um Transkripte aus Videoinhalten zu erstellen und anschließend Artikel und Thumbnails zu generieren mit "GPT-4 Turbo" und "Dall-E-3".

## Web-Frontend (Verzeichnis: `root`)

### Index-Datei (`index.html`)
Die `index.html` definiert die Struktur und das Styling der Web-Oberfläche. Diese Datei dient als Benutzeroberfläche für das Projekt und zeigt den Fortschritt der Inferenzprozesse, den generierten Artikel sowie das Thumbnail an. Sie beinhaltet HTML-Strukturen für die Darstellung von Transkriptionsfortschritten, den Artikel, das Thumbnail-Bild und Verlinkungen zu relevanten Ressourcen.

## Ordnerstruktur und wichtige Dateien

- `.github/workflows/`: Enthält den Terraform CI/CD Workflow (`terraform-ci-workflow.yml`).
- `infrastructure/`: Hauptverzeichnis für Terraform-Konfigurationen (`main.tf`) und Lambda-Funktionsdefinitionen.
- `infrastructure/lambda_functions/`: Beinhaltet die Lambda-Funktion (`1_transcribe_function.py`) zur Verarbeitung von Videos und Erstellung von Transkripten.
- `plots/`: Ordner für Statistiken und Visualisierungen aus den transkribierten Daten.
- `videos/`: Verzeichnis für die Videos, die zur Inferenz verwendet werden.
- `index.html`: Die Haupt-Webseite des Projekts, zeigt die Ergebnisse der Inferenz, den generierten Artikel und das Thumbnail an. Implementiert außerdem das Polling von Backend-Daten und die dynamische Anzeige von Fortschritten und Ergebnissen.

## Technologien und Werkzeuge

- **AWS-Dienste**: Nutzung verschiedener AWS-Dienste wie S3, Lambda und IAM für die Verarbeitung und Speicherung von Daten.
- **Terraform**: Infrastruktur als Code zur Einrichtung und Verwaltung der AWS-Ressourcen.
- **GitHub Actions**: Automatisierung der Deployment-Prozesse durch CI/CD-Pipelines.
- **Python**: Programmiersprache für die Entwicklung der Lambda-Funktionen.
- **HTML/CSS**: Gestaltung und Strukturierung der Web-Frontend-Oberfläche.

## Zukünftige Erweiterungen

- Integration weiterer KI-Dienste wie "OpenAI Whisper" zur Verbesserung der Genauigkeit und Relevanz der generierten Inhalte, sowie senkung der Kosten.
- Skalierung mit "AWS SQS", sodass .mp4 events in eine Queue geschickt werden und beliebig viele Instanzen erstellt werden
- Absicherung aller Secrets nach Best Practices
- Anbindung eines echten Frontends, anstatt der Verwendung eines öffentlichen S3 Buckets.
