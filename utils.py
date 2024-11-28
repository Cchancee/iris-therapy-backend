from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import random
from models import OTP
from sqlalchemy.ext.asyncio import AsyncSession
import aiosmtplib


# Load environment variables
load_dotenv()


async def send_email(recipient_email: str, subject: str, html_content: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Set the HTML content
    msg.attach(MIMEText(html_content, "html"))

    # Send the email
    await aiosmtplib.send(
        msg,
        hostname=smtp_server,
        port=smtp_port,
        start_tls=True,
        username=smtp_user,
        password=smtp_password,
    )


async def generate_and_save_otp(user_id: int, db: AsyncSession):
    otp_code = str(random.randint(100000, 999999))
    expiration = datetime.now() + timedelta(minutes=10)

    
    # Create an OTP instance
    otp_instance = OTP(
        userID=user_id,
        code=otp_code,
        expiry_date=expiration,
    )
    db.add(otp_instance)
    await db.commit()
    return otp_code



# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# JWT token generation
SECRET_KEY = "your_secret_key_here"  # Replace with an actual secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Token creation utility with expiration handling for reset tokens
def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt