import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
//    { duration: '20s', target: 50 },   // разогрев
//    { duration: '20s', target: 200 },  // рост
//    { duration: '20s', target: 500 },  // пик ближе
//    { duration: '30s', target: 510 },  // основной пик
//    { duration: '20s', target: 0 },    // спад

    { duration: '2s', target: 0 }, // spike-test
    { duration: '1s', target: 500 },
    { duration: '20s', target: 500 },
    { duration: '2s', target: 0 },

//    { duration: '1m', target: 100 }, // stress test
//    { duration: '1m', target: 200 },
//    { duration: '1m', target: 300 },
//    { duration: '1m', target: 400 },
//    { duration: '2m', target: 500 },
//    { duration: '1m', target: 0 },
//
//    { duration: '10m', target: 100 }, // soak test
//
//    { duration: '15s', target: 100 }, // wave test
//    { duration: '15s', target: 300 },
//    { duration: '15s', target: 100 },
//    { duration: '15s', target: 500 },
//    { duration: '15s', target: 100 },
//
//    { duration: '30s', target: 100 }, // recurring pattern
//    { duration: '30s', target: 0 },
//    { duration: '30s', target: 200 },
//    { duration: '30s', target: 0 },
//    { duration: '30s', target: 400 },
//    { duration: '30s', target: 0 },

  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% запросов быстрее 2 сек
    http_req_failed: ['rate<0.01'],    // не более 1% ошибок
  },
};

// Тестовые пользователи
const senders = ["user1", "user3", "user4"];
const receiver = "user2";

export default function () {
  const amount = Math.floor(Math.random() * 15) + 1;
  const from_account = senders[Math.floor(Math.random() * senders.length)];
  const to_account = receiver;

  // Определяем тип запроса (20% — тестовые)
  const isTest = Math.random() < 0.2;
  const testParam = isTest ? '?test=true' : '';

  // --- 1. Получение тарифа ---
  const tariffRes = http.get(`http://localhost:8000/tariff?amount=${amount}`);
  check(tariffRes, {
    'tariff status is 200': (r) => r.status === 200,
  });

  // --- 2. Перевод ---
  const payload = JSON.stringify({
    from_account,
    to_account,
    amount,
  });

  const transferRes = http.post(`http://localhost:8000/transfer${testParam}`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(transferRes, {
    'transfer status is 200': (r) => r.status === 200,
    'transfer not empty': (r) => r.body && r.body.length > 0,
  });

  // Логирование только **реальных отказов**
  if (
    transferRes.status === 200 &&
    transferRes.json().status === "declined" &&
    !isTest
  ) {
    console.warn(`⛔ DECLINED (REAL): ${transferRes.body}`);
  }

  sleep(0.3); // Пауза между итерациями
}
