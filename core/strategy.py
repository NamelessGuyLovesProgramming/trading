"""
Abstrakte Basisklasse für Trading-Strategien
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from abc import ABC, abstractmethod

# Importiere Hilfsfunktionen
from utils.helpers import DateTimeUtils, DataUtils

# Logger konfigurieren
logger = logging.getLogger("trading_dashboard.strategy")

class Strategy(ABC):
    """
    Abstrakte Basisklasse für Trading-Strategien
    
    Diese Klasse definiert die Schnittstelle für alle Trading-Strategien im Dashboard.
    Konkrete Implementierungen müssen die abstrakten Methoden implementieren.
    """
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any] = None):
        """
        Initialisiert die Strategie
        
        Args:
            name: Name der Strategie
            description: Beschreibung der Strategie
            parameters: Parameter der Strategie (optional)
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.trades = []
        self.performance_metrics = {}
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generiert Handelssignale basierend auf den Daten
        
        Args:
            df: DataFrame mit OHLCV-Daten
            
        Returns:
            pd.DataFrame: DataFrame mit Handelssignalen
        """
        pass
    
    @abstractmethod
    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        Führt einen Backtest der Strategie durch
        
        Args:
            df: DataFrame mit OHLCV-Daten
            initial_capital: Anfangskapital
            
        Returns:
            Dict[str, Any]: Dictionary mit Backtest-Ergebnissen
        """
        pass
    
    def set_parameter(self, name: str, value: Any) -> None:
        """
        Setzt einen Parameter der Strategie
        
        Args:
            name: Name des Parameters
            value: Wert des Parameters
        """
        self.parameters[name] = value
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Gibt den Wert eines Parameters zurück
        
        Args:
            name: Name des Parameters
            default: Standardwert, falls der Parameter nicht existiert
            
        Returns:
            Any: Wert des Parameters
        """
        return self.parameters.get(name, default)
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Gibt alle Parameter zurück
        
        Returns:
            Dict[str, Any]: Dictionary mit allen Parametern
        """
        return self.parameters
    
    def get_trades(self) -> List[Dict[str, Any]]:
        """
        Gibt alle Trades zurück
        
        Returns:
            List[Dict[str, Any]]: Liste von Dictionaries mit Trade-Informationen
        """
        return self.trades
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Gibt die Performance-Metriken zurück
        
        Returns:
            Dict[str, float]: Dictionary mit Performance-Metriken
        """
        return self.performance_metrics
    
    def _calculate_performance_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """
        Berechnet Performance-Metriken basierend auf der Equity-Kurve
        
        Args:
            equity_curve: Series mit der Equity-Kurve
            
        Returns:
            Dict[str, float]: Dictionary mit Performance-Metriken
        """
        try:
            # Berechne Renditen
            returns = equity_curve.pct_change().dropna()
            
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
            total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
            
            # Annualisierte Rendite (angenommen, dass die Renditen täglich sind)
            annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
            
            # Volatilität
            volatility = returns.std() * np.sqrt(252)
            
            # Sharpe Ratio (angenommen, dass der risikofreie Zinssatz 0 ist)
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
            
            # Maximum Drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.cummax()
            drawdowns = (cumulative_returns / running_max) - 1
            max_drawdown = drawdowns.min()
            
            # Win Rate und Profit Factor aus Trades berechnen
            if len(self.trades) > 0:
                winning_trades = [t for t in self.trades if t.get('profit', 0) > 0]
                win_rate = len(winning_trades) / len(self.trades)
                
                total_profit = sum(t.get('profit', 0) for t in winning_trades)
                total_loss = abs(sum(t.get('profit', 0) for t in self.trades if t.get('profit', 0) < 0))
                profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            else:
                win_rate = 0.0
                profit_factor = 0.0
            
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

class MovingAverageCrossoverStrategy(Strategy):
    """
    Moving Average Crossover Strategie
    
    Diese Strategie generiert Kaufsignale, wenn der schnelle MA den langsamen MA von unten kreuzt,
    und Verkaufssignale, wenn er ihn von oben kreuzt.
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialisiert die Moving Average Crossover Strategie
        
        Args:
            parameters: Parameter der Strategie (optional)
        """
        default_parameters = {
            'fast_ma': 20,
            'slow_ma': 50,
            'sl_pct': 2.0,
            'tp_pct': 4.0
        }
        
        # Kombiniere Standard-Parameter mit übergebenen Parametern
        if parameters:
            default_parameters.update(parameters)
        
        super().__init__(
            name="Moving Average Crossover",
            description="Kauft, wenn der schnelle MA den langsamen MA von unten kreuzt, und verkauft, wenn er ihn von oben kreuzt.",
            parameters=default_parameters
        )
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generiert Handelssignale basierend auf den Daten
        
        Args:
            df: DataFrame mit OHLCV-Daten
            
        Returns:
            pd.DataFrame: DataFrame mit Handelssignalen
        """
        try:
            # Kopiere DataFrame, um das Original nicht zu verändern
            result_df = df.copy()
            
            # Extrahiere Parameter
            fast_ma = self.get_parameter('fast_ma')
            slow_ma = self.get_parameter('slow_ma')
            
            # Berechne Moving Averages
            result_df['fast_ma'] = result_df['close'].rolling(window=fast_ma).mean()
            result_df['slow_ma'] = result_df['close'].rolling(window=slow_ma).mean()
            
            # Berechne Crossover-Signale
            result_df['signal'] = 0
            result_df['position'] = 0
            
            # Kaufsignal: Schneller MA kreuzt langsamen MA von unten
            result_df.loc[(result_df['fast_ma'] > result_df['slow_ma']) & 
                         (result_df['fast_ma'].shift(1) <= result_df['slow_ma'].shift(1)), 'signal'] = 1
            
            # Verkaufssignal: Schneller MA kreuzt langsamen MA von oben
            result_df.loc[(result_df['fast_ma'] < result_df['slow_ma']) & 
                         (result_df['fast_ma'].shift(1) >= result_df['slow_ma'].shift(1)), 'signal'] = -1
            
            # Berechne Position (1 = long, 0 = neutral, -1 = short)
            result_df['position'] = result_df['signal'].cumsum().clip(lower=0, upper=1)
            
            return result_df
        
        except Exception as e:
            logger.error(f"Fehler bei der Generierung von Handelssignalen: {str(e)}")
            return df
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        Führt einen Backtest der Strategie durch
        
        Args:
            df: DataFrame mit OHLCV-Daten
            initial_capital: Anfangskapital
            
        Returns:
            Dict[str, Any]: Dictionary mit Backtest-Ergebnissen
        """
        try:
            # Generiere Signale
            signals_df = self.generate_signals(df)
            
            # Extrahiere Parameter
            sl_pct = self.get_parameter('sl_pct') / 100
            tp_pct = self.get_parameter('tp_pct') / 100
            
            # Initialisiere Variablen
            capital = initial_capital
            position = 0
            entry_price = 0
            stop_loss = 0
            take_profit = 0
            trades = []
            equity_curve = [capital]
            
            # Durchlaufe alle Datenpunkte
            for i in range(1, len(signals_df)):
                current_date = signals_df.index[i]
                current_price = signals_df['close'].iloc[i]
                current_signal = signals_df['signal'].iloc[i]
                
                # Prüfe, ob ein offener Trade geschlossen werden soll
                if position != 0:
                    # Prüfe Stop Loss und Take Profit
                    if position == 1:  # Long-Position
                        if current_price <= stop_loss:  # Stop Loss ausgelöst
                            profit = (stop_loss / entry_price - 1) * capital
                            capital += profit
                            trades.append({
                                'entry_date': entry_date,
                                'entry_price': entry_price,
                                'exit_date': current_date,
                                'exit_price': stop_loss,
                                'type': 'long',
                                'profit': profit,
                                'exit_reason': 'stop_loss'
                            })
                            position = 0
                        elif current_price >= take_profit:  # Take Profit ausgelöst
                            profit = (take_profit / entry_price - 1) * capital
                            capital += profit
                            trades.append({
                                'entry_date': entry_date,
                                'entry_price': entry_price,
                                'exit_date': current_date,
                                'exit_price': take_profit,
                                'type': 'long',
                                'profit': profit,
                                'exit_reason': 'take_profit'
                            })
                            position = 0
                    elif position == -1:  # Short-Position
                        if current_price >= stop_loss:  # Stop Loss ausgelöst
                            profit = (entry_price / stop_loss - 1) * capital
                            capital += profit
                            trades.append({
                                'entry_date': entry_date,
                                'entry_price': entry_price,
                                'exit_date': current_date,
                                'exit_price': stop_loss,
                                'type': 'short',
                                'profit': profit,
                                'exit_reason': 'stop_loss'
                            })
                            position = 0
                        elif current_price <= take_profit:  # Take Profit ausgelöst
                            profit = (entry_price / take_profit - 1) * capital
                            capital += profit
                            trades.append({
                                'entry_date': entry_date,
                                'entry_price': entry_price,
                                'exit_date': current_date,
                                'exit_price': take_profit,
                                'type': 'short',
                                'profit': profit,
                                'exit_reason': 'take_profit'
                            })
                            position = 0
                
                # Prüfe, ob ein neuer Trade eröffnet werden soll
                if position == 0 and current_signal != 0:
                    if current_signal == 1:  # Kaufsignal
                        position = 1
                        entry_price = current_price
                        entry_date = current_date
                        stop_loss = entry_price * (1 - sl_pct)
                        take_profit = entry_price * (1 + tp_pct)
                    elif current_signal == -1:  # Verkaufssignal
                        position = -1
                        entry_price = current_price
                        entry_date = current_date
                        stop_loss = entry_price * (1 + sl_pct)
                        take_profit = entry_price * (1 - tp_pct)
                
                # Aktualisiere Equity-Kurve
                if position == 1:
                    equity = capital * (current_price / entry_price)
                elif position == -1:
                    equity = capital * (2 - current_price / entry_price)
                else:
                    equity = capital
                
                equity_curve.append(equity)
            
            # Schließe offene Position am Ende des Backtests
            if position != 0:
                current_date = signals_df.index[-1]
                current_price = signals_df['close'].iloc[-1]
                
                if position == 1:  # Long-Position
                    profit = (current_price / entry_price - 1) * capital
                    capital += profit
                    trades.append({
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'type': 'long',
                        'profit': profit,
                        'exit_reason': 'end_of_backtest'
                    })
                elif position == -1:  # Short-Position
                    profit = (entry_price / current_price - 1) * capital
                    capital += profit
                    trades.append({
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'type': 'short',
                        'profit': profit,
                        'exit_reason': 'end_of_backtest'
                    })
            
            # Speichere Trades
            self.trades = trades
            
            # Berechne Performance-Metriken
            equity_series = pd.Series(equity_curve, index=signals_df.index[:len(equity_curve)])
            self.performance_metrics = self._calculate_performance_metrics(equity_series)
            
            return {
                'signals': signals_df,
                'trades': trades,
                'equity_curve': equity_series,
                'performance_metrics': self.performance_metrics
            }
        
        except Exception as e:
            logger.error(f"Fehler beim Backtest: {str(e)}")
            return {
                'signals': df,
                'trades': [],
                'equity_curve': pd.Series([initial_capital], index=[df.index[0]]),
                'performance_metrics': {
                    'total_return': 0.0,
                    'annualized_return': 0.0,
                    'volatility': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0
                }
            }

class RSIStrategy(Strategy):
    """
    RSI Strategie
    
    Diese Strategie generiert Kaufsignale, wenn der RSI unter den überverkauften Bereich fällt,
    und Verkaufssignale, wenn er über den überkauften Bereich steigt.
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialisiert die RSI Strategie
        
        Args:
            parameters: Parameter der Strategie (optional)
        """
        default_parameters = {
            'rsi_period': 14,
            'overbought': 70,
            'oversold': 30,
            'sl_pct': 2.0,
            'tp_pct': 4.0
        }
        
        # Kombiniere Standard-Parameter mit übergebenen Parametern
        if parameters:
            default_parameters.update(parameters)
        
        super().__init__(
            name="RSI Strategie",
            description="Kauft, wenn der RSI unter den überverkauften Bereich fällt, und verkauft, wenn er über den überkauften Bereich steigt.",
            parameters=default_parameters
        )
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Berechnet den RSI (Relative Strength Index)
        
        Args:
            prices: Series mit Preisdaten
            period: RSI-Periode
            
        Returns:
            pd.Series: Series mit RSI-Werten
        """
        try:
            # Berechne Preisänderungen
            delta = prices.diff()
            
            # Separiere positive und negative Preisänderungen
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # Berechne durchschnittlichen Gain und Loss
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # Berechne RS (Relative Strength)
            rs = avg_gain / avg_loss
            
            # Berechne RSI
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        
        except Exception as e:
            logger.error(f"Fehler bei der Berechnung des RSI: {str(e)}")
            return pd.Series(index=prices.index)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generiert Handelssignale basierend auf den Daten
        
        Args:
            df: DataFrame mit OHLCV-Daten
            
        Returns:
            pd.DataFrame: DataFrame mit Handelssignalen
        """
        try:
            # Kopiere DataFrame, um das Original nicht zu verändern
            result_df = df.copy()
            
            # Extrahiere Parameter
            rsi_period = self.get_parameter('rsi_period')
            overbought = self.get_parameter('overbought')
            oversold = self.get_parameter('oversold')
            
            # Berechne RSI
            result_df['rsi'] = self._calculate_rsi(result_df['close'], rsi_period)
            
            # Berechne Signale
            result_df['signal'] = 0
            result_df['position'] = 0
            
            # Kaufsignal: RSI kreuzt überverkauften Bereich von unten
            result_df.loc[(result_df['rsi'] > oversold) & 
                         (result_df['rsi'].shift(1) <= oversold), 'signal'] = 1
            
            # Verkaufssignal: RSI kreuzt überkauften Bereich von oben
            result_df.loc[(result_df['rsi'] < overbought) & 
                         (result_df['rsi'].shift(1) >= overbought), 'signal'] = -1
            
            # Berechne Position (1 = long, 0 = neutral, -1 = short)
            result_df['position'] = result_df['signal'].cumsum().clip(lower=0, upper=1)
            
            return result_df
        
        except Exception as e:
            logger.error(f"Fehler bei der Generierung von Handelssignalen: {str(e)}")
            return df
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        Führt einen Backtest der Strategie durch
        
        Args:
            df: DataFrame mit OHLCV-Daten
            initial_capital: Anfangskapital
            
        Returns:
            Dict[str, Any]: Dictionary mit Backtest-Ergebnissen
        """
        try:
            # Generiere Signale
            signals_df = self.generate_signals(df)
            
            # Extrahiere Parameter
            sl_pct = self.get_parameter('sl_pct') / 100
            tp_pct = self.get_parameter('tp_pct') / 100
            
            # Initialisiere Variablen
            capital = initial_capital
            position = 0
            entry_price = 0
            stop_loss = 0
            take_profit = 0
            trades = []
            equity_curve = [capital]
            
            # Durchlaufe alle Datenpunkte
            for i in range(1, len(signals_df)):
                current_date = signals_df.index[i]
                current_price = signals_df['close'].iloc[i]
                current_signal = signals_df['signal'].iloc[i]
                
                # Prüfe, ob ein offener Trade geschlossen werden soll
                if position != 0:
                    # Prüfe Stop Loss und Take Profit
                    if position == 1:  # Long-Position
                        if current_price <= stop_loss:  # Stop Loss ausgelöst
                            profit = (stop_loss / entry_price - 1) * capital
                            capital += profit
                            trades.append({
                                'entry_date': entry_date,
                                'entry_price': entry_price,
                                'exit_date': current_date,
                                'exit_price': stop_loss,
                                'type': 'long',
                                'profit': profit,
                                'exit_reason': 'stop_loss'
                            })
                            position = 0
                        elif current_price >= take_profit:  # Take Profit ausgelöst
                            profit = (take_profit / entry_price - 1) * capital
                            capital += profit
                            trades.append({
                                'entry_date': entry_date,
                                'entry_price': entry_price,
                                'exit_date': current_date,
                                'exit_price': take_profit,
                                'type': 'long',
                                'profit': profit,
                                'exit_reason': 'take_profit'
                            })
                            position = 0
                    elif position == -1:  # Short-Position
                        if current_price >= stop_loss:  # Stop Loss ausgelöst
                            profit = (entry_price / stop_loss - 1) * capital
                            capital += profit
                            trades.append({
                                'entry_date': entry_date,
                                'entry_price': entry_price,
                                'exit_date': current_date,
                                'exit_price': stop_loss,
                                'type': 'short',
                                'profit': profit,
                                'exit_reason': 'stop_loss'
                            })
                            position = 0
                        elif current_price <= take_profit:  # Take Profit ausgelöst
                            profit = (entry_price / take_profit - 1) * capital
                            capital += profit
                            trades.append({
                                'entry_date': entry_date,
                                'entry_price': entry_price,
                                'exit_date': current_date,
                                'exit_price': take_profit,
                                'type': 'short',
                                'profit': profit,
                                'exit_reason': 'take_profit'
                            })
                            position = 0
                
                # Prüfe, ob ein neuer Trade eröffnet werden soll
                if position == 0 and current_signal != 0:
                    if current_signal == 1:  # Kaufsignal
                        position = 1
                        entry_price = current_price
                        entry_date = current_date
                        stop_loss = entry_price * (1 - sl_pct)
                        take_profit = entry_price * (1 + tp_pct)
                    elif current_signal == -1:  # Verkaufssignal
                        position = -1
                        entry_price = current_price
                        entry_date = current_date
                        stop_loss = entry_price * (1 + sl_pct)
                        take_profit = entry_price * (1 - tp_pct)
                
                # Aktualisiere Equity-Kurve
                if position == 1:
                    equity = capital * (current_price / entry_price)
                elif position == -1:
                    equity = capital * (2 - current_price / entry_price)
                else:
                    equity = capital
                
                equity_curve.append(equity)
            
            # Schließe offene Position am Ende des Backtests
            if position != 0:
                current_date = signals_df.index[-1]
                current_price = signals_df['close'].iloc[-1]
                
                if position == 1:  # Long-Position
                    profit = (current_price / entry_price - 1) * capital
                    capital += profit
                    trades.append({
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'type': 'long',
                        'profit': profit,
                        'exit_reason': 'end_of_backtest'
                    })
                elif position == -1:  # Short-Position
                    profit = (entry_price / current_price - 1) * capital
                    capital += profit
                    trades.append({
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'type': 'short',
                        'profit': profit,
                        'exit_reason': 'end_of_backtest'
                    })
            
            # Speichere Trades
            self.trades = trades
            
            # Berechne Performance-Metriken
            equity_series = pd.Series(equity_curve, index=signals_df.index[:len(equity_curve)])
            self.performance_metrics = self._calculate_performance_metrics(equity_series)
            
            return {
                'signals': signals_df,
                'trades': trades,
                'equity_curve': equity_series,
                'performance_metrics': self.performance_metrics
            }
        
        except Exception as e:
            logger.error(f"Fehler beim Backtest: {str(e)}")
            return {
                'signals': df,
                'trades': [],
                'equity_curve': pd.Series([initial_capital], index=[df.index[0]]),
                'performance_metrics': {
                    'total_return': 0.0,
                    'annualized_return': 0.0,
                    'volatility': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0
                }
            }

class StrategyFactory:
    """
    Factory für Trading-Strategien
    
    Diese Klasse erstellt Trading-Strategien basierend auf dem angegebenen Typ.
    """
    
    @staticmethod
    def create_strategy(strategy_type: str, parameters: Dict[str, Any] = None) -> Strategy:
        """
        Erstellt eine Trading-Strategie
        
        Args:
            strategy_type: Typ der Strategie ('ma_crossover', 'rsi', etc.)
            parameters: Parameter der Strategie (optional)
            
        Returns:
            Strategy: Trading-Strategie
        """
        if strategy_type == 'ma_crossover':
            return MovingAverageCrossoverStrategy(parameters)
        elif strategy_type == 'rsi':
            return RSIStrategy(parameters)
        else:
            # Standard: Moving Average Crossover
            logger.warning(f"Unbekannter Strategie-Typ: {strategy_type}, verwende 'ma_crossover'")
            return MovingAverageCrossoverStrategy(parameters)
