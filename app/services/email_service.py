from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_FROM=os.getenv('MAIL_FROM'),
    MAIL_PORT=int(os.getenv('MAIL_PORT', 587)),
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_FROM_NAME=os.getenv('MAIL_FROM_NAME', 'HealthSync'),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

fastmail = FastMail(conf)

async def send_welcome_email(email: EmailStr, username: str):
    message = MessageSchema(
        subject='Welcome to HealthSync!',
        recipients=[email],
        body=f"""
        <html>
            <body>
                <h2>Welcome to HealthSync, {username}!</h2>
                <p>Thank you for registering with HealthSync. Your account has been successfully created.</p>
                <p>Your login credentials:</p>
                <ul>
                    <li>Username: {username}</li>
                    <li>Email: {email}</li>
                </ul>
                <p>You can now log in to access all features of HealthSync:</p>
                <ul>
                    <li>Track your symptoms</li>
                    <li>Get personalized meal recommendations</li>
                    <li>Monitor your health progress</li>
                    <li>Receive AI-powered health insights</li>
                </ul>
                <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                <p>Best regards,<br>The HealthSync Team</p>
            </body>
        </html>
        """,
        subtype='html'
    )
    
    await fastmail.send_message(message)

async def send_password_reset_email(email: EmailStr, reset_token: str):
    message = MessageSchema(
        subject='Reset Your HealthSync Password',
        recipients=[email],
        body=f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your HealthSync password.</p>
                <p>To reset your password, please click the link below:</p>
                <p><a href="http://localhost:8000/reset-password?token={reset_token}">Reset Password</a></p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <p>Best regards,<br>The HealthSync Team</p>
            </body>
        </html>
        """,
        subtype='html'
    )
    
    await fastmail.send_message(message)