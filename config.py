
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://chance:0uBVg3p1ZdyrUvAZlqj60SQ6Oyz7BoiS@dpg-csoteii3esus73ccb800-a.singapore-postgres.render.com/iris_jl4j"


# Create an async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Set up an async session factory
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)