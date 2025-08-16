from __future__ import annotations
from pathlib import Path
from typing import Generator

import pandas as pd
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[1]  # backend/app
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class ProductSale(Base):
    __tablename__ = "product_sales"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    quantity_sold = Column(Float, nullable=False)


class ProductCustomerSale(Base):
    __tablename__ = "product_customer_sales"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    customer_id = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    quantity_sold = Column(Float, nullable=False)


def init_db() -> None:
    # Import models so that SQLAlchemy is aware of all tables before create_all
    # Avoid circular imports by importing inside the function
    try:
        from .models.user import User  # noqa: F401
    except Exception:
        # If user model is not available yet, continue without failing
        # Other tables will still be created
        pass
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_product_sales_df(db: Session, df: pd.DataFrame) -> None:
    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "product_id": str(row["product_id"]),
                "date": pd.to_datetime(row["date"]).date(),
                "quantity_sold": float(row["quantity_sold"]),
            }
        )
    if records:
        db.bulk_insert_mappings(ProductSale, records)
        db.commit()


def save_product_customer_sales_df(db: Session, df: pd.DataFrame) -> None:
    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "product_id": str(row["product_id"]),
                "customer_id": str(row["customer_id"]),
                "date": pd.to_datetime(row["date"]).date(),
                "quantity_sold": float(row["quantity_sold"]),
            }
        )
    if records:
        db.bulk_insert_mappings(ProductCustomerSale, records)
        db.commit()
