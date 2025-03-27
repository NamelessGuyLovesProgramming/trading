"""
Abstrakte Basisklasse für Datenquellen im Trading Dashboard
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from abc import ABC, abstractmethod

# Importiere Hilfsfunktionen
from utils.helpers import DateTimeUtils, DataUtils, CacheManager

# Logger konfigurieren
logger = logging.getLogger("trading_dashboard.data_source")

class DataSource(ABC):
    """
    Abstrakte Basisklasse für Datenquellen
    
    Diese Klasse definiert die Schnittstelle für alle Datenquellen im Trading Dashboard.
    Konkrete Implementierungen müssen die abstrakten Methoden implementieren.
    """
    
    def __init__(self, cache_enabled: bool = True, cache_duration: int = 86400):
        """
        Initialisiert die Datenquelle
        
        Args:
            cache_enabled: Ob Caching aktiviert ist
            cache_duration: Cache-Dauer in Sekunden (Standard: 24 Stunden)
        """
        self.cache_enabled = cache_enabled
        self.cache_duration = cache_duration
        self.cache_manager = CacheManager()
    
    @abstractmethod
    def get_data(self, symbol: str, timeframe: str, start_date: Optional[Union[str, datetime]] = None, 
                end_date: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Ruft Daten für ein Symbol und einen Zeitrahmen ab
        
        Args:
            symbol: Symbol des Assets
            timeframe: Zeitrahmen
            start_date: Startdatum (optional)
            end_date: Enddatum (optional)
            
        Returns:
            pd.DataFrame: DataFrame mit OHLCV-Daten
        """
        pass
    
    @abstractmethod
    def get_available_symbols(self) -> List[Dict[str, str]]:
        """
        Gibt eine Liste verfügbarer Symbole zurück
        
        Returns:
            List[Dict[str, str]]: Liste von Dictionaries mit Symbol-Informationen
        """
        pass
    
    @abstractmethod
    def get_available_timeframes(self) -> List[Dict[str, str]]:
        """
        Gibt eine Liste verfügbarer Zeitrahmen zurück
        
        Returns:
            List[Dict[str, str]]: Liste von Dictionaries mit Zeitrahmen-Informationen
        """
        pass
    
    def _get_cache_key(self, symbol: str, timeframe: str, start_date: Optional[Union[str, datetime]] = None, 
                      end_date: Optional[Union[str, datetime]] = None) -> str:
        """
        Generiert einen Cache-Schlüssel für die angegebenen Parameter
        
        Args:
            symbol: Symbol des Assets
            timeframe: Zeitrahmen
            start_date: Startdatum (optional)
            end_date: Enddatum (optional)
            
        Returns:
            str: Cache-Schlüssel
        """
        # Konvertiere Datumsangaben zu Strings, falls nötig
        start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
        end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date
        
        # Generiere Cache-Schlüssel
        return f"{symbol}_{timeframe}_{start_str}_{end_str}"
    
    def _get_from_cache(self, symbol: str, timeframe: str, start_date: Optional[Union[str, datetime]] = None, 
                       end_date: Optional[Union[str, datetime]] = None) -> Optional[pd.DataFrame]:
        """
        Versucht, Daten aus dem Cache zu laden
        
        Args:
            symbol: Symbol des Assets
            timeframe: Zeitrahmen
            start_date: Startdatum (optional)
            end_date: Enddatum (optional)
            
        Returns:
            Optional[pd.DataFrame]: DataFrame mit OHLCV-Daten oder None, wenn nicht im Cache
        """
        if not self.cache_enabled:
            return None
        
        cache_key = self._get_cache_key(symbol, timeframe, start_date, end_date)
        
        if self.cache_manager.is_cache_valid(cache_key, self.cache_duration):
            return self.cache_manager.get_from_cache(cache_key)
        
        return None
    
    def _save_to_cache(self, df: pd.DataFrame, symbol: str, timeframe: str, 
                      start_date: Optional[Union[str, datetime]] = None, 
                      end_date: Optional[Union[str, datetime]] = None) -> bool:
        """
        Speichert Daten im Cache
        
        Args:
            df: DataFrame mit OHLCV-Daten
            symbol: Symbol des Assets
            timeframe: Zeitrahmen
            start_date: Startdatum (optional)
            end_date: Enddatum (optional)
            
        Returns:
            bool: True, wenn erfolgreich gespeichert, sonst False
        """
        if not self.cache_enabled:
            return False
        
        cache_key = self._get_cache_key(symbol, timeframe, start_date, end_date)
        return self.cache_manager.save_to_cache(cache_key, df)

