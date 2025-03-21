"""
Beispielstrategien für Trading Dashboard
Implementiert verschiedene Handelsstrategien basierend auf der Strategy-Basisklasse
"""

import pandas as pd
import numpy as np
from strategy.strategy_base import Strategy

class MovingAverageCrossover(Strategy):
    """
    Strategie basierend auf dem Kreuzen von gleitenden Durchschnitten
    """
    
    def __init__(self, short_window=20, long_window=50, name="MA Crossover"):
        """
        Initialisiert die Moving Average Crossover Strategie
        
        Args:
            short_window (int): Fenstergröße für den kurzen gleitenden Durchschnitt
            long_window (int): Fenstergröße für den langen gleitenden Durchschnitt
            name (str): Name der Strategie
        """
        super().__init__(name=name)
        self.parameters = {
            'short_window': short_window,
            'long_window': long_window
        }
        
    def generate_signals(self, data):
        """
        Generiert Handelssignale basierend auf dem Kreuzen von gleitenden Durchschnitten
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            
        Returns:
            pandas.DataFrame: DataFrame mit Preisdaten und Signalen
        """
        # Kopiere Daten, um das Original nicht zu verändern
        df = data.copy()
        
        # Extrahiere Parameter
        short_window = self.parameters['short_window']
        long_window = self.parameters['long_window']
        
        # Berechne gleitende Durchschnitte
        df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
        df['SMA_Long'] = df['Close'].rolling(window=long_window).mean()
        
        # Initialisiere Signal-Spalte
        df['Signal'] = 0
        
        # Generiere Signale
        df['Signal'] = np.where(df['SMA_Short'] > df['SMA_Long'], 1, 0)
        
        # Generiere Handelssignale (1 für Kauf, -1 für Verkauf)
        df['Position'] = df['Signal'].diff()
        
        # Ersetze NaN-Werte
        df['Position'] = df['Position'].fillna(0)
        
        # Konvertiere zu Handelssignalen
        df['Signal'] = np.where(df['Position'] > 0, 1, np.where(df['Position'] < 0, -1, 0))
        
        return df
    
    def calculate_stop_loss(self, data, index):
        """
        Berechnet den Stop-Loss für einen Trade basierend auf ATR
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Stop-Loss-Preis
        """
        # Berechne ATR (Average True Range)
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        atr = true_range.rolling(window=14).mean()
        
        # Setze Stop-Loss auf 2 ATR unter dem Einstiegspreis
        current_price = data['Close'].iloc[index]
        current_atr = atr.iloc[index]
        
        return current_price - (current_atr * 2)
    
    def calculate_take_profit(self, data, index):
        """
        Berechnet den Take-Profit für einen Trade basierend auf ATR und Risk-Reward-Ratio
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Take-Profit-Preis
        """
        # Berechne ATR (Average True Range)
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        atr = true_range.rolling(window=14).mean()
        
        # Setze Take-Profit auf 3 ATR über dem Einstiegspreis (Risk-Reward-Ratio von 1.5)
        current_price = data['Close'].iloc[index]
        current_atr = atr.iloc[index]
        
        return current_price + (current_atr * 3)


