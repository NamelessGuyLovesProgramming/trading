"""
Utilities-Modul für gemeinsam genutzte Funktionen im Trading Dashboard
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Union, Tuple, Any, Callable

# Logger konfigurieren
logger = logging.getLogger("trading_dashboard.utils")

class DateTimeUtils:
    """
    Hilfsfunktionen für Datums- und Zeitoperationen
    """
    
    @staticmethod
    def parse_date_string(date_str: str) -> datetime:
        """
        Konvertiert einen Datums-String in ein datetime-Objekt
        
        Args:
            date_str: Datums-String im Format 'YYYY-MM-DD'
            
        Returns:
            datetime: Konvertiertes datetime-Objekt
        """
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Fehler beim Parsen des Datums '{date_str}': {str(e)}")
            # Fallback auf aktuelles Datum
            return datetime.now()
    
    @staticmethod
    def get_date_range(start_date: Union[str, datetime], 
                      end_date: Union[str, datetime], 
                      freq: str = 'D') -> pd.DatetimeIndex:
        """
        Erstellt einen Datumsbereich zwischen Start- und Enddatum
        
        Args:
            start_date: Startdatum als String oder datetime
            end_date: Enddatum als String oder datetime
            freq: Frequenz ('D' für täglich, 'W' für wöchentlich, etc.)
            
        Returns:
            pd.DatetimeIndex: Datumsbereich
        """
        try:
            # Konvertiere Strings zu datetime, falls nötig
            if isinstance(start_date, str):
                start_date = DateTimeUtils.parse_date_string(start_date)
            if isinstance(end_date, str):
                end_date = DateTimeUtils.parse_date_string(end_date)
                
            return pd.date_range(start=start_date, end=end_date, freq=freq)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Datumsbereichs: {str(e)}")
            # Fallback auf letzten Monat
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            return pd.date_range(start=start_date, end=end_date, freq=freq)
    
    @staticmethod
    def get_timeframe_days(timeframe: str) -> int:
        """
        Gibt die Anzahl der Tage für einen Zeitrahmen zurück
        
        Args:
            timeframe: Zeitrahmen ('1m', '1h', '1d', '1w', '1mo', etc.)
            
        Returns:
            int: Anzahl der Tage
        """
        timeframe_map = {
            '1m': 1,
            '2m': 2,
            '5m': 5,
            '15m': 10,
            '30m': 15,
            '1h': 30,
            '1d': 365,
            '1w': 365 * 2,
            '1mo': 365 * 5
        }
        
        return timeframe_map.get(timeframe, 30)  # Standardmäßig 30 Tage

class DataUtils:
    """
    Hilfsfunktionen für Datenoperationen
    """
    
    @staticmethod
    def resample_ohlc(df: pd.DataFrame, 
                     timeframe: str) -> pd.DataFrame:
        """
        Resampled OHLC-Daten auf einen neuen Zeitrahmen
        
        Args:
            df: DataFrame mit OHLC-Daten
            timeframe: Ziel-Zeitrahmen ('1h', '1d', '1w', '1mo', etc.)
            
        Returns:
            pd.DataFrame: Resampled DataFrame
        """
        try:
            # Stelle sicher, dass der Index ein DatetimeIndex ist
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'date' in df.columns:
                    df = df.set_index('date')
                else:
                    logger.error("DataFrame hat keinen DatetimeIndex und keine 'date'-Spalte")
                    return df
            
            # Mapping von Zeitrahmen zu Pandas-Frequenz
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
            
            freq = freq_map.get(timeframe)
            if not freq:
                logger.warning(f"Unbekannter Zeitrahmen: {timeframe}, verwende '1D'")
                freq = '1D'
            
            # Standardisiere Spaltennamen
            df_columns = df.columns.str.lower() if hasattr(df.columns, 'str') else df.columns
            column_mapping = {}
            
            for col in df_columns:
                if col in ['open', 'high', 'low', 'close', 'volume']:
                    column_mapping[col] = col
                elif col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    column_mapping[col] = col.lower()
            
            # Erstelle ein neues DataFrame mit standardisierten Spaltennamen
            new_df = pd.DataFrame()
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    new_df[new_col] = df[old_col]
            
            # Wenn keine Spalten gemappt wurden, verwende das Original-DataFrame
            if new_df.empty:
                new_df = df
            
            # Resample
            resampled = pd.DataFrame()
            if 'open' in new_df.columns:
                resampled['open'] = new_df['open'].resample(freq).first()
            if 'high' in new_df.columns:
                resampled['high'] = new_df['high'].resample(freq).max()
            if 'low' in new_df.columns:
                resampled['low'] = new_df['low'].resample(freq).min()
            if 'close' in new_df.columns:
                resampled['close'] = new_df['close'].resample(freq).last()
            if 'volume' in new_df.columns:
                resampled['volume'] = new_df['volume'].resample(freq).sum()
            
            # Entferne NaN-Werte
            resampled = resampled.dropna()
            
            return resampled
        
        except Exception as e:
            logger.error(f"Fehler beim Resampling der Daten: {str(e)}")
            return df
    
    @staticmethod
    def calculate_returns(prices: Union[pd.Series, np.ndarray, List[float]]) -> np.ndarray:
        """
        Berechnet prozentuale Renditen aus einer Preisreihe
        
        Args:
            prices: Preisreihe als Series, Array oder Liste
            
        Returns:
            np.ndarray: Array mit prozentualen Renditen
        """
        try:
            # Konvertiere zu NumPy-Array, falls nötig
            if isinstance(prices, pd.Series):
                prices_array = prices.values
            elif isinstance(prices, list):
                prices_array = np.array(prices)
            else:
                prices_array = prices
            
            # Berechne prozentuale Renditen
            returns = np.diff(prices_array) / prices_array[:-1]
            
            return returns
        
        except Exception as e:
            logger.error(f"Fehler bei der Berechnung der Renditen: {str(e)}")
            return np.array([])
    
    @staticmethod
    def calculate_performance_metrics(returns: np.ndarray) -> Dict[str, float]:
        """
        Berechnet Performance-Metriken aus Renditen
        
        Args:
            returns: Array mit prozentualen Renditen
            
        Returns:
            Dict[str, float]: Dictionary mit Performance-Metriken
        """
        try:
            if len(returns) == 0:
                return {
                    'total_return': 0.0,
                    'annualized_return': 0.0,
                    'volatility': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0
                }
            
            # Gesamtrendite
            total_return = np.prod(1 + returns) - 1
            
            # Annualisierte Rendite (angenommen, dass die Renditen täglich sind)
            annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
            
            # Volatilität
            volatility = np.std(returns) * np.sqrt(252)
            
            # Sharpe Ratio (angenommen, dass der risikofreie Zinssatz 0 ist)
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
            
            # Maximum Drawdown
            cum_returns = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cum_returns)
            drawdowns = (cum_returns / running_max) - 1
            max_drawdown = np.min(drawdowns)
            
            # Win Rate
            win_rate = np.sum(returns > 0) / len(returns)
            
            # Profit Factor
            gains = np.sum(returns[returns > 0])
            losses = np.abs(np.sum(returns[returns < 0]))
            profit_factor = gains / losses if losses > 0 else float('inf')
            
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'profit_factor': profit_factor
            }
        
        except Exception as e:
            logger.error(f"Fehler bei der Berechnung der Performance-Metriken: {str(e)}")
            return {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0
            }

class ConfigUtils:
    """
    Hilfsfunktionen für Konfigurationsoperationen
    """
    
    @staticmethod
    def get_asset_info(symbol: str) -> Dict[str, str]:
        """
        Gibt Informationen zu einem Asset zurück
        
        Args:
            symbol: Symbol des Assets
            
        Returns:
            Dict[str, str]: Dictionary mit Asset-Informationen
        """
        # Asset-Informationen
        asset_info = {
            "AAPL": {"name": "Apple Inc.", "type": "Aktie", "currency": "USD", "exchange": "NASDAQ"},
            "MSFT": {"name": "Microsoft Corporation", "type": "Aktie", "currency": "USD", "exchange": "NASDAQ"},
            "GOOGL": {"name": "Alphabet Inc.", "type": "Aktie", "currency": "USD", "exchange": "NASDAQ"},
            "AMZN": {"name": "Amazon.com, Inc.", "type": "Aktie", "currency": "USD", "exchange": "NASDAQ"},
            "TSLA": {"name": "Tesla, Inc.", "type": "Aktie", "currency": "USD", "exchange": "NASDAQ"},
            "BTC-USD": {"name": "Bitcoin", "type": "Krypto", "currency": "USD", "exchange": "Crypto"},
            "ETH-USD": {"name": "Ethereum", "type": "Krypto", "currency": "USD", "exchange": "Crypto"},
            "EUR-USD": {"name": "Euro/US-Dollar", "type": "Forex", "currency": "USD", "exchange": "Forex"},
            "GBP-USD": {"name": "Britisches Pfund/US-Dollar", "type": "Forex", "currency": "USD", "exchange": "Forex"},
            "USD-JPY": {"name": "US-Dollar/Japanischer Yen", "type": "Forex", "currency": "JPY", "exchange": "Forex"},
            "NQ=F": {"name": "NASDAQ 100 E-mini Futures", "type": "Futures", "currency": "USD", "exchange": "CME"},
            "NQ": {"name": "NASDAQ 100 E-mini Futures", "type": "Futures", "currency": "USD", "exchange": "CME"},
        }
        
        return asset_info.get(symbol, {"name": symbol, "type": "Unbekannt", "currency": "USD", "exchange": "Unbekannt"})
    
    @staticmethod
    def get_timeframe_info(timeframe: str) -> Dict[str, str]:
        """
        Gibt Informationen zu einem Zeitrahmen zurück
        
        Args:
            timeframe: Zeitrahmen
            
        Returns:
            Dict[str, str]: Dictionary mit Zeitrahmen-Informationen
        """
        # Zeitrahmen-Informationen
        timeframe_info = {
            "1m": {"name": "1 Minute", "group": "Minuten", "pandas_freq": "1min"},
            "2m": {"name": "2 Minuten", "group": "Minuten", "pandas_freq": "2min"},
            "5m": {"name": "5 Minuten", "group": "Minuten", "pandas_freq": "5min"},
            "15m": {"name": "15 Minuten", "group": "Minuten", "pandas_freq": "15min"},
            "30m": {"name": "30 Minuten", "group": "Minuten", "pandas_freq": "30min"},
            "1h": {"name": "1 Stunde", "group": "Stunden", "pandas_freq": "1H"},
            "1d": {"name": "1 Tag", "group": "Tage", "pandas_freq": "1D"},
            "1w": {"name": "1 Woche", "group": "Wochen", "pandas_freq": "1W"},
            "1mo": {"name": "1 Monat", "group": "Monate", "pandas_freq": "1M"},
        }
        
        return timeframe_info.get(timeframe, {"name": timeframe, "group": "Unbekannt", "pandas_freq": "1D"})
    
    @staticmethod
    def get_strategy_info(strategy: str) -> Dict[str, Any]:
        """
        Gibt Informationen zu einer Strategie zurück
        
        Args:
            strategy: Strategie-Name
            
        Returns:
            Dict[str, Any]: Dictionary mit Strategie-Informationen
        """
        # Strategie-Informationen
        strategy_info = {
            "ma_crossover": {
                "name": "Moving Average Crossover",
                "description": "Kauft, wenn der schnelle MA den langsamen MA von unten kreuzt, und verkauft, wenn er ihn von oben kreuzt.",
                "parameters": {
                    "fast_ma": {"type": "int", "default": 20, "min": 1, "max": 200, "description": "Periode des schnellen MA"},
                    "slow_ma": {"type": "int", "default": 50, "min": 1, "max": 200, "description": "Periode des langsamen MA"},
                    "sl_pct": {"type": "float", "default": 2.0, "min": 0.1, "max": 10.0, "description": "Stop Loss in Prozent"},
                    "tp_pct": {"type": "float", "default": 4.0, "min": 0.1, "max": 20.0, "description": "Take Profit in Prozent"},
                }
            },
            "rsi": {
                "name": "RSI Strategie",
                "description": "Kauft, wenn der RSI unter den überkauften Bereich fällt, und verkauft, wenn er über den überverkauften Bereich steigt.",
                "parameters": {
                    "rsi_period": {"type": "int", "default": 14, "min": 1, "max": 50, "description": "RSI-Periode"},
                    "overbought": {"type": "int", "default": 70, "min": 50, "max": 90, "description": "Überkauft-Niveau"},
                    "oversold": {"type": "int", "default": 30, "min": 10, "max": 50, "description": "Überverkauft-Niveau"},
                    "sl_pct": {"type": "float", "default": 2.0, "min": 0.1, "max": 10.0, "description": "Stop Loss in Prozent"},
                    "tp_pct": {"type": "float", "default": 4.0, "min": 0.1, "max": 20.0, "description": "Take Profit in Prozent"},
                }
            },
            "macd": {
                "name": "MACD Strategie",
                "description": "Kauft, wenn die MACD-Linie das Signal von unten kreuzt, und verkauft, wenn sie es von oben kreuzt.",
                "parameters": {
                    "fast_ema": {"type": "int", "default": 12, "min": 1, "max": 50, "description": "Schneller EMA"},
                    "slow_ema": {"type": "int", "default": 26, "min": 1, "max": 50, "description": "Langsamer EMA"},
                    "signal": {"type": "int", "default": 9, "min": 1, "max": 50, "description": "Signal-Periode"},
                    "sl_pct": {"type": "float", "default": 2.0, "min": 0.1, "max": 10.0, "description": "Stop Loss in Prozent"},
                    "tp_pct": {"type": "float", "default": 4.0, "min": 0.1, "max": 20.0, "description": "Take Profit in Prozent"},
                }
            },
            "bollinger": {
                "name": "Bollinger Bands",
                "description": "Kauft, wenn der Preis das untere Band berührt, und verkauft, wenn er das obere Band berührt.",
                "parameters": {
                    "period": {"type": "int", "default": 20, "min": 1, "max": 50, "description": "Bollinger-Periode"},
                    "std_dev": {"type": "float", "default": 2.0, "min": 0.5, "max": 4.0, "description": "Standardabweichungen"},
                    "sl_pct": {"type": "float", "default": 2.0, "min": 0.1, "max": 10.0, "description": "Stop Loss in Prozent"},
                    "tp_pct": {"type": "float", "default": 4.0, "min": 0.1, "max": 20.0, "description": "Take Profit in Prozent"},
                }
            },
        }
        
        return strategy_info.get(strategy, {"name": strategy, "description": "Keine Beschreibung verfügbar", "parameters": {}})

class CacheManager:
    """
    Manager für das Caching von Daten
    """
    
    def __init__(self, cache_dir: str = None):
        """
        Initialisiert den Cache-Manager
        
        Args:
            cache_dir: Verzeichnis für Cache-Dateien
        """
        if cache_dir is None:
            self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cache')
        else:
            self.cache_dir = cache_dir
        
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_file_path(self, key: str) -> str:
        """
        Gibt den Pfad zu einer Cache-Datei zurück
        
        Args:
            key: Schlüssel für die Cache-Datei
            
        Returns:
            str: Pfad zur Cache-Datei
        """
        # Ersetze ungültige Zeichen im Dateinamen
        safe_key = key.replace('/', '_').replace('\\', '_').replace(':', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.csv")
    
    def is_cache_valid(self, key: str, max_age_seconds: int = 86400) -> bool:
        """
        Prüft, ob eine Cache-Datei gültig ist
        
        Args:
            key: Schlüssel für die Cache-Datei
            max_age_seconds: Maximales Alter in Sekunden (Standard: 24 Stunden)
            
        Returns:
            bool: True, wenn die Cache-Datei gültig ist, sonst False
        """
        cache_file = self.get_cache_file_path(key)
        
        if not os.path.exists(cache_file):
            return False
        
        # Prüfe das Alter der Datei
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        return file_age.total_seconds() < max_age_seconds
    
    def get_from_cache(self, key: str) -> Optional[pd.DataFrame]:
        """
        Lädt Daten aus dem Cache
        
        Args:
            key: Schlüssel für die Cache-Datei
            
        Returns:
            Optional[pd.DataFrame]: DataFrame mit den Daten oder None, wenn nicht im Cache
        """
        cache_file = self.get_cache_file_path(key)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        except Exception as e:
            logger.error(f"Fehler beim Laden aus dem Cache: {str(e)}")
            return None
    
    def save_to_cache(self, key: str, df: pd.DataFrame) -> bool:
        """
        Speichert Daten im Cache
        
        Args:
            key: Schlüssel für die Cache-Datei
            df: DataFrame mit den zu speichernden Daten
            
        Returns:
            bool: True, wenn erfolgreich gespeichert, sonst False
        """
        cache_file = self.get_cache_file_path(key)
        
        try:
            df.to_csv(cache_file)
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern im Cache: {str(e)}")
            return False
    
    def clear_cache(self, key: str = None) -> bool:
        """
        Löscht Cache-Dateien
        
        Args:
            key: Schlüssel für die zu löschende Cache-Datei oder None für alle Dateien
            
        Returns:
            bool: True, wenn erfolgreich gelöscht, sonst False
        """
        try:
            if key is not None:
                cache_file = self.get_cache_file_path(key)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            else:
                # Lösche alle Dateien im Cache-Verzeichnis
                for file_name in os.listdir(self.cache_dir):
                    if file_name.endswith('.csv'):
                        os.remove(os.path.join(self.cache_dir, file_name))
            
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Caches: {str(e)}")
            return False
