"""
Trading Dashboard App mit verbesserten Funktionen
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
import os

# Importiere Chart-Utilities
from dashboard.chart_utils import (
    generate_mock_data,
    create_interactive_chart,
    get_available_assets,
    get_available_timeframes
)

# Importiere Fehlerbehandlung
from dashboard.error_handler import ErrorHandler

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard_errors.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trading_dashboard")

# Definiere Farben für das Dashboard
colors = {
    'background': '#121212',
    'card_background': '#1E1E1E',
    'text': '#E0E0E0',
    'primary': '#3B82F6',  # Blau als Akzentfarbe
    'secondary': '#6B7280',
    'success': '#10B981',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'grid': 'rgba(255, 255, 255, 0.1)',
}

# Initialisiere die Dash-App
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    suppress_callback_exceptions=True,
)

app.title = "Trading Dashboard"

# Definiere Header
header = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="mdi:chart-line-variant", width=40, color=colors['primary'])),
                        dbc.Col(dbc.NavbarBrand("Trading Dashboard", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Dashboard", href="#", active=True)),
                        dbc.NavItem(dbc.NavLink("Strategien", href="#")),
                        dbc.NavItem(dbc.NavLink("Backtesting", href="#")),
                        dbc.NavItem(dbc.NavLink("Einstellungen", href="#")),
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
    color="dark",
    dark=True,
    className="mb-4",
    style={"borderBottom": f"1px solid {colors['grid']}"},
)

# Hole verfügbare Assets
available_assets = get_available_assets()

# Erstelle anklickbare Asset-Buttons
def create_asset_buttons():
    asset_groups = {
        "Aktien": [asset for asset in available_assets if asset["value"] in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]],
        "Krypto": [asset for asset in available_assets if "BTC" in asset["value"] or "ETH" in asset["value"]],
        "Forex": [asset for asset in available_assets if "USD" in asset["value"] or "EUR" in asset["value"] or "GBP" in asset["value"] or "JPY" in asset["value"]],
        "Futures": [asset for asset in available_assets if "NQ" in asset["value"]]
    }
    
    asset_buttons = []
    
    for group_name, assets in asset_groups.items():
        asset_buttons.append(html.H6(group_name, className="mt-2 mb-1"))
        group_buttons = []
        
        for asset in assets:
            group_buttons.append(
                dbc.Button(
                    asset["label"],
                    id={"type": "asset-button", "index": asset["value"]},
                    color="secondary",
                    outline=True,
                    size="sm",
                    className="me-1 mb-1"
                )
            )
        
        asset_buttons.append(html.Div(group_buttons, className="mb-2"))
    
    return asset_buttons

# Definiere Sidebar
sidebar = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Datenquelle", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:database", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            html.Div([
                dbc.Label("Symbol", html_for="symbol-input"),
                dbc.Input(
                    id="symbol-input",
                    type="text",
                    value="AAPL",
                    placeholder="z.B. AAPL, MSFT, GOOGL",
                    className="mb-3",
                ),
                dbc.Label("Verfügbare Assets", className="mt-2"),
                html.Div(
                    create_asset_buttons(),
                    className="mb-3 asset-buttons-container",
                    style={"maxHeight": "200px", "overflowY": "auto"}
                ),
                dbc.Label("Zeitraum", html_for="date-range"),
                dcc.DatePickerRange(
                    id="date-range",
                    start_date=datetime.now() - timedelta(days=365),
                    end_date=datetime.now(),
                    display_format="DD.MM.YYYY",
                    className="mb-3 w-100",
                ),
                dbc.Label("Datenquelle", html_for="data-source"),
                dbc.Select(
                    id="data-source",
                    options=[
                        {"label": "Yahoo Finance", "value": "yahoo"},
                        {"label": "Alpha Vantage", "value": "alphavantage"},
                        {"label": "NQ Futures", "value": "nq"},
                    ],
                    value="yahoo",
                    className="mb-3",
                ),
                dbc.Button(
                    [
                        DashIconify(icon="mdi:download", width=20, className="me-2"),
                        "Daten laden",
                    ],
                    id="load-data-button",
                    color="primary",
                    className="w-100 mb-2",
                ),
                dbc.Button(
                    [
                        DashIconify(icon="mdi:refresh", width=20, className="me-2"),
                        "Zurücksetzen",
                    ],
                    id="reset-button",
                    color="secondary",
                    outline=True,
                    className="w-100",
                ),
            ]),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Strategie-Karte
strategy_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Strategie", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:strategy", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dbc.Label("Strategie auswählen", html_for="strategy-select"),
            dbc.Select(
                id="strategy-select",
                options=[
                    {"label": "Moving Average Crossover", "value": "ma_crossover"},
                    {"label": "RSI Strategy", "value": "rsi"},
                    {"label": "MACD Strategy", "value": "macd"},
                    {"label": "Bollinger Bands", "value": "bollinger"},
                ],
                value="ma_crossover",
                className="mb-3",
            ),
            html.Div(id="strategy-params"),
            dbc.Button(
                [
                    DashIconify(icon="mdi:play", width=20, className="me-2"),
                    "Backtest starten",
                ],
                id="run-backtest-button",
                color="success",
                className="w-100 mt-3",
            ),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Chart-Karte
chart_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Chart", className="card-title mb-0 d-inline-block"),
            html.Div([
                dbc.ButtonGroup(
                    [
                        dbc.Button("1m", id="timeframe-1m", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("2m", id="timeframe-2m", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("3m", id="timeframe-3m", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("5m", id="timeframe-5m", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("15m", id="timeframe-15m", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("30m", id="timeframe-30m", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("1h", id="timeframe-1h", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("4h", id="timeframe-4h", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("1D", id="timeframe-1d", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("1W", id="timeframe-1w", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("1M", id="timeframe-1mo", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("ALL", id="timeframe-all", color="primary", outline=True, size="sm", className="timeframe-btn"),
                    ],
                    className="ms-3 d-inline-block",
                    style={"flexWrap": "wrap"}
                ),
                html.Div([
                    DashIconify(icon="mdi:chart-line", width=24, color=colors['primary']),
                ], className="float-end")
            ], className="d-inline-block"),
        ]),
        dbc.CardBody([
            dcc.Loading(
                id="loading-chart",
                type="default",
                children=[
                    dcc.Graph(
                        id="price-chart",
                        figure={
                            "layout": {
                                "paper_bgcolor": colors['card_background'],
                                "plot_bgcolor": colors['card_background'],
                                "font": {"color": colors['text']},
                                "xaxis": {
                                    "gridcolor": colors['grid'],
                                    "zerolinecolor": colors['grid'],
                                },
                                "yaxis": {
                                    "gridcolor": colors['grid'],
                                    "zerolinecolor": colors['grid'],
                                },
                                "margin": {"t": 20, "b": 20, "l": 20, "r": 20},
                                "height": 500,
                            }
                        },
                        config={
                            "displayModeBar": True,
                            "scrollZoom": True,
                            "modeBarButtonsToAdd": ["drawline", "drawopenpath", "eraseshape"],
                        },
                        className="chart-container",
                    ),
                ],
            ),
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                DashIconify(icon="mdi:chart-line", width=20),
                                id="line-chart-button",
                                color="primary",
                                outline=True,
                                className="me-1",
                            ),
                            dbc.Button(
                                DashIconify(icon="mdi:chart-candlestick", width=20),
                                id="candlestick-chart-button",
                                color="primary",
                                outline=False,
                                className="me-1",
                            ),
                            dbc.Button(
                                DashIconify(icon="mdi:chart-bar", width=20),
                                id="ohlc-chart-button",
                                color="primary",
                                outline=True,
                                className="me-1",
                            ),
                        ],
                        className="me-2",
                    ),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                DashIconify(icon="mdi:chart-timeline-variant", width=20),
                                id="trendline-button",
                                color="secondary",
                                outline=True,
                                className="me-1",
                                # tooltip="Trendlinie zeichnen", # Entfernt wegen Kompatibilitätsproblemen
                            ),
                            dbc.Button(
                                DashIconify(icon="mdi:chart-timeline-variant-shimmer", width=20),
                                id="horizontal-button",
                                color="secondary",
                                outline=True,
                                className="me-1",
                                # tooltip="Horizontale Linie zeichnen", # Entfernt wegen Kompatibilitätsproblemen
                            ),
                            dbc.Button(
                                DashIconify(icon="mdi:rectangle-outline", width=20),
                                id="rectangle-button",
                                color="secondary",
                                outline=True,
                                className="me-1",
                                # tooltip="Rechteck zeichnen", # Entfernt wegen Kompatibilitätsproblemen
                            ),
                            dbc.Button(
                                DashIconify(icon="mdi:chart-timeline", width=20),
                                id="fibonacci-button",
                                color="secondary",
                                outline=True,
                                className="me-1",
                                # tooltip="Fibonacci Retracement", # Entfernt wegen Kompatibilitätsproblemen
                            ),
                            dbc.Button(
                                DashIconify(icon="mdi:eraser", width=20),
                                id="delete-drawing-button",
                                color="secondary",
                                outline=True,
                                className="me-1",
                                # tooltip="Zeichnung löschen", # Entfernt wegen Kompatibilitätsproblemen
                            ),
                        ],
                        className="me-2",
                    ),
                ], width="auto"),
                dbc.Col([
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                DashIconify(icon="mdi:content-save", width=20),
                                id="save-chart-button",
                                color="secondary",
                                outline=True,
                                className="me-1",
                                # tooltip="Chart speichern", # Entfernt wegen Kompatibilitätsproblemen
                            ),
                            dbc.Button(
                                DashIconify(icon="mdi:share-variant", width=20),
                                id="share-chart-button",
                                color="secondary",
                                outline=True,
                                className="me-1",
                                # tooltip="Chart teilen", # Entfernt wegen Kompatibilitätsproblemen
                            ),
                        ],
                    ),
                ], width="auto", className="ms-auto"),
            ], className="mt-2"),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Indikatoren-Karte
indicators_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Indikatoren", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:chart-bell-curve-cumulative", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Indikator hinzufügen"),
                    dbc.Select(
                        id="indicator-select",
                        options=[
                            {"label": "Moving Average (MA)", "value": "ma"},
                            {"label": "Exponential MA (EMA)", "value": "ema"},
                            {"label": "Bollinger Bands", "value": "bollinger"},
                            {"label": "RSI", "value": "rsi"},
                            {"label": "MACD", "value": "macd"},
                            {"label": "Stochastic", "value": "stoch"},
                        ],
                        value="ma",
                        className="mb-2",
                    ),
                ], width=8),
                dbc.Col([
                    html.Br(),
                    dbc.Button(
                        [
                            DashIconify(icon="mdi:plus", width=20, className="me-1"),
                            "Hinzufügen",
                        ],
                        id="add-indicator-button",
                        color="primary",
                        className="w-100",
                    ),
                ], width=4),
            ]),
            html.Hr(),
            html.Div(id="active-indicators", className="mt-2"),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Layout
app.layout = dbc.Container(
    [
        # Stores für Zustandsverwaltung
        dcc.Store(id="active-drawing-tool-store"),
        dcc.Store(id="drawing-data-store", data=[]),
        dcc.Store(id="active-timeframe-store", data="1d"),  # Standardmäßig 1 Tag
        dcc.Store(id="active-asset-store", data="AAPL"),  # Standardmäßig Apple
        dcc.Store(id="asset-options", data=get_available_assets()),
        
        # Header
        header,
        
        # Hauptinhalt
        dbc.Row(
            [
                # Linke Spalte (Sidebar)
                dbc.Col(
                    [
                        sidebar,
                        strategy_card,
                    ],
                    width=12, lg=3,
                ),
                
                # Rechte Spalte (Chart und Indikatoren)
                dbc.Col(
                    [
                        chart_card,
                        indicators_card,
                    ],
                    width=12, lg=9,
                ),
            ],
        ),
        
        # Footer
        html.Footer(
            dbc.Container(
                [
                    html.Hr(),
                    html.P(
                        "Trading Dashboard © 2023 - Alle Rechte vorbehalten",
                        className="text-center text-muted",
                    ),
                ]
            ),
            className="mt-4",
        ),
    ],
    style={"backgroundColor": colors['background'], "minHeight": "100vh", "color": colors['text']},
    className="fade-in",
)

# Callback für Asset-Buttons mit visueller Rückmeldung
@app.callback(
    [Output({"type": "asset-button", "index": dash.dependencies.ALL}, "color"),
     Output({"type": "asset-button", "index": dash.dependencies.ALL}, "outline"),
     Output("symbol-input", "value"),
     Output("active-asset-store", "data"),
     Output("data-source", "value")],  # Automatische Datenquellenauswahl
    [Input({"type": "asset-button", "index": dash.dependencies.ALL}, "n_clicks")],
    [State({"type": "asset-button", "index": dash.dependencies.ALL}, "id"),
     State("symbol-input", "value"),
     State("active-asset-store", "data")]
)
def update_asset_selection(n_clicks, ids, current_value, current_active_asset):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Initialer Zustand: AAPL ist standardmäßig ausgewählt
        colors = ["primary" if id["index"] == "AAPL" else "secondary" for id in ids]
        outlines = [False if id["index"] == "AAPL" else True for id in ids]
        return colors, outlines, current_value, current_value, "yahoo"  # Yahoo als Standard-Datenquelle
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "":
        colors = ["primary" if id["index"] == current_active_asset else "secondary" for id in ids]
        outlines = [False if id["index"] == current_active_asset else True for id in ids]
        return colors, outlines, current_value, current_active_asset, get_datasource_for_asset(current_active_asset)
    
    # Extrahiere den Asset-Wert aus der Button-ID
    try:
        button_data = json.loads(button_id)
        if button_data["type"] == "asset-button":
            selected_asset = button_data["index"]
            
            # Setze alle Buttons auf den Standardzustand und den ausgewählten auf aktiv
            colors = ["primary" if id["index"] == selected_asset else "secondary" for id in ids]
            outlines = [False if id["index"] == selected_asset else True for id in ids]
            
            # Bestimme die passende Datenquelle für das Asset
            datasource = get_datasource_for_asset(selected_asset)
            
            return colors, outlines, selected_asset, selected_asset, datasource
    except:
        pass
    
    # Fallback: Behalte den aktuellen Zustand bei
    colors = ["primary" if id["index"] == current_active_asset else "secondary" for id in ids]
    outlines = [False if id["index"] == current_active_asset else True for id in ids]
    return colors, outlines, current_value, current_active_asset, get_datasource_for_asset(current_active_asset)

# Hilfsfunktion zur Bestimmung der passenden Datenquelle für ein Asset
def get_datasource_for_asset(asset):
    """
    Bestimmt die passende Datenquelle basierend auf dem Asset-Typ.
    """
    if "BTC" in asset or "ETH" in asset:
        return "yahoo"  # Yahoo Finance für Kryptowährungen
    elif "USD" in asset or "JPY" in asset or "EUR" in asset or "GBP" in asset:
        return "yahoo"  # Yahoo Finance für Forex
    elif "NQ" in asset:
        return "nq"     # NQ-Datenquelle für NQ Futures
    else:
        return "yahoo"  # Yahoo Finance für Aktien (Standard)

# Callback für Zeitrahmen-Buttons mit visueller Rückmeldung
@app.callback(
    [Output("timeframe-1m", "color"),
     Output("timeframe-1m", "outline"),
     Output("timeframe-2m", "color"),
     Output("timeframe-2m", "outline"),
     Output("timeframe-3m", "color"),
     Output("timeframe-3m", "outline"),
     Output("timeframe-5m", "color"),
     Output("timeframe-5m", "outline"),
     Output("timeframe-15m", "color"),
     Output("timeframe-15m", "outline"),
     Output("timeframe-30m", "color"),
     Output("timeframe-30m", "outline"),
     Output("timeframe-1h", "color"),
     Output("timeframe-1h", "outline"),
     Output("timeframe-4h", "color"),
     Output("timeframe-4h", "outline"),
     Output("timeframe-1d", "color"),
     Output("timeframe-1d", "outline"),
     Output("timeframe-1w", "color"),
     Output("timeframe-1w", "outline"),
     Output("timeframe-1mo", "color"),
     Output("timeframe-1mo", "outline"),
     Output("timeframe-all", "color"),
     Output("timeframe-all", "outline"),
     Output("active-timeframe-store", "data")],
    [Input("timeframe-1m", "n_clicks"),
     Input("timeframe-2m", "n_clicks"),
     Input("timeframe-3m", "n_clicks"),
     Input("timeframe-5m", "n_clicks"),
     Input("timeframe-15m", "n_clicks"),
     Input("timeframe-30m", "n_clicks"),
     Input("timeframe-1h", "n_clicks"),
     Input("timeframe-4h", "n_clicks"),
     Input("timeframe-1d", "n_clicks"),
     Input("timeframe-1w", "n_clicks"),
     Input("timeframe-1mo", "n_clicks"),
     Input("timeframe-all", "n_clicks")],
    [State("active-timeframe-store", "data")]
)
def update_timeframe_selection(clicks_1m, clicks_2m, clicks_3m, clicks_5m, clicks_15m, clicks_30m, 
                              clicks_1h, clicks_4h, clicks_1d, clicks_1w, clicks_1mo, clicks_all, 
                              current_timeframe):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Initialer Zustand: 1d ist standardmäßig ausgewählt
        return set_timeframe_button_states("1d")
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Bestimme den ausgewählten Zeitrahmen basierend auf der Button-ID
    timeframe_mapping = {
        "timeframe-1m": "1m",
        "timeframe-2m": "2m",
        "timeframe-3m": "3m",
        "timeframe-5m": "5m",
        "timeframe-15m": "15m",
        "timeframe-30m": "30m",
        "timeframe-1h": "1h",
        "timeframe-4h": "4h",
        "timeframe-1d": "1d",
        "timeframe-1w": "1w",
        "timeframe-1mo": "1mo",
        "timeframe-all": "max"
    }
    
    selected_timeframe = timeframe_mapping.get(button_id, current_timeframe)
    return set_timeframe_button_states(selected_timeframe)

# Hilfsfunktion zum Setzen der Zustände der Zeitrahmen-Buttons
def set_timeframe_button_states(selected_timeframe):
    """
    Setzt die Farben und Outline-Zustände der Zeitrahmen-Buttons basierend auf dem ausgewählten Zeitrahmen.
    """
    timeframes = ["1m", "2m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo", "max"]
    colors = []
    outlines = []
    
    for tf in timeframes:
        if tf == selected_timeframe:
            colors.append("primary")
            outlines.append(False)
        else:
            colors.append("primary")
            outlines.append(True)
    
    # Füge den ausgewählten Zeitrahmen als letzten Rückgabewert hinzu
    return colors[0], outlines[0], colors[1], outlines[1], colors[2], outlines[2], colors[3], outlines[3], \
           colors[4], outlines[4], colors[5], outlines[5], colors[6], outlines[6], colors[7], outlines[7], \
           colors[8], outlines[8], colors[9], outlines[9], colors[10], outlines[10], colors[11], outlines[11], \
           selected_timeframe

# Hier würden die Callbacks folgen...

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
