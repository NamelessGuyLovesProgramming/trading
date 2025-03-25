import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path
import yfinance as yf
import requests


class NQDataFetcher:
    """
    Spezialisierte Klasse zum Abrufen von NASDAQ 100 Futures (NQ) Daten
    """

    def __init__(self, cache_dir=None):
        """
        Initialisiert den NQDataFetcher

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

    def get_nq_futures_data(self, interval='1d', range_val='1y', use_cache=True, force_refresh=False):
        """
        Ruft NQ Futures Daten für ein bestimmtes Zeitintervall ab

        Args:
            interval (str): Zeitintervall ('1m', '5m', '15m', '30m', '60m', '1h', '1d', '1wk', '1mo')
            range_val (str): Zeitraum ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            use_cache (bool): Ob der Cache verwendet werden soll
            force_refresh (bool): Ob die Daten unabhängig vom Cache neu abgerufen werden sollen

        Returns:
            pandas.DataFrame: DataFrame mit den NQ Futures Daten
        """
        # Standardmäßig verwenden wir das generische NQ Futures Symbol
        symbol = "NQ=F"

        # Alternativ könnten wir einen spezifischen Kontrakt verwenden
        # Aktuelle verfügbare Kontrakte: NQH24, NQM24, NQU24, NQZ24
        # symbol = "NQH24.CME"  # März 2024 Kontrakt

        cache_file = self.cache_dir / f"NQ_Futures_{interval}_{range_val}.csv"

        # Prüfe, ob Cache verwendet werden soll und Datei existiert
        if use_cache and cache_file.exists() and not force_refresh:
            # Prüfe, ob Cache aktuell ist (für tägliche Daten nicht älter als 1 Tag)
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if interval in ['1d', '1wk', '1mo'] and cache_age.days < 1:
                print(f"Verwende gecachte NQ Futures Daten")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
            elif interval.endswith('m') and cache_age.seconds < 3600:  # Für Minutendaten: 1 Stunde Cache
                print(f"Verwende gecachte NQ Futures Daten")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)

        # Versuche zuerst, Daten über yfinance abzurufen
        try:
            print(f"Rufe NQ Futures Daten über yfinance ab...")

            # Stelle sicher, dass Intervall korrekt formatiert ist (yfinance verwendet '1h' statt '60m')
            if interval == '60m':
                yf_interval = '1h'
            else:
                yf_interval = interval

            ticker = yf.Ticker(symbol)
            df = ticker.history(period=range_val, interval=yf_interval)

            if df.empty:
                print(f"Keine Daten für {symbol} mit period={range_val}, interval={yf_interval}.")
                # Verwende die direkte Download-Methode als Fallback
                df = yf.download(symbol, period=range_val, interval=yf_interval)

            if not df.empty:
                # Standardisiere Spaltennamen
                df.columns = [col if col != 'Stock Splits' else 'Splits' for col in df.columns]

                # Speichere Daten im Cache
                if use_cache:
                    df.to_csv(cache_file)

                print(f"Erfolgreich NQ Futures Daten abgerufen, {len(df)} Datenpunkte")
                return df

        except Exception as e:
            print(f"Fehler beim Abrufen der NQ Futures Daten über yfinance: {e}")

        # Wenn yfinance fehlschlägt, versuche die Twelve Data API (benötigt einen API-Schlüssel)
        try:
            # Diese Beispielimplementierung nutzt die Twelve Data API
            # Registrieren Sie sich für einen kostenlosen API-Schlüssel: https://twelvedata.com/
            print("Versuche Twelve Data API als Fallback...")

            # Setzen Sie Ihren API-Schlüssel hier ein oder in einer .env-Datei
            api_key = os.getenv("TWELVE_DATA_API_KEY", "")

            if not api_key:
                print(
                    "Kein API-Schlüssel für Twelve Data gefunden. Bitte setzen Sie die Umgebungsvariable TWELVE_DATA_API_KEY.")
                return pd.DataFrame()

            # Konvertiere Intervall zum Twelve Data-Format
            interval_map = {
                '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
                '60m': '1h', '1h': '1h', '1d': '1day', '1wk': '1week', '1mo': '1month'
            }
            td_interval = interval_map.get(interval, '1day')

            # Bestimme die Anzahl der Datenpunkte basierend auf dem Zeitraum
            # Free API begrenzt auf 5000 Datenpunkte
            output_size = 5000

            # Konstruiere die API-URL
            url = f"https://api.twelvedata.com/time_series"
            params = {
                "symbol": "NQ:GLOIU",  # NASDAQ 100 Futures Symbol bei Twelve Data
                "interval": td_interval,
                "outputsize": output_size,
                "apikey": api_key,
                "format": "JSON"
            }

            response = requests.get(url, params=params)
            data = response.json()

            if "values" in data:
                # Konvertiere JSON zu Pandas DataFrame
                values = data["values"]
                df = pd.DataFrame(values)

                # Konvertiere Spalten
                df["datetime"] = pd.to_datetime(df["datetime"])
                for col in ["open", "high", "low", "close", "volume"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col])

                # Setze datetime als Index und benenne Spalten um
                df.set_index("datetime", inplace=True)
                df.rename(columns={
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume"
                }, inplace=True)

                # Sortiere Daten chronologisch
                df.sort_index(inplace=True)

                # Speichere Daten im Cache
                if use_cache:
                    df.to_csv(cache_file)

                print(f"Erfolgreich NQ Futures Daten von Twelve Data abgerufen, {len(df)} Datenpunkte")

                print("\n----- NQ DATA DEBUG -----")
                print("Datentyp:", type(df))
                print("Spalten:", df.columns.tolist())
                print("Index-Typ:", type(df.index))
                print("Erste Zeilen:")
                print(df.head(3))
                print("Datentypen der Spalten:")
                print(df.dtypes)
                print("-------------------------\n")

                # Nach dem Abrufen der NQ-Daten, vor der Rückgabe
                # Standardisiere Spaltennamen (erster Buchstabe groß)
                column_mapping = {
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }

                # Benenne Spalten um, falls nötig
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns:
                        df.rename(columns={old_col: new_col}, inplace=True)

                    # Nach dem Abrufen der NQ-Daten, vor der Rückgabe
                    # Stelle sicher, dass der Index ein DatetimeIndex ist
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)

                # Stelle sicher, dass die Zeitzone korrekt ist (falls nötig)
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                
                # Stelle sicher, dass keine tzinfo-Attribute vorhanden sind
                df.index = pd.DatetimeIndex([dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') else dt for dt in df.index])


                return df
            else:
                print(f"Fehler bei Twelve Data-Anfrage: {data.get('message', 'Unbekannter Fehler')}")

        except Exception as e:
            print(f"Fehler beim Abrufen der Twelve Data API: {e}")

        # Wenn alle Versuche fehlschlagen, gib einen leeren DataFrame zurück
        print("Alle Versuche, NQ Futures Daten abzurufen, sind fehlgeschlagen.")
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'])


# Beispiel zur Verwendung
if __name__ == "__main__":
    fetcher = NQDataFetcher()
    # Test für verschiedene Zeitrahmen
    intervals = ['1h', '1d']
    for interval in intervals:
        print(f"\nTestdaten für Interval {interval}:")
        data = fetcher.get_nq_futures_data(interval=interval, range_val='1mo')
        if not data.empty:
            print(data.head())
            print(f"Datenpunkte: {len(data)}")
            print(f"Zeitraum: {data.index.min()} bis {data.index.max()}")