class RSIStrategy(Strategy):
    """
    Strategie basierend auf dem Relative Strength Index (RSI)
    """
    
    def __init__(self, rsi_window=14, overbought=70, oversold=30, name="RSI Strategy"):
        """
        Initialisiert die RSI-Strategie
        
        Args:
            rsi_window (int): Fenstergröße für den RSI
            overbought (int): Überkauft-Schwelle
            oversold (int): Überverkauft-Schwelle
            name (str): Name der Strategie
        """
        super().__init__(name=name)
        self.parameters = {
            'rsi_window': rsi_window,
            'overbought': overbought,
            'oversold': oversold
        }
        
    def generate_signals(self, data):
        """
        Generiert Handelssignale basierend auf dem RSI
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            
        Returns:
            pandas.DataFrame: DataFrame mit Preisdaten und Signalen
        """
        # Kopiere Daten, um das Original nicht zu verändern
        df = data.copy()
        
        # Extrahiere Parameter
        rsi_window = self.parameters['rsi_window']
        overbought = self.parameters['overbought']
        oversold = self.parameters['oversold']
        
        # Berechne RSI
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=rsi_window).mean()
        avg_loss = loss.rolling(window=rsi_window).mean()
        
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Initialisiere Signal-Spalte
        df['Signal'] = 0
        
        # Generiere Signale
        # Kaufsignal, wenn RSI unter oversold ist und dann darüber steigt
        # Verkaufssignal, wenn RSI über overbought ist und dann darunter fällt
        for i in range(1, len(df)):
            if df['RSI'].iloc[i-1] < oversold and df['RSI'].iloc[i] >= oversold:
                df['Signal'].iloc[i] = 1  # Kaufsignal
            elif df['RSI'].iloc[i-1] > overbought and df['RSI'].iloc[i] <= overbought:
                df['Signal'].iloc[i] = -1  # Verkaufssignal
                
        return df
    
    def calculate_stop_loss(self, data, index):
        """
        Berechnet den Stop-Loss für einen Trade basierend auf dem letzten Swing Low
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Stop-Loss-Preis
        """
        # Finde das letzte Swing Low (lokales Minimum) in den letzten 10 Tagen
        lookback = min(10, index)
        recent_data = data.iloc[index-lookback:index+1]
        
        # Einfache Methode: Verwende das Minimum der letzten Tage
        swing_low = recent_data['Low'].min()
        
        # Füge einen kleinen Puffer hinzu (0.5%)
        stop_loss = swing_low * 0.995
        
        return stop_loss
    
    def calculate_take_profit(self, data, index):
        """
        Berechnet den Take-Profit für einen Trade basierend auf Risk-Reward-Ratio
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Take-Profit-Preis
        """
        # Berechne den Abstand zum Stop-Loss
        current_price = data['Close'].iloc[index]
        stop_loss = self.calculate_stop_loss(data, index)
        risk = current_price - stop_loss
        
        # Setze Take-Profit basierend auf Risk-Reward-Ratio von 2
        take_profit = current_price + (risk * 2)
        
        return take_profit


