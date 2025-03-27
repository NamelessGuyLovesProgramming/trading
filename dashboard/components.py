"""
Verbesserte Komponenten ohne Symbol-Spalte und mit erweiterten Zeiteinheiten
"""

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash_iconify import DashIconify

# Farben für das Dashboard
colors = {
    'background': '#121212',
    'card': '#1E1E1E',
    'text': '#E0E0E0',
    'primary': '#3B82F6',  # Blau als Akzentfarbe
    'secondary': '#6B7280',
    'success': '#10B981',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'grid': 'rgba(255, 255, 255, 0.1)',
}

# Header mit Tab-Navigation
def create_header():
    return dbc.Navbar(
        dbc.Container(
            [
                # Logo und Titel
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(DashIconify(icon="mdi:chart-line", width=40, color=colors['primary'])),
                            dbc.Col(dbc.NavbarBrand("Trading Dashboard Pro", className="ms-2 fs-2 fw-bold")),
                        ],
                        align="center",
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                
                # Tab-Navigation
                dbc.Nav(
                    [
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    DashIconify(icon="mdi:strategy", width=20, className="me-2"),
                                    "Strategien"
                                ],
                                id="tab-strategien",
                                active="exact",
                                href="/",
                                className="d-flex align-items-center"
                            )
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    DashIconify(icon="mdi:history", width=20, className="me-2"),
                                    "Backtesting"
                                ],
                                id="tab-backtesting",
                                href="/backtesting",
                                className="d-flex align-items-center"
                            )
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    DashIconify(icon="mdi:cog", width=20, className="me-2"),
                                    "Einstellung"
                                ],
                                id="tab-einstellung",
                                href="/einstellung",
                                className="d-flex align-items-center"
                            )
                        ),
                    ],
                    className="ms-auto nav-tabs",
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        color=colors['background'],
        dark=True,
        className="mb-4",
    )

# Sidebar für Strategie-Konfiguration
def create_strategy_sidebar():
    return dbc.Card(
        [
            dbc.CardHeader("Strategie-Konfiguration", className="fs-5"),
            dbc.CardBody(
                [
                    # Symbol-Spalte wurde entfernt, da Assets jetzt über Dropdown ausgewählt werden
                    html.Div(
                        [
                            html.Label("Strategie", className="form-label"),
                            dbc.Select(
                                id="strategy-select",
                                options=[
                                    {"label": "Moving Average Crossover", "value": "ma_crossover"},
                                    {"label": "RSI Strategie", "value": "rsi"},
                                    {"label": "MACD Strategie", "value": "macd"},
                                    {"label": "Bollinger Bands", "value": "bollinger"},
                                ],
                                value="ma_crossover",
                                className="mb-3",
                            ),
                        ]
                    ),
                    html.Div(
                        id="strategy-params",
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            html.Label("Zeitraum", className="form-label"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(
                                            id="start-date",
                                            type="date",
                                            value="2023-01-01",
                                        ),
                                        width=6,
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="end-date",
                                            type="date",
                                            value="2023-12-31",
                                        ),
                                        width=6,
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ]
                    ),
                    dbc.Button(
                        [
                            DashIconify(icon="mdi:play", width=20, className="me-2"),
                            "Strategie ausführen",
                        ],
                        id="run-strategy-button",
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
                ]
            ),
        ],
        className="mb-4 shadow-lg rounded-xl",
    )

