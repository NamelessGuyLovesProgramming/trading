import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import StringIO

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template, ThemeChangerAIO
from dash_iconify import DashIconify
import dash_mantine_components as dmc

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from backtesting.backtest_engine import BacktestEngine
from data.data_fetcher import DataFetcher
from data.data_processor import DataProcessor
from strategy.example_strategies import MovingAverageCrossover, RSIStrategy, MACDStrategy, BollingerBandsStrategy

# Neuen Import für NQ Futures hinzufügen
from data.nq_integration import NQDataFetcher

# Initialisiere die Dash-App mit einem dunklen Theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)

# Zuerst die Verzeichnisse definieren
data_dir = os.path.join(parent_dir, 'data')
cache_dir = os.path.join(data_dir, 'cache')
output_dir = os.path.join(parent_dir, 'output')
os.makedirs(output_dir, exist_ok=True)

# Dann die Fetcher initialisieren
data_fetcher = DataFetcher(cache_dir=cache_dir)
data_processor = DataProcessor()
backtest_engine = BacktestEngine(initial_capital=50000.0)

# Und jetzt den NQDataFetcher hinzufügen
nq_data_fetcher = NQDataFetcher(cache_dir=cache_dir)

# Lade das dunkle Template für Plotly-Figuren
load_figure_template("darkly")


