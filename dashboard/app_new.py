"""
Hauptskript für das Trading Dashboard mit Tab-Navigation
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import StringIO

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template, ThemeChangerAIO
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Importiere Komponenten
from dashboard.components import (
    create_header,
    create_strategy_sidebar,
    create_chart_card,
    create_results_card,
    create_trades_card,
    create_backtesting_content,
    create_settings_content,
    colors
)

# Lade das dunkle Template für Plotly
load_figure_template("darkly")

# Initialisiere die Dash-App
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

# Setze den Titel der App
app.title = "Trading Dashboard Pro"

# Chart-Stil-Konfiguration
chart_style = {
    'layout': {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': colors['text']},
        'xaxis': {
            'gridcolor': colors['grid'],
            'showgrid': True,
            'zeroline': False,
            'showline': False,
        },
        'yaxis': {
            'gridcolor': colors['grid'],
            'showgrid': True,
            'zeroline': False,
            'showline': False,
        },
        'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
        'hovermode': 'closest',
        'showlegend': True,
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1,
            'font': {'color': colors['text']},
        },
    }
}

# Erstelle die Komponenten
header = create_header()
strategy_sidebar = create_strategy_sidebar()
chart_card = create_chart_card()
results_card = create_results_card()
trades_card = create_trades_card()
backtesting_content = create_backtesting_content()
settings_content = create_settings_content()

# Definiere die Inhalte für jeden Tab
strategien_content = html.Div(
    [
        dbc.Row(
            [
                # Linke Spalte mit Sidebar
                dbc.Col(
                    [
                        strategy_sidebar,
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
    ]
)

backtesting_content_div = html.Div(
    [
        backtesting_content,
    ]
)

settings_content_div = html.Div(
    [
        settings_content,
    ]
)

# Definiere das Layout der App
app.layout = html.Div(
    [
        # Versteckte Div-Elemente für Datenspeicherung
        dcc.Store(id="stock-data-store"),
        dcc.Store(id="backtest-results-store"),
        dcc.Store(id="active-timeframe-store", data="1d"),  # Standardmäßig 1 Tag
        dcc.Store(id="active-tab-store", data="strategien"),  # Speichert den aktiven Tab

        # URL-Routing
        dcc.Location(id="url", refresh=False),

        # Header mit Tab-Navigation
        header,

        # Hauptinhalt
        dbc.Container(
            [
                # Bereich für Tab-Inhalte
                html.Div(id="page-content", className="tab-content"),
            ],
            fluid=True,
            className="mt-4",
        ),
    ],
    style={
        "backgroundColor": colors['background'],
        "color": colors['text'],
        "minHeight": "100vh",
    },
)

# Callback für URL-Routing und Tab-Navigation
@callback(
    Output("page-content", "children"),
    Output("tab-strategien", "active"),
    Output("tab-backtesting", "active"),
    Output("tab-einstellung", "active"),
    Output("active-tab-store", "data"),
    Input("url", "pathname"),
    State("active-tab-store", "data"),
)
def display_page(pathname, active_tab):
    """
    Zeigt den entsprechenden Inhalt basierend auf der URL an und aktualisiert die aktiven Tab-Status.
    """
    if pathname == "/" or pathname == "/strategien":
        return strategien_content, True, False, False, "strategien"
    elif pathname == "/backtesting":
        return backtesting_content_div, False, True, False, "backtesting"
    elif pathname == "/einstellung":
        return settings_content_div, False, False, True, "einstellung"
    else:
        # Fallback für unbekannte URLs
        return strategien_content, True, False, False, "strategien"

# Callback für Chart-Typ-Buttons
@callback(
    Output("line-chart-button", "color"),
    Output("line-chart-button", "outline"),
    Output("candlestick-chart-button", "color"),
    Output("candlestick-chart-button", "outline"),
    Output("ohlc-chart-button", "color"),
    Output("ohlc-chart-button", "outline"),
    Input("line-chart-button", "n_clicks"),
    Input("candlestick-chart-button", "n_clicks"),
    Input("ohlc-chart-button", "n_clicks"),
)
def update_chart_type_buttons(line_clicks, candlestick_clicks, ohlc_clicks):
    """
    Aktualisiert die Farben der Chart-Typ-Buttons basierend auf dem ausgewählten Typ.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        # Standardmäßig ist Candlestick ausgewählt
        return "secondary", True, "primary", False, "secondary", True
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "line-chart-button":
        return "primary", False, "secondary", True, "secondary", True
    elif button_id == "candlestick-chart-button":
        return "secondary", True, "primary", False, "secondary", True
    elif button_id == "ohlc-chart-button":
        return "secondary", True, "secondary", True, "primary", False
    
    # Fallback
    return "secondary", True, "primary", False, "secondary", True