# Chart-Karte
def create_chart_card():
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        # Asset-Auswahl
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        dbc.InputGroup(
                                            [
                                                dbc.InputGroupText(
                                                    DashIconify(icon="mdi:magnify", width=20)
                                                ),
                                                dbc.Input(
                                                    id="asset-search",
                                                    placeholder="Asset suchen...",
                                                    type="text",
                                                    className="bg-dark text-light border-secondary",
                                                ),
                                            ],
                                            className="mb-2",
                                        ),
                                        dcc.Dropdown(
                                            id="asset-select",
                                            options=[],
                                            placeholder="Asset auswählen",
                                            className="asset-dropdown",
                                        ),
                                    ],
                                    className="me-2",
                                ),
                            ],
                            md=4,
                            sm=12,
                        ),
                        
                        # Chart-Typ-Buttons
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Span("Chart-Typ: ", className="me-2 d-none d-md-inline"),
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button(
                                                    DashIconify(icon="mdi:chart-line", width=20),
                                                    id="line-chart-button",
                                                    color="secondary",
                                                    outline=True,
                                                    className="btn-sm",
                                                ),
                                                dbc.Button(
                                                    DashIconify(icon="mdi:chart-candlestick", width=20),
                                                    id="candlestick-chart-button",
                                                    color="primary",
                                                    outline=False,
                                                    className="btn-sm",
                                                ),
                                                dbc.Button(
                                                    DashIconify(icon="mdi:chart-bar", width=20),
                                                    id="ohlc-chart-button",
                                                    color="secondary",
                                                    outline=True,
                                                    className="btn-sm",
                                                ),
                                            ],
                                        ),
                                    ],
                                    className="d-flex align-items-center justify-content-center mb-2",
                                ),
                            ],
                            md=4,
                            sm=12,
                        ),
                        
                        # Zeichenwerkzeuge
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Span("Werkzeuge: ", className="me-2 d-none d-md-inline"),
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button(
                                                    DashIconify(icon="mdi:chart-line-variant", width=20),
                                                    id="trendline-button",
                                                    color="secondary",
                                                    outline=True,
                                                    className="btn-sm",
                                                    title="Trendlinie",
                                                ),
                                                dbc.Button(
                                                    DashIconify(icon="mdi:minus", width=20),
                                                    id="horizontal-button",
                                                    color="secondary",
                                                    outline=True,
                                                    className="btn-sm",
                                                    title="Horizontale Linie",
                                                ),
                                                dbc.Button(
                                                    DashIconify(icon="mdi:rectangle-outline", width=20),
                                                    id="rectangle-button",
                                                    color="secondary",
                                                    outline=True,
                                                    className="btn-sm",
                                                    title="Rechteck",
                                                ),
                                                dbc.Button(
                                                    DashIconify(icon="mdi:chart-timeline-variant", width=20),
                                                    id="fibonacci-button",
                                                    color="secondary",
                                                    outline=True,
                                                    className="btn-sm",
                                                    title="Fibonacci",
                                                ),
                                                dbc.Button(
                                                    DashIconify(icon="mdi:eraser", width=20),
                                                    id="delete-drawing-button",
                                                    color="secondary",
                                                    outline=True,
                                                    className="btn-sm",
                                                    title="Löschen",
                                                ),
                                            ],
                                        ),
                                    ],
                                    className="d-flex align-items-center justify-content-end mb-2",
                                ),
                            ],
                            md=4,
                            sm=12,
                        ),
                    ],
                    className="g-2",
                ),
            ),
            dbc.CardBody(
                [
                    # Zeitrahmen-Buttons
                    html.Div(
                        id="timeframe-buttons-container",
                        className="mb-3",
                    ),
                    
                    # Chart
                    dcc.Graph(
                        id="price-chart",
                        figure={},
                        config={
                            "displayModeBar": True,
                            "scrollZoom": True,
                            "modeBarButtonsToRemove": [
                                "select2d",
                                "lasso2d",
                                "autoScale2d",
                                "resetScale2d",
                            ],
                            "displaylogo": False,
                        },
                        className="chart-container",
                        style={"height": "60vh"},
                    ),
                ]
            ),
        ],
        className="mb-4 shadow-lg rounded-xl",
    )

# Ergebniskarte
def create_results_card():
    return dbc.Card(
        [
            dbc.CardHeader("Strategie-Ergebnisse"),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H5("Gewinn/Verlust", className="card-title"),
                                            html.H3(
                                                [
                                                    html.Span(
                                                        "+2.450 €",
                                                        className="text-success",
                                                    ),
                                                    html.Span(
                                                        " (+4,9%)",
                                                        className="text-success fs-6 ms-2",
                                                    ),
                                                ],
                                                className="mb-0",
                                            ),
                                        ],
                                        className="text-center p-3 border rounded",
                                    ),
                                ],
                                md=4,
                                sm=12,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H5("Gewinnrate", className="card-title"),
                                            html.H3(
                                                "68%",
                                                className="text-primary mb-0",
                                            ),
                                        ],
                                        className="text-center p-3 border rounded",
                                    ),
                                ],
                                md=4,
                                sm=12,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H5("Trades", className="card-title"),
                                            html.H3(
                                                [
                                                    html.Span(
                                                        "25",
                                                        className="text-light",
                                                    ),
                                                    html.Span(
                                                        " (17 ✓ / 8 ✗)",
                                                        className="fs-6 ms-2 text-secondary",
                                                    ),
                                                ],
                                                className="mb-0",
                                            ),
                                        ],
                                        className="text-center p-3 border rounded",
                                    ),
                                ],
                                md=4,
                                sm=12,
                                className="mb-3",
                            ),
                        ],
                        className="g-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H5("Drawdown", className="card-title"),
                                            html.H3(
                                                "-1.250 € (-2,5%)",
                                                className="text-danger mb-0",
                                            ),
                                        ],
                                        className="text-center p-3 border rounded",
                                    ),
                                ],
                                md=4,
                                sm=12,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H5("Sharpe Ratio", className="card-title"),
                                            html.H3(
                                                "1.8",
                                                className="text-warning mb-0",
                                            ),
                                        ],
                                        className="text-center p-3 border rounded",
                                    ),
                                ],
                                md=4,
                                sm=12,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H5("Profit Factor", className="card-title"),
                                            html.H3(
                                                "2.3",
                                                className="text-success mb-0",
                                            ),
                                        ],
                                        className="text-center p-3 border rounded",
                                    ),
                                ],
                                md=4,
                                sm=12,
                                className="mb-3",
                            ),
                        ],
                        className="g-2",
                    ),
                ]
            ),
        ],
        className="mb-4 shadow-lg rounded-xl",
    )

