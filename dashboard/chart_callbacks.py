"""
Verbesserte Chart-Callbacks mit Fehlerbehandlung
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash
from dash import html, dcc, callback, Input, Output, State
from dash.exceptions import PreventUpdate
import logging

# Importiere Fehlerbehandlung
from dashboard.error_handler import ErrorHandler

# Importiere Chart-Utilities
from dashboard.chart_utils import (
    generate_mock_data,
    create_interactive_chart,
    get_available_assets,
    get_available_timeframes
)

# Logger konfigurieren
logger = logging.getLogger("trading_dashboard.chart_callbacks")

@callback(
    Output("price-chart", "figure"),
    Input("asset-select", "value"),
    Input("line-chart-button", "n_clicks"),
    Input("candlestick-chart-button", "n_clicks"),
    Input("ohlc-chart-button", "n_clicks"),
    Input("active-timeframe-store", "data"),
    Input("drawing-data-store", "data"),
)
def update_interactive_chart(asset, line_clicks, candlestick_clicks, ohlc_clicks, timeframe, drawing_data):
    """
    Aktualisiert den Preischart basierend auf dem ausgewählten Asset, Chart-Typ und Zeitrahmen.
    """
    try:
        # Wenn kein Asset ausgewählt ist, zeige einen leeren Chart
        if not asset:
            raise PreventUpdate
        
        # Bestimme den Chart-Typ basierend auf den Button-Klicks
        ctx = dash.callback_context
        if not ctx.triggered:
            chart_type = "candlestick"  # Standard
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "line-chart-button":
                chart_type = "line"
            elif button_id == "candlestick-chart-button":
                chart_type = "candlestick"
            elif button_id == "ohlc-chart-button":
                chart_type = "ohlc"
            elif button_id == "asset-select" or button_id == "active-timeframe-store":
                # Wenn Asset oder Zeitrahmen geändert wurde, behalte den aktuellen Chart-Typ bei
                # Bestimme den aktuellen Chart-Typ anhand der Button-Farben
                if line_clicks and candlestick_clicks and ohlc_clicks:
                    # Wenn alle Buttons geklickt wurden, verwende den zuletzt geklickten
                    max_clicks = max(line_clicks or 0, candlestick_clicks or 0, ohlc_clicks or 0)
                    if max_clicks == (line_clicks or 0):
                        chart_type = "line"
                    elif max_clicks == (candlestick_clicks or 0):
                        chart_type = "candlestick"
                    else:
                        chart_type = "ohlc"
                else:
                    # Standard: Candlestick
                    chart_type = "candlestick"
            else:
                chart_type = "candlestick"  # Fallback
        
        # Generiere Daten für das ausgewählte Asset und den Zeitrahmen
        try:
            logger.info(f"Generiere Daten für {asset} mit Zeitrahmen {timeframe}")
            df = generate_mock_data(asset, timeframe)
            
            if df is None or df.empty:
                logger.warning(f"Keine Daten für {asset} mit Zeitrahmen {timeframe}")
                error_info = {
                    "type": "no_data",
                    "message": "Keine Daten verfügbar",
                    "user_action": "Für das ausgewählte Asset und den Zeitraum sind keine Daten verfügbar. Bitte wählen Sie einen anderen Zeitraum oder ein anderes Asset.",
                    "fallback_available": False
                }
                
                # Erstelle leeren Chart mit Fehlermeldung
                fig = go.Figure()
                fig.add_annotation(
                    text=ErrorHandler.create_error_message(error_info),
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(color="#EF4444", size=14)
                )
                return fig
            
            # Erstelle den interaktiven Chart
            fig = create_interactive_chart(df, asset, chart_type, timeframe, drawing_data)
            return fig
            
        except Exception as e:
            logger.error(f"Fehler beim Generieren der Daten: {str(e)}")
            error_info = ErrorHandler.handle_data_error(e, f"Datenabruf für {asset}")
            
            # Erstelle Chart mit Fehlermeldung
            fig = go.Figure()
            fig.add_annotation(
                text=ErrorHandler.create_error_message(error_info),
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(color="#EF4444", size=14)
            )
            
            # Wenn Fallback verfügbar ist, versuche Fallback-Daten zu verwenden
            if error_info.get("fallback_available", False):
                try:
                    # Bestimme Asset-Typ für Fallback-Daten
                    if "BTC" in asset or "ETH" in asset:
                        asset_type = "Krypto"
                    elif "USD" in asset or "JPY" in asset or "EUR" in asset or "GBP" in asset:
                        asset_type = "Forex"
                    elif "NQ" in asset:
                        asset_type = "Futures"
                    else:
                        asset_type = "Aktien"
                    
                    fallback_df = ErrorHandler.get_fallback_data(asset_type, timeframe)
                    if not fallback_df.empty:
                        fig = create_interactive_chart(fallback_df, asset, chart_type, timeframe, drawing_data)
                        
                        # Füge Hinweis hinzu, dass Fallback-Daten verwendet werden
                        fig.add_annotation(
                            text="⚠️ Fallback-Daten werden angezeigt",
                            xref="paper", yref="paper",
                            x=0.5, y=0.99,
                            showarrow=False,
                            font=dict(color="#F59E0B", size=12)
                        )
                except Exception as fallback_error:
                    logger.error(f"Fehler beim Laden der Fallback-Daten: {str(fallback_error)}")
            
            return fig
    
    except Exception as e:
        logger.error(f"Unerwarteter Fehler im Chart-Callback: {str(e)}")
        
        # Erstelle Chart mit Fehlermeldung
        fig = go.Figure()
        fig.add_annotation(
            text=f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#EF4444", size=14)
        )
        return fig

@callback(
    Output("trendline-button", "color"),
    Output("trendline-button", "outline"),
    Output("horizontal-button", "color"),
    Output("horizontal-button", "outline"),
    Output("rectangle-button", "color"),
    Output("rectangle-button", "outline"),
    Output("fibonacci-button", "color"),
    Output("fibonacci-button", "outline"),
    Output("delete-drawing-button", "color"),
    Output("delete-drawing-button", "outline"),
    Output("active-drawing-tool-store", "data"),
    Input("trendline-button", "n_clicks"),
    Input("horizontal-button", "n_clicks"),
    Input("rectangle-button", "n_clicks"),
    Input("fibonacci-button", "n_clicks"),
    Input("delete-drawing-button", "n_clicks"),
    State("active-drawing-tool-store", "data"),
)
def update_drawing_tool_buttons(trendline_clicks, horizontal_clicks, rectangle_clicks, fibonacci_clicks, delete_clicks, active_tool):
    """
    Aktualisiert die Farben der Zeichenwerkzeug-Buttons basierend auf dem ausgewählten Werkzeug.
    """
    try:
        ctx = dash.callback_context
        if not ctx.triggered:
            # Standardmäßig ist kein Werkzeug ausgewählt
            return "secondary", True, "secondary", True, "secondary", True, "secondary", True, "secondary", True, None
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Setze alle Buttons auf inaktiv
        trendline_color, trendline_outline = "secondary", True
        horizontal_color, horizontal_outline = "secondary", True
        rectangle_color, rectangle_outline = "secondary", True
        fibonacci_color, fibonacci_outline = "secondary", True
        delete_color, delete_outline = "secondary", True
        new_active_tool = None
        
        # Aktiviere den geklickten Button
        if button_id == "trendline-button":
            if active_tool == "trendline":
                # Wenn bereits aktiv, deaktiviere
                pass
            else:
                trendline_color, trendline_outline = "primary", False
                new_active_tool = "trendline"
        elif button_id == "horizontal-button":
            if active_tool == "horizontal":
                # Wenn bereits aktiv, deaktiviere
                pass
            else:
                horizontal_color, horizontal_outline = "primary", False
                new_active_tool = "horizontal"
        elif button_id == "rectangle-button":
            if active_tool == "rectangle":
                # Wenn bereits aktiv, deaktiviere
                pass
            else:
                rectangle_color, rectangle_outline = "primary", False
                new_active_tool = "rectangle"
        elif button_id == "fibonacci-button":
            if active_tool == "fibonacci":
                # Wenn bereits aktiv, deaktiviere
                pass
            else:
                fibonacci_color, fibonacci_outline = "primary", False
                new_active_tool = "fibonacci"
        elif button_id == "delete-drawing-button":
            delete_color, delete_outline = "danger", False
            new_active_tool = "delete"
        
        return trendline_color, trendline_outline, horizontal_color, horizontal_outline, rectangle_color, rectangle_outline, fibonacci_color, fibonacci_outline, delete_color, delete_outline, new_active_tool
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Zeichenwerkzeug-Buttons: {str(e)}")
        # Fallback: Alle Buttons inaktiv
        return "secondary", True, "secondary", True, "secondary", True, "secondary", True, "secondary", True, None

@callback(
    Output("asset-select", "options"),
    Input("asset-search", "value"),
)
def update_asset_options(search_value):
    """
    Aktualisiert die Asset-Optionen basierend auf dem Suchbegriff.
    """
    try:
        all_assets = get_available_assets()
        
        if not search_value:
            return all_assets
        
        # Filtere Assets basierend auf dem Suchbegriff
        search_value = search_value.lower()
        filtered_assets = [
            asset for asset in all_assets
            if search_value in asset["label"].lower() or search_value in asset["value"].lower()
        ]
        
        return filtered_assets
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Asset-Optionen: {str(e)}")
        # Fallback: Alle Assets
        return get_available_assets()

@callback(
    Output("timeframe-buttons-container", "children"),
    Output("active-timeframe-store", "data", allow_duplicate=True),
    Input("url", "pathname"),
    State("active-timeframe-store", "data"),
)
def update_timeframe_buttons(pathname, active_timeframe):
    """
    Aktualisiert die Zeitrahmen-Buttons basierend auf den verfügbaren Zeitrahmen.
    """
    try:
        timeframes = get_available_timeframes()
        
        # Gruppiere Zeitrahmen nach Gruppe
        grouped_timeframes = {}
        for tf in timeframes:
            group = tf["group"]
            if group not in grouped_timeframes:
                grouped_timeframes[group] = []
            grouped_timeframes[group].append(tf)
        
        # Erstelle Buttons für jeden Zeitrahmen
        button_groups = []
        
        for group, tfs in grouped_timeframes.items():
            buttons = []
            for tf in tfs:
                # Bestimme, ob der Button aktiv ist
                is_active = tf["value"] == active_timeframe
                
                buttons.append(
                    html.Button(
                        tf["label"],
                        id={"type": "timeframe-button", "index": tf["value"]},
                        className=f"btn {'btn-primary' if is_active else 'btn-outline-secondary'} btn-sm mx-1",
                        style={"minWidth": "40px"}
                    )
                )
            
            # Erstelle eine Button-Gruppe für diese Kategorie
            button_group = html.Div(
                [
                    html.Span(f"{group}: ", className="text-muted me-2 d-none d-md-inline"),
                    html.Div(buttons, className="d-flex flex-wrap")
                ],
                className="d-flex align-items-center mb-2"
            )
            
            button_groups.append(button_group)
        
        return html.Div(button_groups, className="timeframe-buttons"), active_timeframe
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Zeitrahmen-Buttons: {str(e)}")
        # Fallback: Standard-Zeitrahmen-Buttons
        return html.Div([
            html.Button("1h", id="timeframe-1h-button", className="btn btn-outline-secondary btn-sm mx-1"),
            html.Button("1d", id="timeframe-1d-button", className="btn btn-primary btn-sm mx-1"),
            html.Button("1w", id="timeframe-1w-button", className="btn btn-outline-secondary btn-sm mx-1"),
        ]), active_timeframe

@callback(
    Output("active-timeframe-store", "data", allow_duplicate=True),
    Input({"type": "timeframe-button", "index": dash.ALL}, "n_clicks"),
    State("active-timeframe-store", "data"),
    prevent_initial_call=True
)
def handle_timeframe_button_click(n_clicks_list, active_timeframe):
    """
    Behandelt Klicks auf die Zeitrahmen-Buttons.
    """
    try:
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        # Bestimme, welcher Button geklickt wurde
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        timeframe_value = eval(button_id)["index"]
        
        return timeframe_value
    
    except Exception as e:
        logger.error(f"Fehler beim Behandeln der Zeitrahmen-Button-Klicks: {str(e)}")
        # Fallback: Behalte den aktuellen Zeitrahmen bei
        return active_timeframe