# Callback für Zeitrahmen-Buttons
@callback(
    Output("timeframe-1h-button", "color"),
    Output("timeframe-1h-button", "outline"),
    Output("timeframe-1d-button", "color"),
    Output("timeframe-1d-button", "outline"),
    Output("timeframe-1w-button", "color"),
    Output("timeframe-1w-button", "outline"),
    Output("active-timeframe-store", "data"),
    Input("timeframe-1h-button", "n_clicks"),
    Input("timeframe-1d-button", "n_clicks"),
    Input("timeframe-1w-button", "n_clicks"),
    State("active-timeframe-store", "data"),
)
def update_timeframe_buttons(h1_clicks, d1_clicks, w1_clicks, active_timeframe):
    """
    Aktualisiert die Farben der Zeitrahmen-Buttons basierend auf dem ausgewählten Zeitrahmen.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        # Standardmäßig ist 1D ausgewählt
        return "secondary", True, "primary", False, "secondary", True, "1d"
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "timeframe-1h-button":
        return "primary", False, "secondary", True, "secondary", True, "1h"
    elif button_id == "timeframe-1d-button":
        return "secondary", True, "primary", False, "secondary", True, "1d"
    elif button_id == "timeframe-1w-button":
        return "secondary", True, "secondary", True, "primary", False, "1w"
    
    # Fallback
    return "secondary", True, "primary", False, "secondary", True, active_timeframe

# Callback für Preischart
@callback(
    Output("price-chart", "figure"),
    Input("asset-select", "value"),
    Input("line-chart-button", "color"),
    Input("candlestick-chart-button", "color"),
    Input("ohlc-chart-button", "color"),
    Input("active-timeframe-store", "data"),
)
def update_price_chart(symbol, line_color, candlestick_color, ohlc_color, timeframe):
    """
    Aktualisiert den Preischart basierend auf dem ausgewählten Symbol, Chart-Typ und Zeitrahmen.
    """
    if not symbol:
        # Wenn kein Symbol ausgewählt ist, zeige einen leeren Chart
        fig = go.Figure()
        fig.update_layout(**chart_style['layout'])
        fig.add_annotation(
            text="Bitte wählen Sie ein Asset aus",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color=colors['text'])
        )
        return fig
    
    # Bestimme den Chart-Typ basierend auf den Button-Farben
    chart_type = "candlestick"  # Standard
    if line_color == "primary":
        chart_type = "line"
    elif candlestick_color == "primary":
        chart_type = "candlestick"
    elif ohlc_color == "primary":
        chart_type = "ohlc"
    
    # Bestimme den Zeitrahmen
    if timeframe == "1h":
        interval = "1h"
        days_back = 7
    elif timeframe == "1d":
        interval = "1d"
        days_back = 180
    elif timeframe == "1w":
        interval = "1wk"
        days_back = 365 * 2
    else:
        interval = "1d"
        days_back = 180
    
    # Generiere Beispieldaten für den Chart
    # In einer realen Anwendung würden hier Daten von einer API abgerufen werden
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Generiere Datenpunkte basierend auf dem Zeitrahmen
    if interval == "1h":
        periods = days_back * 24
        freq = "H"
    elif interval == "1d":
        periods = days_back
        freq = "D"
    elif interval == "1wk":
        periods = days_back // 7
        freq = "W"
    
    # Generiere Beispieldaten
    np.random.seed(42)  # Für reproduzierbare Ergebnisse
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    # Startpreis
    if symbol == "AAPL":
        base_price = 180
    elif symbol == "MSFT":
        base_price = 350
    elif symbol == "GOOGL":
        base_price = 140
    elif symbol == "AMZN":
        base_price = 170
    elif symbol == "TSLA":
        base_price = 200
    else:
        base_price = 100
    
    # Generiere OHLC-Daten
    volatility = 0.02
    price_data = []
    current_price = base_price
    
    for i in range(len(date_range)):
        # Zufällige Preisbewegung mit Trend
        daily_return = np.random.normal(0.0003, volatility)
        current_price *= (1 + daily_return)
        
        # Generiere OHLC-Daten
        high_low_range = current_price * volatility * 2
        open_price = current_price * (1 + np.random.normal(0, 0.003))
        close_price = current_price
        high_price = max(open_price, close_price) + abs(np.random.normal(0, high_low_range/2))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, high_low_range/2))
        
        price_data.append({
            'date': date_range[i],
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': np.random.randint(1000000, 10000000)
        })
    
    df = pd.DataFrame(price_data)
    
    # Erstelle den Chart basierend auf dem ausgewählten Typ
    fig = go.Figure()
    
    if chart_type == "line":
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['close'],
                mode='lines',
                name=symbol,
                line=dict(color=colors['primary'], width=2),
            )
        )
    elif chart_type == "candlestick":
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=symbol,
                increasing_line_color=colors['success'],
                decreasing_line_color=colors['danger'],
            )
        )
    elif chart_type == "ohlc":
        fig.add_trace(
            go.Ohlc(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=symbol,
                increasing_line_color=colors['success'],
                decreasing_line_color=colors['danger'],
            )
        )
    
    # Füge Volumen als Subplot hinzu
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume',
            marker=dict(color=colors['secondary'], opacity=0.3),
            yaxis="y2",
            showlegend=False,
        )
    )
    
    # Layout-Anpassungen
    layout_params = chart_style['layout'].copy()  # Kopiere das Style-Dictionary
    if 'legend' in layout_params:
        # Entferne das legend dictionary aus den layout_params
        layout_params.pop('legend')
    
    fig.update_layout(
        **layout_params,
        title=f"{symbol} - {timeframe}",
        yaxis=dict(
            title="Preis",
            side="right",
            showgrid=True,
            gridcolor=colors['grid'],
            zeroline=False,
        ),
        yaxis2=dict(
            title="Volumen",
            side="right",
            showgrid=False,
            zeroline=False,
            overlaying="y",
            anchor="x",
            visible=False,
            range=[0, df['volume'].max() * 5],
            domain=[0, 0.2],
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type="date",
            showgrid=True,
            gridcolor=colors['grid'],
            zeroline=False,
        ),
        dragmode="pan",  # Ermöglicht Verschieben per Drag
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=colors['text']),
        ),
    )
    
    return fig

# Callback für Strategie-Parameter
@callback(
    Output("strategy-params", "children"),
    Input("strategy-select", "value"),
)
def update_strategy_params(strategy):
    """
    Aktualisiert die Strategie-Parameter basierend auf der ausgewählten Strategie.
    """
    if strategy == "ma_crossover":
        return html.Div(
            [
                html.Label("MA1 Periode", className="form-label"),
                dbc.Input(
                    id="ma1-input",
                    type="number",
                    value=20,
                    min=1,
                    max=200,
                    className="mb-2",
                ),
                html.Label("MA2 Periode", className="form-label"),
                dbc.Input(
                    id="ma2-input",
                    type="number",
                    value=50,
                    min=1,
                    max=200,
                    className="mb-2",
                ),
            ]
        )
    elif strategy == "rsi":
        return html.Div(
            [
                html.Label("RSI Periode", className="form-label"),
                dbc.Input(
                    id="rsi-period-input",
                    type="number",
                    value=14,
                    min=1,
                    max=50,
                    className="mb-2",
                ),
                html.Label("Überkauft Niveau", className="form-label"),
                dbc.Input(
                    id="rsi-overbought-input",
                    type="number",
                    value=70,
                    min=50,
                    max=90,
                    className="mb-2",
                ),
                html.Label("Überverkauft Niveau", className="form-label"),
                dbc.Input(
                    id="rsi-oversold-input",
                    type="number",
                    value=30,
                    min=10,
                    max=50,
                    className="mb-2",
                ),
            ]
        )
    elif strategy == "macd":
        return html.Div(
            [
                html.Label("Schneller EMA", className="form-label"),
                dbc.Input(
                    id="macd-fast-input",
                    type="number",
                    value=12,
                    min=1,
                    max=50,
                    className="mb-2",
                ),
                html.Label("Langsamer EMA", className="form-label"),
                dbc.Input(
                    id="macd-slow-input",
                    type="number",
                    value=26,
                    min=1,
                    max=100,
                    className="mb-2",
                ),
                html.Label("Signal EMA", className="form-label"),
                dbc.Input(
                    id="macd-signal-input",
                    type="number",
                    value=9,
                    min=1,
                    max=50,
                    className="mb-2",
                ),
            ]
        )
    elif strategy == "bollinger":
        return html.Div(
            [
                html.Label("Periode", className="form-label"),
                dbc.Input(
                    id="bollinger-period-input",
                    type="number",
                    value=20,
                    min=1,
                    max=100,
                    className="mb-2",
                ),
                html.Label("Standardabweichungen", className="form-label"),
                dbc.Input(
                    id="bollinger-std-input",
                    type="number",
                    value=2,
                    min=0.5,
                    max=4,
                    step=0.1,
                    className="mb-2",
                ),
            ]
        )
    else:
        return html.Div("Keine Parameter verfügbar")

# Callback für Trades-Tabelle
@callback(
    Output("trades-table-container", "children"),
    Input("run-strategy-button", "n_clicks"),
)
def update_trades_table(n_clicks):
    """
    Aktualisiert die Trades-Tabelle nach dem Ausführen einer Strategie.
    """
    if n_clicks is None:
        # Zeige eine leere Tabelle, wenn noch keine Strategie ausgeführt wurde
        return dash_table.DataTable(
            id="trades-table",
            columns=[
                {"name": "Datum", "id": "date"},
                {"name": "Typ", "id": "type"},
                {"name": "Preis", "id": "price"},
                {"name": "Menge", "id": "quantity"},
                {"name": "Gewinn/Verlust", "id": "pnl"},
            ],
            data=[],
            style_header={
                "backgroundColor": colors['card'],
                "color": colors['text'],
                "fontWeight": "bold",
                "border": f"1px solid {colors['grid']}",
            },
            style_cell={
                "backgroundColor": colors['background'],
                "color": colors['text'],
                "border": f"1px solid {colors['grid']}",
                "padding": "10px",
                "textAlign": "left",
            },
            style_data_conditional=[
                {
                    "if": {"filter_query": "{type} = 'Kauf'"},
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                },
                {
                    "if": {"filter_query": "{type} = 'Verkauf'"},
                    "backgroundColor": "rgba(239, 68, 68, 0.1)",
                },
                {
                    "if": {"filter_query": "{pnl} contains '+'"},
                    "color": colors['success'],
                },
                {
                    "if": {"filter_query": "{pnl} contains '-'"},
                    "color": colors['danger'],
                },
            ],
            page_size=5,
        )
    
    # Generiere Beispiel-Trades
    np.random.seed(42)  # Für reproduzierbare Ergebnisse
    
    trades = []
    current_date = datetime.now() - timedelta(days=180)
    
    for i in range(25):
        # Zufälliges Datum innerhalb der letzten 180 Tage
        trade_date = current_date + timedelta(days=np.random.randint(1, 7))
        current_date = trade_date
        
        # Zufälliger Trade-Typ
        trade_type = "Kauf" if i % 2 == 0 else "Verkauf"
        
        # Zufälliger Preis
        price = np.random.uniform(150, 200)
        
        # Zufällige Menge
        quantity = np.random.randint(1, 10) * 10
        
        # Zufälliger Gewinn/Verlust (nur für Verkäufe)
        pnl = ""
        if trade_type == "Verkauf":
            pnl_value = np.random.normal(100, 300)
            pnl = f"+{pnl_value:.2f} €" if pnl_value >= 0 else f"{pnl_value:.2f} €"
        
        trades.append({
            "date": trade_date.strftime("%d.%m.%Y %H:%M"),
            "type": trade_type,
            "price": f"{price:.2f} €",
            "quantity": quantity,
            "pnl": pnl,
        })
    
    # Sortiere Trades nach Datum (neueste zuerst)
    trades.sort(key=lambda x: datetime.strptime(x["date"], "%d.%m.%Y %H:%M"), reverse=True)
    
    return dash_table.DataTable(
        id="trades-table",
        columns=[
            {"name": "Datum", "id": "date"},
            {"name": "Typ", "id": "type"},
            {"name": "Preis", "id": "price"},
            {"name": "Menge", "id": "quantity"},
            {"name": "Gewinn/Verlust", "id": "pnl"},
        ],
        data=trades,
        style_header={
            "backgroundColor": colors['card'],
            "color": colors['text'],
            "fontWeight": "bold",
            "border": f"1px solid {colors['grid']}",
        },
        style_cell={
            "backgroundColor": colors['background'],
            "color": colors['text'],
            "border": f"1px solid {colors['grid']}",
            "padding": "10px",
            "textAlign": "left",
        },
        style_data_conditional=[
            {
                "if": {"filter_query": "{type} = 'Kauf'"},
                "backgroundColor": "rgba(16, 185, 129, 0.1)",
            },
            {
                "if": {"filter_query": "{type} = 'Verkauf'"},
                "backgroundColor": "rgba(239, 68, 68, 0.1)",
            },
            {
                "if": {"filter_query": "{pnl} contains '+'"},
                "color": colors['success'],
            },
            {
                "if": {"filter_query": "{pnl} contains '-'"},
                "color": colors['danger'],
            },
        ],
        page_size=5,
    )

# Wenn dieses Skript direkt ausgeführt wird
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