# Callback für Daten abrufen
@app.callback(
    [
        Output("stock-data-store", "data"),
        Output("data-info", "children"),
        Output("symbol-display", "children"),
    ],
    Input("fetch-data-button", "n_clicks"),
    [
        State("symbol-input", "value"),
        State("active-timeframe-store", "data"),
        State("range-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def fetch_stock_data(n_clicks, symbol, interval, range_val):
    if not n_clicks or not symbol:
        return None, "", ""

    try:
        if symbol.upper() in ["NQ", "NQ=F", "NASDAQ", "NASDAQ100", "NQH24"]:
            print("\n----- NQ FETCH DEBUG -----")
            print(f"Abrufen von NQ-Daten mit interval={interval}, range_val={range_val}")

            # Verwende den spezialisierten NQ Futures Data Fetcher
            df = nq_data_fetcher.get_nq_futures_data(interval=interval, range_val=range_val)

            print("\n----- NQ DATA FORMAT -----")
            print("Datentyp:", type(df))
            print("Spalten:", df.columns.tolist())
            print("Index-Typ:", type(df.index))
            print("Index hat Zeitzone:",
                  df.index.tzinfo is not None if hasattr(df.index, 'tzinfo') else 'Kein DatetimeIndex')
            print("DataFrame Info:")
            print(df.info())
            print("Erste 3 Zeilen:")
            print(df.head(3))

            # Wichtig: Zeitzonenhandling
            if hasattr(df.index, 'tzinfo') and df.index.tzinfo is not None:
                print("Zeitzone wird vom Index entfernt")
                df.index = df.index.tz_localize(None)
            elif not isinstance(df.index, pd.DatetimeIndex):
                print("Index wird in DatetimeIndex konvertiert (ohne Zeitzone)")
                # Setze utc=True, um mit Zeitzonen-aware Daten umzugehen
                df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)

            symbol_display = "NASDAQ 100 Futures (NQ)"
        else:
            # Standardmäßig verwende den normalen Data Fetcher
            df = data_fetcher.get_stock_data(symbol, interval, range_val)
            symbol_display = f"{symbol.upper()}"

        if df is None or df.empty:
            print("Keine Daten gefunden!")
            return None, html.Div([
                DashIconify(icon="mdi:alert", width=18, color=colors['danger'], className="me-2"),
                "Keine Daten verfügbar"
            ]), ""

        # Debug vor dem Hinzufügen von Indikatoren
        print("\n----- VOR INDIKATOREN -----")
        print("Spalten:", df.columns.tolist())
        print("Erste Zeile:", df.head(1))
        print("-------------------------\n")

        # Indikatoren hinzufügen
        df = data_processor.add_indicators(df)

        # Debug nach dem Hinzufügen von Indikatoren
        print("\n----- NACH INDIKATOREN -----")
        print("Spalten nach add_indicators:", df.columns.tolist())
        print("Erste Zeile nach add_indicators:", df.head(1))
        print("-------------------------\n")

        # Auf NaN-Werte prüfen
        nan_count = df.isnull().sum().sum()
        if nan_count > 0:
            print(f"WARNUNG: {nan_count} NaN-Werte gefunden, werden gefüllt...")
            df.ffill(inplace=True)

        # Daten in JSON konvertieren
        # Daten in JSON konvertieren
        # Stelle sicher, dass der Index keine Zeitzone mehr hat
        if df.index.tzinfo is not None:
            df.index = df.index.tz_localize(None)

        # Debug-Ausgabe vor der JSON-Konvertierung
        print("Index vor JSON-Konvertierung:", df.index[:3])
        print("Spalten vor JSON-Konvertierung:", df.columns.tolist())

        # Kopie erstellen, um das Original nicht zu verändern
        df_copy = df.copy()

        # Sicherstellen, dass wir eine Date-Spalte haben
        if isinstance(df_copy.index, pd.DatetimeIndex):
            # Reset index, damit der Index als Spalte mitgegeben wird
            df_reset = df_copy.reset_index()
            print("Spalten nach reset_index:", df_reset.columns.tolist())

            # Sicherstellen dass 'Date' als datetime erhalten bleibt
            df_reset['Datetime'] = pd.to_datetime(df_reset['Datetime'])
        else:
            df_reset = df_copy.reset_index()
            print("Spalten nach reset_index:", df_reset.columns.tolist())

        # Daten in JSON konvertieren
        df_json = df_reset.to_json(date_format='iso', orient='records')

        # Info-Text erstellen (weiterhin mit original df)
        start_date = df.index.min().strftime('%d.%m.%Y')
        end_date = df.index.max().strftime('%d.%m.%Y')
        num_days = (df.index.max() - df.index.min()).days

        info_text = html.Div([
            DashIconify(icon="mdi:check-circle", width=18, color=colors['success'], className="me-2"),
            f"{num_days} Tage ({start_date} - {end_date})"
        ])

        return df_json, info_text, symbol_display

    except Exception as e:
        print(f"FEHLER beim Datenabruf: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, html.Div([
            DashIconify(icon="mdi:alert", width=18, color=colors['danger'], className="me-2"),
            f"Fehler: {str(e)}"
        ]), ""


# Callback für Timeframe-Buttons
@app.callback(
    [Output("active-timeframe-store", "data")] +
    [Output(f"tf-{tf}", "className") for tf in ["1min", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mon"]],
    [Input(f"tf-{tf}", "n_clicks") for tf in ["1min", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mon"]],
    [State("active-timeframe-store", "data")],
    prevent_initial_call=True,
)
def update_timeframe(click_1m, click_5m, click_15m, click_30m, click_1h, click_4h, click_1d, click_1w, click_1mo,
                     active_tf):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Standardmäßig 1d aktiv
        return ["1d"] + ["timeframe-button" if tf != "1d" else "timeframe-button active" for tf in
                         ["1min", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mon"]]

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    new_tf = button_id.split("-")[1]

    # Hier müssen Sie auch die Zeitrahmen anpassen wenn "1min" oder "1mon" verwendet wird
    if new_tf == "1min":
        new_tf = "1m"  # Für YahooFinance API
    elif new_tf == "1mon":
        new_tf = "1mo"  # Für YahooFinance API

    # Klassen für alle Buttons aktualisieren
    button_classes = []
    for tf in ["1min", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mon"]:
        if f"tf-{tf}" == button_id:
            button_classes.append("timeframe-button active")
        else:
            button_classes.append("timeframe-button")

    return [new_tf] + button_classes


# Callback für Chart-Typ-Buttons
@app.callback(
    [
        Output("line-chart-button", "color"),
        Output("line-chart-button", "outline"),
        Output("candlestick-chart-button", "color"),
        Output("candlestick-chart-button", "outline"),
        Output("ohlc-chart-button", "color"),
        Output("ohlc-chart-button", "outline"),
    ],
    [
        Input("line-chart-button", "n_clicks"),
        Input("candlestick-chart-button", "n_clicks"),
        Input("ohlc-chart-button", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def update_chart_type_buttons(line_clicks, candlestick_clicks, ohlc_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "secondary", True, "primary", False, "secondary", True

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "line-chart-button":
        return "primary", False, "secondary", True, "secondary", True
    elif button_id == "candlestick-chart-button":
        return "secondary", True, "primary", False, "secondary", True
    elif button_id == "ohlc-chart-button":
        return "secondary", True, "secondary", True, "primary", False

    return "secondary", True, "primary", False, "secondary", True


# Callback für Indikator-Buttons
@app.callback(
    [
        Output("sma-button", "outline"),
        Output("bb-button", "outline"),
        Output("rsi-button", "outline"),
        Output("macd-button", "outline"),
    ],
    [
        Input("sma-button", "n_clicks"),
        Input("bb-button", "n_clicks"),
        Input("rsi-button", "n_clicks"),
        Input("macd-button", "n_clicks"),
    ],
    [
        State("sma-button", "outline"),
        State("bb-button", "outline"),
        State("rsi-button", "outline"),
        State("macd-button", "outline"),
    ],
    prevent_initial_call=True,
)
def toggle_indicator_buttons(sma_clicks, bb_clicks, rsi_clicks, macd_clicks,
                             sma_outline, bb_outline, rsi_outline, macd_outline):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, False, False, False

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "sma-button":
        return not sma_outline, bb_outline, rsi_outline, macd_outline
    elif button_id == "bb-button":
        return sma_outline, not bb_outline, rsi_outline, macd_outline
    elif button_id == "rsi-button":
        return sma_outline, bb_outline, not rsi_outline, macd_outline
    elif button_id == "macd-button":
        return sma_outline, bb_outline, rsi_outline, not macd_outline

    return sma_outline, bb_outline, rsi_outline, macd_outline


# Callback für Preischart
@app.callback(
    Output("price-chart", "figure"),
    [
        Input("stock-data-store", "data"),
        Input("line-chart-button", "color"),
        Input("candlestick-chart-button", "color"),
        Input("ohlc-chart-button", "color"),
        Input("sma-button", "outline"),
        Input("bb-button", "outline"),
        Input("rsi-button", "outline"),
        Input("macd-button", "outline"),
        Input("backtest-results-store", "data"),
    ],
    prevent_initial_call=True,
)
def update_price_chart(data_json, line_color, candlestick_color, ohlc_color,
                       sma_outline, bb_outline, rsi_outline, macd_outline,
                       backtest_results_json):
    if not data_json:
        # Leeres Chart mit Hinweis zurückgeben
        fig = go.Figure()
        fig.update_layout(
            **chart_style['layout'],
            title="",
            annotations=[
                dict(
                    text="Keine Daten verfügbar. Bitte Daten abrufen.",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=16, color=colors['text']),
                )
            ]
        )
        return fig

    # Debug
    print("\n----- CHART UPDATE DEBUG -----")
    print("Chart-Typen:",
          f"Line: {line_color == 'primary'}",
          f"Candlestick: {candlestick_color == 'primary'}",
          f"OHLC: {ohlc_color == 'primary'}")
    print(f"Datentyp von data_json: {type(data_json)}")

    # Daten aus JSON laden
    try:
        # Robust Daten laden je nach Format
        if isinstance(data_json, list):
            # Wenn data_json bereits eine Liste ist
            df = pd.DataFrame(data_json)
            print("Liste direkt in DataFrame konvertiert")
        elif isinstance(data_json, dict):
            # Wenn data_json bereits ein Dictionary ist
            if 'data' in data_json and 'columns' in data_json:
                # Split-Format Dictionary
                df = pd.DataFrame(data_json['data'], columns=data_json['columns'])
            elif 'index' in data_json:
                # DataFrame-Format Dictionary
                df = pd.DataFrame(data_json)
            else:
                # Anderes Dictionary-Format
                df = pd.DataFrame([data_json])
            print("Dictionary direkt in DataFrame konvertiert")
        else:
            # Annahme: Es ist ein JSON-String - versuche verschiedene Methoden
            try:
                # Versuche zuerst mit 'split' Orientation
                df = pd.read_json(StringIO(data_json), orient='split')
                print("JSON mit orient='split' erfolgreich geladen")
            except:
                try:
                    # Versuche mit Records-Orientation
                    df = pd.read_json(StringIO(data_json), orient='records')
                    print("JSON mit orient='records' erfolgreich geladen")
                except:
                    try:
                        # Letzter Versuch: parse als JSON und erstelle manuell
                        import json
                        data_obj = json.loads(data_json)
                        if isinstance(data_obj, list):
                            df = pd.DataFrame(data_obj)
                        else:
                            df = pd.DataFrame([data_obj])
                        print("JSON manuell geparst und in DataFrame konvertiert")
                    except Exception as e:
                        print(f"Alle Versuche, JSON zu parsen, sind fehlgeschlagen: {e}")
                        raise

        # Debug-Ausgaben nach dem erfolgreichen Laden
        print("DataFrame Info:")
        print(f"Spalten: {df.columns.tolist()}")
        print(f"Datentypen: {df.dtypes}")
        print(f"Anzahl Zeilen: {len(df)}")

        # Datumsspalte verarbeiten
        if 'Datetime' in df.columns:
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            df.set_index('Datetime', inplace=True)
            print("Datetime als Index gesetzt")
        elif 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            print("Date als Index gesetzt")
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            print("date als Index gesetzt")
        elif 'index' in df.columns and pd.api.types.is_datetime64_any_dtype(df['index']):
            df.set_index('index', inplace=True)
            print("index als Index gesetzt")
        elif not isinstance(df.index, pd.DatetimeIndex):
            print("Kein Datum-Index gefunden, versuche Index zu konvertieren")
            try:
                # Versuche, den bestehenden Index zu konvertieren
                df.index = pd.to_datetime(df.index)
            except:
                print("Konnte Index nicht zu Datetime konvertieren")

        # Stelle sicher, dass OHLC-Spalten vorhanden sind
        ohlc_cols = ['Open', 'High', 'Low', 'Close']
        for col in ohlc_cols:
            if col not in df.columns:
                # Versuche, Spalten mit Kleinbuchstaben zu finden
                lower_col = col.lower()
                if lower_col in df.columns:
                    df[col] = df[lower_col]
                    print(f"Spalte {lower_col} zu {col} kopiert")
                else:
                    print(f"WARNUNG: Erforderliche Spalte {col} fehlt")

        # Stelle sicher, dass alle OHLC-Spalten numerisch sind
        for col in ohlc_cols:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                print(f"Konvertiere {col} zu numerisch")
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Auf NaN-Werte prüfen und behandeln
        nan_count = df.isnull().sum().sum()
        if nan_count > 0:
            print(f"WARNUNG: {nan_count} NaN-Werte gefunden, werden gefüllt...")
            df = df.ffill().bfill()
    except Exception as e:
        print(f"FEHLER beim Laden der Daten: {str(e)}")
        import traceback
        traceback.print_exc()

        # Leeren Chart zurückgeben
        fig = go.Figure()
        fig.update_layout(
            **chart_style['layout'],
            title="",
            annotations=[
                dict(
                    text=f"Fehler beim Laden der Daten: {str(e)}",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=16, color=colors['danger']),
                )
            ]
        )
        return fig

    # Bestimme Chart-Typ
    chart_type = "candlestick"  # Standard
    if line_color == "primary":
        chart_type = "line"
    elif ohlc_color == "primary":
        chart_type = "ohlc"

    print(f"Ausgewählter Chart-Typ: {chart_type}")

    # Bestimme aktive Indikatoren
    show_sma = not sma_outline
    show_bb = not bb_outline
    show_rsi = not rsi_outline
    show_macd = not macd_outline

    # Bestimme Anzahl der Subplots
    n_rows = 2  # Preis + Volumen als Standard
    if show_rsi:
        n_rows += 1
    if show_macd:
        n_rows += 1

    # Erstelle Subplots
    row_heights = [0.6]  # Preis-Chart
    row_heights.extend([0.1] * (n_rows - 1))  # Weitere Subplots

    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=["", "Volumen"] + (["RSI"] if show_rsi else []) + (["MACD"] if show_macd else [])
    )

    # Debug vor dem Erstellen des Candlestick/Line/OHLC Charts
    print(f"\nChartdaten für {chart_type} werden vorbereitet...")
    if chart_type in ["candlestick", "ohlc"]:
        print("OHLC-Daten für Chart:")
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            print(df[['Open', 'High', 'Low', 'Close']].head(3))
        else:
            missing = [col for col in ['Open', 'High', 'Low', 'Close'] if col not in df.columns]
            print(f"FEHLER: Folgende OHLC-Spalten fehlen: {missing}")

    # Füge Preisdaten hinzu
    try:
        if chart_type == "line":
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    mode='lines',
                    name='Schlusskurs',
                    line=dict(color=colors['primary'], width=2),
                    hovertemplate='%{x}<br>Schlusskurs: %{y:.2f}<extra></extra>',
                ),
                row=1, col=1
            )
            print("Line-Chart erfolgreich erstellt")
        elif chart_type == "candlestick":
            print("Erstelle Candlestick-Chart...")
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='OHLC',
                    increasing=chart_style['candlestick']['increasing'],
                    decreasing=chart_style['candlestick']['decreasing'],
                    hoverinfo='all',
                    text=[
                        f"Eröffnung: {row['Open']:.2f}<br>Hoch: {row['High']:.2f}<br>Tief: {row['Low']:.2f}<br>Schluss: {row['Close']:.2f}"
                        for _, row in df.iterrows()]
                ),
                row=1, col=1
            )
            print("Candlestick-Chart erfolgreich erstellt")
        elif chart_type == "ohlc":
            fig.add_trace(
                go.Ohlc(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='OHLC',
                    increasing=chart_style['candlestick']['increasing'],
                    decreasing=chart_style['candlestick']['decreasing'],
                    hovertemplate='%{x}<br>Eröffnung: %{open:.2f}<br>Hoch: %{high:.2f}<br>Tief: %{low:.2f}<br>Schluss: %{close:.2f}<extra></extra>',
                ),
                row=1, col=1
            )
            print("OHLC-Chart erfolgreich erstellt")

        # Füge Volumen hinzu
        if 'Volume' in df.columns:
            colors_volume = []
            for i in range(len(df)):
                if i > 0:
                    if df['Close'].iloc[i] > df['Close'].iloc[i - 1]:
                        colors_volume.append(colors['up'])
                    else:
                        colors_volume.append(colors['down'])
                else:
                    colors_volume.append(colors['up'])

            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='Volumen',
                    marker=dict(
                        color=colors_volume
                    ),
                    hovertemplate='%{x}<br>Volumen: %{y}<extra></extra>',
                ),
                row=2, col=1
            )
            print("Volumen-Chart erfolgreich erstellt")

        # Füge technische Indikatoren hinzu
        current_row = 3

        # Füge SMA hinzu
        if show_sma:
            for window, color in [(20, colors['success']), (50, colors['primary']), (200, colors['secondary'])]:
                col_name = f'SMA_{window}'
                if col_name in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df[col_name],
                            mode='lines',
                            name=f'SMA {window}',
                            line=dict(color=color, width=1),
                            hovertemplate='%{x}<br>SMA {window}: %{y:.2f}<extra></extra>',
                        ),
                        row=1, col=1
                    )
                    print(f"SMA {window} erfolgreich hinzugefügt")

        # Füge Bollinger Bands hinzu
        if show_bb and all(col in df.columns for col in ['BB_Middle', 'BB_Upper', 'BB_Lower']):
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BB_Middle'],
                    mode='lines',
                    name='BB Mitte',
                    line=dict(color=colors['info'], width=1),
                    hovertemplate='%{x}<br>BB Mitte: %{y:.2f}<extra></extra>',
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BB_Upper'],
                    mode='lines',
                    name='BB Oben',
                    line=dict(color=colors['info'], width=1, dash='dash'),
                    hovertemplate='%{x}<br>BB Oben: %{y:.2f}<extra></extra>',
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BB_Lower'],
                    mode='lines',
                    name='BB Unten',
                    line=dict(color=colors['info'], width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor=f'rgba(0, 188, 212, 0.1)',
                    hovertemplate='%{x}<br>BB Unten: %{y:.2f}<extra></extra>',
                ),
                row=1, col=1
            )
            print("Bollinger Bands erfolgreich hinzugefügt")

        # Füge RSI hinzu
        if show_rsi and 'RSI_14' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['RSI_14'],
                    mode='lines',
                    name='RSI 14',
                    line=dict(color=colors['warning'], width=1),
                    hovertemplate='%{x}<br>RSI: %{y:.2f}<extra></extra>',
                ),
                row=current_row, col=1
            )

            fig.add_hline(
                y=70,
                line=dict(color=colors['danger'], width=1, dash='dash'),
                row=current_row,
                col=1
            )

            fig.add_hline(
                y=30,
                line=dict(color=colors['success'], width=1, dash='dash'),
                row=current_row,
                col=1
            )

            current_row += 1
            print("RSI erfolgreich hinzugefügt")

        # Füge MACD hinzu
        if show_macd and all(col in df.columns for col in ['MACD', 'MACD_Signal', 'MACD_Hist']):
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MACD'],
                    mode='lines',
                    name='MACD',
                    line=dict(color=colors['danger'], width=1),
                    hovertemplate='%{x}<br>MACD: %{y:.2f}<extra></extra>',
                ),
                row=current_row, col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MACD_Signal'],
                    mode='lines',
                    name='Signal',
                    line=dict(color=colors['secondary'], width=1),
                    hovertemplate='%{x}<br>Signal: %{y:.2f}<extra></extra>',
                ),
                row=current_row, col=1
            )

            colors_hist = []
            for val in df['MACD_Hist']:
                if val > 0:
                    colors_hist.append(colors['up'])
                else:
                    colors_hist.append(colors['down'])

            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['MACD_Hist'],
                    name='Histogramm',
                    marker=dict(
                        color=colors_hist
                    ),
                    hovertemplate='%{x}<br>Diff: %{y:.2f}<extra></extra>',
                ),
                row=current_row, col=1
            )

            fig.add_hline(
                y=0,
                line=dict(color=colors['grid'], width=1),
                row=current_row,
                col=1
            )

            print("MACD erfolgreich hinzugefügt")

        # Füge Backtest-Ergebnisse hinzu, wenn vorhanden
        if backtest_results_json:
            try:
                # Deserialisiere Ergebnisse
                if isinstance(backtest_results_json, str):
                    backtest_results = pd.read_json(StringIO(backtest_results_json), orient='split')
                else:
                    backtest_results = pd.DataFrame(backtest_results_json)

                # Handel mit backtest_results-Daten
                if isinstance(backtest_results, dict) and 'trades' in backtest_results:
                    trades = backtest_results['trades']

                    # Markiere Einstiegspunkte
                    entries_x = [trade['entry_date'] for trade in trades if 'entry_date' in trade]
                    entries_y = [trade['entry_price'] for trade in trades if 'entry_price' in trade]

                    if entries_x and entries_y:
                        fig.add_trace(
                            go.Scatter(
                                x=entries_x,
                                y=entries_y,
                                mode='markers',
                                name='Einstieg',
                                marker=dict(
                                    symbol='triangle-up',
                                    size=10,
                                    color=colors['success'],
                                    line=dict(
                                        width=1,
                                        color=colors['text']
                                    )
                                ),
                                hovertemplate='%{x}<br>Einstieg: %{y:.2f}<extra></extra>',
                            ),
                            row=1, col=1
                        )

                    # Markiere Ausstiegspunkte
                    exits_x = [trade['exit_date'] for trade in trades if 'exit_date' in trade]
                    exits_y = [trade['exit_price'] for trade in trades if 'exit_price' in trade]

                    if exits_x and exits_y:
                        fig.add_trace(
                            go.Scatter(
                                x=exits_x,
                                y=exits_y,
                                mode='markers',
                                name='Ausstieg',
                                marker=dict(
                                    symbol='triangle-down',
                                    size=10,
                                    color=colors['danger'],
                                    line=dict(
                                        width=1,
                                        color=colors['text']
                                    )
                                ),
                                hovertemplate='%{x}<br>Ausstieg: %{y:.2f}<extra></extra>',
                            ),
                            row=1, col=1
                        )

                print("Backtest-Ergebnisse erfolgreich hinzugefügt")
            except Exception as e:
                print(f"Fehler beim Hinzufügen von Backtest-Ergebnissen: {e}")

        layout_params = chart_style['layout'].copy()  # Kopiere das Style-Dictionary
        if 'legend' in layout_params:
            # Entferne das legend dictionary aus den layout_params
            layout_params.pop('legend')

        fig.update_layout(
            **layout_params,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=10)
            )
        )
        fig.update_yaxes(title_text="Preis", row=1, col=1)
        fig.update_yaxes(title_text="Volumen", row=2, col=1)

        if show_rsi:
            fig.update_yaxes(title_text="RSI", row=3, col=1)

        if show_macd:
            fig.update_yaxes(title_text="MACD", row=n_rows, col=1)

        fig.update_xaxes(rangebreaks=[
            dict(bounds=["sat", "mon"]),  # Wochenenden ausblenden
        ])

        print("Layout aktualisiert")
    except Exception as e:
        print(f"FEHLER beim Erstellen des Charts: {str(e)}")
        import traceback
        traceback.print_exc()

        # Leeren Chart zurückgeben
        fig = go.Figure()
        fig.update_layout(
            **chart_style['layout'],
            title="",
            annotations=[
                dict(
                    text=f"Fehler beim Erstellen des Charts: {str(e)}",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=16, color=colors['danger']),
                )
            ]
        )

    return fig

    # Debug
    print("\n----- CHART UPDATE DEBUG -----")
    print("Chart-Typen:",
          f"Line: {line_color == 'primary'}",
          f"Candlestick: {candlestick_color == 'primary'}",
          f"OHLC: {ohlc_color == 'primary'}")

    # Daten aus JSON laden
    # Daten aus JSON laden
    try:
        if isinstance(data_json, list):
            # Wenn data_json eine Liste ist, verarbeite sie entsprechend
            df = pd.DataFrame(data_json)
        else:
            # Normaler Fall
            df = pd.read_json(StringIO(data_json), orient='split')

        print("Daten aus JSON erfolgreich geladen")

        # Prüfe, ob 'index' als Spalte existiert, bevor wir versuchen, den Index zu setzen
        if 'index' in df.columns:
            df.set_index('index', inplace=True)
        else:
            print("Spalte 'index' nicht gefunden, Index bleibt unverändert")
        print("DataFrame Info:")
        print(f"Spalten: {df.columns.tolist()}")
        print(f"Index-Typ: {type(df.index)}")
        print(f"Datentypen: {df.dtypes}")
        print(f"Anzahl Zeilen: {len(df)}")
        print("Erste 3 Zeilen:")
        print(df.head(3))

        # Überprüfen, ob OHLC-Spalten vorhanden sind
        ohlc_cols = ['Open', 'High', 'Low', 'Close']
        for col in ohlc_cols:
            print(f"Spalte {col} vorhanden: {col in df.columns}")
            if col in df.columns:
                print(f"Datentyp von {col}: {df[col].dtype}")
                print(f"NaN-Werte in {col}: {df[col].isna().sum()}")

        # Prüfen und ggf. korrigieren der OHLC-Daten
        if not all(col in df.columns for col in ohlc_cols):
            # Möglicherweise sind die Spalten falsch benannt - versuchen, sie zu finden
            column_mapping = {}
            lower_cols = [col.lower() for col in df.columns]
            for required_col in ohlc_cols:
                required_lower = required_col.lower()
                if required_lower in lower_cols:
                    actual_col = df.columns[lower_cols.index(required_lower)]
                    column_mapping[actual_col] = required_col

            if column_mapping:
                print(f"Spaltennamen werden angepasst: {column_mapping}")
                df.rename(columns=column_mapping, inplace=True)

        # Stelle sicher, dass der Index ein DatetimeIndex ist
        if not isinstance(df.index, pd.DatetimeIndex):
            print("Index ist kein DatetimeIndex, wird konvertiert")
            df.index = pd.to_datetime(df.index)

        # Stelle sicher, dass OHLC-Spalten numerisch sind
        for col in ohlc_cols:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                print(f"Spalte {col} nicht numerisch, wird konvertiert")
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Auf NaN-Werte prüfen und behandeln
        nan_count = df.isnull().sum().sum()
        if nan_count > 0:
            print(f"WARNUNG: {nan_count} NaN-Werte gefunden, werden gefüllt...")
            df = df.ffill().bfill()
    except Exception as e:
        print(f"FEHLER beim Laden der JSON-Daten: {str(e)}")
        import traceback
        traceback.print_exc()

        # Leeren Chart zurückgeben
        fig = go.Figure()
        fig.update_layout(
            **chart_style['layout'],
            title="",
            annotations=[
                dict(
                    text=f"Fehler beim Laden der Daten: {str(e)}",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=16, color=colors['danger']),
                )
            ]
        )
        return fig

    # Bestimme Chart-Typ
    chart_type = "candlestick"  # Standard
    if line_color == "primary":
        chart_type = "line"
    elif ohlc_color == "primary":
        chart_type = "ohlc"

    print(f"Ausgewählter Chart-Typ: {chart_type}")

    # Bestimme aktive Indikatoren
    show_sma = not sma_outline
    show_bb = not bb_outline
    show_rsi = not rsi_outline
    show_macd = not macd_outline

    # Bestimme Anzahl der Subplots
    n_rows = 2  # Preis + Volumen als Standard
    if show_rsi:
        n_rows += 1
    if show_macd:
        n_rows += 1

    # Erstelle Subplots
    row_heights = [0.6]  # Preis-Chart
    row_heights.extend([0.1] * (n_rows - 1))  # Weitere Subplots

    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=["", "Volumen"] + (["RSI"] if show_rsi else []) + (["MACD"] if show_macd else [])
    )

    # Debug vor dem Erstellen des Candlestick/Line/OHLC Charts
    print(f"\nChartdaten für {chart_type} werden vorbereitet...")
    if chart_type in ["candlestick", "ohlc"]:
        print("OHLC-Daten für Chart:")
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            print(df[['Open', 'High', 'Low', 'Close']].head(3))
        else:
            missing = [col for col in ['Open', 'High', 'Low', 'Close'] if col not in df.columns]
            print(f"FEHLER: Folgende OHLC-Spalten fehlen: {missing}")

    # Füge Preisdaten hinzu
    try:
        if chart_type == "line":
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    mode='lines',
                    name='Schlusskurs',
                    line=dict(color=colors['primary'], width=2),
                    hovertemplate='%{x}<br>Schlusskurs: %{y:.2f}<extra></extra>',
                ),
                row=1, col=1
            )
            print("Line-Chart erfolgreich erstellt")
        elif chart_type == "candlestick":
            print("Erstelle Candlestick-Chart...")
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='OHLC',
                    increasing=chart_style['candlestick']['increasing'],
                    decreasing=chart_style['candlestick']['decreasing'],
                    # hovertemplate entfernen oder durch hoverinfo und text ersetzen
                    hoverinfo='all',
                    text=[f"Eröffnung: {row['Open']:.2f}<br>Hoch: {row['High']:.2f}<br>Tief: {row['Low']:.2f}<br>Schluss: {row['Close']:.2f}"
                         for _, row in df.iterrows()]
                ),
                row=1, col=1
            )
            print("Candlestick-Chart erfolgreich erstellt")
        elif chart_type == "ohlc":
            fig.add_trace(
                go.Ohlc(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='OHLC',
                    increasing=chart_style['candlestick']['increasing'],
                    decreasing=chart_style['candlestick']['decreasing'],
                    hovertemplate='%{x}<br>Eröffnung: %{open:.2f}<br>Hoch: %{high:.2f}<br>Tief: %{low:.2f}<br>Schluss: %{close:.2f}<extra></extra>',
                ),
                row=1, col=1
            )
            print("OHLC-Chart erfolgreich erstellt")
    except Exception as e:
        print(f"FEHLER beim Erstellen des Hauptcharts: {str(e)}")
        import traceback
        traceback.print_exc()

    # Rest des Callbacks für Volumen und Indikatoren
    # ... [vorhandener Code] ...

