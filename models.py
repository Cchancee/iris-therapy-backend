from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, Time, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'  # Keep table name consistent (capitalize "Users")
    
    userID = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="patient")  # Role: "patient" or "therapist"
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, unique=True, nullable=True)
    profile_picture = Column(String, nullable=True)  # URL or file path to profile picture
    date_of_birth = Column(Date, nullable=True)  # Date of birth
    is_verified = Column(Boolean, default=False)  # Email or phone verification status
    
    # Role-specific fields
    medicalHistory = Column(Text, nullable=True)  # Only for patients
    specialization = Column(String, nullable=True)  # Only for therapists

    # Relationship with OTP model
    otps = relationship("OTP", back_populates="user")


class Session(Base):
    __tablename__ = 'Sessions'
    
    sessionID = Column(Integer, primary_key=True, index=True)
    patientID = Column(Integer, ForeignKey('Users.userID'), nullable=False)  # Ensure capitalization matches
    therapistID = Column(Integer, ForeignKey('Users.userID'), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    status = Column(String, nullable=False, default="pending")  # Session status
    reason = Column(String, nullable=True)  # Reason for the session

    # Optional: Relationships for easy access to patient and therapist
    patient = relationship("User", foreign_keys=[patientID])
    therapist = relationship("User", foreign_keys=[therapistID])


class Feedback(Base):
    __tablename__ = 'Feedback'
    
    feedbackID = Column(Integer, primary_key=True, index=True)
    sessionID = Column(Integer, ForeignKey('Sessions.sessionID'), nullable=False)  # Feedback linked to a session
    rating = Column(Integer, nullable=False)
    comments = Column(Text, nullable=True)


class OTP(Base):
    __tablename__ = "OTPs"  # Keep consistent with capitalization
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True)  # OTP code
    userID = Column(Integer, ForeignKey("Users.userID"), nullable=False)  # Correct capitalization
    expiry_date = Column(DateTime)  # OTP expiry time
    used = Column(Boolean, default=False)  # To track if OTP has been used

    # Relationship back to User
    user = relationship("User", back_populates="otps")
