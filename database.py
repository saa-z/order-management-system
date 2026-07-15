from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Path to our db file
SQLALCHEMY_DATABASE_URL = "sqlite:///./sangiorgio.db"

engine = create_engine(
    # connect_args={"check_same_thread": False}
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal will be called at each request to our db
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# To retrieve the fast API link
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()