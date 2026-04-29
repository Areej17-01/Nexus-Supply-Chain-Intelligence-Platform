from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Generator, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from .config import DATABASE_URL

Base = declarative_base()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True)
    name = Column(String)
    country = Column(String, nullable=False, default="Unknown")
    region = Column(String)
    categories = Column(Text, nullable=False, default="[]")
    capabilities = Column(Text)
    base_price_map = Column(Text)
    price_floor_map = Column(Text)
    lead_time_days = Column(Integer)
    certifications = Column(Text)
    capacity_per_month = Column(Integer, default=1000)
    trust_score = Column(Float, default=0.75)
    fit_score = Column(Float, default=0.50)
    total_deals = Column(Integer, default=0)
    successful_deals = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class SupplierRLStats(Base):
    __tablename__ = "supplier_rl_stats"

    supplier_id = Column(String, primary_key=True)
    negotiations = Column(Integer, default=0)
    total_discount_achieved = Column(Float, default=0.0)
    max_discount_seen = Column(Float, default=0.0)
    best_opening_ask = Column(Float, default=0.15)


class Negotiation(Base):
    __tablename__ = "negotiations"

    id = Column(String, primary_key=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"))
    buyer_id = Column(String, default="buyer-nexus")
    status = Column(String)
    current_round = Column(Integer, default=0)
    max_rounds = Column(Integer, default=3)
    open_offer = Column(Float)
    counter_offer = Column(Float)
    walkaway_price = Column(Float)
    current_price = Column(Float)
    product_category = Column(String)
    quantity = Column(Integer)
    initial_supplier_ask = Column(Float)
    final_price = Column(Float)
    destination_region = Column(String)
    product = Column(String)
    explored = Column(Boolean, default=False)
    bom_snapshot = Column(Text)
    shortlist_snapshot = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    parent_negotiation_id = Column(String, nullable=True)

    supplier = relationship("Supplier")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    negotiation_id = Column(String, ForeignKey("negotiations.id"))
    round = Column(Integer)
    sender = Column(String)
    message_type = Column(String)
    human_message = Column(Text)
    price = Column(Float)
    payload = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class RLScore(Base):
    __tablename__ = "rl_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"))
    negotiation_id = Column(String)
    outcome = Column(String)
    initial_ask = Column(Float)
    final_price = Column(Float)
    discount_given = Column(Float)
    rounds_taken = Column(Integer)
    buyer_budget = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True)
    negotiation_id = Column(String, ForeignKey("negotiations.id"))
    supplier_id = Column(String, ForeignKey("suppliers.id"))
    total_value = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)
    content = Column(Text)


def ensure_supplier_schema() -> None:
    inspector = inspect(engine)
    if "suppliers" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("suppliers")}
    missing = [col for col in Supplier.__table__.columns if col.name not in existing]
    if not missing:
        return
    with engine.begin() as conn:
        for col in missing:
            col_type = col.type.compile(engine.dialect)
            if engine.dialect.name == "postgresql":
                ddl = (
                    f'ALTER TABLE {Supplier.__tablename__} '
                    f'ADD COLUMN IF NOT EXISTS "{col.name}" {col_type}'
                )
            else:
                ddl = (
                    f'ALTER TABLE {Supplier.__tablename__} '
                    f'ADD COLUMN "{col.name}" {col_type}'
                )
            conn.execute(text(ddl))


def init_db() -> None:
    inspector = inspect(engine)
    if "suppliers" in inspector.get_table_names():
        existing_cols = {col["name"] for col in inspector.get_columns("suppliers")}
        model_cols = {col.name for col in Supplier.__table__.columns}
        if existing_cols - model_cols:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS suppliers CASCADE"))
    Base.metadata.create_all(bind=engine)
    ensure_supplier_schema()


def cleanup_expired_negotiations() -> int:
    with get_db_session() as db:
        now = datetime.utcnow()
        expired = db.query(Negotiation).filter(Negotiation.expires_at < now).all()
        if not expired:
            return 0
        expired_ids = [n.id for n in expired]
        db.query(Message).filter(Message.negotiation_id.in_(expired_ids)).delete(synchronize_session=False)
        db.query(Negotiation).filter(Negotiation.id.in_(expired_ids)).delete(synchronize_session=False)
        db.commit()
        return len(expired_ids)


@contextmanager
def get_db_session() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_expiry(hours: int = 24) -> datetime:
    return datetime.utcnow() + timedelta(hours=hours)
