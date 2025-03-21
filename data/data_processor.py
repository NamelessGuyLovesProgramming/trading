"""
Data Processor Module für Trading Dashboard
Verantwortlich für die Verarbeitung und Analyse von Handelsdaten
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class DataProcessor:
    """
    Klasse zur Verarbeitung und Analyse von Handelsdaten
    """
    
    @staticmethod
    def calculate_sma(data, window=20):
        """
        Berechnet den Simple Moving Average (SMA)
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            window (int): Fenstergröße für den gleitenden Durchschnitt
            
        Returns:
            pandas.Series: Serie mit SMA-Werten
        """
        return data['Close'].rolling(window=window).mean()
    
    @staticmethod
    def calculate_ema(data, window=20):
        """
        Berechnet den Exponential Moving Average (EMA)
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            window (int): Fenstergröße für den gleitenden Durchschnitt
            
        Returns:
            pandas.Series: Serie mit EMA-Werten
        """
        return data['Close'].ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data, window=14):
        """
        Berechnet den Relative Strength Index (RSI)
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            window (int): Fenstergröße für den RSI
            
        Returns:
            pandas.Series: Serie mit RSI-Werten
        """
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(data, fast=12, slow=26, signal=9):
        """
        Berechnet den Moving Average Convergence Divergence (MACD)
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            fast (int): Fenstergröße für den schnellen EMA
            slow (int): Fenstergröße für den langsamen EMA
            signal (int): Fenstergröße für die Signallinie
            
        Returns:
            tuple: (MACD-Linie, Signallinie, Histogramm)
        """
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(data, window=20, num_std=2):
        """
        Berechnet die Bollinger Bands
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            window (int): Fenstergröße für den gleitenden Durchschnitt
            num_std (int): Anzahl der Standardabweichungen
            
        Returns:
            tuple: (Mittlere Linie, Obere Linie, Untere Linie)
        """
        middle_band = data['Close'].rolling(window=window).mean()
        std_dev = data['Close'].rolling(window=window).std()
        
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        return middle_band, upper_band, lower_band
    
    @staticmethod
    def calculate_atr(data, window=14):
        """
        Berechnet den Average True Range (ATR)
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            window (int): Fenstergröße für den ATR
            
        Returns:
            pandas.Series: Serie mit ATR-Werten
        """
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        return true_range.rolling(window=window).mean()
    
    @staticmethod
    def calculate_support_resistance(data, window=10):
        """
        Berechnet einfache Support- und Widerstandsniveaus
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            window (int): Fenstergröße für die Berechnung
            
        Returns:
            tuple: (Support-Level, Widerstand-Level)
        """
        # Einfache Methode: Verwende lokale Minima und Maxima
        recent_data = data.tail(window)
        support = recent_data['Low'].min()
        resistance = recent_data['High'].max()
        
        return support, resistance
    
    @staticmethod
    def calculate_stop_loss_take_profit(data, atr_multiplier=2, risk_reward_ratio=2):
        """
        Berechnet Stop-Loss und Take-Profit basierend auf ATR
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            atr_multiplier (float): Multiplikator für den ATR
            risk_reward_ratio (float): Verhältnis von Risiko zu Belohnung
            
        Returns:
            tuple: (Stop-Loss-Level, Take-Profit-Level)
        """
        # Berechne ATR
        atr = DataProcessor.calculate_atr(data)
        
        # Verwende den letzten verfügbaren ATR-Wert
        last_atr = atr.iloc[-1]
        last_close = data['Close'].iloc[-1]
        
        # Berechne Stop-Loss und Take-Profit
        stop_loss = last_close - (last_atr * atr_multiplier)
        take_profit = last_close + (last_atr * atr_multiplier * risk_reward_ratio)
        
        return stop_loss, take_profit
    
    @staticmethod
    def add_indicators(data):
        """
        Fügt gängige technische Indikatoren zu einem DataFrame hinzu
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            
        Returns:
            pandas.DataFrame: DataFrame mit hinzugefügten Indikatoren
        """
        # Kopiere Daten, um das Original nicht zu verändern
        df = data.copy()
        
        # Füge SMA hinzu
        df['SMA_20'] = DataProcessor.calculate_sma(df, window=20)
        df['SMA_50'] = DataProcessor.calculate_sma(df, window=50)
        df['SMA_200'] = DataProcessor.calculate_sma(df, window=200)
        
        # Füge EMA hinzu
        df['EMA_12'] = DataProcessor.calculate_ema(df, window=12)
        df['EMA_26'] = DataProcessor.calculate_ema(df, window=26)
        
        # Füge RSI hinzu
        df['RSI_14'] = DataProcessor.calculate_rsi(df, window=14)
        
        # Füge MACD hinzu
        macd, signal, hist = DataProcessor.calculate_macd(df)
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist
        
        # Füge Bollinger Bands hinzu
        middle, upper, lower = DataProcessor.calculate_bollinger_bands(df)
        df['BB_Middle'] = middle
        df['BB_Upper'] = upper
        df['BB_Lower'] = lower
        
        # Füge ATR hinzu
        df['ATR_14'] = DataProcessor.calculate_atr(df, window=14)
        
        return df
    
    @staticmethod
    def normalize_data(data):
        """
        Normalisiert die Daten für die Visualisierung oder das Machine Learning
        
        Args:
            data (pandas.DataFrame): DataFrame mit Preisdaten
            
        Returns:
            pandas.DataFrame: Normalisierter DataFrame
        """
        # Kopiere Daten, um das Original nicht zu verändern
        df = data.copy()
        
        # Normalisiere numerische Spalten
        for column in df.select_dtypes(include=[np.number]).columns:
            df[column] = (df[column] - df[column].min()) / (df[column].max() - df[column].min())
            
        return df
