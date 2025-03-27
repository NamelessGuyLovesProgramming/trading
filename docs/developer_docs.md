# Trading Dashboard - Entwicklerdokumentation

## Projektübersicht

Das Trading Dashboard ist eine modulare Anwendung zur Darstellung von Handelsdaten, zur Implementierung von Handelsstrategien und zum Backtesting dieser Strategien. Die Anwendung ist in Python geschrieben und verwendet verschiedene Bibliotheken für Datenverarbeitung, Visualisierung und Webinterface.

## Projektstruktur

```
trading_dashboard/
├── data/                  # Datenabfrage und -verarbeitung
│   ├── data_fetcher.py    # Klasse zum Abrufen von Handelsdaten
│   ├── data_processor.py  # Klasse zur Verarbeitung und Analyse von Daten
│   └── cache/             # Cache-Verzeichnis für Handelsdaten
├── strategy/              # Handelsstrategien
│   ├── strategy_base.py   # Basisklasse für Strategien
│   └── example_strategies.py # Implementierte Beispielstrategien
├── backtesting/           # Backtesting-Engine
│   └── backtest_engine.py # Engine zum Testen von Strategien
├── dashboard/             # Interaktives Dashboard
│   └── app.py             # Dash-Anwendung
├── tests/                 # Testskripte
│   └── test_data_module.py # Tests für das Datenmodul
├── docs/                  # Dokumentation
│   ├── user_manual.md     # Benutzerhandbuch
│   └── developer_docs.md  # Entwicklerdokumentation
├── output/                # Ausgabeverzeichnis für Berichte und Grafiken
├── run.py                 # Hauptskript zum Starten der Anwendung
└── test_integration.py    # Integrationstests
```

## Technologiestack

- **Python 3.10+**: Programmiersprache
- **pandas**: Datenverarbeitung und -analyse
- **numpy**: Numerische Berechnungen
- **matplotlib/plotly**: Datenvisualisierung
- **dash**: Interaktives Web-Dashboard
- **yfinance**: Abrufen von Finanzdaten (Fallback)
- **pytest**: Testen

## Modulbeschreibungen

### Datenmodul

#### DataFetcher (data_fetcher.py)

Die `DataFetcher`-Klasse ist verantwortlich für das Abrufen von Handelsdaten. Sie unterstützt zwei Datenquellen:

1. YahooFinance API über den Manus API-Client (wenn verfügbar)
2. yfinance-Bibliothek als Fallback

Hauptmethoden:
- `get_stock_data(symbol, interval, range, use_cache, force_refresh)`: Ruft Daten für ein bestimmtes Symbol ab
- `get_multiple_stocks(symbols, interval, range, use_cache)`: Ruft Daten für mehrere Symbole ab
- `get_technical_indicators(symbol, interval, range)`: Ruft technische Indikatoren ab

Die Klasse implementiert auch einen Cache-Mechanismus, um wiederholte API-Anfragen zu vermeiden.

#### DataProcessor (data_processor.py)

Die `DataProcessor`-Klasse ist verantwortlich für die Verarbeitung und Analyse von Handelsdaten. Sie berechnet verschiedene technische Indikatoren.

Hauptmethoden:
- `calculate_sma(data, window)`: Berechnet den Simple Moving Average
- `calculate_ema(data, window)`: Berechnet den Exponential Moving Average
- `calculate_rsi(data, window)`: Berechnet den Relative Strength Index
- `calculate_macd(data, fast, slow, signal)`: Berechnet den MACD
- `calculate_bollinger_bands(data, window, num_std)`: Berechnet die Bollinger Bands
- `calculate_atr(data, window)`: Berechnet den Average True Range
- `calculate_support_resistance(data, window)`: Berechnet Support- und Widerstandsniveaus
- `calculate_stop_loss_take_profit(data, atr_multiplier, risk_reward_ratio)`: Berechnet Stop-Loss und Take-Profit
- `add_indicators(data)`: Fügt alle gängigen Indikatoren zu einem DataFrame hinzu

### Strategiemodul

#### Strategy (strategy_base.py)

Die `Strategy`-Klasse ist eine abstrakte Basisklasse für alle Handelsstrategien. Sie definiert die Schnittstelle, die alle Strategien implementieren müssen.

