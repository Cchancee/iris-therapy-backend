from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from database import  init_db  # Import init_db to initialize tables
from models import User, OTP, Session
from utils import hash_password, verify_password, create_access_token
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from config import async_session  # however you configured it
from sqlalchemy.future import select
import logging
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, time
from email_validator import validate_email, EmailNotValidError
from utils import send_email, generate_and_save_otp
from email_templates import get_email_template
from fastapi.encoders import jsonable_encoder  # Import for partial updates
from typing import Optional, List
import shutil  # To save the uploaded file locally
from pathlib import Path  # To handle file paths




app = FastAPI()

# Update to allow specific origins
origins = [
    "http://localhost:5173",  # Your frontend development server
    "http://127.0.0.1:5173", # In case localhost resolves differently
    "https://iris-therapy.netlify.app", # Deployed frontend
]

# Add the CORS middleware here
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # For development. Change to your frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tables on app startup
@app.on_event("startup")
async def startup_event():
    await init_db()

# Dependency to get the DB session
async def get_db():
    async with async_session() as db:
        yield db

# Models for endpoints
class UserSignup(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_picture: Optional[str] = None
    date_of_birth: Optional[datetime] = None

    class Config:
        orm_mode = True

class CreateTherapistRequest(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    specialization: Optional[str] = None

class UserResponse(BaseModel):
    userID: int
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None  # Nullable
    last_name: Optional[str] = None   # Nullable
    phone_number: Optional[str] = None  # Nullable
    date_of_birth: Optional[datetime] = None  # Nullable
    role: str
    medicalHistory: Optional[str] = None  # Nullable, only for patients
    specialization: Optional[str] = None  # Nullable, only for therapists

    class Config:
        orm_mode = True


class SessionCreate(BaseModel):
    reason: str
    time: datetime
    patientID: int 
    therapistID: int

    class Config:
        orm_mode = True

class SessionResponse(BaseModel):
    sessionID: int
    patientID: int
    therapistID: int
    date: datetime
    time: str
    reason: str
    status: str

    class Config:
        orm_mode = True

class SessionStatusUpdate(BaseModel):
    status: str  # The status that will be updated (e.g., "pending", "cancelled", etc.)

    class Config:
        orm_mode = True
        


# Signup endpoint
@app.post("/signup")
async def signup(user: UserSignup, db: AsyncSession = Depends(get_db)):
    try:
        # Check if the user already exists
        stmt = select(User).where(User.email == user.email)
        result = await db.execute(stmt)
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password and create a User instance
        hashed_password = hash_password(user.password)
        new_user = User(
            email=user.email,
            password=hashed_password,
            role="patient",  # Default role for new users
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Generate the token and return it
        token = create_access_token({"sub": new_user.email})

        # Return the token and user data
        return {
            "access_token": token,
            "token_type": "bearer",
            "all_users": jsonable_encoder(new_user),
        }

    except HTTPException as e:
        logging.error("Signup failed: %s", str(e))
        raise e
    except Exception as e:
        logging.error("Signup failed: %s", str(e))
        raise HTTPException(status_code=500, detail="An error occurred during signup")

    finally:
        await db.close()


        
# Login endpoint
@app.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        # Validate email format
        try:
            validate_email(user.email)
        except EmailNotValidError:
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Check if the user exists in the database
        stmt = select(User).where(User.email == user.email)
        result = await db.execute(stmt)
        db_user = result.scalars().first()

        if not db_user:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        # Verify password
        if not verify_password(user.password, db_user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")

        # Generate and save OTP for login (if applicable)
        otp_code = await generate_and_save_otp(db_user.userID, db)
        logging.info("OTP generated for login: %s", otp_code)

        # Generate the HTML email content for login OTP
        email_content = get_email_template("login_otp", otp_code)

        # Send email with the OTP content
        await send_email(db_user.email, "Your Login OTP", email_content)

        return {
            "message": "OTP sent to your email for login"}

    except HTTPException as e:
        logging.error(f"HTTP error: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")


@app.post("/verify-login-otp")
async def verify_login_otp(otp_code: str, db: Session = Depends(get_db)):
    # Find the OTP entry
    stmt = select(OTP).where(OTP.code == otp_code, OTP.used == False)
    result = await db.execute(stmt)
    otp = result.scalars().first()

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Check if the OTP has already been used
    if otp.used:
        raise HTTPException(status_code=400, detail="OTP has already been used")


    # Check if OTP has expired
    if otp.expiry_date < datetime.now():
        raise HTTPException(status_code=400, detail="OTP has expired")

    # Fetch user associated with this OTP
    stmt_user = select(User).where(User.userID == otp.userID)
    result_user = await db.execute(stmt_user)
    user = result_user.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark OTP as used
    otp.used = True
    await db.commit()

    # Generate token using user's email
    token = create_access_token({"sub": user.email})

    # Return access token and user data
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": jsonable_encoder(user),  # Encode user data for JSON response
    }




@app.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        logging.info("Starting forgot password process for email: %s", request.email)

         # Validate the email format first
        try:
            validate_email(request.email)
        except EmailNotValidError as e:
            raise HTTPException(status_code=400, detail="Invalid email format")

        
        # Fetch user
        stmt = select(User).where(User.email == request.email)
        result = await db.execute(stmt)
        user = result.scalars().first()
        logging.info("User fetched: %s", user)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Generate and save OTP
        otp_code = await generate_and_save_otp(user.userID, db)
        logging.info("OTP generated: %s", otp_code)

        # Generate the HTML email content using the template function
        email_content = get_email_template("reset_password", otp_code)
        
        # Send email with HTML content
        await send_email(user.email, "Your Password Reset OTP", email_content)

        return {"message": "OTP sent to your email"}

    except HTTPException as e:
        logging.error(f"HTTP error: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")



@app.post("/reset-password")
async def reset_password(otp_code: str, new_password: str, db: Session = Depends(get_db)):
    # Step 1: Check if the OTP exists and is valid
    stmt = select(OTP).where(OTP.code == otp_code)
    result = await db.execute(stmt)
    otp = result.scalars().first()

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Step 2: Check if the OTP has already been used
    if otp.used:
        raise HTTPException(status_code=400, detail="OTP has already been used")

    # Step 3: Check if the OTP has expired
    if otp.expiry_date < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP has expired")

    # Step 4: If OTP is valid and not expired, reset the password
    stmt_user = select(User).where(User.userID == otp.userID)
    result_user = await db.execute(stmt_user)
    user = result_user.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user password (make sure to hash it before saving!)
    hashed_password = hash_password(new_password)
    user.password = hashed_password

    # Step 5: Mark OTP as used
    otp.used = True

    # Commit both the password reset and the OTP update in a single transaction
    await db.commit()

    return {"message": "Password reset successful"}


# Directory to store uploaded files
UPLOAD_DIRECTORY = Path("./uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


@app.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate = Depends(),  # To handle JSON data
    profile_picture: Optional[UploadFile] = File(None),  # File upload for profile picture
    db: AsyncSession = Depends(get_db)
):
    try:
        # Fetch the user from the database
        stmt = select(User).where(User.userID == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Process file upload if provided
        if profile_picture:
            file_path = UPLOAD_DIRECTORY / profile_picture.filename
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(profile_picture.file, buffer)

            # Update the profile picture URL in the database
            user.profile_picture = str(file_path)

        # Update other user fields
        update_data = user_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        # Commit changes to the database
        await db.commit()
        await db.refresh(user)

        return {"message": "User information updated successfully"}

    except HTTPException as e:
        logging.error(f"HTTP error: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")


@app.post("/therapists")
async def create_therapist(request: CreateTherapistRequest, db: AsyncSession = Depends(get_db)):
    # Check if the email or phone number already exists
    stmt = select(User).where((User.email == request.email) | (User.phone_number == request.phone_number))
    result = await db.execute(stmt)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email or phone number already in use")

    # Create a new therapist
    new_therapist = User(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        date_of_birth=request.date_of_birth,
        role="therapist",  # Ensure the role is set to 'therapist'
        specialization=request.specialization,
        password=hash_password("defaultpassword"),  # Set a default password; recommend sending an email for a reset
    )

    # Add the therapist to the database
    db.add(new_therapist)
    await db.commit()
    await db.refresh(new_therapist)

    return {"message": "Therapist created successfully", "therapist_id": new_therapist.userID}


@app.get("/users", response_model=List[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    # Query to fetch all users
    stmt = select(User)
    result = await db.execute(stmt)
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users


@app.get("/therapists", response_model=List[UserResponse])
async def get_therapists(db: AsyncSession = Depends(get_db)):
    # Query to fetch users with the role of "therapist"
    stmt = select(User).where(User.role == "therapist")
    result = await db.execute(stmt)
    therapists = result.scalars().all()

    if not therapists:
        raise HTTPException(status_code=404, detail="No therapists found")

    return therapists


@app.get("/patients", response_model=List[UserResponse])
async def get_patients(db: AsyncSession = Depends(get_db)):
    # Query to fetch users with the role of "patient"
    stmt = select(User).where(User.role == "patient")
    result = await db.execute(stmt)
    patients = result.scalars().all()

    if not patients:
        raise HTTPException(status_code=404, detail="No patients found")

    return patients


@app.post("/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: AsyncSession = Depends(get_db)):
    # Validate therapist exists
    stmt = select(User).where(User.userID == session_data.therapistID, User.role == "therapist")
    result = await db.execute(stmt)
    therapist = result.scalars().first()

    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")

    # Create a new session object
    new_session = Session(
        patientID=session_data.patientID,
        therapistID=session_data.therapistID,
        date=session_data.time.date(),
        time=session_data.time.time(),
        reason=session_data.reason,
    )

    # Add and commit the session to the database
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    # Convert time to string format before returning it
    session_response = SessionResponse(
        sessionID=new_session.sessionID,
        patientID=new_session.patientID,
        therapistID=new_session.therapistID,
        date=new_session.date,
        time=new_session.time.strftime("%H:%M:%S"),  # Format time as string
        status=new_session.status,
        reason=new_session.reason,
    )

    return session_response


@app.get("/session", response_model=List[SessionResponse])
async def get_all_appointments(db: AsyncSession = Depends(get_db)):
    # Query to fetch all appointments (sessions)
    stmt = select(Session)
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    if not sessions:
        raise HTTPException(status_code=404, detail="No appointments found")
    
     # Manually convert time to string in the response
    for session in sessions:
        if isinstance(session.time, time):
            session.time = session.time.strftime("%H:%M:%S")

    return sessions



@app.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session_status(
    session_id: int,
    session_update: SessionStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Fetch the session from the database
        stmt = select(Session).where(Session.sessionID == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Update the status of the session
        session.status = session_update.status

        # Commit changes to the database
        await db.commit()
        await db.refresh(session)

        return session  # Return the updated session as a response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")
