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
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
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

# Stelle sicher, dass das Cache-Verzeichnis existiert
os.makedirs(cache_dir, exist_ok=True)

# Definiere Farbschema
colors = {
    'background': '#121212',
    'card_background': '#1E1E1E',
    'text': '#E0E0E0',
    'primary': '#3B82F6',
    'secondary': '#6B7280',
    'success': '#10B981',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'grid': 'rgba(255, 255, 255, 0.1)',
    'up': '#10B981',
    'down': '#EF4444',
    'selection': 'rgba(59, 130, 246, 0.2)',
}

# Definiere Header
header = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="mdi:chart-line", width=36, color=colors['primary'])),
                        dbc.Col(html.H3("Trading Dashboard Pro", className="ms-2 mb-0")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="#",
                style={"textDecoration": "none", "color": colors['text']},
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
                ),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    color="dark",
    dark=True,
    className="mb-4 shadow",
    style={"borderBottom": f"1px solid {colors['grid']}"},
)

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
                        dbc.Button("1D", id="timeframe-1d", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("1W", id="timeframe-1w", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("1M", id="timeframe-1m", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("1Y", id="timeframe-1y", color="primary", outline=True, size="sm", className="timeframe-btn"),
                        dbc.Button("ALL", id="timeframe-all", color="primary", outline=True, size="sm", className="timeframe-btn"),
                    ],
                    className="ms-3 d-inline-block",
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
                            "modeBarButtonsToRemove": [
                                "select2d",
                                "lasso2d",
                                "autoScale2d",
                            ],
                        },
                    ),
                ],
            ),
            dbc.Tabs(
                [
                    dbc.Tab(
                        dcc.Graph(
                            id="volume-chart",
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
                                    "height": 200,
                                }
                            },
                            config={
                                "displayModeBar": False,
                            },
                        ),
                        label="Volumen",
                        tab_id="volume-tab",
                    ),
                    dbc.Tab(
                        dcc.Graph(
                            id="indicators-chart",
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
                                    "height": 200,
                                }
                            },
                            config={
                                "displayModeBar": False,
                            },
                        ),
                        label="Indikatoren",
                        tab_id="indicators-tab",
                    ),
                ],
                id="chart-tabs",
                active_tab="volume-tab",
            ),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Ergebniskarte
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
                            html.H5("Gesamtrendite", className="text-center mb-1 text-muted"),
                            html.H3(id="total-return", className="text-center mb-0"),
                        ])
                    ], className="mb-3", style={"backgroundColor": colors['background']}),
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Sharpe Ratio", className="text-center mb-1 text-muted"),
                            html.H3(id="sharpe-ratio", className="text-center mb-0"),
                        ])
                    ], className="mb-3", style={"backgroundColor": colors['background']}),
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Max Drawdown", className="text-center mb-1 text-muted"),
                            html.H3(id="max-drawdown", className="text-center mb-0"),
                        ])
                    ], className="mb-3", style={"backgroundColor": colors['background']}),
                ], width=4),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Gewinn-Trades", className="text-center mb-1 text-muted"),
                            html.H3(id="winning-trades", className="text-center mb-0"),
                        ])
                    ], className="mb-3", style={"backgroundColor": colors['background']}),
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Verlust-Trades", className="text-center mb-1 text-muted"),
                            html.H3(id="losing-trades", className="text-center mb-0"),
                        ])
                    ], className="mb-3", style={"backgroundColor": colors['background']}),
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Win Rate", className="text-center mb-1 text-muted"),
                            html.H3(id="win-rate", className="text-center mb-0"),
                        ])
                    ], className="mb-3", style={"backgroundColor": colors['background']}),
                ], width=4),
            ]),
            dcc.Graph(
                id="equity-curve",
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
                        "height": 250,
                    }
                },
                config={
                    "displayModeBar": False,
                },
            ),
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

# Hier würden die Callbacks folgen...

if __name__ == "__main__":
    app.run_server(debug=True)
