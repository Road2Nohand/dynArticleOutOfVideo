# Sports Video to Article to Thumbnail

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
