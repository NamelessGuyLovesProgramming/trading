"""
Backtesting Engine für Trading Dashboard
Verantwortlich für das Testen von Handelsstrategien mit historischen Daten
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import os
from pathlib import Path

class BacktestEngine:
    """
    Engine zum Backtesten von Handelsstrategien mit historischen Daten
    """
    
    def __init__(self, initial_capital=50000.0, commission=0.001):
        """
        Initialisiert die Backtesting-Engine
        
        Args:
            initial_capital (float): Anfangskapital für den Backtest
            commission (float): Provisionsrate pro Trade (z.B. 0.001 für 0.1%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.reset()
        
    def reset(self):
        """
        Setzt die Engine auf den Anfangszustand zurück
        """
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
        self.current_trade = None
        
    def run(self, data, strategy, verbose=False):
        """
        Führt einen Backtest mit einer bestimmten Strategie durch
        
        Args:
            data (pandas.DataFrame): DataFrame mit historischen Preisdaten
            strategy: Strategie-Objekt mit generate_signals-Methode
            verbose (bool): Ob detaillierte Ausgaben angezeigt werden sollen
            
        Returns:
            dict: Ergebnisse des Backtests
        """
        # Setze Engine zurück
        self.reset()
        
        # Generiere Handelssignale
        signals = strategy.generate_signals(data)
        
        # Kombiniere Daten und Signale
        if isinstance(signals, pd.Series):
            data = data.copy()
            data['Signal'] = signals
        else:
            data = signals
            
        # Initialisiere Ergebnisarrays
        equity = np.zeros(len(data))
        positions = np.zeros(len(data))
        equity[0] = self.capital
        
        # Durchlaufe jeden Zeitpunkt
        for i in range(1, len(data)):
            # Aktueller Preis
            current_price = data['Close'].iloc[i]
            prev_price = data['Close'].iloc[i-1]
            
            # Aktuelles Signal
            signal = data['Signal'].iloc[i]
            
            # Aktualisiere Position basierend auf Signal
            if signal == 1 and self.position == 0:  # Kaufsignal
                # Berechne Anzahl der Aktien, die gekauft werden können
                shares = self._calculate_position_size(current_price)
                
                # Kaufe Aktien
                cost = shares * current_price * (1 + self.commission)
                self.capital -= cost
                self.position = shares
                
                # Zeichne Trade auf
                self.current_trade = {
                    'entry_date': data.index[i],
                    'entry_price': current_price,
                    'shares': shares,
                    'type': 'long',
                    'stop_loss': strategy.calculate_stop_loss(data, i) if hasattr(strategy, 'calculate_stop_loss') else None,
                    'take_profit': strategy.calculate_take_profit(data, i) if hasattr(strategy, 'calculate_take_profit') else None
                }
                
                if verbose:
                    print(f"KAUF: {data.index[i]}, Preis: {current_price:.2f}, Anteile: {shares:.2f}, Kapital: {self.capital:.2f}")
                    
            elif signal == -1 and self.position > 0:  # Verkaufssignal
                # Verkaufe Aktien
                proceeds = self.position * current_price * (1 - self.commission)
                self.capital += proceeds
                
                # Berechne Gewinn/Verlust
                if self.current_trade:
                    self.current_trade['exit_date'] = data.index[i]
                    self.current_trade['exit_price'] = current_price
                    self.current_trade['profit'] = proceeds - (self.current_trade['shares'] * self.current_trade['entry_price'] * (1 + self.commission))
                    self.current_trade['profit_pct'] = (current_price / self.current_trade['entry_price']) - 1
                    self.trades.append(self.current_trade)
                    self.current_trade = None
                
                self.position = 0
                
                if verbose:
                    print(f"VERKAUF: {data.index[i]}, Preis: {current_price:.2f}, Kapital: {self.capital:.2f}")
                    
            # Überprüfe Stop-Loss und Take-Profit, wenn eine Position besteht
            elif self.position > 0 and self.current_trade:
                # Überprüfe Stop-Loss
                if self.current_trade['stop_loss'] is not None and current_price <= self.current_trade['stop_loss']:
                    # Verkaufe Aktien zum Stop-Loss-Preis
                    proceeds = self.position * self.current_trade['stop_loss'] * (1 - self.commission)
                    self.capital += proceeds
                    
                    # Berechne Gewinn/Verlust
                    self.current_trade['exit_date'] = data.index[i]
                    self.current_trade['exit_price'] = self.current_trade['stop_loss']
                    self.current_trade['profit'] = proceeds - (self.current_trade['shares'] * self.current_trade['entry_price'] * (1 + self.commission))
                    self.current_trade['profit_pct'] = (self.current_trade['stop_loss'] / self.current_trade['entry_price']) - 1
                    self.current_trade['exit_reason'] = 'stop_loss'
                    self.trades.append(self.current_trade)
                    self.current_trade = None
                    
                    self.position = 0
                    
                    if verbose:
                        print(f"STOP-LOSS: {data.index[i]}, Preis: {self.current_trade['stop_loss']:.2f}, Kapital: {self.capital:.2f}")
                
                # Überprüfe Take-Profit
                elif self.current_trade['take_profit'] is not None and current_price >= self.current_trade['take_profit']:
                    # Verkaufe Aktien zum Take-Profit-Preis
                    proceeds = self.position * self.current_trade['take_profit'] * (1 - self.commission)
                    self.capital += proceeds
                    
                    # Berechne Gewinn/Verlust
                    self.current_trade['exit_date'] = data.index[i]
                    self.current_trade['exit_price'] = self.current_trade['take_profit']
                    self.current_trade['profit'] = proceeds - (self.current_trade['shares'] * self.current_trade['entry_price'] * (1 + self.commission))
                    self.current_trade['profit_pct'] = (self.current_trade['take_profit'] / self.current_trade['entry_price']) - 1
                    self.current_trade['exit_reason'] = 'take_profit'
                    self.trades.append(self.current_trade)
                    self.current_trade = None
                    
                    self.position = 0
                    
                    if verbose:
                        print(f"TAKE-PROFIT: {data.index[i]}, Preis: {self.current_trade['take_profit']:.2f}, Kapital: {self.capital:.2f}")
            
            # Aktualisiere Equity und Positionen
            equity[i] = self.capital + (self.position * current_price)
            positions[i] = self.position
            
        # Erstelle Equity-Kurve
        equity_curve = pd.Series(equity, index=data.index)
        positions_series = pd.Series(positions, index=data.index)
        
        # Berechne Performance-Metriken
        metrics = self._calculate_performance_metrics(equity_curve, data)
        
        # Erstelle Ergebnis-Dictionary
        results = {
            'equity_curve': equity_curve,
            'positions': positions_series,
            'trades': self.trades,
            'metrics': metrics,
            'data': data
        }
        
        return results
    
    def _calculate_position_size(self, price):
        """
        Berechnet die Positionsgröße basierend auf verfügbarem Kapital
        
        Args:
            price (float): Aktueller Preis
            
        Returns:
            float: Anzahl der Aktien, die gekauft werden können
        """
        # Verwende 95% des verfügbaren Kapitals für den Trade
        available_capital = self.capital * 0.95
        
        # Berechne Anzahl der Aktien
        shares = available_capital / (price * (1 + self.commission))
        
        return shares
    
    def _calculate_performance_metrics(self, equity_curve, data):
        """
        Berechnet Performance-Metriken für den Backtest
        
        Args:
            equity_curve (pandas.Series): Equity-Kurve
            data (pandas.DataFrame): Originaldaten
            
        Returns:
            dict: Performance-Metriken
        """
        # Berechne Rendite
        total_return = (equity_curve.iloc[-1] / self.initial_capital) - 1
        
        # Berechne annualisierte Rendite
        days = (data.index[-1] - data.index[0]).days
        annual_return = ((1 + total_return) ** (365 / max(days, 1))) - 1
        
        # Berechne Drawdown
        rolling_max = equity_curve.cummax()
        drawdown = (equity_curve / rolling_max) - 1
        max_drawdown = drawdown.min()
        
        # Berechne Sharpe Ratio (vereinfacht)
        returns = equity_curve.pct_change().dropna()
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Berechne Trade-Statistiken
        if self.trades:
            winning_trades = [t for t in self.trades if t['profit'] > 0]
            losing_trades = [t for t in self.trades if t['profit'] <= 0]
            
            win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
            
            avg_profit = np.mean([t['profit'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['profit'] for t in losing_trades]) if losing_trades else 0
            
            profit_factor = abs(sum(t['profit'] for t in winning_trades) / sum(t['profit'] for t in losing_trades)) if losing_trades and sum(t['profit'] for t in losing_trades) != 0 else float('inf')
            
            # Berechne durchschnittliche Haltedauer
            hold_times = [(t['exit_date'] - t['entry_date']).days for t in self.trades]
            avg_hold_time = np.mean(hold_times) if hold_times else 0
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
            avg_hold_time = 0
        
        # Erstelle Metriken-Dictionary
        metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'num_trades': len(self.trades),
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_hold_time': avg_hold_time,
            'final_capital': equity_curve.iloc[-1]
        }
        
        return metrics
    
    def plot_results(self, results, output_dir=None, filename='backtest_results.png'):
        """
        Visualisiert die Ergebnisse des Backtests
        
        Args:
            results (dict): Ergebnisse des Backtests
            output_dir (str, optional): Verzeichnis für die Ausgabedatei
            filename (str, optional): Name der Ausgabedatei
        """
        # Extrahiere Daten
        equity_curve = results['equity_curve']
        data = results['data']
        trades = results['trades']
        metrics = results['metrics']
        
        # Erstelle Figure
        fig = plt.figure(figsize=(15, 10))
        
        # Plot Equity-Kurve
        ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=1)
        ax1.plot(equity_curve, label='Kapital')
        ax1.set_title('Equity-Kurve')
        ax1.legend()
        ax1.grid(True)
        
        # Plot Preisdaten und Trades
        ax2 = plt.subplot2grid((4, 1), (1, 0), rowspan=2)
        ax2.plot(data['Close'], label='Schlusskurs')
        
        # Markiere Trades
        for trade in trades:
            # Markiere Einstieg
            ax2.plot(trade['entry_date'], trade['entry_price'], '^', markersize=8, color='g')
            
            # Markiere Ausstieg
            if 'exit_date' in trade and 'exit_price' in trade:
                color = 'r' if trade['profit'] < 0 else 'b'
                ax2.plot(trade['exit_date'], trade['exit_price'], 'v', markersize=8, color=color)
                
                # Verbinde Ein- und Ausstieg
                ax2.plot([trade['entry_date'], trade['exit_date']], 
                         [trade['entry_price'], trade['exit_price']], 
                         color=color, linestyle='--', alpha=0.5)
                
            # Markiere Stop-Loss und Take-Profit
            if 'stop_loss' in trade and trade['stop_loss'] is not None:
                # Berechne relative Position für xmin und xmax (0 bis 1)
                xmin = (trade['entry_date'] - data.index[0]).total_seconds() / (data.index[-1] - data.index[0]).total_seconds() if hasattr(trade['entry_date'], 'total_seconds') else 0.1
                xmax = (trade['exit_date'] - data.index[0]).total_seconds() / (data.index[-1] - data.index[0]).total_seconds() if 'exit_date' in trade and hasattr(trade['exit_date'], 'total_seconds') else 0.9
                
                # Stelle sicher, dass xmin und xmax im gültigen Bereich sind
                xmin = max(0, min(xmin, 1))
                xmax = max(0, min(xmax, 1))
                
                ax2.axhline(y=trade['stop_loss'], color='r', linestyle='--', alpha=0.3, 
                            xmin=xmin, xmax=xmax)
                
            if 'take_profit' in trade and trade['take_profit'] is not None:
                # Berechne relative Position für xmin und xmax (0 bis 1)
                xmin = (trade['entry_date'] - data.index[0]).total_seconds() / (data.index[-1] - data.index[0]).total_seconds() if hasattr(trade['entry_date'], 'total_seconds') else 0.1
                xmax = (trade['exit_date'] - data.index[0]).total_seconds() / (data.index[-1] - data.index[0]).total_seconds() if 'exit_date' in trade and hasattr(trade['exit_date'], 'total_seconds') else 0.9
                
                # Stelle sicher, dass xmin und xmax im gültigen Bereich sind
                xmin = max(0, min(xmin, 1))
                xmax = max(0, min(xmax, 1))
                
                ax2.axhline(y=trade['take_profit'], color='g', linestyle='--', alpha=0.3,
                            xmin=xmin, xmax=xmax)
        
        ax2.set_title('Preisdaten und Trades')
        ax2.legend()
        ax2.grid(True)
        
        # Plot Drawdown
        ax3 = plt.subplot2grid((4, 1), (3, 0), rowspan=1)
        rolling_max = equity_curve.cummax()
        drawdown = (equity_curve / rolling_max) - 1
        ax3.fill_between(drawdown.index, drawdown, 0, color='r', alpha=0.3)
        ax3.set_title('Drawdown')
        ax3.grid(True)
        
        # Füge Metriken hinzu
        metrics_text = f"""
        Gesamtrendite: {metrics['total_return']:.2%}
        Jährliche Rendite: {metrics['annual_return']:.2%}
        Max. Drawdown: {metrics['max_drawdown']:.2%}
        Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
        Anzahl Trades: {metrics['num_trades']}
        Gewinnrate: {metrics['win_rate']:.2%}
        Durchschn. Gewinn: {metrics['avg_profit']:.2f}
        Durchschn. Verlust: {metrics['avg_loss']:.2f}
        Profit Factor: {metrics['profit_factor']:.2f}
        Durchschn. Haltedauer: {metrics['avg_hold_time']:.1f} Tage
        Endkapital: {metrics['final_capital']:.2f}
        """
        
        plt.figtext(0.01, 0.01, metrics_text, fontsize=10, va='bottom')
        
        plt.tight_layout()
        
        # Speichere Grafik, wenn Ausgabeverzeichnis angegeben ist
        if output_dir:
            output_path = Path(output_dir) / filename
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(output_path)
            print(f"Grafik gespeichert unter: {output_path}")
        
        return fig
    
    def generate_report(self, results, output_dir=None, filename='backtest_report.html'):
        """
        Generiert einen HTML-Bericht für den Backtest
        
        Args:
            results (dict): Ergebnisse des Backtests
            output_dir (str, optional): Verzeichnis für die Ausgabedatei
            filename (str, optional): Name der Ausgabedatei
            
        Returns:
            str: Pfad zur HTML-Datei
        """
        # Extrahiere Daten
        equity_curve = results['equity_curve']
        trades = results['trades']
        metrics = results['metrics']
        
        # Erstelle HTML-Bericht mit manueller Formatierung statt String-Formatierung
        total_return_class = "positive" if metrics['total_return'] > 0 else "negative"
        annual_return_class = "positive" if metrics['annual_return'] > 0 else "negative"
        sharpe_class = "positive" if metrics['sharpe_ratio'] > 1 else "negative"
        win_rate_class = "positive" if metrics['win_rate'] > 0.5 else "negative"
        profit_factor_class = "positive" if metrics['profit_factor'] > 1 else "negative"
        final_capital_class = "positive" if metrics['final_capital'] > self.initial_capital else "negative"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Backtest-Bericht</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
        .metrics {{ display: flex; flex-wrap: wrap; }}
        .metric-box {{ border: 1px solid #ddd; padding: 10px; margin: 5px; flex: 1; min-width: 200px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
        .trades-table {{ margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>Backtest-Bericht</h1>
    
    <h2>Performance-Metriken</h2>
    <div class="metrics">
        <div class="metric-box">
            <div>Gesamtrendite</div>
            <div class="metric-value {total_return_class}">{metrics['total_return']:.2%}</div>
        </div>
        <div class="metric-box">
            <div>Jährliche Rendite</div>
            <div class="metric-value {annual_return_class}">{metrics['annual_return']:.2%}</div>
        </div>
        <div class="metric-box">
            <div>Max. Drawdown</div>
            <div class="metric-value negative">{metrics['max_drawdown']:.2%}</div>
        </div>
        <div class="metric-box">
            <div>Sharpe Ratio</div>
            <div class="metric-value {sharpe_class}">{metrics['sharpe_ratio']:.2f}</div>
        </div>
        <div class="metric-box">
            <div>Gewinnrate</div>
            <div class="metric-value {win_rate_class}">{metrics['win_rate']:.2%}</div>
        </div>
        <div class="metric-box">
            <div>Profit Factor</div>
            <div class="metric-value {profit_factor_class}">{metrics['profit_factor']:.2f}</div>
        </div>
        <div class="metric-box">
            <div>Anzahl Trades</div>
            <div class="metric-value">{metrics['num_trades']}</div>
        </div>
        <div class="metric-box">
            <div>Endkapital</div>
            <div class="metric-value {final_capital_class}">{metrics['final_capital']:.2f}</div>
        </div>
    </div>
    
    <h2>Trades</h2>
    <table class="trades-table">
        <tr>
            <th>Nr.</th>
            <th>Einstieg</th>
            <th>Einstiegspreis</th>
            <th>Ausstieg</th>
            <th>Ausstiegspreis</th>
            <th>Typ</th>
            <th>Anteile</th>
            <th>Gewinn/Verlust</th>
            <th>Rendite</th>
            <th>Ausstiegsgrund</th>
        </tr>
        """
        
        # Füge Trades hinzu
        for i, trade in enumerate(trades):
            exit_date = trade.get('exit_date', 'Offen')
            exit_price = trade.get('exit_price', '-')
            profit = trade.get('profit', 0)
            profit_pct = trade.get('profit_pct', 0)
            exit_reason = trade.get('exit_reason', 'signal')
            
            html += """
                <tr>
                    <td>{0}</td>
                    <td>{1}</td>
                    <td>{2:.2f}</td>
                    <td>{3}</td>
                    <td>{4}</td>
                    <td>{5}</td>
                    <td>{6:.2f}</td>
                    <td class="{7}">{8:.2f}</td>
                    <td class="{9}">{10:.2%}</td>
                    <td>{11}</td>
                </tr>
            """.format(
                i + 1,
                trade['entry_date'].strftime('%Y-%m-%d'),
                trade['entry_price'],
                exit_date if isinstance(exit_date, str) else exit_date.strftime('%Y-%m-%d'),
                exit_price if isinstance(exit_price, str) else f"{exit_price:.2f}",
                trade['type'],
                trade['shares'],
                "positive" if profit > 0 else "negative",
                profit,
                "positive" if profit_pct > 0 else "negative",
                profit_pct,
                exit_reason
            )
        
        html += """
            </table>
        </body>
        </html>
        """
        
        # Speichere HTML-Bericht, wenn Ausgabeverzeichnis angegeben ist
        if output_dir:
            output_path = Path(output_dir) / filename
            os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(html)
                
            print(f"HTML-Bericht gespeichert unter: {output_path}")
            return str(output_path)
        
        return html
