"""
Verbesserte Chart-Utilities mit Fehlerbehandlung und NQ-Integration
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import logging

# Importiere Fehlerbehandlung
from dashboard.error_handler import ErrorHandler

# Importiere NQ-Integration
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from data.nq_integration import NQDataFetcher

# Logger konfigurieren
logger = logging.getLogger("trading_dashboard.chart_utils")

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

def generate_mock_data(symbol, timeframe, days_back=180):
    """
    Generiert Mock-Daten für den Chart basierend auf Symbol und Zeitrahmen.
    
    Args:
        symbol (str): Das Symbol des Assets (z.B. "AAPL")
        timeframe (str): Der Zeitrahmen ("1m", "2m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo")
        days_back (int): Anzahl der Tage in der Vergangenheit
        
    Returns:
        pd.DataFrame: DataFrame mit OHLCV-Daten
    """
    try:
        # Prüfe, ob es sich um NQ handelt
        if symbol == "NQ=F" or symbol == "NQ":
            logger.info(f"Rufe NQ-Daten für Zeitrahmen {timeframe} ab")
            nq_fetcher = NQDataFetcher()
            
            # Konvertiere Zeitrahmen zum NQ-Format
            if timeframe == "1m":
                interval = "1m"
                range_val = "1d"
            elif timeframe == "2m":
                interval = "2m"
                range_val = "5d"
            elif timeframe == "5m":
                interval = "5m"
                range_val = "5d"
            elif timeframe == "15m":
                interval = "15m"
                range_val = "5d"
            elif timeframe == "30m":
                interval = "30m"
                range_val = "5d"
            elif timeframe == "60m" or timeframe == "1h":
                interval = "60m"
                range_val = "1mo"
            elif timeframe == "1d":
                interval = "1d"
                range_val = "1y"
            elif timeframe == "1wk" or timeframe == "1w":
                interval = "1wk"
                range_val = "2y"
            elif timeframe == "1mo":
                interval = "1mo"
                range_val = "5y"
            else:
                interval = "1d"
                range_val = "1y"
            
            df = nq_fetcher.get_nq_futures_data(interval=interval, range_val=range_val)
            
            # Wenn Daten erfolgreich abgerufen wurden
            if not df.empty:
                # Standardisiere Spaltennamen
                if 'date' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
                    df['date'] = df.index
                
                # Stelle sicher, dass alle erforderlichen Spalten vorhanden sind
                required_columns = ['open', 'high', 'low', 'close', 'volume']
                column_mapping = {
                    'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
                }
                
                # Konvertiere Spaltennamen zu Kleinbuchstaben
                df.columns = [col.lower() if col in column_mapping.values() else col for col in df.columns]
                
                # Füge fehlende Spalten hinzu
                for col in required_columns:
                    if col not in df.columns:
                        # Versuche, die Spalte mit Großbuchstaben zu finden
                        cap_col = col.capitalize()
                        if cap_col in df.columns:
                            df[col] = df[cap_col]
                        else:
                            # Fallback: Fülle mit Dummy-Daten
                            if col == 'volume':
                                df[col] = 1000000
                            else:
                                df[col] = df['close'] if 'close' in df.columns else df.iloc[:, 0]
                
                logger.info(f"NQ-Daten erfolgreich abgerufen: {len(df)} Datenpunkte")
                return df
            
            # Wenn keine Daten abgerufen werden konnten, verwende Fallback
            logger.warning("Keine NQ-Daten verfügbar, verwende Fallback-Daten")
        
        # Bestimme den Zeitrahmen
        if timeframe == "1m":
            interval = "1m"
            days_back = min(days_back, 7)  # Begrenze auf 7 Tage für 1-Minuten-Daten
        elif timeframe == "2m":
            interval = "2m"
            days_back = min(days_back, 10)  # Begrenze auf 10 Tage für 2-Minuten-Daten
        elif timeframe == "5m":
            interval = "5m"
            days_back = min(days_back, 15)  # Begrenze auf 15 Tage für 5-Minuten-Daten
        elif timeframe == "15m":
            interval = "15m"
            days_back = min(days_back, 20)  # Begrenze auf 20 Tage für 15-Minuten-Daten
        elif timeframe == "30m":
            interval = "30m"
            days_back = min(days_back, 25)  # Begrenze auf 25 Tage für 30-Minuten-Daten
        elif timeframe == "60m" or timeframe == "1h":
            interval = "1h"
            days_back = min(days_back, 30)  # Begrenze auf 30 Tage für stündliche Daten
        elif timeframe == "1d":
            interval = "1d"
        elif timeframe == "1wk" or timeframe == "1w":
            interval = "1wk"
            days_back = max(days_back, 365)  # Mindestens 1 Jahr für wöchentliche Daten
        elif timeframe == "1mo":
            interval = "1mo"
            days_back = max(days_back, 365*2)  # Mindestens 2 Jahre für monatliche Daten
        else:
            interval = "1d"
        
        # Generiere Datenpunkte basierend auf dem Zeitrahmen
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        if interval == "1m":
            # Für 1-Minuten-Daten nur Handelszeiten (9:30-16:00 ET)
            trading_hours = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Montag bis Freitag
                    for hour in range(9, 16):
                        minute_start = 30 if hour == 9 else 0
                        minute_end = 60
                        for minute in range(minute_start, minute_end):
                            trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            if trading_time <= end_date:
                                trading_hours.append(trading_time)
                current_date += timedelta(days=1)
            date_range = pd.DatetimeIndex(trading_hours)
        elif interval == "2m":
            # Für 2-Minuten-Daten
            trading_hours = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Montag bis Freitag
                    for hour in range(9, 16):
                        minute_start = 30 if hour == 9 else 0
                        minute_end = 60
                        for minute in range(minute_start, minute_end, 2):
                            trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            if trading_time <= end_date:
                                trading_hours.append(trading_time)
                current_date += timedelta(days=1)
            date_range = pd.DatetimeIndex(trading_hours)
        elif interval == "5m":
            # Für 5-Minuten-Daten
            trading_hours = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Montag bis Freitag
                    for hour in range(9, 16):
                        minute_start = 30 if hour == 9 else 0
                        minute_end = 60
                        for minute in range(minute_start, minute_end, 5):
                            trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            if trading_time <= end_date:
                                trading_hours.append(trading_time)
                current_date += timedelta(days=1)
            date_range = pd.DatetimeIndex(trading_hours)
        elif interval == "15m":
            # Für 15-Minuten-Daten
            trading_hours = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Montag bis Freitag
                    for hour in range(9, 16):
                        minute_start = 30 if hour == 9 else 0
                        minute_end = 60
                        for minute in range(minute_start, minute_end, 15):
                            trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            if trading_time <= end_date:
                                trading_hours.append(trading_time)
                current_date += timedelta(days=1)
            date_range = pd.DatetimeIndex(trading_hours)
        elif interval == "30m":
            # Für 30-Minuten-Daten
            trading_hours = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Montag bis Freitag
                    for hour in range(9, 16):
                        minute_start = 30 if hour == 9 else 0
                        minute_end = 60
                        for minute in range(minute_start, minute_end, 30):
                            trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            if trading_time <= end_date:
                                trading_hours.append(trading_time)
                current_date += timedelta(days=1)
            date_range = pd.DatetimeIndex(trading_hours)
        elif interval == "1h":
            # Für 1-Stunden-Daten
            trading_hours = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Montag bis Freitag
                    for hour in range(9, 16):
                        if hour == 9:
                            trading_time = current_date.replace(hour=hour, minute=30, second=0, microsecond=0)
                        else:
                            trading_time = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                        if trading_time <= end_date:
                            trading_hours.append(trading_time)
                current_date += timedelta(days=1)
            date_range = pd.DatetimeIndex(trading_hours)
        elif interval == "1d":
            # Für Tagesdaten nur Handelstage (Montag bis Freitag)
            trading_days = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Montag bis Freitag
                    trading_days.append(current_date)
                current_date += timedelta(days=1)
            date_range = pd.DatetimeIndex(trading_days)
        elif interval == "1wk":
            # Für Wochendaten
            date_range = pd.date_range(start=start_date, end=end_date, freq="W-FRI")
        elif interval == "1mo":
            # Für Monatsdaten
            date_range = pd.date_range(start=start_date, end=end_date, freq="BM")
        else:
            # Fallback auf Tagesdaten
            date_range = pd.date_range(start=start_date, end=end_date, freq="B")
        
        # Generiere Beispieldaten
        np.random.seed(hash(symbol) % 100)  # Unterschiedliche Seed für jedes Symbol
        
        # Startpreis basierend auf Symbol
        symbol_prices = {
            "AAPL": 180,
            "MSFT": 350,
            "GOOGL": 140,
            "AMZN": 170,
            "TSLA": 200,
            "BTC-USD": 60000,
            "ETH-USD": 3000,
            "EUR-USD": 1.08,
            "GBP-USD": 1.27,
            "USD-JPY": 150,
            "NQ=F": 17500,
            "NQ": 17500,
        }
        
        base_price = symbol_prices.get(symbol, 100)
        
        # Generiere OHLC-Daten mit realistischeren Preisbewegungen
        volatility = 0.02
        if "BTC" in symbol or "ETH" in symbol:
            volatility = 0.04  # Höhere Volatilität für Kryptowährungen
        elif "NQ" in symbol:
            volatility = 0.03  # Mittlere Volatilität für NQ Futures
        
        price_data = []
        current_price = base_price
        trend = np.random.choice([-1, 1]) * 0.0001  # Zufälliger Trend
        
        for i in range(len(date_range)):
            # Ändere den Trend gelegentlich
            if i % 20 == 0:
                trend = np.random.normal(0, 0.0003)
            
            # Zufällige Preisbewegung mit Trend
            daily_return = np.random.normal(trend, volatility)
            current_price *= (1 + daily_return)
            
            # Generiere OHLC-Daten
            high_low_range = current_price * volatility * 2
            open_price = current_price * (1 + np.random.normal(0, 0.003))
            close_price = current_price
            high_price = max(open_price, close_price) + abs(np.random.normal(0, high_low_range/2))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, high_low_range/2))
            
            # Volumen mit höheren Werten bei größeren Preisbewegungen
            volume_base = np.random.randint(1000000, 10000000)
            volume_factor = 1 + abs(daily_return) * 10
            volume = int(volume_base * volume_factor)
            
            price_data.append({
                'date': date_range[i],
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        return pd.DataFrame(price_data)
    
    except Exception as e:
        # Bei Fehlern verwende Fallback-Daten
        logger.error(f"Fehler beim Generieren von Daten für {symbol}: {str(e)}")
        
        # Bestimme Asset-Typ für Fallback-Daten
        if "BTC" in symbol or "ETH" in symbol:
            asset_type = "Krypto"
        elif "USD" in symbol or "JPY" in symbol or "EUR" in symbol or "GBP" in symbol:
            asset_type = "Forex"
        elif "NQ" in symbol:
            asset_type = "Futures"
        else:
            asset_type = "Aktien"
        
        # Verwende Fallback-Daten
        return ErrorHandler.get_fallback_data(asset_type, timeframe)

def create_interactive_chart(df, symbol, chart_type="candlestick", timeframe="1d", drawing_data=None):
    """
    Erstellt einen interaktiven Chart mit den angegebenen Daten und Einstellungen.
    
    Args:
        df (pd.DataFrame): DataFrame mit OHLCV-Daten
        symbol (str): Das Symbol des Assets
        chart_type (str): Der Chart-Typ ("line", "candlestick", "ohlc")
        timeframe (str): Der Zeitrahmen ("1m", "2m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo")
        drawing_data (dict): Daten für Zeichnungen auf dem Chart
        
    Returns:
        go.Figure: Plotly Figure-Objekt
    """
    try:
        # Prüfe, ob Daten vorhanden sind
        if df is None or df.empty:
            logger.warning(f"Keine Daten für {symbol} mit Zeitrahmen {timeframe}")
            # Erstelle leeren Chart mit Fehlermeldung
            fig = go.Figure()
            fig.add_annotation(
                text="Keine Daten verfügbar",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(color=colors['danger'], size=20)
            )
            fig.update_layout(
                paper_bgcolor=colors['background'],
                plot_bgcolor=colors['background'],
                font=dict(color=colors['text']),
            )
            return fig
        
        # Standardisiere Spaltennamen (falls nötig)
        column_mapping = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
            'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'
        }
        
        # Überprüfe und konvertiere Spaltennamen
        df_columns = df.columns.tolist()
        for old_col, new_col in column_mapping.items():
            if old_col in df_columns and new_col not in df_columns:
                df[new_col] = df[old_col]
        
        # Stelle sicher, dass 'date' vorhanden ist
        if 'date' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
            df['date'] = df.index
        
        # Bestimme die Währung oder Einheit basierend auf dem Symbol
        currency_map = {
            "AAPL": "USD",
            "MSFT": "USD",
            "GOOGL": "USD",
            "AMZN": "USD",
            "TSLA": "USD",
            "BTC-USD": "USD",
            "ETH-USD": "USD",
            "EUR-USD": "USD",
            "GBP-USD": "USD",
            "USD-JPY": "JPY",
            "NQ=F": "USD",
            "NQ": "USD",
        }
        
        currency = currency_map.get(symbol, "")
        
        # Bestimme den Y-Achsen-Titel basierend auf dem Asset-Typ
        if "BTC" in symbol or "ETH" in symbol:
            y_axis_title = f"Preis ({currency})"
        elif "USD" in symbol or "JPY" in symbol or "EUR" in symbol or "GBP" in symbol:
            y_axis_title = f"Kurs ({currency})"
        elif "NQ" in symbol:
            y_axis_title = f"Punktestand"
        else:
            y_axis_title = f"Preis ({currency})"
        
        # Erstelle den Chart basierend auf dem ausgewählten Typ
        fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.8, 0.2],
            subplot_titles=("", "Volumen")
        )
        
        # Hauptchart
        if chart_type == "line":
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['close'],
                    mode='lines',
                    name=symbol,
                    line=dict(color=colors['primary'], width=2),
                ),
                row=1, col=1
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
                ),
                row=1, col=1
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
                ),
                row=1, col=1
            )
        
        # Volumen-Chart
        colors_volume = [colors['danger'] if df['close'][i] < df['open'][i] else colors['success'] 
                        for i in range(len(df))]
        
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name='Volumen',
                marker=dict(color=colors_volume, opacity=0.7),
            ),
            row=2, col=1
        )
        
        # Füge Zeichnungen hinzu, wenn vorhanden
        if drawing_data:
            for drawing in drawing_data:
                if drawing['type'] == 'trendline':
                    fig.add_trace(
                        go.Scatter(
                            x=[drawing['x0'], drawing['x1']],
                            y=[drawing['y0'], drawing['y1']],
                            mode='lines',
                            name='Trendlinie',
                            line=dict(color=colors['warning'], width=2, dash='solid'),
                        ),
                        row=1, col=1
                    )
                elif drawing['type'] == 'horizontal':
                    fig.add_shape(
                        type="line",
                        x0=df['date'].min(),
                        y0=drawing['y0'],
                        x1=df['date'].max(),
                        y1=drawing['y0'],
                        line=dict(color=colors['warning'], width=2, dash='dash'),
                        row=1, col=1
                    )
                elif drawing['type'] == 'rectangle':
                    fig.add_shape(
                        type="rect",
                        x0=drawing['x0'],
                        y0=drawing['y0'],
                        x1=drawing['x1'],
                        y1=drawing['y1'],
                        line=dict(color=colors['warning'], width=2),
                        fillcolor=colors['warning'] + '20',  # 20% Opazität
                        row=1, col=1
                    )
                elif drawing['type'] == 'fibonacci':
                    # Fibonacci-Retracement-Levels: 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1
                    levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
                    y_range = drawing['y1'] - drawing['y0']
                    
                    for level in levels:
                        y_level = drawing['y0'] + y_range * level
                        fig.add_shape(
                            type="line",
                            x0=drawing['x0'],
                            y0=y_level,
                            x1=drawing['x1'],
                            y1=y_level,
                            line=dict(color=colors['warning'], width=1, dash='dot'),
                            row=1, col=1
                        )
                        
                        # Beschriftung
                        fig.add_annotation(
                            x=drawing['x1'],
                            y=y_level,
                            text=f"{level:.3f}",
                            showarrow=False,
                            xanchor="left",
                            font=dict(color=colors['warning'], size=10),
                            row=1, col=1
                        )
        
        # Layout-Anpassungen
        fig.update_layout(
            paper_bgcolor=colors['background'],
            plot_bgcolor=colors['background'],
            font=dict(color=colors['text']),
            title=f"{symbol} - {timeframe}",
            xaxis=dict(
                rangeslider=dict(visible=False),
                type="date",
                showgrid=True,
                gridcolor=colors['grid'],
                zeroline=False,
            ),
            yaxis=dict(
                title=y_axis_title,  # Dynamisches Y-Achsen-Label
                showgrid=True,
                gridcolor=colors['grid'],
                zeroline=False,
                side="right",
            ),
            xaxis2=dict(
                showgrid=True,
                gridcolor=colors['grid'],
                zeroline=False,
            ),
            yaxis2=dict(
                title="Volumen",
                showgrid=False,
                zeroline=False,
            ),
            dragmode="pan",  # Ermöglicht Verschieben per Drag
            hovermode="closest",
            showlegend=False,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        
        # Konfiguriere den Chart für Mausrad-Zoom auf beide Achsen
        fig.update_layout(
            modebar=dict(
                orientation='v',
                bgcolor='rgba(0,0,0,0.5)',
                color='white',
                activecolor=colors['primary']
            ),
        )
        
        # Konfiguriere Zoom-Verhalten
        fig.update_xaxes(
            rangeslider_visible=False,
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # Verstecke Wochenenden
            ] if timeframe not in ["1m", "2m", "5m", "15m", "30m", "60m", "1h"] else [],  # Nur für Tages- und Wochencharts
        )
        
        # Konfiguriere Interaktivität
        fig.update_layout(
            hoverlabel=dict(
                bgcolor=colors['card'],
                font_size=12,
                font_family="Arial",
            ),
        )
        
        return fig
    
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Charts: {str(e)}")
        
        # Erstelle einen Fallback-Chart mit Fehlermeldung
        fig = go.Figure()
        fig.add_annotation(
            text=f"Fehler beim Erstellen des Charts: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color=colors['danger'], size=16)
        )
        fig.update_layout(
            paper_bgcolor=colors['background'],
            plot_bgcolor=colors['background'],
            font=dict(color=colors['text']),
        )
        return fig

def get_available_assets():
    """
    Gibt eine Liste verfügbarer Assets zurück.
    
    Returns:
        list: Liste von Dictionaries mit Asset-Informationen
    """
    return [
        {"label": "Apple (AAPL)", "value": "AAPL", "group": "Aktien"},
        {"label": "Microsoft (MSFT)", "value": "MSFT", "group": "Aktien"},
        {"label": "Google (GOOGL)", "value": "GOOGL", "group": "Aktien"},
        {"label": "Amazon (AMZN)", "value": "AMZN", "group": "Aktien"},
        {"label": "Tesla (TSLA)", "value": "TSLA", "group": "Aktien"},
        {"label": "NASDAQ 100 (NQ)", "value": "NQ=F", "group": "Futures"},  # NQ hinzugefügt
        {"label": "Bitcoin (BTC-USD)", "value": "BTC-USD", "group": "Krypto"},
        {"label": "Ethereum (ETH-USD)", "value": "ETH-USD", "group": "Krypto"},
        {"label": "EUR/USD", "value": "EUR-USD", "group": "Forex"},
        {"label": "GBP/USD", "value": "GBP-USD", "group": "Forex"},
        {"label": "USD/JPY", "value": "USD-JPY", "group": "Forex"},
    ]

def get_available_timeframes():
    """
    Gibt eine Liste verfügbarer Zeitrahmen zurück.
    
    Returns:
        list: Liste von Dictionaries mit Zeitrahmen-Informationen
    """
    return [
        {"label": "1m", "value": "1m", "group": "Minuten"},
        {"label": "2m", "value": "2m", "group": "Minuten"},
        {"label": "5m", "value": "5m", "group": "Minuten"},
        {"label": "15m", "value": "15m", "group": "Minuten"},
        {"label": "30m", "value": "30m", "group": "Minuten"},
        {"label": "1h", "value": "1h", "group": "Stunden"},
        {"label": "1d", "value": "1d", "group": "Tage"},
        {"label": "1w", "value": "1w", "group": "Wochen"},
        {"label": "1mo", "value": "1mo", "group": "Monate"},
    ]

def get_currency_for_symbol(symbol):
    """
    Gibt die Währung oder Einheit für ein Symbol zurück.
    
    Args:
        symbol (str): Das Symbol des Assets
    
    Returns:
        str: Währung oder Einheit
    """
    currency_map = {
        "AAPL": "USD",
        "MSFT": "USD",
        "GOOGL": "USD",
        "AMZN": "USD",
        "TSLA": "USD",
        "BTC-USD": "USD",
        "ETH-USD": "USD",
        "EUR-USD": "USD",
        "GBP-USD": "USD",
        "USD-JPY": "JPY",
        "NQ=F": "Punkte",
        "NQ": "Punkte",
    }
    
    return currency_map.get(symbol, "")
