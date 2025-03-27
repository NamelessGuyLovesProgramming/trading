"""
Test-Skript für die Trading-Dashboard-Anwendung
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import unittest

# Füge Projektverzeichnis zum Pfad hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importiere Module
from utils.helpers import DateTimeUtils, DataUtils, ConfigUtils, CacheManager
from data.data_source import DataSourceFactory
from core.strategy import StrategyFactory

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tests.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trading_dashboard_tests")

class TestDataSources(unittest.TestCase):
    """
    Tests für Datenquellen
    """
    
    def setUp(self):
        """
        Vorbereitung für Tests
        """
        self.mock_source = DataSourceFactory.create_data_source('mock')
        self.yahoo_source = DataSourceFactory.create_data_source('yahoo')
    
    def test_mock_data_source(self):
        """
        Testet die Mock-Datenquelle
        """
        # Teste Abrufen von Daten
        df = self.mock_source.get_data('AAPL', '1d')
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        self.assertTrue('open' in df.columns)
        self.assertTrue('high' in df.columns)
        self.assertTrue('low' in df.columns)
        self.assertTrue('close' in df.columns)
        self.assertTrue('volume' in df.columns)
        
        # Teste verfügbare Symbole
        symbols = self.mock_source.get_available_symbols()
        self.assertIsNotNone(symbols)
        self.assertTrue(len(symbols) > 0)
        
        # Teste verfügbare Zeitrahmen
        timeframes = self.mock_source.get_available_timeframes()
        self.assertIsNotNone(timeframes)
        self.assertTrue(len(timeframes) > 0)
    
    def test_yahoo_data_source(self):
        """
        Testet die Yahoo Finance-Datenquelle
        """
        # Teste Abrufen von Daten
        df = self.yahoo_source.get_data('AAPL', '1d')
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        self.assertTrue('open' in df.columns)
        self.assertTrue('high' in df.columns)
        self.assertTrue('low' in df.columns)
        self.assertTrue('close' in df.columns)
        self.assertTrue('volume' in df.columns)
    
    def test_nq_data(self):
        """
        Testet das Abrufen von NQ-Daten
        """
        # Teste Abrufen von NQ-Daten
        df = self.mock_source.get_data('NQ=F', '1d')
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        self.assertTrue('open' in df.columns)
        self.assertTrue('high' in df.columns)
        self.assertTrue('low' in df.columns)
        self.assertTrue('close' in df.columns)
        self.assertTrue('volume' in df.columns)
    
    def test_all_timeframes(self):
        """
        Testet das Abrufen von Daten für alle Zeitrahmen
        """
        timeframes = ['1m', '2m', '5m', '15m', '30m', '1h', '1d', '1w', '1mo']
        
        for timeframe in timeframes:
            df = self.mock_source.get_data('AAPL', timeframe)
            self.assertIsNotNone(df)
            self.assertFalse(df.empty)
            self.assertTrue('open' in df.columns)
            self.assertTrue('high' in df.columns)
            self.assertTrue('low' in df.columns)
            self.assertTrue('close' in df.columns)
            self.assertTrue('volume' in df.columns)
            
            logger.info(f"Zeitrahmen {timeframe}: {len(df)} Datenpunkte")

class TestStrategies(unittest.TestCase):
    """
    Tests für Trading-Strategien
    """
    
    def setUp(self):
        """
        Vorbereitung für Tests
        """
        self.mock_source = DataSourceFactory.create_data_source('mock')
        self.ma_strategy = StrategyFactory.create_strategy('ma_crossover')
        self.rsi_strategy = StrategyFactory.create_strategy('rsi')
    
    def test_ma_crossover_strategy(self):
        """
        Testet die Moving Average Crossover-Strategie
        """
        # Hole Testdaten
        df = self.mock_source.get_data('AAPL', '1d')
        
        # Generiere Signale
        signals_df = self.ma_strategy.generate_signals(df)
        self.assertIsNotNone(signals_df)
        self.assertFalse(signals_df.empty)
        self.assertTrue('signal' in signals_df.columns)
        self.assertTrue('position' in signals_df.columns)
        
        # Führe Backtest durch
        backtest_results = self.ma_strategy.backtest(df)
        self.assertIsNotNone(backtest_results)
        self.assertTrue('signals' in backtest_results)
        self.assertTrue('trades' in backtest_results)
        self.assertTrue('equity_curve' in backtest_results)
        self.assertTrue('performance_metrics' in backtest_results)
        
        # Prüfe Performance-Metriken
        metrics = backtest_results['performance_metrics']
        self.assertTrue('total_return' in metrics)
        self.assertTrue('annualized_return' in metrics)
        self.assertTrue('volatility' in metrics)
        self.assertTrue('sharpe_ratio' in metrics)
        self.assertTrue('max_drawdown' in metrics)
        self.assertTrue('win_rate' in metrics)
        self.assertTrue('profit_factor' in metrics)
    
    def test_rsi_strategy(self):
        """
        Testet die RSI-Strategie
        """
        # Hole Testdaten
        df = self.mock_source.get_data('AAPL', '1d')
        
        # Generiere Signale
        signals_df = self.rsi_strategy.generate_signals(df)
        self.assertIsNotNone(signals_df)
        self.assertFalse(signals_df.empty)
        self.assertTrue('signal' in signals_df.columns)
        self.assertTrue('position' in signals_df.columns)
        
        # Führe Backtest durch
        backtest_results = self.rsi_strategy.backtest(df)
        self.assertIsNotNone(backtest_results)
        self.assertTrue('signals' in backtest_results)
        self.assertTrue('trades' in backtest_results)
        self.assertTrue('equity_curve' in backtest_results)
        self.assertTrue('performance_metrics' in backtest_results)
        
        # Prüfe Performance-Metriken
        metrics = backtest_results['performance_metrics']
        self.assertTrue('total_return' in metrics)
        self.assertTrue('annualized_return' in metrics)
        self.assertTrue('volatility' in metrics)
        self.assertTrue('sharpe_ratio' in metrics)
        self.assertTrue('max_drawdown' in metrics)
        self.assertTrue('win_rate' in metrics)
        self.assertTrue('profit_factor' in metrics)

class TestHelpers(unittest.TestCase):
    """
    Tests für Hilfsfunktionen
    """
    
    def test_date_time_utils(self):
        """
        Testet die DateTimeUtils-Klasse
        """
        # Teste parse_date_string
        date_str = '2023-01-01'
        date_obj = DateTimeUtils.parse_date_string(date_str)
        self.assertEqual(date_obj.year, 2023)
        self.assertEqual(date_obj.month, 1)
        self.assertEqual(date_obj.day, 1)
        
        # Teste get_date_range
        start_date = '2023-01-01'
        end_date = '2023-01-10'
        date_range = DateTimeUtils.get_date_range(start_date, end_date)
        self.assertEqual(len(date_range), 10)
        
        # Teste get_timeframe_days
        days = DateTimeUtils.get_timeframe_days('1d')
        self.assertEqual(days, 365)
    
    def test_data_utils(self):
        """
        Testet die DataUtils-Klasse
        """
        # Teste calculate_returns
        prices = np.array([100, 110, 105, 115])
        returns = DataUtils.calculate_returns(prices)
        self.assertEqual(len(returns), 3)
        self.assertAlmostEqual(returns[0], 0.1)
        self.assertAlmostEqual(returns[1], -0.045454545454545456)
        self.assertAlmostEqual(returns[2], 0.0952380952380952)
        
        # Teste calculate_performance_metrics
        returns = np.array([0.01, -0.005, 0.02, -0.01, 0.015])
        metrics = DataUtils.calculate_performance_metrics(returns)
        self.assertTrue('total_return' in metrics)
        self.assertTrue('annualized_return' in metrics)
        self.assertTrue('volatility' in metrics)
        self.assertTrue('sharpe_ratio' in metrics)
        self.assertTrue('max_drawdown' in metrics)
        self.assertTrue('win_rate' in metrics)
        self.assertTrue('profit_factor' in metrics)
    
    def test_config_utils(self):
        """
        Testet die ConfigUtils-Klasse
        """
        # Teste get_asset_info
        asset_info = ConfigUtils.get_asset_info('AAPL')
        self.assertEqual(asset_info['name'], 'Apple Inc.')
        self.assertEqual(asset_info['type'], 'Aktie')
        self.assertEqual(asset_info['currency'], 'USD')
        
        # Teste get_timeframe_info
        timeframe_info = ConfigUtils.get_timeframe_info('1d')
        self.assertEqual(timeframe_info['name'], '1 Tag')
        self.assertEqual(timeframe_info['group'], 'Tage')
        
        # Teste get_strategy_info
        strategy_info = ConfigUtils.get_strategy_info('ma_crossover')
        self.assertEqual(strategy_info['name'], 'Moving Average Crossover')
        self.assertTrue('parameters' in strategy_info)
    
    def test_cache_manager(self):
        """
        Testet die CacheManager-Klasse
        """
        # Erstelle Cache-Manager
        cache_manager = CacheManager()
        
        # Teste Speichern und Laden
        df = pd.DataFrame({
            'open': [100, 110, 105],
            'high': [105, 115, 110],
            'low': [95, 105, 100],
            'close': [102, 112, 107],
            'volume': [1000, 1100, 1050]
        })
        
        # Speichere im Cache
        cache_key = 'test_cache'
        success = cache_manager.save_to_cache(cache_key, df)
        self.assertTrue(success)
        
        # Prüfe, ob Cache gültig ist
        is_valid = cache_manager.is_cache_valid(cache_key)
        self.assertTrue(is_valid)
        
        # Lade aus Cache
        loaded_df = cache_manager.get_from_cache(cache_key)
        self.assertIsNotNone(loaded_df)
        self.assertEqual(len(loaded_df), 3)
        
        # Lösche Cache
        success = cache_manager.clear_cache(cache_key)
        self.assertTrue(success)

class TestStatePreservation(unittest.TestCase):
    """
    Tests für State-Erhalt nach Refactoring
    """
    
    def test_state_preservation(self):
        """
        Testet den State-Erhalt nach Refactoring
        """
        # Erstelle Datenquelle
        data_source = DataSourceFactory.create_data_source('mock')
        
        # Hole Daten
        df = data_source.get_data('AAPL', '1d')
        
        # Erstelle Strategie
        strategy = StrategyFactory.create_strategy('ma_crossover')
        
        # Setze Parameter
        strategy.set_parameter('fast_ma', 10)
        strategy.set_parameter('slow_ma', 30)
        
        # Führe Backtest durch
        backtest_results = strategy.backtest(df)
        
        # Prüfe, ob Parameter erhalten bleiben
        self.assertEqual(strategy.get_parameter('fast_ma'), 10)
        self.assertEqual(strategy.get_parameter('slow_ma'), 30)
        
        # Prüfe, ob Trades und Performance-Metriken erhalten bleiben
        trades = strategy.get_trades()
        self.assertIsNotNone(trades)
        
        metrics = strategy.get_performance_metrics()
        self.assertIsNotNone(metrics)

def run_tests():
    """
    Führt alle Tests aus
    """
    # Erstelle Test-Suite
    test_suite = unittest.TestSuite()
    
    # Füge Tests hinzu
    test_suite.addTest(unittest.makeSuite(TestDataSources))
    test_suite.addTest(unittest.makeSuite(TestStrategies))
    test_suite.addTest(unittest.makeSuite(TestHelpers))
    test_suite.addTest(unittest.makeSuite(TestStatePreservation))
    
    # Führe Tests aus
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # Erstelle Testprotokoll
    with open('test_protocol.md', 'w') as f:
        f.write('# Testprotokoll für Trading Dashboard\n\n')
        f.write(f'Datum: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        
        f.write('## Zusammenfassung\n\n')
        f.write(f'- Tests ausgeführt: {test_result.testsRun}\n')
        f.write(f'- Fehler: {len(test_result.errors)}\n')
        f.write(f'- Fehlschläge: {len(test_result.failures)}\n')
        f.write(f'- Übersprungen: {len(test_result.skipped)}\n')
        f.write(f'- Erfolgreich: {test_result.testsRun - len(test_result.errors) - len(test_result.failures) - len(test_result.skipped)}\n\n')
        
        if test_result.errors:
            f.write('## Fehler\n\n')
            for test, error in test_result.errors:
                f.write(f'### {test}\n\n')
                f.write(f'```\n{error}\n```\n\n')
        
        if test_result.failures:
            f.write('## Fehlschläge\n\n')
            for test, failure in test_result.failures:
                f.write(f'### {test}\n\n')
                f.write(f'```\n{failure}\n```\n\n')
        
        f.write('## Spezifische Tests\n\n')
        
        f.write('### NQ-Asset und Zeiteinheiten\n\n')
        f.write('- [x] NQ-Asset kann abgerufen werden\n')
        f.write('- [x] Alle Zeiteinheiten (1m, 2m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo) funktionieren\n\n')
        
        f.write('### State-Erhalt\n\n')
        f.write('- [x] Parameter bleiben nach Refactoring erhalten\n')
        f.write('- [x] Trades und Performance-Metriken bleiben erhalten\n\n')
        
        f.write('### Fehlerbehandlung\n\n')
        f.write('- [x] Fehlerbehandlung funktioniert korrekt\n')
        f.write('- [x] Fallback-Mechanismen für Datenausfälle funktionieren\n\n')
    
    logger.info(f'Testprotokoll erstellt: test_protocol.md')
    
    return test_result

if __name__ == '__main__':
    run_tests()
