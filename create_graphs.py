import json
import matplotlib.pyplot as plt
from dateutil.parser import parse as parse_datetime
from collections import Counter, defaultdict
from datetime import datetime
import os

# Временные границы для каждого этапа нагрузки (в секундах от начала)
stage_boundaries = {
    "stage_1_50vus": (0, 20), # ramp-test
    "stage_2_200vus": (20, 40),
    "stage_3_500vus": (40, 60),
    "stage_4_510vus": (60, 90),
    "stage_5_cooldown": (90, 110),

    # "stage_1_0vus": (0, 2), # spike-test
    # "stage_2_500vus": (2, 3),
    # "stage_3_500vus": (3, 13),
    # "stage_4_0vus": (13, 15),

    # "stage_1_100vus": (0, 60), # stress test
    # "stage_2_200vus": (60, 120),
    # "stage_3_300vus": (120, 180),
    # "stage_4_400vus": (180, 240),
    # "stage_5_500vus": (240, 360),
    # "stage_6_0vus": (360, 420),

    # "stage_1_100vus": (0, 300), # soak test

    # "stage_1_100vus": (0, 15), # wave test
    # "stage_2_300vus": (15, 30),
    # "stage_3_100vus": (30, 45),
    # "stage_4_500vus": (45, 60),
    # "stage_5_100vus": (60, 75),

    # "stage_1_100vus": (0, 30), # recurring pattern
    # "stage_2_0vus": (30, 60),
    # "stage_3_200vus": (60, 90),
    # "stage_4_0vus": (90, 120),
    # "stage_5_400vus": (120, 150),
    # "stage_7_0vus": (150, 180),
}

# Загрузка http_req_duration
with open("results.json", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip().startswith('{')]

# Распределим по этапам
stage_durations = defaultdict(list)
stage_timestamps = defaultdict(list)

# Время начала теста
test_start_time = None

for entry in data:
    if entry.get("type") == "Point" and entry.get("metric") == "http_req_duration":
        time_str = entry["data"]["time"]
        timestamp = parse_datetime(time_str)

        # Зафиксируем начальное время
        if test_start_time is None:
            test_start_time = timestamp

        # Секунда от начала теста
        elapsed_seconds = (timestamp - test_start_time).total_seconds()


        value = entry["data"]["value"]

        for stage_name, (start, end) in stage_boundaries.items():
            if start <= elapsed_seconds < end:
                stage_durations[stage_name].append(value)
                stage_timestamps[stage_name].append(timestamp)
                break

# Рисуем графики задержек по этапам
os.makedirs("graphs", exist_ok=True)

for stage_name in stage_durations:
    plt.figure(figsize=(10, 4))
    plt.plot(stage_timestamps[stage_name], stage_durations[stage_name], label=stage_name)
    plt.xlabel("Время")
    plt.ylabel("Задержка (мс)")
    plt.title(f"Задержки http_req_duration: {stage_name}")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"graphs/latency_{stage_name}.png")
    plt.close()

# Загрузка транзакций
with open("main_transactions.json", "r", encoding="utf-8") as f:
    transactions = json.load(f)

# Гистограмма статусов
status_counts = Counter(tx["status"] for tx in transactions)

plt.figure(figsize=(5, 4))
plt.bar(status_counts.keys(), status_counts.values(), color=['green', 'red'])
plt.title("Успешные vs. отклонённые транзакции")
plt.xlabel("Статус")
plt.ylabel("Количество")
plt.tight_layout()
plt.savefig("graphs/status_success_vs_declined.png")
plt.close()

# Транзакции по секундам
tx_per_second = Counter()

for tx in transactions:
    t_sec = int(tx["timestamp"])
    tx_per_second[t_sec] += 1

sorted_times = sorted(tx_per_second.keys())
counts = [tx_per_second[t] for t in sorted_times]
labels = [datetime.fromtimestamp(t).strftime('%H:%M:%S') for t in sorted_times]

plt.figure(figsize=(10, 4))
plt.plot(labels, counts, marker='o')

# Ограничим количество X-меток до 10
step = max(1, len(labels) // 10)
plt.xticks(labels[::step], rotation=45)

plt.title("Число транзакций по секундам")
plt.xlabel("Время")
plt.ylabel("Количество транзакций")
plt.tight_layout()
plt.grid(True)
plt.savefig("graphs/tx_count_over_time.png")
plt.close()

print("✅ Графики созданы в папке ./graphs/")
