import requests
import yaml
import re
import os
from urllib.parse import urlparse, parse_qs
from base64 import urlsafe_b64decode

SUBSCRIPTION_URL = "https://xeovo.com/proxy/pw/MGEpOQtBnz1iN6SPxCCSUOoUCefQx8Ao/plain/config/"
TEMPLATE_PATH = "template.yaml"
OUTPUT_PATH = "config.yaml"

def parse_vless_url(url):
    """Парсит vless:// ссылку и возвращает Clash-совместимый словарь."""
    try:
        raw = url[8:]  # Убираем 'vless://'
        userinfo, rest = raw.split('@', 1)
        uuid = userinfo
        host, params = rest.split('?', 1) if '?' in rest else (rest, '')
        address, port = host.split(':')
        query = parse_qs(params)

        name = query.get('sni', [address])[0]  # или ps, или просто host
        return {
            "name": name,
            "type": "vless",
            "server": address,
            "port": int(port),
            "uuid": uuid,
            "network": query.get("type", ["ws"])[0],
            "tls": True,
            "udp": True,
            "client-fingerprint": "chrome"
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