# Definiere Strategien
strategies = {
    'MA Crossover': MovingAverageCrossover(),
    'RSI Strategy': RSIStrategy(),
    'MACD Strategy': MACDStrategy(),
    'Bollinger Bands Strategy': BollingerBandsStrategy()
}

# Definiere Farbpalette für das Dashboard
colors = {
    'background': '#131722',  # TradingView Hintergrundfarbe
    'card_background': '#1E222D',  # TradingView Kartenfarbe
    'text': '#D1D4DC',  # TradingView Textfarbe
    'primary': '#2962FF',  # TradingView Blau
    'secondary': '#787B86',  # TradingView Grau
    'success': '#26A69A',  # TradingView Grün
    'danger': '#EF5350',  # TradingView Rot
    'warning': '#FF9800',  # TradingView Orange
    'info': '#00BCD4',  # TradingView Cyan
    'up': '#26A69A',  # TradingView Grün für steigende Kurse
    'down': '#EF5350',  # TradingView Rot für fallende Kurse
    'grid': '#2A2E39',  # TradingView Gitterfarbe
    'axis': '#787B86',  # TradingView Achsenfarbe
    'selection': 'rgba(41, 98, 255, 0.3)',  # TradingView Auswahlfarbe
}

# Definiere Chart-Stile
chart_style = {
    'candlestick': {
        'increasing': {'line': {'color': colors['up']}, 'fillcolor': colors['up']},
        'decreasing': {'line': {'color': colors['down']}, 'fillcolor': colors['down']},
    },
    'volume': {
        'increasing': {'fillcolor': colors['up'], 'line': {'color': colors['up']}},
        'decreasing': {'fillcolor': colors['down'], 'line': {'color': colors['down']}},
    },
    'layout': {
        'paper_bgcolor': colors['background'],
        'plot_bgcolor': colors['background'],
        'font': {'color': colors['text'], 'family': 'Trebuchet MS, sans-serif'},
        'xaxis': {
            'gridcolor': colors['grid'],
            'linecolor': colors['grid'],
            'tickfont': {'color': colors['text']},
            'title': {'text': '', 'font': {'color': colors['text']}},
            'rangeslider': {'visible': False},
            'showgrid': True,
            'gridwidth': 0.5,
        },
        'yaxis': {
            'gridcolor': colors['grid'],
            'linecolor': colors['grid'],
            'tickfont': {'color': colors['text']},
            'title': {'text': '', 'font': {'color': colors['text']}},
            'showgrid': True,
            'gridwidth': 0.5,
            'side': 'right',  # TradingView hat Y-Achse auf der rechten Seite
        },
        'legend': {'font': {'color': colors['text']}},
        'margin': {'l': 10, 'r': 50, 't': 10, 'b': 10},
        'dragmode': 'zoom',
        'selectdirection': 'h',
        'modebar': {
            'bgcolor': 'rgba(0,0,0,0)',
            'color': colors['text'],
            'activecolor': colors['primary']
        },
    }
}

