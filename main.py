from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uuid
import asyncio  # <-- заменили time.sleep на await asyncio.sleep
import logging

app = FastAPI(title="Mock API СБП")

# --- ЛОГИ ---
logging.basicConfig(level=logging.INFO)

# --- МОДЕЛИ ---
class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float

# --- ХРАНИЛИЩА ---
accounts = {
    "user1": 500000.0,
    "user2": 100000.0,
    "user3": 500000.0,
    "user4": 500000.0
}
transactions = []

# --- ROOT ---
@app.get("/")
async def root():
    return {"message": "Добро пожаловать в mock API СБП!"}

# --- ТАРИФАЦИЯ ---
@app.get("/tariff")
async def get_tariff(amount: float = Query(..., gt=0)):
    await asyncio.sleep(0.5)  # <-- асинхронная задержка
    if amount <= 1000:
        fee = 10
    elif amount <= 5000:
        fee = 30
    else:
        fee = 50
    return {"amount": amount, "fee": fee}

# --- ПРОВЕДЕНИЕ ПЕРЕВОДА ---
@app.post("/transfer")
async def transfer(req: TransferRequest, test: bool = Query(False)):
    logging.info(f"⏳ Запрос перевода: {req.from_account} → {req.to_account} | {req.amount}₽")

    # Тестовый режим: задержка и отказ
    if test:
        await asyncio.sleep(2)  # <-- асинхронная задержка
        failed_tx = {
            "id": str(uuid.uuid4()),
            "from": req.from_account,
            "to": req.to_account,
            "amount": req.amount,
            "status": "declined",
            "reason": "Тестовый отказ",
            "timestamp": asyncio.get_event_loop().time()
        }
        transactions.append(failed_tx)
        logging.warning(f"⚠️ Отказ (тест): {failed_tx}")
        return failed_tx

    # Проверка баланса
    sender_balance = accounts.get(req.from_account, 0)
    if sender_balance < req.amount:
        failed_tx = {
            "id": str(uuid.uuid4()),
            "from": req.from_account,
            "to": req.to_account,
            "amount": req.amount,
            "status": "declined",
            "reason": "Недостаточно средств",
            "timestamp": asyncio.get_event_loop().time()
        }
        transactions.append(failed_tx)
        logging.warning(f"❌ Отказ: {failed_tx}")
        return failed_tx

    # Проведение перевода
    accounts[req.from_account] -= req.amount
    accounts[req.to_account] = accounts.get(req.to_account, 0) + req.amount

    success_tx = {
        "id": str(uuid.uuid4()),
        "from": req.from_account,
        "to": req.to_account,
        "amount": req.amount,
        "status": "success",
        "timestamp": asyncio.get_event_loop().time()
    }
    transactions.append(success_tx)
    logging.info(f"✅ Успех: {success_tx}")
    return success_tx

# --- ПОЛУЧЕНИЕ БАЛАНСА ---
@app.get("/balance/{account_id}")
async def get_balance(account_id: str):
    balance = accounts.get(account_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    return {"account": account_id, "balance": balance}

# --- ИСТОРИЯ ТРАНЗАКЦИЙ ---
@app.get("/transactions")
async def get_transactions():
    return transactions

# --- СТАТИСТИКА ---
@app.get("/stats")
async def stats():
    total = len(transactions)
    declined = sum(1 for tx in transactions if tx["status"] == "declined")
    success_sum = sum(tx["amount"] for tx in transactions if tx["status"] == "success")
    return {
        "total_transactions": total,
        "declined": declined,
        "successful_amount": success_sum
    }
