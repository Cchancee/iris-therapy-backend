
from datetime import datetime


def get_email_template(purpose: str, otp_code: str):
    templates = {
        "reset_password": f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        color: #333;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: auto;
                        background-color: #ffffff;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #0056b3;
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    .otp-code {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #333;
                        text-align: center;
                        padding: 15px;
                        background-color: #f4f4f4;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .message {{
                        font-size: 16px;
                        line-height: 1.6;
                        color: #555;
                        margin-bottom: 20px;
                    }}
                    .footer {{
                        text-align: center;
                        font-size: 12px;
                        color: #999;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">Password Reset Verification</div>
                    <div class="message">
                        Hello,<br><br>
                        Use the OTP code below to reset your password. It’s valid for 10 minutes, so be quick! ⚡
                    </div>
                    <div class="otp-code">{otp_code}</div>
                    <div class="message">
                        If you didn’t request this, just ignore it.
                    </div>
                    <div class="footer">
                        &copy; {datetime.now().year} Iris Therapy | Need help? Contact us at this email
                    </div>
                </div>
            </body>
        </html>
    """,
    "login_otp": f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        color: #333;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: auto;
                        background-color: #ffffff;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #0056b3;
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    .otp-code {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #333;
                        text-align: center;
                        padding: 15px;
                        background-color: #f4f4f4;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .message {{
                        font-size: 16px;
                        line-height: 1.6;
                        color: #555;
                        margin-bottom: 20px;
                    }}
                    .footer {{
                        text-align: center;
                        font-size: 12px;
                        color: #999;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">Login Verification</div>
                    <div class="message">
                        Hello,<br><br>
                        Use the OTP code below to complete your login. This code is valid for 10 minutes.
                    </div>
                    <div class="otp-code">{otp_code}</div>
                    <div class="message">
                        If you didn’t try to log in, please ignore this email or contact support if this wasn’t you.
                    </div>
                    <div class="footer">
                        &copy; {datetime.now().year} Iris Therapy | Need help? Contact us at this email
                    </div>
                </div>
            </body>
        </html>
        """
        # Additional templates as needed
    }
    return templates.get(purpose, "Default email message")