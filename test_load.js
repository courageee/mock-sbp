import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
    vus: 20, // virtual users
    duration: '25s', // how long the test runs
};

export default function () {
    const amount = Math.floor(Math.random() * 10000) + 1;

    // Тестирование тарификации
    let res = http.get(`http://localhost:8000/tariff?amount=${amount}`);
    check(res, {
        'status is 200': (r) => r.status === 200,
    });

    // Тестирование перевода
    const payload = JSON.stringify({
        from_account: "user1",
        to_account: "user2",
        amount: amount
    });

    res = http.post('http://localhost:8000/transfer', payload, {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'transfer status is 200': (r) => r.status === 200,
    });

    sleep(0.5); // пауза между запросами
}
