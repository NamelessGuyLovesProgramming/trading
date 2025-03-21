"""
Test-Skript für das gesamte Trading Dashboard System
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Importiere die Module
from data.data_fetcher import DataFetcher
from data.data_processor import DataProcessor
from backtesting.backtest_engine import BacktestEngine
from strategy.example_strategies import MovingAverageCrossover, RSIStrategy, MACDStrategy, BollingerBandsStrategy

def test_integration():
    """
    Führt einen End-to-End-Test des gesamten Systems durch
    """
    print("=== Trading Dashboard System-Test ===")
    
    # Initialisiere Komponenten
    print("\n1. Initialisiere Komponenten...")
    data_dir = Path(current_dir) / 'data'
    cache_dir = data_dir / 'cache'
    output_dir = Path(current_dir) / 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    fetcher = DataFetcher(cache_dir=cache_dir)
    processor = DataProcessor()
    backtest_engine = BacktestEngine(initial_capital=50000.0)
    
    # Teste Datenabfrage
    print("\n2. Teste Datenabfrage...")
    symbol = 'AAPL'
    interval = '1d'
    range_val = '1y'
    
    data = fetcher.get_stock_data(symbol, interval, range_val)
    
    if data is not None and not data.empty:
        print(f"✓ Erfolgreich Daten für {symbol} abgerufen")
        print(f"  Datengröße: {data.shape}")
        print(f"  Zeitraum: {data.index.min()} bis {data.index.max()}")
    else:
        print(f"✗ Fehler beim Abrufen von Daten für {symbol}")
        return
    
    # Teste Datenverarbeitung
    print("\n3. Teste Datenverarbeitung...")
    data_with_indicators = processor.add_indicators(data)
    
    if 'SMA_20' in data_with_indicators.columns and 'RSI_14' in data_with_indicators.columns:
        print("✓ Erfolgreich technische Indikatoren hinzugefügt")
        print(f"  Verfügbare Indikatoren: {', '.join([col for col in data_with_indicators.columns if col not in data.columns])}")
    else:
        print("✗ Fehler beim Hinzufügen von technischen Indikatoren")
    
    # Teste Strategien
    print("\n4. Teste Handelsstrategien...")
    strategies = [
        ("Moving Average Crossover", MovingAverageCrossover(short_window=20, long_window=50)),
        ("RSI Strategy", RSIStrategy(rsi_window=14, overbought=70, oversold=30)),
        ("MACD Strategy", MACDStrategy(fast=12, slow=26, signal=9)),
        ("Bollinger Bands Strategy", BollingerBandsStrategy(window=20, num_std=2))
    ]
    
    for name, strategy in strategies:
        print(f"\nTeste {name}...")
        signals = strategy.generate_signals(data_with_indicators)
        
        if 'Signal' in signals.columns:
            buy_signals = signals[signals['Signal'] == 1]
            sell_signals = signals[signals['Signal'] == -1]
            
            print(f"✓ Erfolgreich Signale generiert")
            print(f"  Kaufsignale: {len(buy_signals)}")
            print(f"  Verkaufssignale: {len(sell_signals)}")
            
            # Teste Stop-Loss und Take-Profit
            if len(buy_signals) > 0:
                index = buy_signals.index[0]
                idx = signals.index.get_loc(index)
                
                stop_loss = strategy.calculate_stop_loss(signals, idx)
                take_profit = strategy.calculate_take_profit(signals, idx)
                
                print(f"  Stop-Loss: {stop_loss:.2f}")
                print(f"  Take-Profit: {take_profit:.2f}")
                print(f"  Aktueller Preis: {signals['Close'].iloc[idx]:.2f}")
        else:
            print(f"✗ Fehler beim Generieren von Signalen für {name}")
    
    # Teste Backtesting
    print("\n5. Teste Backtesting-Engine...")
    strategy = MovingAverageCrossover(short_window=20, long_window=50)
    
    results = backtest_engine.run(data_with_indicators, strategy)
    
    if results and 'metrics' in results:
        print("✓ Erfolgreich Backtest durchgeführt")
        print(f"  Gesamtrendite: {results['metrics']['total_return']:.2%}")
        print(f"  Gewinnrate: {results['metrics']['win_rate']:.2%}")
        print(f"  Anzahl Trades: {results['metrics']['num_trades']}")
        print(f"  Max. Drawdown: {results['metrics']['max_drawdown']:.2%}")
        
        # Visualisiere Ergebnisse
        print("\n6. Visualisiere Backtesting-Ergebnisse...")
        fig = backtest_engine.plot_results(results, output_dir=output_dir)
        
        # Generiere HTML-Bericht
        report_path = backtest_engine.generate_report(results, output_dir=output_dir)
        print(f"  HTML-Bericht gespeichert unter: {report_path}")
    else:
        print("✗ Fehler beim Durchführen des Backtests")
    
    print("\n=== System-Test abgeschlossen ===")
    print("\nDas Trading Dashboard kann mit 'python run.py' gestartet werden.")

if __name__ == "__main__":
    test_integration()
