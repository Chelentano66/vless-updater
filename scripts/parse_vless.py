import requests
import re
import yaml

SUBSCRIPTION_URL = "https://xeovo.com/proxy/pw/MGEpOQtBnz1iN6SPxCCSUOoUCefQx8Ao/plain/config/"

def parse_links(text):
    # Регулярка для всех прокси ссылок
    pattern = re.compile(r'^(vmess|vless|trojan|ss)://[^\s]+', re.MULTILINE)
    return pattern.findall(text)

def filter_vless(text):
    # Возвращаем только VLESS ссылки из текста
    return re.findall(r'^vless://[^\s]+', text, re.MULTILINE)

def main():
    print("🔄 Скачиваем подписку...")
    response = requests.get(SUBSCRIPTION_URL)
    response.raise_for_status()
    text = response.text

    vless_links = filter_vless(text)
    print(f"Найдено VLESS ссылок: {len(vless_links)}")

    # Далее преобразуем VLESS ссылки в нужный формат конфига (пример упрощённый)
    proxies = []
    for link in vless_links:
        # Разбор и преобразование ссылки (зависит от формата)
        # Например, просто кладём в конфиг имя и адрес сервера
        # Здесь нужно реализовать парсинг параметров ссылки
        proxies.append({
            "name": "VLESS Proxy",
            "type": "vless",
            "server": "example.com",  # тут нужно брать из ссылки
            "port": 443,
            "uuid": "uuid-from-link",
            "tls": True,
            "network": "ws",
            "ws-opts": {
                "path": "/",
                "headers": {
                    "Host": "example.com"
                }
            }
        })

    config = {
        "mixed-port": 7890,
        "proxies": proxies,
        # остальной конфиг...
    }

    with open("config.yaml", "w") as f:
        yaml.dump(config, f)

    print("Готово! Конфиг записан в config.yaml")

if __name__ == "__main__":
    main()
