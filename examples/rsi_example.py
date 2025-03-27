"""
Beispiel für die Verwendung der RSI Strategie
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import matplotlib.pyplot as plt

# Füge Projektverzeichnis zum Pfad hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importiere Module
from data.data_source import DataSourceFactory
from core.strategy import StrategyFactory

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rsi_example.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("rsi_example")

def run_rsi_example():
    """
    Führt ein Beispiel für die RSI Strategie aus
    """
    try:
        # Erstelle Datenquelle
        data_source = DataSourceFactory.create_data_source('yahoo')
        
        # Hole Daten für NQ Futures
        symbol = 'NQ=F'
        timeframe = '1d'
        
        logger.info(f"Hole Daten für {symbol} ({timeframe})...")
        df = data_source.get_data(symbol, timeframe)
        
        if df.empty:
            logger.error(f"Keine Daten für {symbol} gefunden")
            return
        
        logger.info(f"Daten für {symbol} erfolgreich abgerufen: {len(df)} Datenpunkte")
        
        # Erstelle RSI Strategie
        strategy = StrategyFactory.create_strategy('rsi')
        
        # Setze Parameter
        strategy.set_parameter('rsi_period', 14)
        strategy.set_parameter('overbought', 70)
        strategy.set_parameter('oversold', 30)
        strategy.set_parameter('sl_pct', 2.0)
        strategy.set_parameter('tp_pct', 4.0)
        
        logger.info(f"Führe Backtest für {symbol} mit RSI Strategie durch...")
        
        # Führe Backtest durch
        backtest_results = strategy.backtest(df)
        
        # Zeige Ergebnisse
        signals_df = backtest_results['signals']
        trades = backtest_results['trades']
        equity_curve = backtest_results['equity_curve']
        performance_metrics = backtest_results['performance_metrics']
        
        logger.info("Backtest abgeschlossen")
        logger.info(f"Anzahl der Trades: {len(trades)}")
        logger.info(f"Performance-Metriken:")
        for key, value in performance_metrics.items():
            logger.info(f"  {key}: {value:.4f}")
        
        # Speichere Ergebnisse
        signals_df.to_csv('rsi_signals.csv')
        pd.DataFrame(trades).to_csv('rsi_trades.csv')
        equity_curve.to_csv('rsi_equity_curve.csv')
        
        logger.info("Ergebnisse gespeichert")
        
        # Erstelle Plots
        plt.figure(figsize=(12, 10))
        
        # Plot 1: Preise
        plt.subplot(3, 1, 1)
        plt.plot(signals_df.index, signals_df['close'], label='Close')
        
        # Markiere Kauf- und Verkaufssignale
        buy_signals = signals_df[signals_df['signal'] == 1]
        sell_signals = signals_df[signals_df['signal'] == -1]
        
        plt.scatter(buy_signals.index, buy_signals['close'], marker='^', color='g', label='Buy Signal')
        plt.scatter(sell_signals.index, sell_signals['close'], marker='v', color='r', label='Sell Signal')
        
        plt.title(f'RSI Strategie - {symbol}')
        plt.ylabel('Preis')
        plt.legend()
        plt.grid(True)
        
        # Plot 2: RSI
        plt.subplot(3, 1, 2)
        plt.plot(signals_df.index, signals_df['rsi'], label='RSI')
        plt.axhline(y=strategy.get_parameter('overbought'), color='r', linestyle='--', label='Überkauft')
        plt.axhline(y=strategy.get_parameter('oversold'), color='g', linestyle='--', label='Überverkauft')
        
        plt.title('RSI Indikator')
        plt.ylabel('RSI')
        plt.legend()
        plt.grid(True)
        
        # Plot 3: Equity-Kurve
        plt.subplot(3, 1, 3)
        plt.plot(equity_curve.index, equity_curve, label='Equity Curve')
        plt.title('Equity-Kurve')
        plt.xlabel('Datum')
        plt.ylabel('Kapital')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig('rsi_results.png')
        
        logger.info("Plots erstellt und gespeichert")
        
        return backtest_results
    
    except Exception as e:
        logger.error(f"Fehler beim Ausführen des Beispiels: {str(e)}")
        return None

if __name__ == '__main__':
    run_rsi_example()