class MACDStrategy(Strategy):
    """
    Strategie basierend auf dem Moving Average Convergence Divergence (MACD)
    """
    
    def __init__(self, fast=12, slow=26, signal=9, name="MACD Strategy"):
        """
        Initialisiert die MACD-Strategie
        
        Args:
            fast (int): Fenstergröße für den schnellen EMA
            slow (int): Fenstergröße für den langsamen EMA
            signal (int): Fenstergröße für die Signallinie
            name (str): Name der Strategie
        """
        super().__init__(name=name)
        self.parameters = {
            'fast': fast,
            'slow': slow,
            'signal': signal
        }
        
    def generate_signals(self, data):
        """
        Generiert Handelssignale basierend auf dem MACD
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            
        Returns:
            pandas.DataFrame: DataFrame mit Preisdaten und Signalen
        """
        # Kopiere Daten, um das Original nicht zu verändern
        df = data.copy()
        
        # Extrahiere Parameter
        fast = self.parameters['fast']
        slow = self.parameters['slow']
        signal_window = self.parameters['signal']
        
        # Berechne MACD
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        
        df['MACD'] = ema_fast - ema_slow
        df['Signal_Line'] = df['MACD'].ewm(span=signal_window, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal_Line']
        
        # Initialisiere Signal-Spalte
        df['Signal'] = 0
        
        # Generiere Signale
        # Kaufsignal, wenn MACD die Signallinie von unten kreuzt
        # Verkaufssignal, wenn MACD die Signallinie von oben kreuzt
        for i in range(1, len(df)):
            if df['MACD'].iloc[i-1] < df['Signal_Line'].iloc[i-1] and df['MACD'].iloc[i] >= df['Signal_Line'].iloc[i]:
                df['Signal'].iloc[i] = 1  # Kaufsignal
            elif df['MACD'].iloc[i-1] > df['Signal_Line'].iloc[i-1] and df['MACD'].iloc[i] <= df['Signal_Line'].iloc[i]:
                df['Signal'].iloc[i] = -1  # Verkaufssignal
                
        return df
    
    def calculate_stop_loss(self, data, index):
        """
        Berechnet den Stop-Loss für einen Trade basierend auf dem letzten Swing Low und ATR
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Stop-Loss-Preis
        """
        # Berechne ATR (Average True Range)
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        atr = true_range.rolling(window=14).mean()
        
        # Finde das letzte Swing Low (lokales Minimum) in den letzten 10 Tagen
        lookback = min(10, index)
        recent_data = data.iloc[index-lookback:index+1]
        
        # Einfache Methode: Verwende das Minimum der letzten Tage
        swing_low = recent_data['Low'].min()
        
        # Verwende den niedrigeren Wert von:
        # 1. Swing Low - 0.5%
        # 2. Aktueller Preis - 2 ATR
        current_price = data['Close'].iloc[index]
        current_atr = atr.iloc[index] if not pd.isna(atr.iloc[index]) else current_price * 0.02
        
        stop_loss_swing = swing_low * 0.995
        stop_loss_atr = current_price - (current_atr * 2)
        
        return min(stop_loss_swing, stop_loss_atr)
    
    def calculate_take_profit(self, data, index):
        """
        Berechnet den Take-Profit für einen Trade basierend auf Risk-Reward-Ratio
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Take-Profit-Preis
        """
        # Berechne den Abstand zum Stop-Loss
        current_price = data['Close'].iloc[index]
        stop_loss = self.calculate_stop_loss(data, index)
        risk = current_price - stop_loss
        
        # Setze Take-Profit basierend auf Risk-Reward-Ratio von 2
        take_profit = current_price + (risk * 2)
        
        return take_profit


class BollingerBandsStrategy(Strategy):
    """
    Strategie basierend auf Bollinger Bands
    """
    
    def __init__(self, window=20, num_std=2, name="Bollinger Bands Strategy"):
        """
        Initialisiert die Bollinger Bands Strategie
        
        Args:
            window (int): Fenstergröße für den gleitenden Durchschnitt
            num_std (int): Anzahl der Standardabweichungen
            name (str): Name der Strategie
        """
        super().__init__(name=name)
        self.parameters = {
            'window': window,
            'num_std': num_std
        }
        
    def generate_signals(self, data):
        """
        Generiert Handelssignale basierend auf Bollinger Bands
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            
        Returns:
            pandas.DataFrame: DataFrame mit Preisdaten und Signalen
        """
        # Kopiere Daten, um das Original nicht zu verändern
        df = data.copy()
        
        # Extrahiere Parameter
        window = self.parameters['window']
        num_std = self.parameters['num_std']
        
        # Berechne Bollinger Bands
        df['Middle_Band'] = df['Close'].rolling(window=window).mean()
        df['Std_Dev'] = df['Close'].rolling(window=window).std()
        
        df['Upper_Band'] = df['Middle_Band'] + (df['Std_Dev'] * num_std)
        df['Lower_Band'] = df['Middle_Band'] - (df['Std_Dev'] * num_std)
        
        # Initialisiere Signal-Spalte
        df['Signal'] = 0
        
        # Generiere Signale
        # Kaufsignal, wenn Preis die untere Band berührt oder unterschreitet und dann wieder darüber steigt
        # Verkaufssignal, wenn Preis die obere Band berührt oder überschreitet und dann wieder darunter fällt
        for i in range(1, len(df)):
            if df['Close'].iloc[i-1] <= df['Lower_Band'].iloc[i-1] and df['Close'].iloc[i] > df['Lower_Band'].iloc[i]:
                df['Signal'].iloc[i] = 1  # Kaufsignal
            elif df['Close'].iloc[i-1] >= df['Upper_Band'].iloc[i-1] and df['Close'].iloc[i] < df['Upper_Band'].iloc[i]:
                df['Signal'].iloc[i] = -1  # Verkaufssignal
                
        return df
    
    def calculate_stop_loss(self, data, index):
        """
        Berechnet den Stop-Loss für einen Trade basierend auf der unteren Bollinger Band
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Stop-Loss-Preis
        """
        # Verwende die untere Bollinger Band als Stop-Loss
        # Füge einen kleinen Puffer hinzu (1%)
        lower_band = data['Lower_Band'].iloc[index]
        stop_loss = lower_band * 0.99
        
        return stop_loss
    
    def calculate_take_profit(self, data, index):
        """
        Berechnet den Take-Profit für einen Trade basierend auf der oberen Bollinger Band
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            index (int): Index des aktuellen Zeitpunkts
            
        Returns:
            float: Take-Profit-Preis
        """
        # Verwende die obere Bollinger Band als Take-Profit
        upper_band = data['Upper_Band'].iloc[index]
        
        return upper_band
