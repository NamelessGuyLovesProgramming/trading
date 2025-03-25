# Fehleranalyse und Verbesserungen für das Trading Dashboard

## 1. Identifizierte Fehler und Probleme

- **Symbol-Spalte**: Die Symbol-Spalte ist redundant, da Assets jetzt über Dropdowns ausgewählt werden
- **Fehlende NQ-Assets**: NASDAQ 100 Futures (NQ) fehlen in der Asset-Liste
- **Begrenzte Zeiteinheiten**: Nur 1h, 1d und 1w sind implementiert, weitere Zeiteinheiten fehlen
- **Y-Achsen-Label**: Die Y-Achse zeigt keine dynamische Beschriftung (z.B. "Preis in USD")
- **Code-Redundanzen**: Mehrere Stellen mit ähnlicher Logik in verschiedenen Dateien
- **Fehlerbehandlung**: Unzureichende Fehlerbehandlung bei Datenabfragen und UI-Interaktionen

## 2. Lösungsansätze

### 2.1 Fehlerbehebung
- Implementierung von Fehlerbehandlung für Datenlücken und API-Timeouts
- Hinzufügen von Fallback-Lösungen mit Benutzerhinweisen

### 2.2 Symbol-Spalte entfernen
- Entfernen der Symbol-Spalte aus allen Tabellen und Formularen
- Anpassung der Daten-Pipelines zur Vermeidung von Abhängigkeiten

### 2.3 NQ-Asset und Zeiteinheiten
- Integration von NQ in die Asset-Liste
- Hinzufügen aller Zeiteinheiten als Toggle-Buttons

### 2.4 Y-Achsen-Label
- Implementierung dynamischer Labels basierend auf Asset-Typ
- Synchronisierung der Skalierung beim Scrollen/Zoom

### 2.5 Code-Refactoring
- Zentralisierung wiederkehrender Logik
- Modularisierung der Projektstruktur
- Implementierung von Abstraktion für bessere Erweiterbarkeit

## 3. Priorisierung
1. Fehlerbehebung und NQ/Zeiteinheiten (kritisch für Funktionalität)
2. Symbol-Spalte entfernen und Y-Achsen-Label korrigieren (UI-Verbesserungen)
3. Code-Refactoring (langfristige Wartbarkeit)
