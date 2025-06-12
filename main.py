from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import random
import time
import uuid

app = FastAPI(title="Mock SBP API")

# Модель запроса для перевода
class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float
    purpose: Optional[str] = None

@app.get("/")
async def index():
    return {"message": "Добро пожаловать в mock API СБП!"}

# 📥 Тарификация
@app.get("/tariff")
async def get_tariff(amount: float = 0):
    # Имитируем задержку ответа
    time.sleep(random.uniform(0.1, 0.2))

    if amount < 1000:
        tariff = 0
    elif amount < 10000:
        tariff = amount * 0.005
    else:
        tariff = amount * 0.01

    return {
        "amount": amount,
        "tariff": round(tariff, 2),
        "currency": "RUB"
    }

# 💸 Проведение перевода
@app.post("/transfer")
async def transfer_funds(req: TransferRequest):
    # Имитируем задержку и обработку
    time.sleep(random.uniform(0.1, 0.3))

    # 10% шанс отказа
    if random.random() < 0.1:
        return {
            "status": "declined",
            "reason": "Недостаточно средств",
            "code": "DECLINE_FUNDS"
        }

    transaction_id = str(uuid.uuid4())
    return {
        "status": "success",
        "transaction_id": transaction_id,
        "from": req.from_account,
        "to": req.to_account,
        "amount": req.amount,
        "currency": "RUB"
    }

# 📊 Получение баланса
@app.get("/balance/{account_id}")
async def get_balance(account_id: str):
    balance = round(random.uniform(1000, 100000), 2)
    return {
        "account_id": account_id,
        "balance": balance,
        "currency": "RUB"
    }
