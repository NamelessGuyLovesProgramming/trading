# Trading Dashboard - Benutzerhandbuch

## Übersicht

Das Trading Dashboard ist eine interaktive Anwendung zur Darstellung von Handelsdaten in Charts, zur Programmierung von Handelsstrategien und zum Backtesting dieser Strategien mit historischen Daten. Die Anwendung ermöglicht es Ihnen, verschiedene Handelsstrategien zu testen, ihre Performance zu analysieren und die Ergebnisse in Form von Metriken und Visualisierungen zu betrachten.

## Funktionen

- **Datenabfrage**: Abrufen von Handelsdaten für verschiedene Aktien und Zeiträume
- **Technische Indikatoren**: Berechnung und Visualisierung von technischen Indikatoren wie SMA, EMA, RSI, MACD und Bollinger Bands
- **Handelsstrategien**: Implementierung und Testen verschiedener Handelsstrategien
- **Backtesting**: Rückwärtstesten von Strategien mit historischen Daten
- **Performance-Metriken**: Berechnung von Metriken wie Gewinnrate, Gesamtrendite und Drawdown
- **Stop-Loss und Take-Profit**: Automatische Berechnung von Stop-Loss- und Take-Profit-Levels
- **Interaktives Dashboard**: Benutzerfreundliche Oberfläche zur Visualisierung und Analyse

## Installation und Start

### Voraussetzungen

- Python 3.8 oder höher
- Pip (Python-Paketmanager)

### Installation

1. Klonen Sie das Repository oder entpacken Sie die Anwendung in ein Verzeichnis Ihrer Wahl
2. Öffnen Sie ein Terminal und navigieren Sie zum Projektverzeichnis
3. Installieren Sie die erforderlichen Abhängigkeiten:

```bash
pip install -r requirements.txt
```

### Start der Anwendung

Führen Sie im Projektverzeichnis den folgenden Befehl aus:

```bash
python run.py
```

Die Anwendung wird gestartet und ist unter http://localhost:8050 in Ihrem Webbrowser verfügbar.

## Verwendung des Dashboards

### Dateneinstellungen

Im oberen Bereich des Dashboards können Sie die Dateneinstellungen konfigurieren:

1. **Symbol**: Geben Sie das Aktiensymbol ein (z.B. "AAPL" für Apple, "MSFT" für Microsoft)
2. **Zeitintervall**: Wählen Sie das Zeitintervall für die Daten (z.B. 1 Tag, 1 Stunde)
3. **Zeitraum**: Wählen Sie den Zeitraum für die Daten (z.B. 1 Jahr, 6 Monate)
4. Klicken Sie auf "Daten abrufen", um die Daten zu laden

### Preischart

Nach dem Abrufen der Daten wird ein Preischart angezeigt, der folgende Elemente enthält:

- Candlestick-Chart mit Preisinformationen
- Gleitende Durchschnitte (SMA 20, SMA 50, SMA 200)
- Bollinger Bands (wenn verfügbar)
- Volumen-Chart
- RSI-Indikator

### Strategie-Einstellungen

Im Bereich "Strategie-Einstellungen" können Sie eine Handelsstrategie auswählen und konfigurieren:

1. **Strategie**: Wählen Sie eine der verfügbaren Strategien aus:
   - MA Crossover (Moving Average Crossover)
   - RSI Strategy (Relative Strength Index)
   - MACD Strategy (Moving Average Convergence Divergence)
   - Bollinger Bands Strategy
2. **Parameter**: Konfigurieren Sie die Parameter der Strategie
3. **Startkapital**: Legen Sie das Startkapital für den Backtest fest (Standard: 50.000 €)
4. **Kommission**: Legen Sie die Kommission pro Trade fest (in Prozent)
5. Klicken Sie auf "Backtest durchführen", um die Strategie zu testen

### Backtest-Ergebnisse

Nach dem Durchführen eines Backtests werden die Ergebnisse in folgenden Bereichen angezeigt:

1. **Performance-Metriken**:
   - Gesamtrendite
   - Gewinnrate
   - Anzahl der Trades
   - Maximaler Drawdown
