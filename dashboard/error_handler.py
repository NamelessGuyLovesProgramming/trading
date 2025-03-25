"""
Verbesserte Fehlerbehandlung für das Trading Dashboard
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback
import logging

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard_errors.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trading_dashboard")

class ErrorHandler:
    """
    Zentrale Klasse zur Fehlerbehandlung im Trading Dashboard
    """
    
    @staticmethod
    def handle_data_error(error, context="Datenverarbeitung"):
        """
        Behandelt Fehler bei der Datenverarbeitung
        
        Args:
            error: Der aufgetretene Fehler
            context: Kontext, in dem der Fehler aufgetreten ist
        
        Returns:
            dict: Fehlermeldung und Handlungsempfehlung
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        logger.error(f"Fehler bei {context}: {error_type} - {error_message}")
        logger.debug(traceback.format_exc())
        
        # Spezifische Fehlerbehandlung basierend auf Fehlertyp
        if "Timeout" in error_type or "ConnectionError" in error_type:
            return {
                "type": "connection",
                "message": "Verbindungsproblem beim Datenabruf",
                "user_action": "Bitte überprüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.",
                "fallback_available": True
            }
        elif "KeyError" in error_type or "ValueError" in error_type:
            return {
                "type": "data_format",
                "message": "Problem mit dem Datenformat",
                "user_action": "Die angeforderten Daten sind nicht im erwarteten Format verfügbar.",
                "fallback_available": True
            }
        elif "EmptyDataError" in error_type or "empty" in error_message.lower():
            return {
                "type": "no_data",
                "message": "Keine Daten verfügbar",
                "user_action": "Für das ausgewählte Asset und den Zeitraum sind keine Daten verfügbar. Bitte wählen Sie einen anderen Zeitraum oder ein anderes Asset.",
                "fallback_available": False
            }
        else:
            return {
                "type": "unknown",
                "message": f"Unerwarteter Fehler: {error_message}",
                "user_action": "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.",
                "fallback_available": True
            }
    
    @staticmethod
    def handle_ui_error(error, component="UI-Komponente"):
        """
        Behandelt Fehler in der Benutzeroberfläche
        
        Args:
            error: Der aufgetretene Fehler
            component: Die betroffene UI-Komponente
        
        Returns:
            dict: Fehlermeldung und Handlungsempfehlung
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        logger.error(f"UI-Fehler in {component}: {error_type} - {error_message}")
        logger.debug(traceback.format_exc())
        
        return {
            "type": "ui_error",
            "message": f"Fehler in der Benutzeroberfläche: {error_message}",
            "user_action": "Bitte aktualisieren Sie die Seite und versuchen Sie es erneut.",
            "component": component
        }
    
    @staticmethod
    def create_error_message(error_info):
        """
        Erstellt eine benutzerfreundliche Fehlermeldung
        
        Args:
            error_info: Informationen zum Fehler
        
        Returns:
            str: Formatierte Fehlermeldung
        """
        message = f"⚠️ {error_info['message']}\n\n"
        message += f"Empfehlung: {error_info['user_action']}"
        
        if error_info.get('fallback_available', False):
            message += "\n\nEs werden Ersatzdaten angezeigt, die möglicherweise nicht aktuell sind."
        
        return message
    
    @staticmethod
    def get_fallback_data(asset_type, timeframe):
        """
        Liefert Fallback-Daten für den Fall, dass keine aktuellen Daten verfügbar sind
        
        Args:
            asset_type: Typ des Assets (Aktie, Krypto, Forex)
            timeframe: Zeitrahmen der Daten
        
        Returns:
            pd.DataFrame: Fallback-Daten
        """
        logger.info(f"Verwende Fallback-Daten für {asset_type} mit Zeitrahmen {timeframe}")
        
        # Lade gecachte Daten, falls vorhanden
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cache')
        
        # Fallback-Dateinamen basierend auf Asset-Typ
        fallback_files = {
            "Aktien": "AAPL_1d_1y.csv",
            "Krypto": "BTC-USD_1d_1y.csv",
            "Forex": "EUR-USD_1d_1y.csv",
            "Futures": "NQ_Futures_1d_1y.csv"
        }
        
        file_name = fallback_files.get(asset_type, fallback_files["Aktien"])
        file_path = os.path.join(cache_dir, file_name)
        
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                logger.info(f"Fallback-Daten geladen: {len(df)} Datenpunkte")
                return df
        except Exception as e:
            logger.error(f"Fehler beim Laden der Fallback-Daten: {e}")
        
        # Wenn keine gecachten Daten verfügbar sind, generiere synthetische Daten
        logger.info("Generiere synthetische Fallback-Daten")
        
        end_date = datetime.now()
        if timeframe == "1h":
            start_date = end_date - timedelta(days=7)
            freq = "H"
        elif timeframe == "1d":
            start_date = end_date - timedelta(days=365)
            freq = "D"
        else:
            start_date = end_date - timedelta(days=365*2)
            freq = "W"
        
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Basis-Preis je nach Asset-Typ
        if asset_type == "Aktien":
            base_price = 150.0
        elif asset_type == "Krypto":
            base_price = 50000.0
        elif asset_type == "Forex":
            base_price = 1.1
        elif asset_type == "Futures":
            base_price = 17000.0
        else:
            base_price = 100.0
        
        # Generiere synthetische OHLCV-Daten
        np.random.seed(42)  # Für reproduzierbare Ergebnisse
        
        price_data = []
        current_price = base_price
        
        for i in range(len(date_range)):
            daily_return = np.random.normal(0.0001, 0.02)
            current_price *= (1 + daily_return)
            
            high_low_range = current_price * 0.02
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            close_price = current_price
            high_price = max(open_price, close_price) + abs(np.random.normal(0, high_low_range/2))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, high_low_range/2))
            
            volume = np.random.randint(1000000, 10000000)
            
            price_data.append({
                'date': date_range[i],
                'Open': open_price,
                'High': high_price,
                'Low': low_price,
                'Close': close_price,
                'Volume': volume,
                'Adj Close': close_price
            })
        
        df = pd.DataFrame(price_data)
        df.set_index('date', inplace=True)
        
        # Speichere die synthetischen Daten im Cache für zukünftige Verwendung
        try:
            os.makedirs(cache_dir, exist_ok=True)
            df.to_csv(os.path.join(cache_dir, f"synthetic_{asset_type}_{timeframe}.csv"))
        except Exception as e:
            logger.error(f"Fehler beim Speichern der synthetischen Daten: {e}")
        
        return df
