import yaml

TEMPLATE_PATH = "scripts/template.yaml"
OUTPUT_PATH = "config.yaml"

# 🔹 Здесь предполагаем, что у тебя уже есть список прокси:
# Пример прокси-объекта:
proxies = [
    {
        "name": "US-VLESS",
        "type": "vless",
        "server": "us.example.com",
        "port": 443,
        "uuid": "your-uuid-here",
        "tls": True,
        "network": "ws",
        "ws-opts": {
            "path": "/websocket",
            "headers": {
                "Host": "us.example.com"
            }
        }
    },
    {
        "name": "DE-VLESS",
        "type": "vless",
        "server": "de.example.com",
        "port": 443,
        "uuid": "your-uuid-here",
        "tls": True,
        "network": "ws",
        "ws-opts": {
            "path": "/path",
            "headers": {
                "Host": "de.example.com"
            }
        }
    }
    # ... и т.д.
]

# 🔸 Загружаем шаблон
with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    template = yaml.safe_load(f)

# 🔸 Вставляем список прокси
template["proxies"] = proxies

# 🔸 Вставляем только имена в MAIN proxy-group
for group in template.get("proxy-groups", []):
    if group.get("name") == "MAIN":
        group["proxies"] = [proxy["name"] for proxy in proxies]
        break

# 🔸 Сохраняем готовый конфиг
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    yaml.dump(template, f, allow_unicode=True, sort_keys=False)