Hauptmethoden:
- `generate_signals(data)`: Generiert Handelssignale basierend auf den Daten (abstrakt)
- `calculate_stop_loss(data, index)`: Berechnet den Stop-Loss für einen Trade
- `calculate_take_profit(data, index)`: Berechnet den Take-Profit für einen Trade
- `set_parameters(**kwargs)`: Setzt die Parameter der Strategie
- `get_parameters()`: Gibt die Parameter der Strategie zurück
- `optimize(data, param_grid, metric, backtest_engine)`: Optimiert die Parameter der Strategie

#### Beispielstrategien (example_strategies.py)

Das Modul implementiert verschiedene Handelsstrategien, die von der `Strategy`-Basisklasse erben:

1. `MovingAverageCrossover`: Strategie basierend auf dem Kreuzen von gleitenden Durchschnitten
2. `RSIStrategy`: Strategie basierend auf dem Relative Strength Index
3. `MACDStrategy`: Strategie basierend auf dem Moving Average Convergence Divergence
4. `BollingerBandsStrategy`: Strategie basierend auf Bollinger Bands

Jede Strategie implementiert die `generate_signals`-Methode und kann die `calculate_stop_loss`- und `calculate_take_profit`-Methoden überschreiben.

### Backtesting-Modul

#### BacktestEngine (backtest_engine.py)

Die `BacktestEngine`-Klasse ist verantwortlich für das Backtesting von Handelsstrategien mit historischen Daten.

Hauptmethoden:
- `run(data, strategy, verbose)`: Führt einen Backtest mit einer bestimmten Strategie durch
- `plot_results(results, output_dir, filename)`: Visualisiert die Ergebnisse des Backtests
- `generate_report(results, output_dir, filename)`: Generiert einen HTML-Bericht für den Backtest

Die Engine simuliert Trades basierend auf den Signalen der Strategie und berechnet verschiedene Performance-Metriken wie Gesamtrendite, Gewinnrate, maximaler Drawdown und Sharpe Ratio.

### Dashboard-Modul

#### App (app.py)

Die `app.py`-Datei implementiert das interaktive Dashboard mit Dash. Es besteht aus verschiedenen Komponenten:

1. Dateneinstellungen: Eingabefelder für Symbol, Zeitintervall und Zeitraum
2. Preischart: Visualisierung der Preisdaten und technischen Indikatoren
3. Strategie-Einstellungen: Auswahl und Konfiguration der Handelsstrategie
4. Backtest-Ergebnisse: Anzeige der Performance-Metriken und Equity-Kurve
5. Trades: Tabelle mit allen durchgeführten Trades

Das Dashboard verwendet Callbacks, um auf Benutzerinteraktionen zu reagieren und die Anzeige dynamisch zu aktualisieren.

## Erweiterung der Anwendung

### Hinzufügen einer neuen Strategie

Um eine neue Handelsstrategie hinzuzufügen, erstellen Sie eine neue Klasse, die von der `Strategy`-Basisklasse erbt:

```python
from strategy.strategy_base import Strategy

class MyNewStrategy(Strategy):
    def __init__(self, param1=10, param2=20, name="My New Strategy"):
        super().__init__(name=name)
        self.parameters = {
            'param1': param1,
            'param2': param2
        }
    
    def generate_signals(self, data):
        # Implementieren Sie Ihre Signalgenerierungslogik hier
        df = data.copy()
        df['Signal'] = 0
        
        # Beispiel: Generiere Kaufsignal, wenn Bedingung erfüllt ist
        for i in range(1, len(df)):
            if some_condition:
                df.loc[df.index[i], 'Signal'] = 1  # Kaufsignal
            elif other_condition:
                df.loc[df.index[i], 'Signal'] = -1  # Verkaufssignal
        
        return df
    
    def calculate_stop_loss(self, data, index):
        # Implementieren Sie Ihre Stop-Loss-Logik hier
        current_price = data['Close'].iloc[index]
        return current_price * 0.95  # 5% unter dem aktuellen Preis
    
    def calculate_take_profit(self, data, index):
        # Implementieren Sie Ihre Take-Profit-Logik hier
        current_price = data['Close'].iloc[index]
        return current_price * 1.10  # 10% über dem aktuellen Preis
```

Fügen Sie dann die neue Strategie zum Dashboard hinzu, indem Sie sie in der `strategies`-Dictionary in `app.py` registrieren:

