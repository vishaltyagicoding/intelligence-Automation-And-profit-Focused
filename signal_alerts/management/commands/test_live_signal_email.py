"""
Test Live Signal Email
======================
Fetches real live market data, detects current signal, and sends test email
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from signal_alerts.email_utils import send_signal_alert_email
import requests
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Test signal email with real live market data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            default='BTCUSD',
            help='Crypto symbol (default: BTCUSD)'
        )
        parser.add_argument(
            '--timeframe',
            type=str,
            default='1h',
            help='Timeframe (default: 1h)'
        )

    def handle(self, *args, **options):
        symbol = options['symbol']
        timeframe = options['timeframe']
        
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("🔴 LIVE SIGNAL EMAIL TEST"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"Symbol: {symbol}")
        self.stdout.write(f"Timeframe: {timeframe}")
        self.stdout.write("")
        
        # Step 1: Fetch real live market data from Binance
        self.stdout.write("📊 Fetching live market data from Binance...")
        
        try:
            # Map symbol to Binance format
            binance_symbol = symbol.replace('USD', 'USDT')
            if symbol == 'XAUUSD':
                binance_symbol = 'PAXGUSDT'  # Gold
            
            # Map timeframe to Binance format
            binance_timeframe = {
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '2h': '2h',
                '4h': '4h',
                '1d': '1d'
            }.get(timeframe, '1h')
            
            # Fetch latest candle data from Binance.com (matches TradingView)
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': binance_symbol,
                'interval': binance_timeframe,
                'limit': 2  # Get last 2 candles
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            candles = response.json()
            
            if not candles:
                self.stdout.write(self.style.ERROR("❌ No market data received"))
                return
            
            # Get latest completed candle
            latest_candle = candles[-2]  # -2 because -1 is still forming
            
            open_price = float(latest_candle[1])
            high_price = float(latest_candle[2])
            low_price = float(latest_candle[3])
            close_price = float(latest_candle[4])
            timestamp = latest_candle[0]
            
            self.stdout.write(self.style.SUCCESS("✅ Live market data fetched"))
            self.stdout.write(f"   Open:  ${open_price:,.2f}")
            self.stdout.write(f"   High:  ${high_price:,.2f}")
            self.stdout.write(f"   Low:   ${low_price:,.2f}")
            self.stdout.write(f"   Close: ${close_price:,.2f}")
            self.stdout.write("")
            
            # Step 2: Determine signal type based on price action
            self.stdout.write("🔍 Analyzing signal...")
            
            # Simple signal logic: BUY if close > open, SELL if close < open
            if close_price > open_price:
                signal_type = 'BUY'
                entry_price = close_price
                target_price = high_price * 1.02  # 2% above high
            else:
                signal_type = 'SELL'
                entry_price = close_price
                target_price = low_price * 0.98  # 2% below low
            
            self.stdout.write(self.style.SUCCESS(f"✅ Signal detected: {signal_type}"))
            self.stdout.write(f"   Entry Price: ${entry_price:,.2f}")
            self.stdout.write(f"   Target Price: ${target_price:,.2f}")
            
            # Calculate Stop Loss (50% of distance)
            if signal_type == 'BUY':
                distance = target_price - entry_price
                stop_loss = entry_price - (distance * 0.5)
            else:
                distance = entry_price - target_price
                stop_loss = entry_price + (distance * 0.5)
            
            self.stdout.write(f"   Distance: ${abs(distance):,.2f}")
            self.stdout.write(f"   Stop Loss: ${stop_loss:,.2f}")
            self.stdout.write("")
            
            # Step 3: Prepare signal data
            signal_data = {
                'crypto': symbol,
                'timeframe': timeframe,
                'signal_type': signal_type,
                'entry_price': f"{entry_price:.2f}",
                'target': f"{target_price:.2f}",
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            }
            
            # Step 4: Send email to alberttyagi123@gmail.com
            self.stdout.write("📧 Sending test email to alberttyagi123@gmail.com...")
            
            success = send_signal_alert_email(
                email='alberttyagi123@gmail.com',
                username='Albert (Test)',
                signal_data=signal_data
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS("✅ EMAIL SENT SUCCESSFULLY!"))
                self.stdout.write("")
                self.stdout.write("=" * 70)
                self.stdout.write("📧 EMAIL DETAILS:")
                self.stdout.write("=" * 70)
                self.stdout.write(f"To: alberttyagi123@gmail.com")
                self.stdout.write(f"Subject: 🔔 New {signal_type} Signal: {symbol} ({timeframe})")
                self.stdout.write("")
                self.stdout.write("Email Content:")
                self.stdout.write(f"  - Signal Type: {signal_type}")
                self.stdout.write(f"  - Crypto: {symbol}")
                self.stdout.write(f"  - Timeframe: {timeframe}")
                self.stdout.write(f"  - Entry Price: ${entry_price:,.2f}")
                self.stdout.write(f"  - Target Price: ${target_price:,.2f}")
                self.stdout.write(f"  - Stop Loss: ${stop_loss:,.2f}")
                self.stdout.write("")
                self.stdout.write(self.style.SUCCESS("✅ Check your email inbox!"))
            else:
                self.stdout.write(self.style.ERROR("❌ Failed to send email"))
                self.stdout.write("Check Django logs for error details")
            
            self.stdout.write("=" * 70)
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"❌ Error fetching market data: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            logger.exception("Error in test_live_signal_email")