class MockDataSource(DataSource):
    """
    Mock-Datenquelle für Testzwecke
    
    Diese Klasse generiert synthetische Daten für Tests und Entwicklung.
    """
    
    def get_data(self, symbol: str, timeframe: str, start_date: Optional[Union[str, datetime]] = None, 
                end_date: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Generiert synthetische Daten für ein Symbol und einen Zeitrahmen
        
        Args:
            symbol: Symbol des Assets
            timeframe: Zeitrahmen
            start_date: Startdatum (optional)
            end_date: Enddatum (optional)
            
        Returns:
            pd.DataFrame: DataFrame mit synthetischen OHLCV-Daten
        """
        try:
            # Versuche, Daten aus dem Cache zu laden
            cached_data = self._get_from_cache(symbol, timeframe, start_date, end_date)
            if cached_data is not None:
                logger.info(f"Daten für {symbol} ({timeframe}) aus Cache geladen")
                return cached_data
            
            # Bestimme Start- und Enddatum
            if end_date is None:
                end_date = datetime.now()
            elif isinstance(end_date, str):
                end_date = DateTimeUtils.parse_date_string(end_date)
            
            if start_date is None:
                # Bestimme Startdatum basierend auf Zeitrahmen
                days_back = DateTimeUtils.get_timeframe_days(timeframe)
                start_date = end_date - timedelta(days=days_back)
            elif isinstance(start_date, str):
                start_date = DateTimeUtils.parse_date_string(start_date)
            
            # Bestimme Frequenz basierend auf Zeitrahmen
            freq_map = {
                '1m': '1min',
                '2m': '2min',
                '5m': '5min',
                '15m': '15min',
                '30m': '30min',
                '1h': '1H',
                '1d': '1D',
                '1w': '1W',
                '1mo': '1M'
            }
            
            freq = freq_map.get(timeframe, '1D')
            
            # Generiere Datenpunkte
            if timeframe in ['1m', '2m', '5m', '15m', '30m', '1h']:
                # Für Intraday-Daten nur Handelszeiten (9:30-16:00 ET)
                trading_hours = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        for hour in range(9, 16):
                            minute_start = 30 if hour == 9 else 0
                            minute_end = 60
                            step = int(timeframe.replace('m', '')) if timeframe.endswith('m') else 60
                            for minute in range(minute_start, minute_end, step):
                                trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                if trading_time <= end_date:
                                    trading_hours.append(trading_time)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_hours)
            elif timeframe == '1d':
                # Für Tagesdaten nur Handelstage (Montag bis Freitag)
                trading_days = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        trading_days.append(current_date)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_days)
            else:
                # Für andere Zeitrahmen
                date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
            
            # Generiere synthetische OHLCV-Daten
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
            
            df = pd.DataFrame(price_data)
            df.set_index('date', inplace=True)
            
            # Speichere die Daten im Cache
            self._save_to_cache(df, symbol, timeframe, start_date, end_date)
            
            logger.info(f"Synthetische Daten für {symbol} ({timeframe}) generiert: {len(df)} Datenpunkte")
            return df
        
        except Exception as e:
            logger.error(f"Fehler beim Generieren synthetischer Daten für {symbol}: {str(e)}")
            return pd.DataFrame()  # Leerer DataFrame bei Fehler
    
    def get_available_symbols(self) -> List[Dict[str, str]]:
        """
        Gibt eine Liste verfügbarer Symbole zurück
        
        Returns:
            List[Dict[str, str]]: Liste von Dictionaries mit Symbol-Informationen
        """
        return [
            {"label": "Apple (AAPL)", "value": "AAPL", "group": "Aktien"},
            {"label": "Microsoft (MSFT)", "value": "MSFT", "group": "Aktien"},
            {"label": "Google (GOOGL)", "value": "GOOGL", "group": "Aktien"},
            {"label": "Amazon (AMZN)", "value": "AMZN", "group": "Aktien"},
            {"label": "Tesla (TSLA)", "value": "TSLA", "group": "Aktien"},
            {"label": "NASDAQ 100 (NQ)", "value": "NQ=F", "group": "Futures"},
            {"label": "Bitcoin (BTC-USD)", "value": "BTC-USD", "group": "Krypto"},
            {"label": "Ethereum (ETH-USD)", "value": "ETH-USD", "group": "Krypto"},
            {"label": "EUR/USD", "value": "EUR-USD", "group": "Forex"},
            {"label": "GBP/USD", "value": "GBP-USD", "group": "Forex"},
            {"label": "USD/JPY", "value": "USD-JPY", "group": "Forex"},
        ]
    
    def get_available_timeframes(self) -> List[Dict[str, str]]:
        """
        Gibt eine Liste verfügbarer Zeitrahmen zurück
        
        Returns:
            List[Dict[str, str]]: Liste von Dictionaries mit Zeitrahmen-Informationen
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

class YahooFinanceDataSource(DataSource):
    """
    Datenquelle für Yahoo Finance
    
    Diese Klasse ruft Daten von der Yahoo Finance API ab.
    """
    
    def get_data(self, symbol: str, timeframe: str, start_date: Optional[Union[str, datetime]] = None, 
                end_date: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Ruft Daten von Yahoo Finance ab
        
        Args:
            symbol: Symbol des Assets
            timeframe: Zeitrahmen
            start_date: Startdatum (optional)
            end_date: Enddatum (optional)
            
        Returns:
            pd.DataFrame: DataFrame mit OHLCV-Daten
        """
        try:
            # Versuche, Daten aus dem Cache zu laden
            cached_data = self._get_from_cache(symbol, timeframe, start_date, end_date)
            if cached_data is not None:
                logger.info(f"Daten für {symbol} ({timeframe}) aus Cache geladen")
                return cached_data
            
            # Konvertiere Zeitrahmen zum Yahoo Finance-Format
            interval_map = {
                '1m': '1m',
                '2m': '2m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '60m',
                '1d': '1d',
                '1w': '1wk',
                '1mo': '1mo'
            }
            
            yahoo_interval = interval_map.get(timeframe, '1d')
            
            # Bestimme Zeitraum
            if start_date is None and end_date is None:
                # Verwende range-Parameter
                range_val = '1y'  # Standard: 1 Jahr
                
                # Bestimme range basierend auf Zeitrahmen
                if timeframe in ['1m', '2m', '5m']:
                    range_val = '5d'  # Für Minuten-Daten maximal 5 Tage
                elif timeframe in ['15m', '30m', '1h']:
                    range_val = '1mo'  # Für Stunden-Daten maximal 1 Monat
                
                # Verwende die Yahoo Finance API mit range-Parameter
                try:
                    # Importiere die API-Client-Bibliothek
                    sys.path.append('/opt/.manus/.sandbox-runtime')
                    from data_api import ApiClient
                    client = ApiClient()
                    
                    # Rufe Daten über die API ab
                    response = client.call_api('YahooFinance/get_stock_chart', query={
                        'symbol': symbol,
                        'interval': yahoo_interval,
                        'range': range_val,
                        'includePrePost': False,
                        'includeAdjustedClose': True
                    })
                    
                    # Verarbeite die Antwort
                    if response and 'chart' in response and 'result' in response['chart'] and response['chart']['result']:
                        result = response['chart']['result'][0]
                        
                        # Extrahiere Zeitstempel und Indikatoren
                        timestamps = result['timestamp']
                        quote = result['indicators']['quote'][0]
                        
                        # Erstelle DataFrame
                        df = pd.DataFrame({
                            'open': quote['open'],
                            'high': quote['high'],
                            'low': quote['low'],
                            'close': quote['close'],
                            'volume': quote['volume']
                        })
                        
                        # Füge Zeitstempel als Index hinzu
                        df.index = pd.to_datetime([datetime.fromtimestamp(ts) for ts in timestamps])
                        df.index.name = 'date'
                        
                        # Speichere Daten im Cache
                        self._save_to_cache(df, symbol, timeframe, start_date, end_date)
                        
                        logger.info(f"Daten für {symbol} ({timeframe}) erfolgreich abgerufen: {len(df)} Datenpunkte")
                        return df
                    else:
                        logger.error(f"Fehler beim Abrufen der Daten für {symbol}: Ungültiges Antwortformat")
                except Exception as api_error:
                    logger.error(f"Fehler beim Abrufen der Daten für {symbol} über API: {str(api_error)}")
            
            # Fallback: Verwende Mock-Daten
            logger.warning(f"Verwende Mock-Daten für {symbol} ({timeframe})")
            mock_source = MockDataSource(self.cache_enabled, self.cache_duration)
            return mock_source.get_data(symbol, timeframe, start_date, end_date)
        
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Daten für {symbol}: {str(e)}")
            
            # Fallback: Verwende Mock-Daten
            logger.warning(f"Verwende Mock-Daten für {symbol} ({timeframe})")
            mock_source = MockDataSource(self.cache_enabled, self.cache_duration)
            return mock_source.get_data(symbol, timeframe, start_date, end_date)
    
    def get_available_symbols(self) -> List[Dict[str, str]]:
        """
        Gibt eine Liste verfügbarer Symbole zurück
        
        Returns:
            List[Dict[str, str]]: Liste von Dictionaries mit Symbol-Informationen
        """
        # Verwende die gleiche Liste wie MockDataSource
        mock_source = MockDataSource()
        return mock_source.get_available_symbols()
    
    def get_available_timeframes(self) -> List[Dict[str, str]]:
        """
        Gibt eine Liste verfügbarer Zeitrahmen zurück
        
        Returns:
            List[Dict[str, str]]: Liste von Dictionaries mit Zeitrahmen-Informationen
        """
        # Verwende die gleiche Liste wie MockDataSource
        mock_source = MockDataSource()
        return mock_source.get_available_timeframes()

class DataSourceFactory:
    """
    Factory für Datenquellen
    
    Diese Klasse erstellt Datenquellen basierend auf dem angegebenen Typ.
    """
    
    @staticmethod
    def create_data_source(source_type: str, cache_enabled: bool = True, cache_duration: int = 86400) -> DataSource:
        """
        Erstellt eine Datenquelle
        
        Args:
            source_type: Typ der Datenquelle ('mock', 'yahoo', etc.)
            cache_enabled: Ob Caching aktiviert ist
            cache_duration: Cache-Dauer in Sekunden (Standard: 24 Stunden)
            
        Returns:
            DataSource: Datenquelle
        """
        if source_type == 'yahoo':
            return YahooFinanceDataSource(cache_enabled, cache_duration)
        else:
            # Standard: Mock-Datenquelle
            return MockDataSource(cache_enabled, cache_duration)
