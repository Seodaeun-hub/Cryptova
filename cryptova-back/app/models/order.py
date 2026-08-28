from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    signal_id = Column(Integer, ForeignKey("ai_signals.id"), nullable=True, index=True)

    exchange = Column(String(50), default="bybit", nullable=False)
    symbol = Column(String(50), default="BTCUSDT", nullable=False)

    signal = Column(String(20), nullable=False)
    side = Column(String(20), nullable=True)

    order_type = Column(String(30), default="Market", nullable=False)
    qty = Column(Float, default=0.0, nullable=False)

    entry_price = Column(Float, default=0.0, nullable=False)
    status = Column(String(30), default="PENDING", nullable=False)

    bybit_order_id = Column(String(100), nullable=True)

    message = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    signal_obj = relationship("AISignal")