# Definiere benutzerdefinierte CSS-Stile
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Trading Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            /* TradingView-ähnliche Stile */
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif;
                background-color: ''' + colors['background'] + ''';
                color: ''' + colors['text'] + ''';
                margin: 0;
                padding: 0;
            }

            /* Scrollbar-Stile */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            ::-webkit-scrollbar-track {
                background: ''' + colors['background'] + ''';
            }
            ::-webkit-scrollbar-thumb {
                background: ''' + colors['grid'] + ''';
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: ''' + colors['secondary'] + ''';
            }

            /* Karten-Stile */
            .card {
                border-radius: 4px;
                border: 1px solid ''' + colors['grid'] + ''';
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }
            .card:hover {
                box-shadow: 0 6px 10px rgba(0, 0, 0, 0.15);
            }
            .card-header {
                border-bottom: 1px solid ''' + colors['grid'] + ''';
                padding: 12px 16px;
                font-weight: 600;
            }

            /* Button-Stile */
            .btn {
                border-radius: 4px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            }
            .btn:active {
                transform: translateY(0);
                box-shadow: none;
            }

            /* Input-Stile */
            .form-control, .form-select {
                background-color: ''' + colors['card_background'] + ''';
                border: 1px solid ''' + colors['grid'] + ''';
                color: ''' + colors['text'] + ''';
                border-radius: 4px;
            }
            .form-control:focus, .form-select:focus {
                border-color: ''' + colors['primary'] + ''';
                box-shadow: 0 0 0 0.25rem rgba(41, 98, 255, 0.25);
            }

            /* Tabellen-Stile */
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table {
                border-collapse: separate;
                border-spacing: 0;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
                background-color: ''' + colors['card_background'] + ''';
                color: ''' + colors['text'] + ''';
                font-weight: 600;
                padding: 12px 16px;
                border-bottom: 2px solid ''' + colors['grid'] + ''';
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
                padding: 10px 16px;
                border-bottom: 1px solid ''' + colors['grid'] + ''';
            }

            /* Tooltip-Stile */
            .tooltip {
                background-color: ''' + colors['card_background'] + ''';
                color: ''' + colors['text'] + ''';
                border: 1px solid ''' + colors['grid'] + ''';
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }

            /* Chart-Container-Stile */
            .chart-container {
                position: relative;
                border-radius: 4px;
                overflow: hidden;
                border: 1px solid ''' + colors['grid'] + ''';
            }

            /* Toolbar-Stile */
            .chart-toolbar {
                position: absolute;
                top: 10px;
                left: 10px;
                z-index: 1000;
                display: flex;
                gap: 5px;
                background-color: rgba(30, 34, 45, 0.7);
                padding: 5px;
                border-radius: 4px;
                backdrop-filter: blur(5px);
            }

            /* Timeframe-Buttons */
            .timeframe-buttons {
                display: flex;
                gap: 2px;
                margin-bottom: 10px;
            }
            .timeframe-button {
                padding: 2px 8px;
                font-size: 12px;
                background-color: ''' + colors['card_background'] + ''';
                color: ''' + colors['text'] + ''';
                border: 1px solid ''' + colors['grid'] + ''';
                border-radius: 3px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .timeframe-button:hover {
                background-color: ''' + colors['grid'] + ''';
            }
            .timeframe-button.active {
                background-color: ''' + colors['primary'] + ''';
                color: white;
                border-color: ''' + colors['primary'] + ''';
            }

            /* Indikator-Badge */
            .indicator-badge {
                display: inline-block;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: 500;
                border-radius: 3px;
                margin-right: 5px;
                background-color: ''' + colors['grid'] + ''';
                color: ''' + colors['text'] + ''';
            }

            /* Animationen */
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .fade-in {
                animation: fadeIn 0.3s ease-in-out;
            }

            /* Responsive Anpassungen */
            @media (max-width: 992px) {
                .sidebar {
                    margin-bottom: 20px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Definiere Header mit Logo und Titel
header = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="mdi:chart-line", width=40, color=colors['primary'])),
                        dbc.Col(dbc.NavbarBrand("Trading Dashboard Pro", className="ms-2 fs-2 fw-bold")),
                    ],
                    align="center",
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink(
                            [DashIconify(icon="mdi:view-dashboard", width=18, className="me-2"), "Dashboard"], href="#",
                            active=True)),
                        dbc.NavItem(
                            dbc.NavLink([DashIconify(icon="mdi:strategy", width=18, className="me-2"), "Strategien"],
                                        href="#")),
                        dbc.NavItem(dbc.NavLink(
                            [DashIconify(icon="mdi:chart-timeline-variant", width=18, className="me-2"), "Backtesting"],
                            href="#")),
                        dbc.NavItem(
                            dbc.NavLink([DashIconify(icon="mdi:cog", width=18, className="me-2"), "Einstellungen"],
                                        href="#")),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    color=colors['background'],
    dark=True,
    className="mb-4 border-bottom border-secondary",
    style={"borderColor": colors['grid'] + " !important"},
)

