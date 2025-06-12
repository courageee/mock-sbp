import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
    vus: 100, // количество виртуальных пользователей
    duration: '20s', // длительность теста
};

// Массив отправителей с балансом (подразумевается, что в бэке есть эти аккаунты)
const senders = ["user1", "user3", "user4"];
const receiver = "user2";

export default function () {
    const amount = Math.floor(Math.random() * 1500) + 1;

    // Выбираем случайного отправителя
    const from_account = senders[Math.floor(Math.random() * senders.length)];
    const to_account = receiver;

    // 20% запросов в тестовом режиме (с отказом)
    const isTest = Math.random() < 0.2;
    const testParam = isTest ? '?test=true' : '';

    // 1. Тест тарификации
    let res = http.get(`http://localhost:8000/tariff?amount=${amount}`);
    check(res, {
        'tariff status is 200': (r) => r.status === 200,
    });

    // 2. Тест перевода
    const payload = JSON.stringify({
        from_account,
        to_account,
        amount,
    });

    res = http.post(`http://localhost:8000/transfer${testParam}`, payload, {
        headers: { 'Content-Type': 'application/json' },
    });

    check(res, {
        'transfer status is 200': (r) => r.status === 200,
    });

    if (res.status === 200 && res.json().status === "declined") {
        console.warn(`⛔ DECLINED: ${res.body}`);
    }

    // 3. (Опционально) Проверка баланса отправителя
    // let balanceRes = http.get(`http://localhost:8000/balance/${from_account}`);
    // check(balanceRes, { 'balance status is 200': (r) => r.status === 200 });

    sleep(0.5);
}
