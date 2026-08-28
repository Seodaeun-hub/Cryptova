from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class TradingPosition(Base):
    __tablename__ = "trading_positions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    signal_id = Column(Integer, ForeignKey("ai_signals.id"), nullable=True, index=True)
    entry_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    exchange = Column(String(50), default="bybit", nullable=False)
    symbol = Column(String(50), default="BTCUSDT", nullable=False)

    side = Column(String(20), nullable=False)
    qty = Column(Float, default=0.0, nullable=False)

    entry_price = Column(Float, default=0.0, nullable=False)
    exit_price = Column(Float, nullable=True)

    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    result = Column(String(30), nullable=True)

    status = Column(String(30), default="OPEN", nullable=False)
    holding_strategy = Column(String(50), default="24h Fixed", nullable=False)

    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    hold_until = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    is_dry_run = Column(Boolean, default=True, nullable=False)

    user = relationship("User")
    signal_obj = relationship("AISignal")
    entry_order = relationship("Order")