# Trades-Karte
def create_trades_card():
    return dbc.Card(
        [
            dbc.CardHeader("Trade-Historie"),
            dbc.CardBody(
                [
                    dash_table.DataTable(
                        id="trades-table",
                        columns=[
                            {"name": "Datum", "id": "date"},
                            {"name": "Typ", "id": "type"},
                            {"name": "Preis", "id": "price"},
                            {"name": "Menge", "id": "quantity"},
                            {"name": "Gewinn/Verlust", "id": "pnl"},
                        ],
                        data=[
                            {
                                "date": "2023-12-15",
                                "type": "Kauf",
                                "price": "180,50 €",
                                "quantity": "10",
                                "pnl": "-",
                            },
                            {
                                "date": "2023-12-20",
                                "type": "Verkauf",
                                "price": "195,20 €",
                                "quantity": "10",
                                "pnl": "+147,00 €",
                            },
                            {
                                "date": "2023-12-22",
                                "type": "Kauf",
                                "price": "192,30 €",
                                "quantity": "15",
                                "pnl": "-",
                            },
                            {
                                "date": "2023-12-28",
                                "type": "Verkauf",
                                "price": "188,10 €",
                                "quantity": "15",
                                "pnl": "-63,00 €",
                            },
                            {
                                "date": "2024-01-05",
                                "type": "Kauf",
                                "price": "187,40 €",
                                "quantity": "20",
                                "pnl": "-",
                            },
                        ],
                        style_header={
                            "backgroundColor": colors["card"],
                            "color": colors["text"],
                            "fontWeight": "bold",
                            "border": f"1px solid {colors['grid']}",
                        },
                        style_cell={
                            "backgroundColor": colors["background"],
                            "color": colors["text"],
                            "border": f"1px solid {colors['grid']}",
                            "padding": "8px",
                            "textAlign": "center",
                        },
                        style_data_conditional=[
                            {
                                "if": {"column_id": "pnl", "filter_query": "{pnl} contains +"},
                                "color": colors["success"],
                                "fontWeight": "bold",
                            },
                            {
                                "if": {"column_id": "pnl", "filter_query": "{pnl} contains -"},
                                "color": colors["danger"],
                                "fontWeight": "bold",
                            },
                            {
                                "if": {"column_id": "type", "filter_query": "{type} = Kauf"},
                                "color": colors["primary"],
                            },
                            {
                                "if": {"column_id": "type", "filter_query": "{type} = Verkauf"},
                                "color": colors["warning"],
                            },
                        ],
                        page_size=5,
                    ),
                ]
            ),
        ],
        className="mb-4 shadow-lg rounded-xl",
    )

