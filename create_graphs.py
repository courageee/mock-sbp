import json
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter

# Загрузка файла
with open("results.json", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip().startswith('{')]

# 1. График распределения задержек (http_req_duration) по времени
durations = []
timestamps = []

for entry in data:
    if (
        entry.get("type") == "Point" and
        entry.get("metric") == "http_req_duration"
    ):
        time_str = entry["data"]["time"]
        timestamp = datetime.fromisoformat(time_str)
        value = entry["data"]["value"]
        timestamps.append(timestamp)
        durations.append(value)

plt.figure(figsize=(10, 4))
plt.plot(timestamps, durations, label="http_req_duration (ms)", color='blue')
plt.xlabel("Время")
plt.ylabel("Задержка (мс)")
plt.title("График 1: Распределение задержек http_req_duration по времени")
plt.grid(True)
plt.tight_layout()
plt.savefig("graph1_latency_over_time.png")
plt.close()

# 2. Гистограмма отклонённых vs. успешных транзакций
with open("main_transactions.json", "r", encoding="utf-8") as f:
    transactions = json.load(f)

status_counts = Counter(tx["status"] for tx in transactions)

plt.figure(figsize=(5, 4))
plt.bar(status_counts.keys(), status_counts.values(), color=['green', 'red'])
plt.title("График 2: Успешные vs. отклонённые транзакции")
plt.xlabel("Статус")
plt.ylabel("Количество")
plt.tight_layout()
plt.savefig("graph2_success_vs_declined.png")
plt.close()

# 3. Линейный график количества транзакций по секундам
tx_per_second = Counter()

for tx in transactions:
    t_sec = int(tx["timestamp"])
    tx_per_second[t_sec] += 1

# Сортируем по времени
sorted_times = sorted(tx_per_second.keys())
counts = [tx_per_second[t] for t in sorted_times]
labels = [datetime.fromtimestamp(t).strftime('%H:%M:%S') for t in sorted_times]

plt.figure(figsize=(10, 4))
plt.plot(labels, counts, marker='o')
plt.xticks(rotation=45)
plt.title("График 3: Количество транзакций по времени (сек)")
plt.xlabel("Время (сек)")
plt.ylabel("Число транзакций")
plt.tight_layout()
plt.grid(True)
plt.savefig("graph3_tx_per_second.png")
plt.close()

print("✅ Все графики сохранены: graph1_latency_over_time.png, graph2_success_vs_declined.png, graph3_tx_per_second.png")
