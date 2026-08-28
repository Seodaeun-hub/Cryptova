from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TradingRun(Base):
    __tablename__ = "trading_runs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(50), default="BTCUSDT", nullable=False)

    action = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)

    signal_id = Column(Integer, ForeignKey("ai_signals.id"), nullable=True, index=True)
    signal = Column(String(20), nullable=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    order_status = Column(String(50), nullable=True)

    position_id = Column(Integer, ForeignKey("trading_positions.id"), nullable=True, index=True)
    position_status = Column(String(50), nullable=True)

    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)

    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