# Definiere Timeframe-Buttons
timeframe_buttons = html.Div(
    [
        html.Button("1m", id="tf-1min", className="timeframe-button"),  # Änderung von "tf-1m" zu "tf-1min"
        html.Button("5m", id="tf-5m", className="timeframe-button"),
        html.Button("15m", id="tf-15m", className="timeframe-button"),
        html.Button("30m", id="tf-30m", className="timeframe-button"),
        html.Button("1h", id="tf-1h", className="timeframe-button"),
        html.Button("4h", id="tf-4h", className="timeframe-button"),
        html.Button("1D", id="tf-1d", className="timeframe-button active"),
        html.Button("1W", id="tf-1w", className="timeframe-button"),
        html.Button("1M", id="tf-1mon", className="timeframe-button"),  # Änderung von "tf-1m" zu "tf-1mon"
    ],
    className="timeframe-buttons",
)

# Definiere Sidebar für Dateneinstellungen
sidebar = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Dateneinstellungen", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:database-cog", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Symbol", html_for="symbol-input", className="mb-1"),
                        dbc.InputGroup([
                            dbc.InputGroupText(DashIconify(icon="mdi:finance", width=18)),
                            dbc.Input(
                                id="symbol-input",
                                type="text",
                                value="AAPL",
                                placeholder="z.B. AAPL, MSFT",
                                className="border-start-0",
                            ),
                        ], className="mb-3"),
                    ]),
                ]),

                dbc.Label("Zeitrahmen", className="mb-1"),
                timeframe_buttons,

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Zeitraum", html_for="range-dropdown", className="mb-1"),
                        dbc.InputGroup([
                            dbc.InputGroupText(DashIconify(icon="mdi:calendar-range", width=18)),
                            dbc.Select(
                                id="range-dropdown",
                                options=[
                                    {"label": "1 Tag", "value": "1d"},
                                    {"label": "5 Tage", "value": "5d"},
                                    {"label": "1 Monat", "value": "1mo"},
                                    {"label": "3 Monate", "value": "3mo"},
                                    {"label": "6 Monate", "value": "6mo"},
                                    {"label": "1 Jahr", "value": "1y"},
                                    {"label": "2 Jahre", "value": "2y"},
                                    {"label": "5 Jahre", "value": "5y"},
                                    {"label": "Max", "value": "max"},
                                ],
                                value="1y",
                                className="border-start-0",
                            ),
                        ], className="mb-3"),
                    ]),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [DashIconify(icon="mdi:refresh", width=18, className="me-2"), "Daten abrufen"],
                            id="fetch-data-button",
                            color="primary",
                            className="w-100 mb-3",
                        ),
                    ]),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Spinner(
                            html.Div(id="data-info", className="text-center text-muted small"),
                            color="primary",
                            size="sm",
                            spinner_style={"width": "1rem", "height": "1rem"}
                        ),
                    ]),
                ]),
            ]),
        ]),
    ],
    className="mb-4 shadow sidebar",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Hauptbereich für Charts