# Backtesting-Inhalt
def create_backtesting_content():
    return html.Div(
        [
            dbc.Card(
                [
                    dbc.CardHeader("Backtesting-Ergebnisse"),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H5("Strategie auswählen"),
                                            dbc.Select(
                                                id="backtest-strategy-select",
                                                options=[
                                                    {"label": "Moving Average Crossover", "value": "ma_crossover"},
                                                    {"label": "RSI Strategie", "value": "rsi"},
                                                    {"label": "MACD Strategie", "value": "macd"},
                                                    {"label": "Bollinger Bands", "value": "bollinger"},
                                                ],
                                                value="ma_crossover",
                                                className="mb-3",
                                            ),
                                            html.H5("Zeitraum"),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dbc.Input(
                                                            id="backtest-start-date",
                                                            type="date",
                                                            value="2023-01-01",
                                                        ),
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        dbc.Input(
                                                            id="backtest-end-date",
                                                            type="date",
                                                            value="2023-12-31",
                                                        ),
                                                        width=6,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            html.H5("Asset auswählen"),
                                            dcc.Dropdown(
                                                id="backtest-asset-select",
                                                options=[],
                                                placeholder="Asset auswählen",
                                                className="asset-dropdown mb-3",
                                            ),
                                            dbc.Button(
                                                "Backtest starten",
                                                id="run-backtest-button",
                                                color="primary",
                                                className="w-100 mb-3",
                                            ),
                                        ],
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.H5("Performance-Übersicht"),
                                            dcc.Graph(
                                                id="backtest-performance-chart",
                                                figure={},
                                                config={
                                                    "displayModeBar": False,
                                                },
                                                style={"height": "300px"},
                                            ),
                                            html.H5("Metriken", className="mt-3"),
                                            dash_table.DataTable(
                                                id="backtest-metrics-table",
                                                columns=[
                                                    {"name": "Metrik", "id": "metric"},
                                                    {"name": "Wert", "id": "value"},
                                                ],
                                                data=[
                                                    {"metric": "Gesamtrendite", "value": "12,5%"},
                                                    {"metric": "Jährliche Rendite", "value": "8,2%"},
                                                    {"metric": "Sharpe Ratio", "value": "1,8"},
                                                    {"metric": "Max. Drawdown", "value": "-5,3%"},
                                                    {"metric": "Gewinnrate", "value": "68%"},
                                                    {"metric": "Profit Factor", "value": "2,3"},
                                                ],
                                                style_header={
                                                    "backgroundColor": colors["card"],
                                                    "color": colors["text"],
                                                    "fontWeight": "bold",
                                                    "border": f"1px solid {colors['grid']}",
                                                },
                                                style_cell={
                                                    "backgroundColor": colors["background"],
                                                    "color": colors["text"],
                                                    "border": f"1px solid {colors['grid']}",
                                                    "padding": "8px",
                                                },
                                            ),
                                        ],
                                        md=8,
                                    ),
                                ],
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-lg rounded-xl",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Backtest-Historie"),
                    dbc.CardBody(
                        [
                            dash_table.DataTable(
                                id="backtest-history-table",
                                columns=[
                                    {"name": "Datum", "id": "date"},
                                    {"name": "Asset", "id": "asset"},
                                    {"name": "Strategie", "id": "strategy"},
                                    {"name": "Zeitraum", "id": "period"},
                                    {"name": "Rendite", "id": "return"},
                                    {"name": "Sharpe", "id": "sharpe"},
                                    {"name": "Aktionen", "id": "actions"},
                                ],
                                data=[
                                    {
                                        "date": "2024-01-15",
                                        "asset": "AAPL",
                                        "strategy": "MA Crossover",
                                        "period": "2023-01-01 bis 2023-12-31",
                                        "return": "+12,5%",
                                        "sharpe": "1,8",
                                        "actions": "Details",
                                    },
                                    {
                                        "date": "2024-01-10",
                                        "asset": "MSFT",
                                        "strategy": "RSI",
                                        "period": "2023-01-01 bis 2023-12-31",
                                        "return": "+8,3%",
                                        "sharpe": "1,5",
                                        "actions": "Details",
                                    },
                                    {
                                        "date": "2024-01-05",
                                        "asset": "GOOGL",
                                        "strategy": "MACD",
                                        "period": "2023-01-01 bis 2023-12-31",
                                        "return": "+15,7%",
                                        "sharpe": "2,1",
                                        "actions": "Details",
                                    },
                                ],
                                style_header={
                                    "backgroundColor": colors["card"],
                                    "color": colors["text"],
                                    "fontWeight": "bold",
                                    "border": f"1px solid {colors['grid']}",
                                },
                                style_cell={
                                    "backgroundColor": colors["background"],
                                    "color": colors["text"],
                                    "border": f"1px solid {colors['grid']}",
                                    "padding": "8px",
                                    "textAlign": "center",
                                },
                                style_data_conditional=[
                                    {
                                        "if": {"column_id": "return", "filter_query": "{return} contains +"},
                                        "color": colors["success"],
                                        "fontWeight": "bold",
                                    },
                                    {
                                        "if": {"column_id": "return", "filter_query": "{return} contains -"},
                                        "color": colors["danger"],
                                        "fontWeight": "bold",
                                    },
                                    {
                                        "if": {"column_id": "actions"},
                                        "color": colors["primary"],
                                        "cursor": "pointer",
                                        "textDecoration": "underline",
                                    },
                                ],
                                page_size=10,
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-lg rounded-xl",
            ),
        ]
    )

