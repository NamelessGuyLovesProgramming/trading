"""
Data Fetcher Module für Trading Dashboard
Verantwortlich für das Abrufen von Handelsdaten über die YahooFinance API
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path

# Importiere yfinance global, damit es in allen Methoden verfügbar ist
import yfinance as yf

# Versuche, die Manus API zu importieren, ansonsten verwende nur yfinance
try:
    sys.path.append('/opt/.manus/.sandbox-runtime')
    from data_api import ApiClient
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("Manus API nicht verfügbar, verwende yfinance als Fallback")

class DataFetcher:
    """
    Klasse zum Abrufen und Verwalten von Handelsdaten
    """
    def __init__(self, cache_dir=None):
        """
        Initialisiert den DataFetcher
        
        Args:
            cache_dir (str, optional): Verzeichnis für den Daten-Cache. 
                                      Standardmäßig wird ein 'cache' Verzeichnis im data-Ordner verwendet.
        """
        if cache_dir is None:
            # Standardverzeichnis für den Cache
            self.cache_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'cache'
        else:
            self.cache_dir = Path(cache_dir)
            
        # Stelle sicher, dass das Cache-Verzeichnis existiert
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialisiere API-Client, wenn verfügbar
        if API_AVAILABLE:
            self.client = ApiClient()
        
    def get_stock_data(self, symbol, interval='1d', range='1y', use_cache=True, force_refresh=False):
        """
        Ruft Aktiendaten für ein bestimmtes Symbol ab
        
        Args:
            symbol (str): Das Aktiensymbol (z.B. 'AAPL')
            interval (str): Zeitintervall ('1m', '2m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
            range (str): Zeitraum ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            use_cache (bool): Ob der Cache verwendet werden soll
            force_refresh (bool): Ob die Daten unabhängig vom Cache neu abgerufen werden sollen
            
        Returns:
            pandas.DataFrame: DataFrame mit den Aktiendaten
        """
        cache_file = self.cache_dir / f"{symbol}_{interval}_{range}.csv"
        
        # Prüfe, ob Cache verwendet werden soll und Datei existiert
        if use_cache and cache_file.exists() and not force_refresh:
            # Prüfe, ob Cache aktuell ist (für tägliche Daten nicht älter als 1 Tag)
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if interval in ['1d', '1wk', '1mo'] and cache_age.days < 1:
                print(f"Verwende gecachte Daten für {symbol}")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
            elif interval.endswith('m') and cache_age.seconds < 3600:  # Für Minutendaten: 1 Stunde Cache
                print(f"Verwende gecachte Daten für {symbol}")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        
        # Daten abrufen
        if API_AVAILABLE:
            try:
                data = self._fetch_data_from_api(symbol, interval, range)
                if data is not None and not data.empty:
                    # Speichere Daten im Cache
                    if use_cache:
                        data.to_csv(cache_file)
                    return data
            except Exception as e:
                print(f"Fehler beim Abrufen der Daten über API: {e}")
                print("Verwende yfinance als Fallback...")
        
        # Fallback zu yfinance
        data = self._fetch_data_from_yfinance(symbol, interval, range)
        
        # Speichere Daten im Cache
        if use_cache and data is not None and not data.empty:
            data.to_csv(cache_file)
            
        return data
    
    def _fetch_data_from_api(self, symbol, interval, range):
        """
        Ruft Daten über die Manus API ab
        """
        try:
            # Verwende die YahooFinance API über den Manus API-Client
            response = self.client.call_api('YahooFinance/get_stock_chart', query={
                'symbol': symbol,
                'interval': interval,
                'range': range,
                'includeAdjustedClose': True
            })
            
            # Verarbeite die Antwort
            if response and 'chart' in response and 'result' in response['chart'] and response['chart']['result']:
                result = response['chart']['result'][0]
                
                # Extrahiere Zeitstempel und Indikatoren
                timestamps = result.get('timestamp', [])
                indicators = result.get('indicators', {})
                
                # Extrahiere Preisdaten
                quote = indicators.get('quote', [{}])[0]
                adjclose = indicators.get('adjclose', [{}])[0].get('adjclose', [])
                
                # Erstelle DataFrame
                data = {
                    'Open': quote.get('open', []),
                    'High': quote.get('high', []),
                    'Low': quote.get('low', []),
                    'Close': quote.get('close', []),
                    'Volume': quote.get('volume', []),
                    'Adj Close': adjclose
                }
                
                # Konvertiere Zeitstempel zu Datetime
                index = pd.to_datetime([datetime.fromtimestamp(ts) for ts in timestamps], unit='s')
                
                # Erstelle DataFrame
                df = pd.DataFrame(data, index=index)
                
                # Entferne Zeilen mit NaN-Werten
                df = df.dropna()
                
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Fehler beim Abrufen der Daten über API: {e}")
            return pd.DataFrame()
    
    def _fetch_data_from_yfinance(self, symbol, interval, range):
        """
        Ruft Daten über yfinance ab (Fallback)
        """
        try:
            # Verwende yfinance als Fallback
            ticker = yf.Ticker(symbol)
            
            # Konvertiere range zu period für yfinance
            period = range
            
            # Rufe Historiendaten ab
            df = ticker.history(period=period, interval=interval)
            
            # Wenn keine Daten zurückgegeben wurden, versuche es mit einem anderen Ansatz
            if df.empty:
                print(f"Keine Daten für {symbol} mit period={period}, interval={interval}. Versuche direkten Download...")
                # Verwende die direkte Download-Methode
                end_date = datetime.now()
                
                # Bestimme das Startdatum basierend auf dem angegebenen Bereich
                if range == '1d':
                    start_date = end_date - timedelta(days=1)
                elif range == '5d':
                    start_date = end_date - timedelta(days=5)
                elif range == '1mo':
                    start_date = end_date - timedelta(days=30)
                elif range == '3mo':
                    start_date = end_date - timedelta(days=90)
                elif range == '6mo':
                    start_date = end_date - timedelta(days=180)
                elif range == '1y':
                    start_date = end_date - timedelta(days=365)
                elif range == '2y':
                    start_date = end_date - timedelta(days=730)
                elif range == '5y':
                    start_date = end_date - timedelta(days=1825)
                elif range == '10y':
                    start_date = end_date - timedelta(days=3650)
                elif range == 'ytd':
                    start_date = datetime(end_date.year, 1, 1)
                else:  # 'max'
                    start_date = end_date - timedelta(days=3650)  # Default to 10 years
                
                # Formatiere Daten für yfinance
                start_str = start_date.strftime('%Y-%m-%d')
                end_str = end_date.strftime('%Y-%m-%d')
                
                # Versuche den direkten Download
                df = yf.download(symbol, start=start_str, end=end_str, interval=interval)
            
            # Standardisiere Spaltennamen
            if not df.empty:
                df.columns = [col if col != 'Stock Splits' else 'Splits' for col in df.columns]
            
            return df
            
        except Exception as e:
            print(f"Fehler beim Abrufen der Daten über yfinance: {e}")
            # Erstelle einen leeren DataFrame mit den erwarteten Spalten
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'])
    
    def get_multiple_stocks(self, symbols, interval='1d', range='1y', use_cache=True):
        """
        Ruft Daten für mehrere Aktien ab
        
        Args:
            symbols (list): Liste von Aktiensymbolen
            interval (str): Zeitintervall
            range (str): Zeitraum
            use_cache (bool): Ob der Cache verwendet werden soll
            
        Returns:
            dict: Dictionary mit Symbol als Schlüssel und DataFrame als Wert
        """
        result = {}
        for symbol in symbols:
            result[symbol] = self.get_stock_data(symbol, interval, range, use_cache)
        return result
    
    def get_technical_indicators(self, symbol, interval='1d', range='1y'):
        """
        Ruft technische Indikatoren für ein Symbol ab
        
        Args:
            symbol (str): Das Aktiensymbol
            interval (str): Zeitintervall
            range (str): Zeitraum
            
        Returns:
            dict: Dictionary mit technischen Indikatoren
        """
        if not API_AVAILABLE:
            print("Technische Indikatoren sind nur über die Manus API verfügbar")
            return {}
            
        try:
            # Verwende die YahooFinance API über den Manus API-Client
            response = self.client.call_api('YahooFinance/get_stock_insights', query={
                'symbol': symbol
            })
            
            if response and 'finance' in response and 'result' in response['finance']:
                result = response['finance']['result']
                
                # Extrahiere technische Indikatoren
                if 'instrumentInfo' in result and 'technicalEvents' in result['instrumentInfo']:
                    return result['instrumentInfo']['technicalEvents']
                    
                # Extrahiere Stop-Loss und Widerstand
                if 'instrumentInfo' in result and 'keyTechnicals' in result['instrumentInfo']:
                    return result['instrumentInfo']['keyTechnicals']
            
            return {}
            
        except Exception as e:
            print(f"Fehler beim Abrufen der technischen Indikatoren: {e}")
            return {}
