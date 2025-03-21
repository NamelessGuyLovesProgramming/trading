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

from data.data_fetcher import DataFetcher
from data.data_processor import DataProcessor
from backtesting.backtest_engine import BacktestEngine
from strategy.example_strategies import MovingAverageCrossover, RSIStrategy, MACDStrategy, BollingerBandsStrategy

# Lade das dunkle Template für Plotly-Figuren
load_figure_template("darkly")

# Initialisiere die Dash-App mit einem dunklen Theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)

# Initialisiere Komponenten
data_dir = os.path.join(parent_dir, 'data')
cache_dir = os.path.join(data_dir, 'cache')
output_dir = os.path.join(parent_dir, 'output')
os.makedirs(output_dir, exist_ok=True)

data_fetcher = DataFetcher(cache_dir=cache_dir)
data_processor = DataProcessor()
backtest_engine = BacktestEngine(initial_capital=50000.0)

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
                        dbc.NavItem(dbc.NavLink([DashIconify(icon="mdi:view-dashboard", width=18, className="me-2"), "Dashboard"], href="#", active=True)),
                        dbc.NavItem(dbc.NavLink([DashIconify(icon="mdi:strategy", width=18, className="me-2"), "Strategien"], href="#")),
                        dbc.NavItem(dbc.NavLink([DashIconify(icon="mdi:chart-timeline-variant", width=18, className="me-2"), "Backtesting"], href="#")),
                        dbc.NavItem(dbc.NavLink([DashIconify(icon="mdi:cog", width=18, className="me-2"), "Einstellungen"], href="#")),
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
        html.Button("1m", id="tf-1m", className="timeframe-button"),
        html.Button("5m", id="tf-5m", className="timeframe-button"),
        html.Button("15m", id="tf-15m", className="timeframe-button"),
        html.Button("30m", id="tf-30m", className="timeframe-button"),
        html.Button("1h", id="tf-1h", className="timeframe-button"),
        html.Button("4h", id="tf-4h", className="timeframe-button"),
        html.Button("1D", id="tf-1d", className="timeframe-button active"),
        html.Button("1W", id="tf-1w", className="timeframe-button"),
        html.Button("1M", id="tf-1m", className="timeframe-button"),
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
                    html.Span("MACD(12,26,9)", className="indicator-badge", style={"backgroundColor": colors['danger']}),
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

