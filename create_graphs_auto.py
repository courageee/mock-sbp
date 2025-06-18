import json
import matplotlib.pyplot as plt
from dateutil.parser import parse as parse_datetime
from collections import Counter, defaultdict
from datetime import datetime
import os
import re
import argparse

# === Аргументы командной строки ===
parser = argparse.ArgumentParser()
parser.add_argument("--mode", type=str, required=False, help="Режим нагрузки: ramp, spike, soak и т.д.")
args = parser.parse_args()
manual_mode = args.mode

# === Получаем количество стадий из test_load.js ===
def get_stage_count_from_js(js_path, mode_override=None):
    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Найдём объект loadProfiles
    match = re.search(r'const\s+loadProfiles\s*=\s*{(.*?)};\s*export', content, re.DOTALL)
    if not match:
        raise ValueError("❌ Не удалось найти объект loadProfiles в test_load.js")
    load_profiles_block = match.group(1)

    # Найдём режим по умолчанию
    mode_match = re.search(r"const\s+mode\s*=\s*__ENV\.MODE\s*\|\|\s*['\"](\w+)['\"]", content)
    if not mode_match:
        raise ValueError("❌ Не удалось определить режим по умолчанию")
    default_mode = mode_match.group(1)

    current_mode = mode_override or default_mode

    # Найдём блок текущего режима
    mode_pattern = rf"{current_mode}\s*:\s*\[((?:.|\n)*?)\]"
    mode_block_match = re.search(mode_pattern, load_profiles_block)
    if not mode_block_match:
        raise ValueError(f"❌ Не найден блок для режима '{current_mode}' в loadProfiles")

    mode_block = mode_block_match.group(1)

    # Подсчёт stage-объектов
    stages = re.findall(r'{\s*duration\s*:\s*["\'].*?["\']\s*,\s*target\s*:\s*\d+\s*}', mode_block)
    print(f"📘 Режим нагрузки: {current_mode}, стадий: {len(stages)}")
    return len(stages)

# === Основной код ===
num_stages = get_stage_count_from_js("test_load.js", manual_mode)

# === Загрузка результатов теста ===
with open("results.json", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip().startswith('{')]

http_data = [
    (
        parse_datetime(entry["data"]["time"]),
        entry["data"]["value"]
    )
    for entry in data
    if entry.get("type") == "Point" and entry.get("metric") == "http_req_duration"
]

if not http_data:
    print("❌ Нет метрик http_req_duration в results.json")
    exit()

# === Разбиение на стадии ===
http_data.sort()
start_time = http_data[0][0]
end_time = http_data[-1][0]
total_duration = (end_time - start_time).total_seconds()

stage_durations = defaultdict(list)
stage_timestamps = defaultdict(list)

for timestamp, value in http_data:
    elapsed = (timestamp - start_time).total_seconds()
    stage_index = min(int(elapsed // (total_duration / num_stages)) + 1, num_stages)
    stage_name = f"stage_{stage_index}"
    stage_durations[stage_name].append(value)
    stage_timestamps[stage_name].append(timestamp)

# Удаляем возможную пустую стадию
stage_durations = {k: v for k, v in stage_durations.items() if v}
stage_timestamps = {k: v for k, v in stage_timestamps.items() if v}

# === Построение графиков ===
os.makedirs("graphs", exist_ok=True)

for stage_name in sorted(stage_durations.keys(), key=lambda x: int(x.split("_")[1])):
    plt.figure(figsize=(10, 4))
    plt.plot(stage_timestamps[stage_name], stage_durations[stage_name])
    plt.xlabel("Время")
    plt.ylabel("Задержка (мс)")
    plt.title(f"Latency: {stage_name}")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"graphs/latency_{stage_name}.png")
    plt.close()

# === main_transactions.json: статус транзакций ===
with open("main_transactions.json", "r", encoding="utf-8") as f:
    transactions = json.load(f)

status_counts = Counter(tx["status"] for tx in transactions)
plt.figure(figsize=(5, 4))
plt.bar(status_counts.keys(), status_counts.values(), color=['green', 'red'])
plt.title("Успешные vs. отклонённые транзакции")
plt.xlabel("Статус")
plt.ylabel("Количество")
plt.tight_layout()
plt.savefig("graphs/status_success_vs_declined.png")
plt.close()

# === График транзакций по секундам ===
tx_per_second = Counter()
for tx in transactions:
    t_sec = int(tx["timestamp"])
    tx_per_second[t_sec] += 1

sorted_times = sorted(tx_per_second.keys())
counts = [tx_per_second[t] for t in sorted_times]
labels = [datetime.fromtimestamp(t).strftime('%H:%M:%S') for t in sorted_times]

plt.figure(figsize=(10, 4))
plt.plot(labels, counts, marker='o')
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