2. **Equity-Kurve**: Visualisierung der Kapitalentwicklung während des Backtests
3. **Trades**: Tabelle mit allen durchgeführten Trades, einschließlich Ein- und Ausstiegsdaten, Preisen und Gewinnen/Verlusten

## Handelsstrategien

### Moving Average Crossover

Diese Strategie generiert Kaufsignale, wenn der kurzfristige gleitende Durchschnitt den langfristigen gleitenden Durchschnitt von unten nach oben kreuzt, und Verkaufssignale, wenn der kurzfristige gleitende Durchschnitt den langfristigen gleitenden Durchschnitt von oben nach unten kreuzt.

Parameter:
- **Short Window**: Fenstergröße für den kurzfristigen gleitenden Durchschnitt
- **Long Window**: Fenstergröße für den langfristigen gleitenden Durchschnitt

### RSI Strategy

Diese Strategie generiert Kaufsignale, wenn der RSI-Indikator unter die Überverkauft-Schwelle fällt und dann wieder darüber steigt, und Verkaufssignale, wenn der RSI-Indikator über die Überkauft-Schwelle steigt und dann wieder darunter fällt.

Parameter:
- **RSI Window**: Fenstergröße für den RSI-Indikator
- Die Überkauft-Schwelle ist standardmäßig auf 70 gesetzt
- Die Überverkauft-Schwelle ist standardmäßig auf 30 gesetzt

### MACD Strategy

Diese Strategie generiert Kaufsignale, wenn die MACD-Linie die Signallinie von unten nach oben kreuzt, und Verkaufssignale, wenn die MACD-Linie die Signallinie von oben nach unten kreuzt.

Parameter:
- **Fast**: Fenstergröße für den schnellen EMA
- **Slow**: Fenstergröße für den langsamen EMA
- **Signal**: Fenstergröße für die Signallinie

### Bollinger Bands Strategy

Diese Strategie generiert Kaufsignale, wenn der Preis die untere Bollinger-Band berührt oder unterschreitet und dann wieder darüber steigt, und Verkaufssignale, wenn der Preis die obere Bollinger-Band berührt oder überschreitet und dann wieder darunter fällt.

Parameter:
- **Window**: Fenstergröße für den gleitenden Durchschnitt
- **Num Std**: Anzahl der Standardabweichungen für die Bollinger Bands

## Stop-Loss und Take-Profit

Alle Strategien berechnen automatisch Stop-Loss- und Take-Profit-Levels für jeden Trade. Diese werden wie folgt berechnet:

- **Stop-Loss**: Basierend auf dem ATR (Average True Range) oder dem letzten Swing Low
- **Take-Profit**: Basierend auf dem Risk-Reward-Ratio (standardmäßig 2:1)

Diese Levels werden im Backtest berücksichtigt und können in der Praxis für manuelle Trades verwendet werden.

## Tipps für die Verwendung

- Testen Sie verschiedene Strategien mit unterschiedlichen Parametern, um die beste Performance zu erzielen
- Verwenden Sie längere Zeiträume für aussagekräftigere Backtesting-Ergebnisse
- Achten Sie auf die Gewinnrate und den maximalen Drawdown, um die Risiken einer Strategie zu bewerten
- Optimieren Sie die Parameter einer Strategie, um die Performance zu verbessern
- Berücksichtigen Sie die Kommissionen, um realistische Ergebnisse zu erhalten

## Fehlerbehebung

- **Keine Daten verfügbar**: Überprüfen Sie das Aktiensymbol und stellen Sie sicher, dass es korrekt ist
- **Keine Signale generiert**: Passen Sie die Parameter der Strategie an oder wählen Sie einen längeren Zeitraum
- **Langsame Performance**: Reduzieren Sie den Zeitraum oder wählen Sie ein größeres Zeitintervall

## Erweiterung der Anwendung

Die Anwendung ist modular aufgebaut und kann leicht erweitert werden. Sie können:

- Neue Strategien hinzufügen, indem Sie die Strategy-Basisklasse erweitern
- Weitere technische Indikatoren implementieren
- Das Dashboard um zusätzliche Visualisierungen erweitern

Weitere Informationen finden Sie in der Entwicklerdokumentation.
