"""
Database models for CommerceCalc using SQLAlchemy.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean,
    DateTime, ForeignKey, JSON, Float, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), index=True)
    category = Column(String(100))
    product_type = Column(String(50), default="physical")  # physical, digital, dropshipping, etc.
    supplier_name = Column(String(255))
    channel = Column(String(100))
    description = Column(Text)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Cost fields
    purchase_cost = Column(Numeric(15, 4), default=0)
    packaging_cost = Column(Numeric(15, 4), default=0)
    preparation_cost = Column(Numeric(15, 4), default=0)
    inbound_shipping = Column(Numeric(15, 4), default=0)
    inspection_cost = Column(Numeric(15, 4), default=0)
    overhead_allocated = Column(Numeric(15, 4), default=0)
    import_cost = Column(Numeric(15, 4), default=0)
    other_cost = Column(Numeric(15, 4), default=0)

    # GST settings
    gst_rate_pct = Column(Numeric(5, 2), default=0)
    gst_inclusive = Column(Boolean, default=False)
    itc_eligible = Column(Boolean, default=True)
    hsn_code = Column(String(20))

    # Linked scenarios
    scenarios = relationship("Scenario", back_populates="product", cascade="all, delete-orphan")


class MarketplaceFeeProfile(Base):
    __tablename__ = "marketplace_fee_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    platform = Column(String(100))
    category = Column(String(100))
    currency = Column(String(10), default="INR")
    is_verified = Column(Boolean, default=False)
    source_url = Column(String(500))
    source_document = Column(String(500))
    last_verified_date = Column(DateTime)
    effective_from = Column(DateTime)
    notes = Column(Text)
    is_archived = Column(Boolean, default=False)
    fee_rules_json = Column(JSON)   # Serialized FeeRule list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    scenario_type = Column(String(50), default="profit")

    # Selling details
    listed_price = Column(Numeric(15, 4), default=0)
    actual_selling_price = Column(Numeric(15, 4), default=0)
    quantity = Column(Integer, default=1)
    customer_discount = Column(Numeric(15, 4), default=0)
    coupon_discount = Column(Numeric(15, 4), default=0)
    seller_funded_promo = Column(Numeric(15, 4), default=0)
    customer_paid_shipping = Column(Numeric(15, 4), default=0)
    payment_method = Column(String(50), default="prepaid")
    marketplace_profile_id = Column(String(100))

    # Selling expenses
    marketplace_commission = Column(Numeric(15, 4), default=0)
    closing_fee = Column(Numeric(15, 4), default=0)
    payment_gateway_fee = Column(Numeric(15, 4), default=0)
    forward_shipping = Column(Numeric(15, 4), default=0)
    reverse_shipping = Column(Numeric(15, 4), default=0)
    packaging_fulfillment = Column(Numeric(15, 4), default=0)
    cod_charge = Column(Numeric(15, 4), default=0)
    affiliate_commission = Column(Numeric(15, 4), default=0)
    advertising_cost = Column(Numeric(15, 4), default=0)
    return_expense = Column(Numeric(15, 4), default=0)
    rto_expense = Column(Numeric(15, 4), default=0)
    other_variable_cost = Column(Numeric(15, 4), default=0)

    # Result cache (JSON)
    result_json = Column(JSON)
    is_profitable = Column(Boolean)
    contribution_margin_pct = Column(Numeric(8, 4))
    net_profit = Column(Numeric(15, 4))

    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="scenarios")


class CalculationHistory(Base):
    __tablename__ = "calculation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calculator_type = Column(String(100))  # 'profit', 'pricing', 'gst', etc.
    inputs_json = Column(JSON)
    results_json = Column(JSON)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AppSettings(Base):
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text)
    value_type = Column(String(20), default="string")  # string, int, decimal, bool, json
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500))
    total_rows = Column(Integer, default=0)
    successful_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    marketplace_profile_id = Column(String(100))
    status = Column(String(50), default="pending")  # pending, processing, complete, failed
    error_log_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
