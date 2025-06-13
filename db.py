import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
SessionLocal = None

if DATABASE_URL and DATABASE_URL != "placeholder":
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        print(f"Skipping DB connection due to invalid DATABASE_URL: {e}")

Base = declarative_base()








# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker 
# from sqlalchemy.ext.declarative import declarative_base
# import os
# from dotenv import load_dotenv
# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()