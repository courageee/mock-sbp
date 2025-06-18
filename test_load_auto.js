import http from 'k6/http';
import { sleep, check } from 'k6';

const mode = __ENV.MODE || 'ramp'; // Выбор режима нагрузки (по умолчанию — ramp)

// Нагрузочные профили
const loadProfiles = {
  ramp: [
    { duration: '15s', target: 50 },
    { duration: '15s', target: 100 },
    { duration: '15s', target: 300 },
    { duration: '15s', target: 400 },
    { duration: '15s', target: 0 },
  ],
  spike: [
    { duration: '5s', target: 0 },
    { duration: '2s', target: 500 },  // Резкий всплеск
    { duration: '10s', target: 500 },
    { duration: '5s', target: 0 },
  ],
  stress: [
    { duration: '10s', target: 200 },
    { duration: '10s', target: 400 },
    { duration: '10s', target: 500 },
    { duration: '10s', target: 450 },
    { duration: '5s', target: 0 },
  ],
  soak: [
    { duration: '1m', target: 300 },  // Долгая стабильная нагрузка
    { duration: '30s', target: 0 },
  ],
  wave: [
    { duration: '5s', target: 100 },
    { duration: '5s', target: 300 },
    { duration: '5s', target: 100 },
    { duration: '5s', target: 400 },
    { duration: '5s', target: 100 },
    { duration: '5s', target: 0 },
  ],
  recurring: [
    { duration: '10s', target: 200 },
    { duration: '10s', target: 0 },
    { duration: '10s', target: 200 },
    { duration: '10s', target: 0 },
    { duration: '10s', target: 200 },
    { duration: '10s', target: 0 },
  ],
};

export const options = {
  stages: loadProfiles[mode] || loadProfiles["ramp"],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% запросов < 2 сек
    http_req_failed: ['rate<0.01'],    // < 1% ошибок
  },
};

// Пользователи
const senders = ["user1", "user3", "user4"];
const receiver = "user2";

export default function () {
  const amount = Math.floor(Math.random() * 15) + 1;
  const from_account = senders[Math.floor(Math.random() * senders.length)];
  const to_account = receiver;
  const isTest = Math.random() < 0.2;
  const testParam = isTest ? '?test=true' : '';

  // 1. Тариф
  let res = http.get(`http://localhost:8000/tariff?amount=${amount}`);
  check(res, { 'tariff status is 200': (r) => r.status === 200 });

  // 2. Перевод
  const payload = JSON.stringify({ from_account, to_account, amount });

  res = http.post(`http://localhost:8000/transfer${testParam}`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(res, {
    'transfer status is 200': (r) => r.status === 200,
    'transfer not empty': (r) => r.body.length > 0,
  });

  if (res.status === 200 && res.json().status === "declined" && !isTest) {
    console.warn(`⛔ DECLINED (REAL): ${res.body}`);
  }

  sleep(0.3);
}
