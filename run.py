"""
Hauptskript zum Starten des Trading Dashboards
"""

import os
import sys
from pathlib import Path

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Importiere die Dashboard-App
from dashboard.app import app

if __name__ == "__main__":
    print("Starte Trading Dashboard auf http://localhost:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
