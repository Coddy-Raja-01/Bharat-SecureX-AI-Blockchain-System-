import os
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))
except ImportError:
    pass

from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///sih_database.db")

connect_args = {}
engine = None

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    print("[Database] Using SQLite storage (sih_database.db)")
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print("[Database] PostgreSQL engine configured.")

# Enable foreign keys for SQLite
from sqlalchemy import event
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Node(Base):
    __tablename__ = "nodes"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, nullable=False)  # Person, Phone, BankAccount, Vehicle, Address
    label = Column(String, nullable=False)
    attributes = Column(JSON, default=dict)  # Stores demographic/metadata attributes

class Edge(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)  # CALL, TRANSACTION, CO_ACCUSED, ASSOCIATE, SHARED_ADDRESS, SHARED_VEHICLE
    attributes = Column(JSON, default=dict)  # frequency, duration, amount, etc.
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class GroundTruth(Base):
    __tablename__ = "ground_truth"

    node_id = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True, index=True)
    is_criminal = Column(Boolean, default=False, nullable=False)
    role = Column(String, default="normal", nullable=False)  # kingpin, financier, associate, normal
    cell_id = Column(Integer, nullable=True)  # ID of the injected criminal cell

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