# Callback für Strategie-Parameter
@app.callback(
    Output("strategy-params", "children"),
    Input("strategy-dropdown", "value"),
)
def update_strategy_params(strategy_name):
    if not strategy_name or strategy_name not in strategies:
        return []
    
    strategy = strategies[strategy_name]
    params = strategy.get_parameters()
    
    param_inputs = []
    
    if strategy_name == "MA Crossover":
        param_inputs = [
            dbc.Row([
                dbc.Col([
                    dbc.Label("Kurzer MA", html_for="short-window-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:chart-line-variant", width=18)),
                        dbc.Input(
                            id="short-window-input",
                            type="number",
                            value=params.get("short_window", 20),
                            min=5,
                            max=50,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=6),
                dbc.Col([
                    dbc.Label("Langer MA", html_for="long-window-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:chart-line-variant", width=18)),
                        dbc.Input(
                            id="long-window-input",
                            type="number",
                            value=params.get("long_window", 50),
                            min=20,
                            max=200,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=6),
            ]),
        ]
    elif strategy_name == "RSI Strategy":
        param_inputs = [
            dbc.Row([
                dbc.Col([
                    dbc.Label("RSI Periode", html_for="rsi-window-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:chart-bell-curve", width=18)),
                        dbc.Input(
                            id="rsi-window-input",
                            type="number",
                            value=params.get("rsi_window", 14),
                            min=5,
                            max=30,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=4),
                dbc.Col([
                    dbc.Label("Überkauft", html_for="overbought-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:arrow-up-bold", width=18)),
                        dbc.Input(
                            id="overbought-input",
                            type="number",
                            value=params.get("overbought", 70),
                            min=60,
                            max=90,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=4),
                dbc.Col([
                    dbc.Label("Überverkauft", html_for="oversold-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:arrow-down-bold", width=18)),
                        dbc.Input(
                            id="oversold-input",
                            type="number",
                            value=params.get("oversold", 30),
                            min=10,
                            max=40,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=4),
            ]),
        ]
    elif strategy_name == "MACD Strategy":
        param_inputs = [
            dbc.Row([
                dbc.Col([
                    dbc.Label("Schneller EMA", html_for="fast-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:chart-line-variant", width=18)),
                        dbc.Input(
                            id="fast-input",
                            type="number",
                            value=params.get("fast", 12),
                            min=5,
                            max=30,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=4),
                dbc.Col([
                    dbc.Label("Langsamer EMA", html_for="slow-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:chart-line-variant", width=18)),
                        dbc.Input(
                            id="slow-input",
                            type="number",
                            value=params.get("slow", 26),
                            min=15,
                            max=50,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=4),
                dbc.Col([
                    dbc.Label("Signal", html_for="signal-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:chart-line-variant", width=18)),
                        dbc.Input(
                            id="signal-input",
                            type="number",
                            value=params.get("signal", 9),
                            min=5,
                            max=20,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=4),
            ]),
        ]
    elif strategy_name == "Bollinger Bands Strategy":
        param_inputs = [
            dbc.Row([
                dbc.Col([
                    dbc.Label("Periode", html_for="bb-window-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:chart-bell-curve", width=18)),
                        dbc.Input(
                            id="bb-window-input",
                            type="number",
                            value=params.get("window", 20),
                            min=10,
                            max=50,
                            step=1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=6),
                dbc.Col([
                    dbc.Label("Standardabweichungen", html_for="num-std-input", className="mb-1"),
                    dbc.InputGroup([
                        dbc.InputGroupText(DashIconify(icon="mdi:sigma", width=18)),
                        dbc.Input(
                            id="num-std-input",
                            type="number",
                            value=params.get("num_std", 2),
                            min=1,
                            max=3,
                            step=0.1,
                            className="border-start-0",
                        ),
                    ]),
                ], width=6),
            ]),
        ]
    
    return param_inputs

# Callback für Timeframe-Buttons
@app.callback(
    [Output("active-timeframe-store", "data")] + 
    [Output(f"tf-{tf}", "className") for tf in ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1m"]],
    [Input(f"tf-{tf}", "n_clicks") for tf in ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1m"]],
    [State("active-timeframe-store", "data")],
    prevent_initial_call=True,
)
def update_timeframe(click_1m, click_5m, click_15m, click_30m, click_1h, click_4h, click_1d, click_1w, click_1mo, active_tf):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Standardmäßig 1d aktiv
        return ["1d"] + ["timeframe-button" if tf != "1d" else "timeframe-button active" for tf in ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1m"]]
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    new_tf = button_id.split("-")[1]
    
    # Klassen für alle Buttons aktualisieren
    button_classes = []
    for tf in ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1m"]:
        if f"tf-{tf}" == button_id:
            button_classes.append("timeframe-button active")
        else:
            button_classes.append("timeframe-button")
    
    return [new_tf] + button_classes

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
        # Daten abrufen
        df = data_fetcher.get_stock_data(symbol, interval, range_val)
        
        if df is None or df.empty:
            return None, html.Div([
                DashIconify(icon="mdi:alert", width=18, color=colors['danger'], className="me-2"),
                "Keine Daten verfügbar"
            ]), ""
        
        # Indikatoren hinzufügen
        df = data_processor.add_indicators(df)
        
        # Daten in JSON konvertieren
        df_json = df.reset_index().to_json(date_format='iso', orient='split')
        
        # Info-Text erstellen
        start_date = df.index.min().strftime('%d.%m.%Y')
        end_date = df.index.max().strftime('%d.%m.%Y')
        num_days = (df.index.max() - df.index.min()).days
        
        info_text = html.Div([
            DashIconify(icon="mdi:check-circle", width=18, color=colors['success'], className="me-2"),
            f"{num_days} Tage ({start_date} - {end_date})"
        ])
        
        # Symbol-Anzeige
        symbol_display = f"{symbol.upper()}"
        
        return df_json, info_text, symbol_display
    
    except Exception as e:
        return None, html.Div([
            DashIconify(icon="mdi:alert", width=18, color=colors['danger'], className="me-2"),
            f"Fehler: {str(e)}"
        ]), ""

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
    
    # Daten aus JSON laden
    df = pd.read_json(StringIO(data_json), orient='split')
    df.set_index('index', inplace=True)
    
    # Bestimme Chart-Typ
    chart_type = "candlestick"  # Standard
    if line_color == "primary":
        chart_type = "line"
    elif ohlc_color == "primary":
        chart_type = "ohlc"
    
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
    
    # Füge Preisdaten hinzu
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
    elif chart_type == "candlestick":
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
                hovertemplate='%{x}<br>Eröffnung: %{open:.2f}<br>Hoch: %{high:.2f}<br>Tief: %{low:.2f}<br>Schluss: %{close:.2f}<extra></extra>',
            ),
            row=1, col=1
        )
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
    
    # Füge SMA hinzu
    if show_sma and 'SMA_20' in df.columns and 'SMA_50' in df.columns and 'SMA_200' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['SMA_20'],
                mode='lines',
                name='SMA 20',
                line=dict(color=colors['success'], width=1.5),
                hovertemplate='%{x}<br>SMA 20: %{y:.2f}<extra></extra>',
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['SMA_50'],
                mode='lines',
                name='SMA 50',
                line=dict(color=colors['warning'], width=1.5),
                hovertemplate='%{x}<br>SMA 50: %{y:.2f}<extra></extra>',
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['SMA_200'],
                mode='lines',
                name='SMA 200',
                line=dict(color=colors['danger'], width=1.5),
                hovertemplate='%{x}<br>SMA 200: %{y:.2f}<extra></extra>',
            ),
            row=1, col=1
        )
    
    # Füge Bollinger Bands hinzu
    if show_bb and 'BB_Upper' in df.columns and 'BB_Middle' in df.columns and 'BB_Lower' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['BB_Upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color=colors['info'], width=1),
                opacity=0.7,
                hovertemplate='%{x}<br>BB Upper: %{y:.2f}<extra></extra>',
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['BB_Middle'],
                mode='lines',
                name='BB Middle',
                line=dict(color=colors['info'], width=1.5),
                opacity=0.7,
                hovertemplate='%{x}<br>BB Middle: %{y:.2f}<extra></extra>',
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['BB_Lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color=colors['info'], width=1),
                opacity=0.7,
                fill='tonexty',
                fillcolor='rgba(0, 188, 212, 0.1)',
                hovertemplate='%{x}<br>BB Lower: %{y:.2f}<extra></extra>',
            ),
            row=1, col=1
        )
    
    # Füge Volumen hinzu
    colors_volume = np.where(df['Close'] >= df['Open'], colors['up'], colors['down'])
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volumen',
            marker=dict(
                color=colors_volume,
                line=dict(color=colors_volume, width=1),
            ),
            hovertemplate='%{x}<br>Volumen: %{y:,.0f}<extra></extra>',
        ),
        row=2, col=1
    )
    
    # Füge RSI hinzu
    current_row = 3
    if show_rsi and 'RSI_14' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['RSI_14'],
                mode='lines',
                name='RSI (14)',
                line=dict(color=colors['warning'], width=1.5),
                hovertemplate='%{x}<br>RSI: %{y:.2f}<extra></extra>',
            ),
            row=current_row, col=1
        )
        
        # Füge Überkauft/Überverkauft-Linien hinzu
        fig.add_trace(
            go.Scatter(
                x=[df.index[0], df.index[-1]],
                y=[70, 70],
                mode='lines',
                name='Überkauft',
                line=dict(color=colors['danger'], width=1, dash='dash'),
                hoverinfo='skip',
            ),
            row=current_row, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=[df.index[0], df.index[-1]],
                y=[30, 30],
                mode='lines',
                name='Überverkauft',
                line=dict(color=colors['success'], width=1, dash='dash'),
                hoverinfo='skip',
            ),
            row=current_row, col=1
        )
        
        # Füge Mittellinie hinzu
        fig.add_trace(
            go.Scatter(
                x=[df.index[0], df.index[-1]],
                y=[50, 50],
                mode='lines',
                name='Neutral',
                line=dict(color=colors['secondary'], width=1, dash='dot'),
                hoverinfo='skip',
            ),
            row=current_row, col=1
        )
        
        current_row += 1
    
    # Füge MACD hinzu
    if show_macd and 'MACD' in df.columns and 'MACD_Signal' in df.columns and 'MACD_Hist' in df.columns:
        # MACD und Signal-Linie
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color=colors['primary'], width=1.5),
                hovertemplate='%{x}<br>MACD: %{y:.4f}<extra></extra>',
            ),
            row=current_row, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MACD_Signal'],
                mode='lines',
                name='Signal',
                line=dict(color=colors['danger'], width=1.5),
                hovertemplate='%{x}<br>Signal: %{y:.4f}<extra></extra>',
            ),
            row=current_row, col=1
        )
        
        # MACD-Histogramm
        colors_hist = np.where(df['MACD_Hist'] >= 0, colors['up'], colors['down'])
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['MACD_Hist'],
                name='Histogramm',
                marker=dict(
                    color=colors_hist,
                    line=dict(color=colors_hist, width=1),
                ),
                hovertemplate='%{x}<br>Histogramm: %{y:.4f}<extra></extra>',
            ),
            row=current_row, col=1
        )
    
    # Füge Handelssignale hinzu, wenn Backtest-Ergebnisse vorhanden sind
    if backtest_results_json:
        try:
            results = json.loads(backtest_results_json)
            trades = results.get('trades', [])
            
            for trade in trades:
                # Kaufsignale
                if 'entry_date' in trade and 'entry_price' in trade:
                    entry_date = pd.to_datetime(trade['entry_date'])
                    entry_price = trade['entry_price']
                    
                    fig.add_trace(
                        go.Scatter(
                            x=[entry_date],
                            y=[entry_price],
                            mode='markers',
                            name='Kauf',
                            marker=dict(
                                symbol='triangle-up',
                                size=12,
                                color=colors['up'],
                                line=dict(width=1, color=colors['text']),
                            ),
                            hovertemplate='%{x}<br>Kauf: %{y:.2f}<extra></extra>',
                            showlegend=False,
                        ),
                        row=1, col=1
                    )
                
                # Verkaufssignale
                if 'exit_date' in trade and 'exit_price' in trade:
                    exit_date = pd.to_datetime(trade['exit_date'])
                    exit_price = trade['exit_price']
                    
                    fig.add_trace(
                        go.Scatter(
                            x=[exit_date],
                            y=[exit_price],
                            mode='markers',
                            name='Verkauf',
                            marker=dict(
                                symbol='triangle-down',
                                size=12,
                                color=colors['down'],
                                line=dict(width=1, color=colors['text']),
                            ),
                            hovertemplate='%{x}<br>Verkauf: %{y:.2f}<extra></extra>',
                            showlegend=False,
                        ),
                        row=1, col=1
                    )
                
                # Stop-Loss und Take-Profit
                if 'entry_date' in trade and 'stop_loss' in trade and trade['stop_loss'] is not None:
                    entry_date = pd.to_datetime(trade['entry_date'])
                    stop_loss = trade['stop_loss']
                    
                    # Finde den nächsten Datenpunkt im DataFrame
                    closest_idx = df.index.get_indexer([entry_date], method='nearest')[0]
                    
                    # Bestimme das Ende des Trades oder verwende das Ende des Datensatzes
                    exit_date = pd.to_datetime(trade.get('exit_date', df.index[-1]))
                    
                    # Erstelle eine Maske für den Zeitraum des Trades
                    mask = (df.index >= entry_date) & (df.index <= exit_date)
                    trade_period = df.index[mask]
                    
                    if len(trade_period) > 0:
                        fig.add_trace(
                            go.Scatter(
                                x=trade_period,
                                y=[stop_loss] * len(trade_period),
                                mode='lines',
                                name='Stop-Loss',
                                line=dict(color=colors['danger'], width=1, dash='dash'),
                                hovertemplate='Stop-Loss: %{y:.2f}<extra></extra>',
                                showlegend=False,
                            ),
                            row=1, col=1
                        )
                
                if 'entry_date' in trade and 'take_profit' in trade and trade['take_profit'] is not None:
                    entry_date = pd.to_datetime(trade['entry_date'])
                    take_profit = trade['take_profit']
                    
                    # Finde den nächsten Datenpunkt im DataFrame
                    closest_idx = df.index.get_indexer([entry_date], method='nearest')[0]
                    
                    # Bestimme das Ende des Trades oder verwende das Ende des Datensatzes
                    exit_date = pd.to_datetime(trade.get('exit_date', df.index[-1]))
                    
                    # Erstelle eine Maske für den Zeitraum des Trades
                    mask = (df.index >= entry_date) & (df.index <= exit_date)
                    trade_period = df.index[mask]
                    
                    if len(trade_period) > 0:
                        fig.add_trace(
                            go.Scatter(
                                x=trade_period,
                                y=[take_profit] * len(trade_period),
                                mode='lines',
                                name='Take-Profit',
                                line=dict(color=colors['success'], width=1, dash='dash'),
                                hovertemplate='Take-Profit: %{y:.2f}<extra></extra>',
                                showlegend=False,
                            ),
                            row=1, col=1
                        )
        except Exception as e:
            print(f"Fehler beim Hinzufügen von Handelssignalen: {str(e)}")
    
    # Update Layout
    fig.update_layout(
        **chart_style['layout'],
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10),
            bgcolor=colors['card_background'],
            bordercolor=colors['grid'],
        ),
        dragmode='zoom',
        hovermode='x unified',
        margin=dict(l=10, r=50, t=10, b=10),
        hoverlabel=dict(
            bgcolor=colors['card_background'],
            font_size=12,
            font_family="-apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif",
        ),
        selectdirection='h',
    )
    
    # Update Achsen
    fig.update_xaxes(
        rangeslider_visible=False,
        gridcolor=colors['grid'],
        zerolinecolor=colors['grid'],
        showgrid=True,
        gridwidth=0.5,
        showline=True,
        linewidth=1,
        linecolor=colors['grid'],
        row=n_rows, col=1,  # Nur für die unterste Zeile
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # Wochenenden ausblenden
        ],
        tickformat='%d.%m.%y',  # Deutsches Datumsformat
    )
    
    for i in range(1, n_rows + 1):
        fig.update_yaxes(
            gridcolor=colors['grid'],
            zerolinecolor=colors['grid'],
            showgrid=True,
            gridwidth=0.5,
            showline=True,
            linewidth=1,
            linecolor=colors['grid'],
            row=i, col=1,
            side='right',  # TradingView hat Y-Achse auf der rechten Seite
            tickformat='.2f',  # Zwei Dezimalstellen
        )
    
    # Spezielle Einstellungen für RSI
    if show_rsi:
        rsi_row = 3
        fig.update_yaxes(
            range=[0, 100],
            row=rsi_row, col=1,
        )
    
    return fig

