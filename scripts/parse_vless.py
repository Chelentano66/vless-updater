import base64
import requests
import yaml
from urllib.parse import urlparse, parse_qs, unquote

SUBSCRIPTION_URL = "https://xeovo.com/proxy/pw/MGEpOQtBnz1iN6SPxCCSUOoUCefQx8Ao/plain/config/"
TEMPLATE_PATH = "scripts/template.yaml"
OUTPUT_PATH = "output/vless.yaml"

def parse_vless_link(link):
    # Пример vless://uuid@host:port/path?query#name
    # Парсим вручную
    # Уберём префикс
    link = link[len("vless://"):]
    
    # Разобьём на основную часть и #name
    if "#" in link:
        main_part, name = link.split("#", 1)
        name = unquote(name)
    else:
        main_part = link
        name = ""
    
    # Разделим на userinfo и query
    if "?" in main_part:
        userinfo_hostport, query_str = main_part.split("?", 1)
        query = parse_qs(query_str)
    else:
        userinfo_hostport = main_part
        query = {}
    
    # userinfo_hostport: uuid@host:port/path
    # Разобьём на uuid и host:port/path
    if "@" in userinfo_hostport:
        uuid, host_port_path = userinfo_hostport.split("@", 1)
    else:
        raise ValueError("No UUID found in link")
    
    # Теперь host_port_path: host:port/path
    # Нам нужно отделить host, port и path
    # Разобьём сначала по "/"
    if "/" in host_port_path:
        host_port, path = host_port_path.split("/", 1)
        path = "/" + path
    else:
        host_port = host_port_path
        path = ""
    
    # Разделим host и port
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        # иногда тут может быть порт с лишним "/path" - лучше сразу int, если ошибка - кидаем
        try:
            port = int(port_str)
        except ValueError:
            # Если порт не число - ошибка
            raise ValueError(f"Invalid port: {port_str}")
    else:
        host = host_port
        port = 443  # дефолтный порт
    
    # Параметры из query
    # Пример: type=ws, encryption=none, security=tls, sni=host, host=host, path=/potosi
    type_ = query.get("type", [""])[0]
    encryption = query.get("encryption", [""])[0]
    security = query.get("security", [""])[0]
    sni = query.get("sni", [""])[0]
    host_header = query.get("host", [""])[0]
    path_query = query.get("path", [""])[0]
    
    return {
        "name": name or f"{host}:{port}",
        "type": "vless",
        "server": host,
        "port": port,
        "uuid": uuid,
        "encryption": encryption,
        "security": security,
        "network": type_,
        "sni": sni,
        "host": host_header,
        "path": path_query,
    }

def main():
    print("🔄 Скачиваем подписку...")
    response = requests.get(SUBSCRIPTION_URL)
    response.raise_for_status()

    # Подписка в base64, декодируем
    decoded = base64.b64decode(response.text).decode("utf-8")

    # Разбиваем на строки (ссылки)
    links = decoded.strip().splitlines()

    print("🔍 Фильтруем VLESS ссылки...")
    vless_links = [l for l in links if l.startswith("vless://")]

    print(f"✅ Найдено VLESS прокси: {len(vless_links)}")

    proxies = []
    for link in vless_links:
        try:
            proxy = parse_vless_link(link)
            proxies.append(proxy)
        except Exception as e:
            print(f"❌ Ошибка при парсинге: {link} -> {e}")

    print("📄 Загружаем шаблон...")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = yaml.safe_load(f)

    # Вставляем proxies в конфиг
    template["proxies"] = proxies

    # В proxy-groups ищем группу MAIN и вставляем туда имена прокси
    proxy_names = [p["name"] for p in proxies]

    if "proxy-groups" in template:
        for group in template["proxy-groups"]:
            if group.get("name") == "MAIN":
                group["proxies"] = proxy_names

    print(f"💾 Сохраняем результат в {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(template, f, allow_unicode=True)

    print("✅ Готово!")

if __name__ == "__main__":
    main()
