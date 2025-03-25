"""
Dieses Skript korrigiert die Importpfade und startet das Trading Dashboard
"""

import os
import sys
from pathlib import Path

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)  # Wichtig: Am Anfang des Pfads einfügen

# Überprüfe, ob die Module gefunden werden können
print(f"Projektpfad: {current_dir}")
print(f"Python-Suchpfad enthält Projektpfad: {current_dir in sys.path}")

try:
    # Importiere notwendige Module zum Testen
    print("Versuche Module zu importieren...")
    from backtesting.backtest_engine import BacktestEngine

    print("✓ backtest_engine erfolgreich importiert")
    from data.data_fetcher import DataFetcher

    print("✓ data_fetcher erfolgreich importiert")
    from dashboard.app import app

    print("✓ app erfolgreich importiert")

    # Starte das Dashboard
    print("\nStarte Trading Dashboard auf http://localhost:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
except Exception as e:
    print(f"Fehler beim Import: {e}")
    print("\nVersuche einen alternativen Ansatz...")

    # Erstelle leere __init__.py Dateien in jedem Verzeichnis
    for folder in ['backtesting', 'data', 'strategy', 'dashboard']:
        init_file = os.path.join(current_dir, folder, '__init__.py')
        if not os.path.exists(init_file):
            print(f"Erstelle {init_file}")
            with open(init_file, 'w') as f:
                pass  # Erstelle eine leere Datei

    print("\nBitte starten Sie das Programm erneut mit: python fix_imports.py")