# Callback für Backtest durchführen
@app.callback(
    [
        Output("backtest-results-store", "data"),
        Output("total-return", "children"),
        Output("total-return", "className"),
        Output("win-rate", "children"),
        Output("win-rate", "className"),
        Output("num-trades", "children"),
        Output("max-drawdown", "children"),
        Output("max-drawdown", "className"),
        Output("equity-chart", "figure"),
        Output("trades-table", "data"),
    ],
    Input("run-backtest-button", "n_clicks"),
    [
        State("stock-data-store", "data"),
        State("strategy-dropdown", "value"),
        State("capital-input", "value"),
        State("commission-input", "value"),
        # MA Crossover Parameter
        State("short-window-input", "value"),
        State("long-window-input", "value"),
        # RSI Parameter
        State("rsi-window-input", "value"),
        State("overbought-input", "value"),
        State("oversold-input", "value"),
        # MACD Parameter
        State("fast-input", "value"),
        State("slow-input", "value"),
        State("signal-input", "value"),
        # Bollinger Bands Parameter
        State("bb-window-input", "value"),
        State("num-std-input", "value"),
    ],
    prevent_initial_call=True,
)
def run_backtest(n_clicks, data_json, strategy_name, capital, commission,
                short_window, long_window, rsi_window, overbought, oversold,
                fast, slow, signal, bb_window, num_std):
    if not n_clicks or not data_json or not strategy_name:
        # Leere Ergebnisse zurückgeben
        empty_fig = go.Figure()
        empty_fig.update_layout(
            **chart_style['layout'],
            title="",
            annotations=[
                dict(
                    text="Führen Sie einen Backtest durch, um Ergebnisse zu sehen",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=16, color=colors['text']),
                )
            ]
        )
        return None, "N/A", "card-text text-center", "N/A", "card-text text-center", "N/A", "N/A", "card-text text-center", empty_fig, []
    
    try:
        # Daten aus JSON laden
        df = pd.read_json(StringIO(data_json), orient='split')
        df.set_index('index', inplace=True)
        
        # Strategie konfigurieren
        strategy = None
        if strategy_name == "MA Crossover":
            strategy = MovingAverageCrossover(short_window=short_window, long_window=long_window)
        elif strategy_name == "RSI Strategy":
            strategy = RSIStrategy(rsi_window=rsi_window, overbought=overbought, oversold=oversold)
        elif strategy_name == "MACD Strategy":
            strategy = MACDStrategy(fast=fast, slow=slow, signal=signal)
        elif strategy_name == "Bollinger Bands Strategy":
            strategy = BollingerBandsStrategy(window=bb_window, num_std=num_std)
        
        if not strategy:
            raise ValueError(f"Unbekannte Strategie: {strategy_name}")
        
        # Backtest-Engine konfigurieren
        backtest_engine.initial_capital = float(capital)
        backtest_engine.commission_pct = float(commission) / 100.0
        
        # Backtest durchführen
        results = backtest_engine.run(df, strategy)
        
        if not results:
            raise ValueError("Backtest ergab keine Ergebnisse")
        
        # Ergebnisse extrahieren
        metrics = results['metrics']
        equity_curve = results['equity_curve']
        trades = results['trades']
        
        # Metriken formatieren
        total_return_pct = metrics['total_return'] * 100
        total_return_text = f"{total_return_pct:.2f}%"
        total_return_class = "card-text text-center text-success" if total_return_pct >= 0 else "card-text text-center text-danger"
        
        win_rate_pct = metrics['win_rate'] * 100
        win_rate_text = f"{win_rate_pct:.2f}%"
        win_rate_class = "card-text text-center text-success" if win_rate_pct >= 50 else "card-text text-center text-danger"
        
        num_trades_text = str(metrics['num_trades'])
        
        max_drawdown_pct = metrics['max_drawdown'] * 100
        max_drawdown_text = f"{max_drawdown_pct:.2f}%"
        max_drawdown_class = "card-text text-center text-danger"
        
        # Equity-Kurve erstellen
        equity_fig = go.Figure()
        
        # Füge Equity-Kurve hinzu
        equity_fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['equity'],
                mode='lines',
                name='Kapital',
                line=dict(color=colors['primary'], width=2),
                fill='tozeroy',
                fillcolor=f"rgba({int(colors['primary'][1:3], 16)}, {int(colors['primary'][3:5], 16)}, {int(colors['primary'][5:7], 16)}, 0.1)",
                hovertemplate='%{x}<br>Kapital: %{y:,.2f} €<extra></extra>',
            )
        )
        
        # Füge Drawdown-Kurve hinzu
        equity_fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['drawdown'] * -1,  # Negativ für bessere Visualisierung
                mode='lines',
                name='Drawdown',
                line=dict(color=colors['danger'], width=1),
                fill='tozeroy',
                fillcolor=f"rgba({int(colors['danger'][1:3], 16)}, {int(colors['danger'][3:5], 16)}, {int(colors['danger'][5:7], 16)}, 0.1)",
                visible='legendonly',  # Standardmäßig ausgeblendet
                hovertemplate='%{x}<br>Drawdown: %{y:,.2f}%<extra></extra>',
            )
        )
        
        # Füge Kaufsignale hinzu
        buy_dates = []
        buy_equities = []
        for trade in trades:
            if 'entry_date' in trade:
                entry_date = pd.to_datetime(trade['entry_date'])
                if entry_date in equity_curve.index:
                    buy_dates.append(entry_date)
                    buy_equities.append(equity_curve.loc[entry_date, 'equity'])
        
        if buy_dates:
            equity_fig.add_trace(
                go.Scatter(
                    x=buy_dates,
                    y=buy_equities,
                    mode='markers',
                    name='Kauf',
                    marker=dict(
                        symbol='triangle-up',
                        size=10,
                        color=colors['up'],
                        line=dict(width=1, color=colors['text']),
                    ),
                    hovertemplate='%{x}<br>Kauf: %{y:,.2f} €<extra></extra>',
                )
            )
        
        # Füge Verkaufssignale hinzu
        sell_dates = []
        sell_equities = []
        for trade in trades:
            if 'exit_date' in trade:
                exit_date = pd.to_datetime(trade['exit_date'])
                if exit_date in equity_curve.index:
                    sell_dates.append(exit_date)
                    sell_equities.append(equity_curve.loc[exit_date, 'equity'])
        
        if sell_dates:
            equity_fig.add_trace(
                go.Scatter(
                    x=sell_dates,
                    y=sell_equities,
                    mode='markers',
                    name='Verkauf',
                    marker=dict(
                        symbol='triangle-down',
                        size=10,
                        color=colors['down'],
                        line=dict(width=1, color=colors['text']),
                    ),
                    hovertemplate='%{x}<br>Verkauf: %{y:,.2f} €<extra></extra>',
                )
            )
        
        equity_fig.update_layout(
            **chart_style['layout'],
            title="",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor=colors['card_background'],
                bordercolor=colors['grid'],
            ),
            margin=dict(l=10, r=50, t=10, b=10),
            hoverlabel=dict(
                bgcolor=colors['card_background'],
                font_size=12,
                font_family="-apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif",
            ),
        )
        
        # Trades-Tabelle erstellen
        trades_data = []
        for i, trade in enumerate(trades):
            trade_data = {
                "index": i + 1,
                "entry_date": pd.to_datetime(trade['entry_date']).strftime('%d.%m.%Y'),
                "entry_price": f"{trade['entry_price']:.2f}",
                "exit_date": pd.to_datetime(trade['exit_date']).strftime('%d.%m.%Y') if 'exit_date' in trade else "Offen",
                "exit_price": f"{trade['exit_price']:.2f}" if 'exit_price' in trade else "N/A",
                "type": "Long" if trade['type'] == 'long' else "Short",
                "shares": f"{trade['shares']:.0f}",
                "pnl": f"{trade['pnl']:.2f}",
                "return": f"{trade['return'] * 100:.2f}%",
                "stop_loss": f"{trade['stop_loss']:.2f}" if 'stop_loss' in trade and trade['stop_loss'] is not None else "N/A",
                "take_profit": f"{trade['take_profit']:.2f}" if 'take_profit' in trade and trade['take_profit'] is not None else "N/A",
            }
            trades_data.append(trade_data)
        
        # Ergebnisse als JSON zurückgeben
        results_json = json.dumps(results, default=str)
        
        return results_json, total_return_text, total_return_class, win_rate_text, win_rate_class, num_trades_text, max_drawdown_text, max_drawdown_class, equity_fig, trades_data
    
    except Exception as e:
        print(f"Fehler beim Backtest: {str(e)}")
        
        # Leere Ergebnisse zurückgeben
        empty_fig = go.Figure()
        empty_fig.update_layout(
            **chart_style['layout'],
            title="",
            annotations=[
                dict(
                    text=f"Fehler beim Backtest: {str(e)}",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=16, color=colors['danger']),
                )
            ]
        )
        return None, "Fehler", "card-text text-center text-danger", "Fehler", "card-text text-center text-danger", "Fehler", "Fehler", "card-text text-center text-danger", empty_fig, []
