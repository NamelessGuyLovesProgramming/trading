"""
Test-Skript für das Datenabfragemodul
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Importiere die Module
from data.data_fetcher import DataFetcher
from data.data_processor import DataProcessor

def test_data_fetcher():
    """
    Testet die Funktionalität des DataFetcher-Moduls
    """
    print("=== Test des DataFetcher-Moduls ===")
    
    # Initialisiere DataFetcher
    data_dir = Path(parent_dir) / 'data'
    cache_dir = data_dir / 'cache'
    fetcher = DataFetcher(cache_dir=cache_dir)
    
    # Teste das Abrufen von Daten für ein einzelnes Symbol
    symbol = 'AAPL'
    print(f"\nAbrufen von Daten für {symbol}...")
    data = fetcher.get_stock_data(symbol, interval='1d', range='1y')
    
    if data is not None and not data.empty:
        print(f"Erfolgreich Daten für {symbol} abgerufen!")
        print(f"Datengröße: {data.shape}")
        print(f"Zeitraum: {data.index.min()} bis {data.index.max()}")
        print(f"Spalten: {data.columns.tolist()}")
        print("\nErste 5 Zeilen:")
        print(data.head())
    else:
        print(f"Fehler beim Abrufen von Daten für {symbol}")
    
    # Teste das Abrufen von Daten für mehrere Symbole
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    print(f"\nAbrufen von Daten für mehrere Symbole: {symbols}...")
    multi_data = fetcher.get_multiple_stocks(symbols, interval='1d', range='1mo')
    
    if multi_data:
        print(f"Erfolgreich Daten für mehrere Symbole abgerufen!")
        for sym, df in multi_data.items():
            if df is not None and not df.empty:
                print(f"{sym}: {df.shape} Datenpunkte")
            else:
                print(f"{sym}: Keine Daten")
    else:
        print("Fehler beim Abrufen von Daten für mehrere Symbole")
    
    return data

def test_data_processor(data):
    """
    Testet die Funktionalität des DataProcessor-Moduls
    """
    print("\n=== Test des DataProcessor-Moduls ===")
    
    if data is None or data.empty:
        print("Keine Daten zum Verarbeiten verfügbar")
        return
    
    # Initialisiere DataProcessor
    processor = DataProcessor()
    
    # Teste das Hinzufügen von Indikatoren
    print("\nHinzufügen von technischen Indikatoren...")
    data_with_indicators = processor.add_indicators(data)
    
    if data_with_indicators is not None:
        print("Erfolgreich Indikatoren hinzugefügt!")
        print(f"Ursprüngliche Spalten: {data.columns.tolist()}")
        print(f"Neue Spalten: {data_with_indicators.columns.tolist()}")
        print("\nErste 5 Zeilen mit Indikatoren:")
        print(data_with_indicators.head())
    else:
        print("Fehler beim Hinzufügen von Indikatoren")
    
    # Teste die Berechnung von Stop-Loss und Take-Profit
    print("\nBerechnung von Stop-Loss und Take-Profit...")
    stop_loss, take_profit = processor.calculate_stop_loss_take_profit(data)
    
    print(f"Stop-Loss: {stop_loss:.2f}")
    print(f"Take-Profit: {take_profit:.2f}")
    print(f"Aktueller Preis: {data['Close'].iloc[-1]:.2f}")
    
    # Visualisiere einige Indikatoren
    print("\nVisualisierung von Indikatoren...")
    try:
        plt.figure(figsize=(12, 8))
        
        # Plot Preisdaten und gleitende Durchschnitte
        plt.subplot(3, 1, 1)
        plt.plot(data_with_indicators.index, data_with_indicators['Close'], label='Schlusskurs')
        plt.plot(data_with_indicators.index, data_with_indicators['SMA_20'], label='SMA 20')
        plt.plot(data_with_indicators.index, data_with_indicators['SMA_50'], label='SMA 50')
        plt.title('Preisdaten und gleitende Durchschnitte')
        plt.legend()
        
        # Plot RSI
        plt.subplot(3, 1, 2)
        plt.plot(data_with_indicators.index, data_with_indicators['RSI_14'], label='RSI 14')
        plt.axhline(y=70, color='r', linestyle='-', alpha=0.3)
        plt.axhline(y=30, color='g', linestyle='-', alpha=0.3)
        plt.title('Relative Strength Index (RSI)')
        plt.legend()
        
        # Plot MACD
        plt.subplot(3, 1, 3)
        plt.plot(data_with_indicators.index, data_with_indicators['MACD'], label='MACD')
        plt.plot(data_with_indicators.index, data_with_indicators['MACD_Signal'], label='Signal')
        plt.bar(data_with_indicators.index, data_with_indicators['MACD_Hist'], label='Histogramm', alpha=0.3)
        plt.title('Moving Average Convergence Divergence (MACD)')
        plt.legend()
        
        plt.tight_layout()
        
        # Speichere die Grafik
        output_dir = Path(parent_dir) / 'data' / 'output'
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(output_dir / 'indicators_test.png')
        print(f"Grafik gespeichert unter: {output_dir / 'indicators_test.png'}")
        
    except Exception as e:
        print(f"Fehler bei der Visualisierung: {e}")

if __name__ == "__main__":
    # Führe Tests aus
    stock_data = test_data_fetcher()
    test_data_processor(stock_data)
    
    print("\n=== Tests abgeschlossen ===")