```python
strategies = {
    'MA Crossover': MovingAverageCrossover(),
    'RSI Strategy': RSIStrategy(),
    'MACD Strategy': MACDStrategy(),
    'Bollinger Bands Strategy': BollingerBandsStrategy(),
    'My New Strategy': MyNewStrategy()  # Neue Strategie hinzufügen
}
```

### Hinzufügen eines neuen technischen Indikators

Um einen neuen technischen Indikator hinzuzufügen, erweitern Sie die `DataProcessor`-Klasse in `data_processor.py`:

```python
@staticmethod
def calculate_my_indicator(data, param1, param2):
    """
    Berechnet meinen neuen Indikator
    
    Args:
        data (pandas.DataFrame): DataFrame mit Preisdaten
        param1: Parameter 1
        param2: Parameter 2
        
    Returns:
        pandas.Series: Serie mit Indikatorwerten
    """
    # Implementieren Sie Ihre Indikatorberechnung hier
    result = some_calculation(data, param1, param2)
    return result
```

Fügen Sie dann den neuen Indikator zur `add_indicators`-Methode hinzu:

```python
def add_indicators(data):
    # Bestehender Code...
    
    # Füge neuen Indikator hinzu
    df['My_Indicator'] = DataProcessor.calculate_my_indicator(df, param1, param2)
    
    return df
```

### Anpassen des Dashboards

Um das Dashboard anzupassen, können Sie die Layout-Definition in `app.py` ändern. Beispielsweise können Sie eine neue Karte für einen zusätzlichen Chart hinzufügen:

```python
dbc.Row([
    dbc.Col([
        dbc.Card([
            dbc.CardHeader("Mein neuer Chart"),
            dbc.CardBody([
                dcc.Graph(id="my-new-chart", style={"height": "300px"})
            ])
        ], className="mb-4")
    ], width=12)
])
```

Und dann einen neuen Callback hinzufügen, um den Chart zu aktualisieren:

```python
@app.callback(
    Output("my-new-chart", "figure"),
    Input("stock-data-store", "data"),
    prevent_initial_call=True
)
def update_my_new_chart(data_json):
    # Implementieren Sie Ihre Chart-Logik hier
    # ...
    return fig
```

## Bekannte Einschränkungen und zukünftige Verbesserungen

1. **Pandas-Warnungen**: Die Strategien verwenden `iloc` zum Setzen von Werten, was zu SettingWithCopyWarning führt. Dies könnte durch Verwendung von `loc` behoben werden.
2. **Datenquellen**: Derzeit werden nur Yahoo Finance-Daten unterstützt. Die Unterstützung für weitere Datenquellen könnte hinzugefügt werden.
3. **Optimierung**: Die Parameteroptimierung könnte durch Parallelisierung beschleunigt werden.
4. **Risikomanagement**: Erweiterte Risikomanagement-Funktionen könnten implementiert werden.
5. **Echtzeit-Daten**: Die Unterstützung für Echtzeit-Daten könnte hinzugefügt werden.
6. **Benutzerauthentifizierung**: Für den Mehrbenutzerbetrieb könnte eine Benutzerauthentifizierung implementiert werden.

## Testen

Die Anwendung enthält verschiedene Tests:

1. **Modultests**: Tests für einzelne Module (z.B. `test_data_module.py`)
2. **Integrationstests**: End-to-End-Tests für das gesamte System (`test_integration.py`)

Um die Tests auszuführen:

```bash
# Modultests
python -m pytest tests/

# Integrationstests
python test_integration.py
```

## Deployment

Die Anwendung kann lokal ausgeführt werden, indem `run.py` ausgeführt wird. Für ein Produktions-Deployment könnte die Anwendung mit Gunicorn oder einem ähnlichen WSGI-Server bereitgestellt werden:

```bash
gunicorn -w 4 -b 0.0.0.0:8050 'run:app.server'
```

Alternativ könnte die Anwendung in einem Docker-Container bereitgestellt werden.

## Abhängigkeiten

Die Anwendung verwendet die folgenden Hauptabhängigkeiten:

- pandas
- numpy
- matplotlib
- plotly
- dash
- dash-bootstrap-components
- yfinance
- pytest

Eine vollständige Liste der Abhängigkeiten finden Sie in der `requirements.txt`-Datei.
