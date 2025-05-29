import requests
import yaml
import re
import os
from urllib.parse import urlparse, parse_qs
from base64 import urlsafe_b64decode

SUBSCRIPTION_URL = "https://xeovo.com/proxy/pw/MGEpOQtBnz1iN6SPxCCSUOoUCefQx8Ao/plain/config/"
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.yaml")
OUTPUT_PATH = "config.yaml"

def parse_vless_url(url):
    try:
        parsed = urlparse(url)
        uuid = parsed.username
        server = parsed.hostname
        port = int(parsed.port)
        path = parsed.path
        query = parse_qs(parsed.query)
        name = parsed.fragment or server

        return {
            "name": name,
            "type": "vless",
            "server": server,
            "port": port,
            "uuid": uuid,
            "network": query.get("type", ["ws"])[0],
            "tls": True,
            "udp": True,
            "client-fingerprint": "chrome",
            "ws-opts": {
                "path": path,
                "headers": {
                    "Host": query.get("host", [server])[0]
                }
            }
        }
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {url} -> {e}")
        return None

def main():
    print("🔄 Скачиваем подписку...")
    response = requests.get(SUBSCRIPTION_URL)
    response.raise_for_status()
    text = response.text

    print("🔍 Фильтруем VLESS ссылки...")
    vless_urls = [line.strip() for line in text.splitlines() if line.startswith("vless://")]
    proxies = list(filter(None, [parse_vless_url(url) for url in vless_urls]))

    print(f"✅ Найдено VLESS прокси: {len(proxies)}")

    print("📄 Загружаем шаблон...")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print("🧩 Вставляем прокси в шаблон...")
    config["proxies"] = proxies
    for group in config.get("proxy-groups", []):
        if group.get("name") == "MAIN":
            group["proxies"] = [p["name"] for p in proxies]

    print("💾 Сохраняем в config.yaml...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    print("🎉 Готово! Конфиг сохранён.")

if __name__ == "__main__":
    main()
