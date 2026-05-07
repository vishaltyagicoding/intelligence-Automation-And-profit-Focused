"""
Email Utility for Sending OTP
==============================
Uses Gmail SMTP to send verification emails
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_email(email, otp, username):
    """
    Send OTP verification email to user
    
    Args:
        email (str): Recipient email address
        otp (str): 6-digit OTP code
        username (str): User's username
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify Your SmartRisk Account - OTP Code"
        message["From"] = f"SmartRisk <{sender_email}>"
        message["To"] = email
        
        # Email body (HTML)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    border-radius: 10px;
                    padding: 30px;
                    color: #fff;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #06b6d4;
                    margin-bottom: 10px;
                }}
                .otp-box {{
                    background: rgba(6, 182, 212, 0.1);
                    border: 2px solid #06b6d4;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .otp-code {{
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #06b6d4;
                    margin: 10px 0;
                }}
                .info {{
                    background: rgba(59, 130, 246, 0.1);
                    border-left: 4px solid #3b82f6;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .warning {{
                    background: rgba(251, 191, 36, 0.1);
                    border-left: 4px solid #fbbf24;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                    color: #fbbf24;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    font-size: 14px;
                    color: #94a3b8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">SmartRisk</div>
                    <p style="color: #94a3b8; margin: 0;">Powered by SmartRisk Trading Platform</p>
                </div>
                
                <h2 style="color: #fff; margin-bottom: 20px;">Welcome, {username}!</h2>
                
                <p>Thank you for signing up for SmartRisk. To complete your registration and activate your <strong>3-day free trial</strong>, please verify your email address.</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #94a3b8;">Your verification code is:</p>
                    <div class="otp-code">{otp}</div>
                    <p style="margin: 0; color: #94a3b8; font-size: 14px;">Enter this code on the verification page</p>
                </div>
                
                <div class="info">
                    <strong>⏰ This code expires in 10 minutes</strong><br>
                    Please enter the code promptly to complete your registration.
                </div>
                
                <div class="warning">
                    <strong>🔒 Security Notice</strong><br>
                    Never share this code with anyone. SmartRisk will never ask for your verification code via phone or email.
                </div>
                
                <p style="margin-top: 30px;">If you didn't request this code, please ignore this email. Your account will not be created without verification.</p>
                
                <div class="footer">
                    <p>© 2026 SmartRisk. Powered by SmartRisk trading signals for crypto markets.</p>
                    <p>Questions? Contact us at <a href="mailto:alberttyagi123@gmail.com" style="color: #06b6d4;">alberttyagi123@gmail.com</a> or <a href="mailto:smarttriskfx@gmail.com" style="color: #06b6d4;">smarttriskfx@gmail.com</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (fallback)
        text_body = f"""
        SmartRisk - Email Verification
        
        Welcome, {username}!
        
        Your verification code is: {otp}
        
        This code expires in 10 minutes.
        
        Enter this code on the verification page to complete your registration and activate your 3-day free trial.
        
        If you didn't request this code, please ignore this email.
        
        © 2026 SmartRisk
        Contact: alberttyagi123@gmail.com or smarttriskfx@gmail.com
        """
        
        # Attach both versions
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        
        logger.info(f"✅ OTP email sent successfully to {email} with code: {otp}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send OTP email to {email}: {e}", exc_info=True)
        return False


def send_welcome_email(email, username):
    """
    Send welcome email after successful verification
    
    Args:
        email (str): User email address
        username (str): User's username
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Welcome to SmartRisk - Your 3-Day Free Trial is Active!"
        message["From"] = f"SmartRisk <{sender_email}>"
        message["To"] = email
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    border-radius: 10px;
                    padding: 30px;
                    color: #fff;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #06b6d4;
                    margin-bottom: 10px;
                }}
                .success-box {{
                    background: rgba(16, 185, 129, 0.1);
                    border: 2px solid #10b981;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .feature {{
                    background: rgba(59, 130, 246, 0.1);
                    border-left: 4px solid #3b82f6;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
                    color: #fff;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    font-size: 14px;
                    color: #94a3b8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">SmartRisk</div>
                    <p style="color: #94a3b8; margin: 0;">Powered by SmartRisk Trading Platform</p>
                </div>
                
                <div class="success-box">
                    <h2 style="color: #10b981; margin: 0;">🎉 Welcome to SmartRisk!</h2>
                    <p style="margin: 10px 0 0 0; color: #94a3b8;">Your 3-day free trial is now active</p>
                </div>
                
                <p>Hi {username},</p>
                
                <p>Congratulations! Your email has been verified and your account is now active. You have <strong>3 days of FREE access</strong> to all SmartRisk features.</p>
                
                <h3 style="color: #06b6d4;">What you get with SmartRisk:</h3>
                
                <div class="feature">
                    <strong>📊 Real-Time Trading Signals</strong><br>
                    SmartRisk BUY and SELL signals for Bitcoin, Ethereum, BNB, and Solana
                </div>
                
                <div class="feature">
                    <strong>⏰ Multiple Timeframes</strong><br>
                    5-minute, 15-minute, 1-hour, 4-hour, and daily signals
                </div>
                
                <div class="feature">
                    <strong>📈 Live Market Data</strong><br>
                    Real-time price updates and market analysis
                </div>
                
                <div class="feature">
                    <strong>📜 Signal History</strong><br>
                    Track all past signals and analyze performance
                </div>
                
                <p style="margin-top: 30px;">Need help? We're here for you! Contact us anytime at <a href="mailto:alberttyagi123@gmail.com" style="color: #06b6d4;">alberttyagi123@gmail.com</a> or <a href="mailto:smarttriskfx@gmail.com" style="color: #06b6d4;">smarttriskfx@gmail.com</a></p>
                
                <div class="footer">
                    <p>© 2026 SmartRisk. Powered by SmartRisk trading signals for crypto markets.</p>
                    <p><strong>Disclaimer:</strong> Trading cryptocurrencies carries risk. Past performance does not guarantee future results.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to SmartRisk!
        
        Hi {username},
        
        Your email has been verified and your 3-day free trial is now active!
        
        What you get:
        - Real-time trading signals for BTC, ETH, BNB, SOL
        - Multiple timeframes (5m, 15m, 1h, 4h, 1d)
        - Live market data
        - Signal history tracking
        
        Log in to your SmartRisk account to access all features.
        
        Need help? Contact us at alberttyagi123@gmail.com or smarttriskfx@gmail.com
        
        © 2026 SmartRisk
        """
        
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        
        logger.info(f"✅ Welcome email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send welcome email to {email}: {e}", exc_info=True)
        return False


def send_password_reset_email(email, otp, username):
    """
    Send password reset OTP email to user
    
    Args:
        email (str): Recipient email address
        otp (str): 6-digit OTP code
        username (str): User's username
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Reset Your SmartRisk Password - OTP Code"
        message["From"] = f"SmartRisk <{sender_email}>"
        message["To"] = email
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    border-radius: 10px;
                    padding: 30px;
                    color: #fff;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #06b6d4;
                    margin-bottom: 10px;
                }}
                .otp-box {{
                    background: rgba(6, 182, 212, 0.1);
                    border: 2px solid #06b6d4;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .otp-code {{
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #06b6d4;
                    margin: 10px 0;
                }}
                .info {{
                    background: rgba(59, 130, 246, 0.1);
                    border-left: 4px solid #3b82f6;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .warning {{
                    background: rgba(251, 191, 36, 0.1);
                    border-left: 4px solid #fbbf24;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                    color: #fbbf24;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    font-size: 14px;
                    color: #94a3b8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">SmartRisk</div>
                    <p style="color: #94a3b8; margin: 0;">Powered by SmartRisk Trading Platform</p>
                </div>
                
                <h2 style="color: #fff; margin-bottom: 20px;">🔒 Password Reset Request</h2>
                
                <p>Hi {username},</p>
                
                <p>We received a request to reset your password. Use the code below to reset your password:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #94a3b8;">Your password reset code is:</p>
                    <div class="otp-code">{otp}</div>
                    <p style="margin: 0; color: #94a3b8; font-size: 14px;">Enter this code on the password reset page</p>
                </div>
                
                <div class="info">
                    <strong>⏰ This code expires in 10 minutes</strong><br>
                    Please enter the code promptly to reset your password.
                </div>
                
                <div class="warning">
                    <strong>🔒 Security Notice</strong><br>
                    If you didn't request a password reset, please ignore this email and your password will remain unchanged. Someone may have entered your email address by mistake.
                </div>
                
                <p style="margin-top: 30px;">For security reasons, never share this code with anyone. SmartRisk will never ask for your verification code via phone or email.</p>
                
                <div class="footer">
                    <p>© 2026 SmartRisk. Powered by SmartRisk trading signals for crypto markets.</p>
                    <p>Questions? Contact us at <a href="mailto:alberttyagi123@gmail.com" style="color: #06b6d4;">alberttyagi123@gmail.com</a> or <a href="mailto:smarttriskfx@gmail.com" style="color: #06b6d4;">smarttriskfx@gmail.com</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        SmartRisk - Password Reset
        
        Hi {username},
        
        Your password reset code is: {otp}
        
        This code expires in 10 minutes.
        
        Enter this code on the password reset page to create a new password.
        
        If you didn't request this, please ignore this email.
        
        © 2026 SmartRisk
        Contact: alberttyagi123@gmail.com or smarttriskfx@gmail.com
        """
        
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        
        logger.info(f"✅ Password reset email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send password reset email to {email}: {e}", exc_info=True)
        return False



def send_subscription_activated_email(email, username, activation_date=None, expiry_date=None):
    """
    Send subscription activation email to user (for paid subscription, not trial)
    
    Args:
        email (str): Recipient email address
        username (str): User's username
        activation_date (datetime): When subscription was activated
        expiry_date (datetime): When subscription will expire
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        from django.utils import timezone
        
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD
        
        # Format dates
        if activation_date:
            activated_on = activation_date.strftime("%B %d, %Y at %I:%M %p")
        else:
            activated_on = timezone.now().strftime("%B %d, %Y at %I:%M %p")
        
        if expiry_date:
            expires_on = expiry_date.strftime("%B %d, %Y at %I:%M %p")
        else:
            expires_on = (timezone.now() + timezone.timedelta(days=30)).strftime("%B %d, %Y at %I:%M %p")
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "🎉 Your SmartRisk Subscription is Now Active!"
        message["From"] = f"SmartRisk <{sender_email}>"
        message["To"] = email
        
        # Email body (HTML)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px;
                    padding: 40px;
                    text-align: center;
                    color: white;
                }}
                .crown {{
                    font-size: 60px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: white;
                    margin: 0 0 20px 0;
                }}
                .message {{
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .date-box {{
                    background: rgba(255, 255, 255, 0.15);
                    border-radius: 8px;
                    padding: 15px;
                    margin: 15px 0;
                    text-align: left;
                }}
                .features {{
                    text-align: left;
                    background: white;
                    color: #333;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .feature-item {{
                    margin: 10px 0;
                    padding-left: 25px;
                    position: relative;
                }}
                .feature-item:before {{
                    content: "✓";
                    position: absolute;
                    left: 0;
                    color: #10b981;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: rgba(255, 255, 255, 0.8);
                }}
                .button {{
                    display: inline-block;
                    background: white;
                    color: #667eea;
                    padding: 15px 30px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="crown">👑</div>
                <h1>Subscription Activated!</h1>
                
                <div class="message">
                    <p style="font-size: 18px; margin: 0;">
                        Hello <strong>{username}</strong>,
                    </p>
                    <p style="font-size: 16px;">
                        Great news! Your SmartRisk subscription has been activated and you now have <strong>full access</strong> to all premium features for the next <strong>30 days</strong>!
                    </p>
                    
                    <div class="date-box">
                        <p style="margin: 5px 0;"><strong>📅 Activated On:</strong> {activated_on}</p>
                        <p style="margin: 5px 0;"><strong>⏰ Expires On:</strong> {expires_on}</p>
                    </div>
                </div>
                
                <div class="features">
                    <h3 style="color: #667eea; margin-top: 0;">What You Get:</h3>
                    <div class="feature-item">Real-time SmartRisk trading signals</div>
                    <div class="feature-item">4 Cryptocurrencies (BTC, ETH, XAU, LTC)</div>
                    <div class="feature-item">10 Different timeframes (1m to 1 month)</div>
                    <div class="feature-item">Complete signal history (last 5 months)</div>
                    <div class="feature-item">Live market data and price updates</div>
                    <div class="feature-item">Priority customer support</div>
                </div>
                
                <div class="footer">
                    <p>Your subscription will automatically expire on <strong>{expires_on}</strong></p>
                    <p>Need help? Contact us at <strong>alberttyagi123@gmail.com</strong> or <strong>smarttriskfx@gmail.com</strong></p>
                    <p style="margin-top: 20px;">
                        © 2026 SmartRisk. Powered by SmartRisk trading signals.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        logger.info(f"✅ Subscription activation email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send subscription activation email to {email}: {e}")
        return False


def send_subscription_deactivated_email(email, username):
    """
    Send subscription deactivation email to user
    
    Args:
        email (str): Recipient email address
        username (str): User's username
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your SmartRisk Subscription Has Ended"
        message["From"] = f"SmartRisk <{sender_email}>"
        message["To"] = email
        
        # Email body (HTML)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
                    border-radius: 10px;
                    padding: 40px;
                    text-align: center;
                    color: white;
                }}
                .icon {{
                    font-size: 60px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: white;
                    margin: 0 0 20px 0;
                }}
                .message {{
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: rgba(255, 255, 255, 0.8);
                }}
                .button {{
                    display: inline-block;
                    background: white;
                    color: #ef4444;
                    padding: 15px 30px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">⏰</div>
                <h1>Subscription Ended</h1>
                
                <div class="message">
                    <p style="font-size: 18px; margin: 0;">
                        Hello <strong>{username}</strong>,
                    </p>
                    <p style="font-size: 16px;">
                        Your SmartRisk subscription has ended. You no longer have access to premium features including the dashboard and trading signals.
                    </p>
                    <p style="font-size: 16px;">
                        To continue enjoying Powered by SmartRisk trading signals and full access, please contact our support team to reactivate your subscription.
                    </p>
                </div>
                
                <a href="mailto:alberttyagi123@gmail.com,smarttriskfx@gmail.com?subject=Subscription Reactivation Request" class="button">
                    Contact Support
                </a>
                
                <div class="footer">
                    <p>Thank you for using SmartRisk!</p>
                    <p>Need help? Email us at <strong>alberttyagi123@gmail.com</strong> or <strong>smarttriskfx@gmail.com</strong></p>
                    <p style="margin-top: 20px;">
                        © 2026 SmartRisk. Powered by SmartRisk trading signals.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        logger.info(f"✅ Subscription deactivation email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send subscription deactivation email to {email}: {e}")
        return False



def send_trial_expired_email(email, username):
    """
    Send trial expiration email to user (different from paid subscription end)
    
    Args:
        email (str): Recipient email address
        username (str): User's username
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your SmartRisk Free Trial Has Ended"
        message["From"] = f"SmartRisk <{sender_email}>"
        message["To"] = email
        
        # Email body (HTML)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                    border-radius: 10px;
                    padding: 40px;
                    text-align: center;
                    color: white;
                }}
                .icon {{
                    font-size: 60px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: white;
                    margin: 0 0 20px 0;
                }}
                .message {{
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .benefits {{
                    text-align: left;
                    background: white;
                    color: #333;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .benefit-item {{
                    margin: 10px 0;
                    padding-left: 25px;
                    position: relative;
                }}
                .benefit-item:before {{
                    content: "⭐";
                    position: absolute;
                    left: 0;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: rgba(255, 255, 255, 0.8);
                }}
                .button {{
                    display: inline-block;
                    background: white;
                    color: #3b82f6;
                    padding: 15px 30px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">⏰</div>
                <h1>Your Free Trial Has Ended</h1>
                
                <div class="message">
                    <p style="font-size: 18px; margin: 0;">
                        Hello <strong>{username}</strong>,
                    </p>
                    <p style="font-size: 16px;">
                        Your 3-day free trial of SmartRisk has come to an end. We hope you enjoyed exploring our Powered by SmartRisk trading signals!
                    </p>
                    <p style="font-size: 16px;">
                        To continue accessing premium features and stay ahead in the crypto markets, please contact us to activate your subscription.
                    </p>
                </div>
                
                <div class="benefits">
                    <h3 style="color: #3b82f6; margin-top: 0;">Continue Enjoying:</h3>
                    <div class="benefit-item">Real-time trading signals for 4 cryptocurrencies</div>
                    <div class="benefit-item">10 different timeframes for precise analysis</div>
                    <div class="benefit-item">Complete signal history and performance tracking</div>
                    <div class="benefit-item">Live market data and price updates</div>
                    <div class="benefit-item">24/7 customer support</div>
                </div>
                
                <a href="mailto:alberttyagi123@gmail.com,smarttriskfx@gmail.com?subject=Subscription Activation Request" class="button">
                    Activate Subscription →
                </a>
                
                <div class="footer">
                    <p><strong>Ready to get started?</strong></p>
                    <p>Contact us at <strong>alberttyagi123@gmail.com</strong> or <strong>smarttriskfx@gmail.com</strong> to activate your subscription.</p>
                    <p>We're available 24/7 to help you get back to trading!</p>
                    <p style="margin-top: 20px;">
                        © 2026 SmartRisk. Powered by SmartRisk trading signals.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        logger.info(f"✅ Trial expiration email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send trial expiration email to {email}: {e}")
        return False