chart_card = dbc.Card(
    [
        dbc.CardHeader([
            html.Div([
                html.H4("Preischart", className="card-title d-inline mb-0 me-2"),
                html.Span(id="symbol-display", className="text-primary fw-bold"),
            ], className="d-inline-block"),

            html.Div([
                dbc.ButtonGroup([
                    dbc.Button(
                        DashIconify(icon="mdi:chart-line", width=18),
                        id="line-chart-button",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="me-1",
                    ),
                    dbc.Button(
                        DashIconify(icon="mdi:chart-candlestick", width=18),
                        id="candlestick-chart-button",
                        color="primary",
                        outline=False,
                        size="sm",
                        className="me-1",
                    ),
                    dbc.Button(
                        DashIconify(icon="mdi:chart-bar", width=18),
                        id="ohlc-chart-button",
                        color="secondary",
                        outline=True,
                        size="sm",
                    ),
                ], className="me-2"),

                dbc.ButtonGroup([
                    dbc.Button(
                        "SMA",
                        id="sma-button",
                        color="success",
                        outline=False,
                        size="sm",
                        className="me-1",
                    ),
                    dbc.Button(
                        "BB",
                        id="bb-button",
                        color="info",
                        outline=False,
                        size="sm",
                        className="me-1",
                    ),
                    dbc.Button(
                        "RSI",
                        id="rsi-button",
                        color="warning",
                        outline=False,
                        size="sm",
                        className="me-1",
                    ),
                    dbc.Button(
                        "MACD",
                        id="macd-button",
                        color="danger",
                        outline=False,
                        size="sm",
                    ),
                ]),

                dbc.Button(
                    DashIconify(icon="mdi:dots-vertical", width=18),
                    id="chart-options-button",
                    color="secondary",
                    outline=True,
                    size="sm",
                    className="ms-2",
                ),
            ], className="float-end d-flex")
        ]),

        dbc.CardBody([
            html.Div([
                dcc.Loading(
                    dcc.Graph(
                        id="price-chart",
                        config={
                            'modeBarButtonsToAdd': [
                                'drawline',
                                'drawopenpath',
                                'drawcircle',
                                'drawrect',
                                'eraseshape'
                            ],
                            'scrollZoom': True,
                            'displaylogo': False,
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': 'trading_chart',
                                'height': 800,
                                'width': 1200,
                                'scale': 2
                            }
                        },
                        style={"height": "65vh"},
                        className="p-0",
                    ),
                    type="circle",
                    color=colors['primary'],
                ),

                # Chart-Toolbar (TradingView-ähnlich)
                html.Div([
                    dbc.Button(
                        DashIconify(icon="mdi:magnify-plus-outline", width=16),
                        id="zoom-in-button",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="p-1",
                    ),
                    dbc.Button(
                        DashIconify(icon="mdi:magnify-minus-outline", width=16),
                        id="zoom-out-button",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="p-1",
                    ),
                    dbc.Button(
                        DashIconify(icon="mdi:arrow-expand-all", width=16),
                        id="zoom-reset-button",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="p-1",
                    ),
                    dbc.Button(
                        DashIconify(icon="mdi:crosshairs", width=16),
                        id="crosshair-button",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="p-1",
                    ),
                    dbc.Button(
                        DashIconify(icon="mdi:chart-timeline-variant", width=16),
                        id="indicators-button",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="p-1",
                    ),
                ], className="chart-toolbar"),

                # Aktive Indikatoren-Anzeige
                html.Div([
                    html.Span("SMA(20)", className="indicator-badge", style={"backgroundColor": colors['success']}),
                    html.Span("BB(20,2)", className="indicator-badge", style={"backgroundColor": colors['info']}),
                    html.Span("RSI(14)", className="indicator-badge", style={"backgroundColor": colors['warning']}),
                    html.Span("MACD(12,26,9)", className="indicator-badge",
                              style={"backgroundColor": colors['danger']}),
                ], className="mt-2 ms-2"),
            ], className="chart-container"),
        ], className="p-2"),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Bereich für Strategie-Einstellungen
strategy_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Strategie-Einstellungen", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:strategy", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Strategie", html_for="strategy-dropdown", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:chart-timeline-variant", width=18)),
                        dbc.Select(
                            id="strategy-dropdown",
                            options=[
                                {"label": "Moving Average Crossover", "value": "MA Crossover"},
                                {"label": "RSI Strategy", "value": "RSI Strategy"},
                                {"label": "MACD Strategy", "value": "MACD Strategy"},
                                {"label": "Bollinger Bands Strategy", "value": "Bollinger Bands Strategy"},
                            ],
                            value="MA Crossover",
                            className="border-start-0",
                        ),
                    ]),
                ], width=12, className="mb-3"),
            ]),

            html.Div(id="strategy-params", className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Startkapital (€)", html_for="capital-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:currency-eur", width=18)),
                        dbc.Input(
                            id="capital-input",
                            type="number",
                            value=50000,
                            min=1000,
                            step=1000,
                            className="border-start-0",
                        ),
                    ]),
                ], width=6),
                dbc.Col([
                    dbc.Label("Kommission (%)", html_for="commission-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:percent", width=18)),
                        dbc.Input(
                            id="commission-input",
                            type="number",
                            value=0.1,
                            min=0,
                            max=5,
                            step=0.01,
                            className="border-start-0",
                        ),
                    ]),
                ], width=6),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [DashIconify(icon="mdi:play", width=18, className="me-2"), "Backtest durchführen"],
                        id="run-backtest-button",
                        color="success",
                        className="w-100",
                    ),
                ]),
            ]),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Bereich für Backtest-Ergebnisse
