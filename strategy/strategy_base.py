"""
Strategie-Basisklasse für Trading Dashboard
Definiert die Schnittstelle für Handelsstrategien
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class Strategy(ABC):
    """
    Abstrakte Basisklasse für Handelsstrategien
    """
    
    def __init__(self, name="Basisstrategie"):
        """
        Initialisiert die Strategie
        
        Args:
            name (str): Name der Strategie
        """
        self.name = name
        self.parameters = {}
        
    @abstractmethod
    def generate_signals(self, data):
        """
        Generiert Handelssignale basierend auf den Daten
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            
        Returns:
            pandas.Series or pandas.DataFrame: Handelssignale (1 für Kauf, -1 für Verkauf, 0 für Halten)
        """
        pass
    
    def calculate_stop_loss(self, data, index):
        """
        Berechnet den Stop-Loss für einen Trade
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Stop-Loss-Preis
        """
        # Standardimplementierung: 5% unter dem Einstiegspreis
        return data['Close'].iloc[index] * 0.95
    
    def calculate_take_profit(self, data, index):
        """
        Berechnet den Take-Profit für einen Trade
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Take-Profit-Preis
        """
        # Standardimplementierung: 10% über dem Einstiegspreis
        return data['Close'].iloc[index] * 1.10
    
    def set_parameters(self, **kwargs):
        """
        Setzt die Parameter der Strategie
        
        Args:
            **kwargs: Parameter als Schlüssel-Wert-Paare
        """
        self.parameters.update(kwargs)
        
    def get_parameters(self):
        """
        Gibt die Parameter der Strategie zurück
        
        Returns:
            dict: Parameter der Strategie
        """
        return self.parameters
    
    def optimize(self, data, param_grid, metric='total_return', backtest_engine=None):
        """
        Optimiert die Parameter der Strategie
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            param_grid (dict): Dictionary mit Parameternamen als Schlüssel und Listen von Werten
            metric (str): Metrik, die optimiert werden soll
            backtest_engine: Backtesting-Engine für die Optimierung
            
        Returns:
            tuple: (Beste Parameter, Beste Metrik, Alle Ergebnisse)
        """
        if backtest_engine is None:
            from backtesting.backtest_engine import BacktestEngine
            backtest_engine = BacktestEngine()
            
        # Generiere alle Parameterkombinationen
        import itertools
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        # Initialisiere Ergebnisse
        results = []
        best_metric_value = float('-inf')
        best_params = None
        
        # Teste jede Parameterkombination
        for params in param_combinations:
            # Setze Parameter
            param_dict = dict(zip(param_names, params))
            self.set_parameters(**param_dict)
            
            # Führe Backtest durch
            backtest_result = backtest_engine.run(data, self)
            
            # Extrahiere Metrik
            metric_value = backtest_result['metrics'][metric]
            
            # Speichere Ergebnis
            result = {
                'params': param_dict,
                'metrics': backtest_result['metrics']
            }
            results.append(result)
            
            # Aktualisiere beste Parameter
            if metric_value > best_metric_value:
                best_metric_value = metric_value
                best_params = param_dict
                
        # Setze beste Parameter
        if best_params:
            self.set_parameters(**best_params)
            
        return best_params, best_metric_value, results
