import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

from app.models.user import User
from app.models.strategy_setting import StrategySetting
from app.models.ai_signal import AISignal
from app.models.backtest_result import BacktestResult
from app.models.api_key import ApiKey
from app.models.order import Order
from app.models.trading_position import TradingPosition
from app.models.trading_run import TradingRun

from app.routers import auth, strategy, signals, backtest, exchange, orders, positions, trading, market
from app.services.trading_scheduler import start_scheduler, shutdown_scheduler


Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="Cryptova Backend API",
    description="Backend server for Cryptova AI crypto trading assistant",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(strategy.router)
app.include_router(signals.router)
app.include_router(backtest.router)
app.include_router(exchange.router)
app.include_router(orders.router)
app.include_router(positions.router)
app.include_router(trading.router)
app.include_router(market.router)

@app.get("/")
def root():
    return {"message": "Cryptova Backend API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