# Einstellungen-Inhalt
def create_settings_content():
    return html.Div(
        [
            dbc.Card(
                [
                    dbc.CardHeader("Allgemeine Einstellungen"),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H5("Darstellung"),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Farbschema"),
                                                    dbc.Select(
                                                        id="color-theme-select",
                                                        options=[
                                                            {"label": "Dunkel", "value": "dark"},
                                                            {"label": "Hell", "value": "light"},
                                                        ],
                                                        value="dark",
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Chart-Standardtyp"),
                                                    dbc.Select(
                                                        id="default-chart-type-select",
                                                        options=[
                                                            {"label": "Linie", "value": "line"},
                                                            {"label": "Candlestick", "value": "candlestick"},
                                                            {"label": "OHLC", "value": "ohlc"},
                                                        ],
                                                        value="candlestick",
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Standard-Zeitrahmen"),
                                                    dbc.Select(
                                                        id="default-timeframe-select",
                                                        options=[
                                                            {"label": "1 Minute", "value": "1m"},
                                                            {"label": "2 Minuten", "value": "2m"},
                                                            {"label": "5 Minuten", "value": "5m"},
                                                            {"label": "15 Minuten", "value": "15m"},
                                                            {"label": "30 Minuten", "value": "30m"},
                                                            {"label": "1 Stunde", "value": "1h"},
                                                            {"label": "1 Tag", "value": "1d"},
                                                            {"label": "1 Woche", "value": "1w"},
                                                            {"label": "1 Monat", "value": "1mo"},
                                                        ],
                                                        value="1d",
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                        ],
                                        md=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.H5("Backtesting"),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Anfangskapital"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="initial-capital-input",
                                                                type="number",
                                                                value=50000,
                                                                min=1000,
                                                                step=1000,
                                                            ),
                                                            dbc.InputGroupText("€"),
                                                        ],
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Kommission pro Trade"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="commission-input",
                                                                type="number",
                                                                value=0.1,
                                                                min=0,
                                                                max=5,
                                                                step=0.01,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ],
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Slippage"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="slippage-input",
                                                                type="number",
                                                                value=0.05,
                                                                min=0,
                                                                max=1,
                                                                step=0.01,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ],
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                        ],
                                        md=6,
                                    ),
                                ],
                            ),
                            dbc.Button(
                                "Einstellungen speichern",
                                id="save-settings-button",
                                color="primary",
                                className="mt-3",
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-lg rounded-xl",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Datenquellen"),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H5("API-Einstellungen"),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Primäre Datenquelle"),
                                                    dbc.Select(
                                                        id="primary-data-source-select",
                                                        options=[
                                                            {"label": "Yahoo Finance", "value": "yahoo"},
                                                            {"label": "Alpha Vantage", "value": "alphavantage"},
                                                            {"label": "Twelve Data", "value": "twelvedata"},
                                                        ],
                                                        value="yahoo",
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("API-Schlüssel (falls erforderlich)"),
                                                    dbc.Input(
                                                        id="api-key-input",
                                                        type="password",
                                                        placeholder="API-Schlüssel eingeben",
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                        ],
                                        md=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.H5("Cache-Einstellungen"),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Cache verwenden"),
                                                    dbc.Checklist(
                                                        options=[
                                                            {"label": "Daten-Cache aktivieren", "value": 1},
                                                        ],
                                                        value=[1],
                                                        id="use-cache-checkbox",
                                                        switch=True,
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Cache-Dauer für Tagesdaten"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="daily-cache-duration-input",
                                                                type="number",
                                                                value=1,
                                                                min=1,
                                                                max=30,
                                                            ),
                                                            dbc.InputGroupText("Tage"),
                                                        ],
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Cache-Dauer für Intraday-Daten"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="intraday-cache-duration-input",
                                                                type="number",
                                                                value=1,
                                                                min=1,
                                                                max=24,
                                                            ),
                                                            dbc.InputGroupText("Stunden"),
                                                        ],
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            dbc.Button(
                                                "Cache leeren",
                                                id="clear-cache-button",
                                                color="danger",
                                                outline=True,
                                                className="mt-3",
                                            ),
                                        ],
                                        md=6,
                                    ),
                                ],
                            ),
                            dbc.Button(
                                "Datenquellen-Einstellungen speichern",
                                id="save-data-settings-button",
                                color="primary",
                                className="mt-3",
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-lg rounded-xl",
            ),
        ]
    )
