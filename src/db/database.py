"""Database initialization and session management for CommerceCalc."""
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, AppSettings, MarketplaceFeeProfile
import json
from datetime import datetime

# Database file location
APP_DATA_DIR = Path(os.environ.get("COMMERCE_CALC_DATA", Path.home() / ".commercecalc"))
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DATA_DIR / "commercecalc.db"


def get_engine(db_url: str = None):
    """Create SQLAlchemy engine."""
    url = db_url or f"sqlite:///{DB_PATH}"
    return create_engine(
        url,
        connect_args={"check_same_thread": False},
        echo=False,
    )


def init_db(engine=None):
    """Initialize database tables."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
    _seed_defaults(engine)
    return engine


def get_session_factory(engine=None):
    """Return a session factory."""
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine, autoflush=True, autocommit=False)


def _seed_defaults(engine):
    """Seed default settings and profiles on first run."""
    SessionFactory = get_session_factory(engine)
    with SessionFactory() as session:
        # Default app settings
        defaults = [
            ("currency", "INR", "string", "Display currency"),
            ("gst_rate_pct", "18", "decimal", "Default GST rate %"),
            ("gst_inclusive", "false", "bool", "Prices inclusive of GST by default"),
            ("price_rounding", "end_99", "string", "Default price rounding method"),
            ("theme", "dark", "string", "UI theme: light or dark"),
            ("language", "en", "string", "UI language"),
            ("decimal_places", "2", "int", "Currency display decimal places"),
            ("default_marketplace", "custom", "string", "Default marketplace profile"),
        ]
        for key, value, vtype, desc in defaults:
            existing = session.get(AppSettings, key)
            if not existing:
                session.add(AppSettings(key=key, value=value, value_type=vtype, description=desc))

        # Seed empty marketplace profiles if not present
        from ..core.fees import (
            create_empty_amazon_india_profile,
            create_empty_flipkart_profile,
            create_empty_meesho_profile,
        )
        seed_profiles = [
            ("amazon_in_default", create_empty_amazon_india_profile),
            ("flipkart_default", create_empty_flipkart_profile),
            ("meesho_default", create_empty_meesho_profile),
        ]
        for profile_id, factory in seed_profiles:
            existing = session.query(MarketplaceFeeProfile).filter_by(
                profile_id=profile_id
            ).first()
            if not existing:
                p = factory(profile_id)
                rules_data = [
                    {
                        "name": r.name,
                        "fee_type": r.fee_type,
                        "amount": str(r.amount),
                        "min_amount": str(r.min_amount) if r.min_amount else None,
                        "max_amount": str(r.max_amount) if r.max_amount else None,
                        "applies_to": r.applies_to,
                        "condition": r.condition,
                        "is_taxable": r.is_taxable,
                        "fee_gst_rate_pct": str(r.fee_gst_rate_pct),
                        "enabled": r.enabled,
                        "notes": r.notes,
                    }
                    for r in p.fee_rules
                ]
                session.add(MarketplaceFeeProfile(
                    profile_id=p.id,
                    name=p.name,
                    platform=p.platform,
                    is_verified=p.is_verified,
                    source_url=p.source_url,
                    notes=p.notes,
                    fee_rules_json=rules_data,
                ))

        session.commit()


def backup_database(backup_path: str = None) -> str:
    """Create a backup copy of the database."""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path or str(APP_DATA_DIR / f"backup_{timestamp}.db")
    shutil.copy2(str(DB_PATH), backup_file)
    return backup_file


def restore_database(backup_path: str) -> bool:
    """Restore database from a backup file."""
    import shutil
    backup = Path(backup_path)
    if not backup.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    shutil.copy2(str(backup), str(DB_PATH))
    return True