results_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Backtest-Ergebnisse", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:finance", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Gesamtrendite", className="card-subtitle text-center text-muted mb-1"),
                            html.H3(id="total-return", className="card-text text-center mb-0"),
                        ]),
                    ], className="mb-3 border-0 shadow-sm", style={"backgroundColor": colors['card_background']}),
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Gewinnrate", className="card-subtitle text-center text-muted mb-1"),
                            html.H3(id="win-rate", className="card-text text-center mb-0"),
                        ]),
                    ], className="mb-3 border-0 shadow-sm", style={"backgroundColor": colors['card_background']}),
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Anzahl Trades", className="card-subtitle text-center text-muted mb-1"),
                            html.H3(id="num-trades", className="card-text text-center mb-0"),
                        ]),
                    ], className="mb-3 border-0 shadow-sm", style={"backgroundColor": colors['card_background']}),
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Max. Drawdown", className="card-subtitle text-center text-muted mb-1"),
                            html.H3(id="max-drawdown", className="card-text text-center mb-0"),
                        ]),
                    ], className="mb-3 border-0 shadow-sm", style={"backgroundColor": colors['card_background']}),
                ], width=3),
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(
                            id="equity-chart",
                            config={
                                'displayModeBar': False,
                                'scrollZoom': True,
                            },
                            style={"height": "30vh"},
                        ),
                        type="circle",
                        color=colors['primary'],
                    ),
                ]),
            ]),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Bereich für Trades-Tabelle
trades_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Trades", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:table", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dash_table.DataTable(
                id="trades-table",
                columns=[
                    {"name": "Nr.", "id": "index"},
                    {"name": "Einstieg", "id": "entry_date"},
                    {"name": "Einstiegspreis", "id": "entry_price"},
                    {"name": "Ausstieg", "id": "exit_date"},
                    {"name": "Ausstiegspreis", "id": "exit_price"},
                    {"name": "Typ", "id": "type"},
                    {"name": "Anteile", "id": "shares"},
                    {"name": "Gewinn/Verlust", "id": "pnl"},
                    {"name": "Rendite", "id": "return"},
                    {"name": "Stop-Loss", "id": "stop_loss"},
                    {"name": "Take-Profit", "id": "take_profit"},
                ],
                style_header={
                    'backgroundColor': colors['card_background'],
                    'color': colors['text'],
                    'fontWeight': 'bold',
                    'border': f'1px solid {colors["grid"]}',
                    'textAlign': 'center',
                },
                style_cell={
                    'backgroundColor': colors['background'],
                    'color': colors['text'],
                    'border': f'1px solid {colors["grid"]}',
                    'padding': '8px',
                    'textAlign': 'center',
                    'fontFamily': '-apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif',
                },
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{pnl} > 0'},
                        'color': colors['up'],
                    },
                    {
                        'if': {'filter_query': '{pnl} < 0'},
                        'color': colors['down'],
                    },
                    {
                        'if': {'state': 'selected'},
                        'backgroundColor': colors['selection'],
                        'border': f'1px solid {colors["primary"]}',
                    },
                ],
                page_size=5,
                style_table={'overflowX': 'auto'},
                sort_action='native',
                filter_action='native',
                row_selectable='single',
            ),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere das Layout der App
app.layout = html.Div(
    [
        # Versteckte Div-Elemente für Datenspeicherung
        dcc.Store(id="stock-data-store"),
        dcc.Store(id="backtest-results-store"),
        dcc.Store(id="active-timeframe-store", data="1d"),  # Standardmäßig 1 Tag

        # Header
        header,

        # Hauptinhalt
        dbc.Container(
            [
                dbc.Row(
                    [
                        # Linke Spalte mit Sidebar
                        dbc.Col(
                            [
                                sidebar,
                                strategy_card,
                            ],
                            lg=3,
                            md=12,
                            className="sidebar",
                        ),

                        # Rechte Spalte mit Charts und Ergebnissen
                        dbc.Col(
                            [
                                chart_card,
                                results_card,
                                trades_card,
                            ],
                            lg=9,
                            md=12,
                        ),
                    ]
                ),
            ],
            fluid=True,
            className="mb-4",
        ),

        # Footer
        dbc.Container(
            dbc.Row(
                dbc.Col(
                    html.P(
                        [
                            "© 2025 Trading Dashboard Pro | ",
                            html.A("Dokumentation", href="#", className="text-light"),
                            " | ",
                            html.A("Hilfe", href="#", className="text-light"),
                        ],
                        className="text-center text-muted small py-3 mb-0",
                    ),
                    width=12,
                ),
            ),
            fluid=True,
            className="border-top",
            style={"borderColor": colors['grid'] + " !important", "backgroundColor": colors['background']},
        ),
    ],
    style={"backgroundColor": colors['background'], "minHeight": "100vh", "color": colors['text']},
    className="fade-in",
)