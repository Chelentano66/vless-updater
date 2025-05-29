import requests
import yaml
from urllib.parse import urlparse, parse_qs, unquote

# Пути к файлам
SUBSCRIPTION_URL = "https://xeovo.com/proxy/pw/MGEpOQtBnz1iN6SPxCCSUOoUCefQx8Ao/plain/config/"
TEMPLATE_PATH = "scripts/template.yaml"
OUTPUT_PATH = "config.yaml"

def parse_vless(url):
    # Пример vless ссылки:
    # vless://UUID@host:port/path?query#remark
    # Пример: vless://913d91d6-245e-44c1-bd10-fe378302eefc@uk-global2.xeovo.net:443/potosi?type=ws&encryption=none&security=tls&sni=uk-global2.xeovo.net&host=uk-global2.xeovo.net&path=%2Fpotosi#UK / VLESS (WS+TLS, for Xray)

    if not url.startswith("vless://"):
        return None

    # Уберём префикс для парсинга
    url_ = url[len("vless://"):]

    # Разобьём на UUID и остальное по "@"
    try:
        user_uuid, rest = url_.split("@", 1)
    except ValueError:
        return None

    # Теперь надо аккуратно разобрать host:port/path?query#fragment
    # У urlparse порт и path идут вместе, но в нашем случае порт может содержать "/path" сразу,
    # поэтому парсим вручную:
    # Разобьём rest на hostport и query+fragment
    # Сначала отделим #remark
    if "#" in rest:
        rest, remark = rest.split("#", 1)
    else:
        remark = ""

    # Отделим query
    if "?" in rest:
        hostport_path, query_string = rest.split("?", 1)
    else:
        hostport_path = rest
        query_string = ""

    # Теперь из hostport_path выделим host, port, path
    # hostport_path = "uk-global2.xeovo.net:443/potosi"
    # разделим по ":" (первое вхождение)
    if ":" not in hostport_path:
        return None
    host, port_path = hostport_path.split(":", 1)

    # port_path = "443/potosi"
    # отделим порт (числа) от пути
    port = ""
    path = "/"
    for i, ch in enumerate(port_path):
        if ch.isdigit():
            port += ch
        else:
            path = port_path[i:]
            break
    else:
        # весь port_path — порт
        path = "/"

    if port == "":
        return None
    port = int(port)

    # Распарсим query параметры
    query = parse_qs(query_string)

    # Вытаскиваем нужные параметры (например, type, encryption, security и др.)
    # Пример заполнения словаря:
    proxy = {
        "name": remark or f"{host}:{port}",
        "type": "vless",
        "server": host,
        "port": port,
        "uuid": user_uuid,
        "alterId": 0,
        "encryption": query.get("encryption", ["none"])[0],
        "network": query.get("type", ["tcp"])[0],
        "security": query.get("security", ["none"])[0],
    }

    # Если network == ws, добавляем wsSettings
    if proxy["network"] == "ws":
        ws_path = query.get("path", [path])[0]
        # unquote для корректного декодирования
        ws_path = unquote(ws_path)
        ws_host = query.get("host", [""])[0]
        proxy["ws-opts"] = {
            "path": ws_path,
        }
        if ws_host:
            proxy["ws-opts"]["headers"] = {"Host": ws_host}

    return proxy


def main():
    print("🔄 Скачиваем подписку...")
    response = requests.get(SUBSCRIPTION_URL)
    response.raise_for_status()
    decoded = response.text  # plain текст

    print("🔍 Фильтруем VLESS ссылки...")
    lines = decoded.splitlines()
    proxies = []
    for line in lines:
        line = line.strip()
        if line.startswith("vless://"):
            proxy = parse_vless(line)
            if proxy:
                proxies.append(proxy)

    print(f"✅ Найдено VLESS прокси: {len(proxies)}")

    print("📄 Загружаем шаблон...")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = yaml.safe_load(f)

    # Вставляем proxies в шаблон
    template["proxies"] = proxies

    # Вставляем имена прокси в proxy-groups -> MAIN -> proxies
    proxy_names = [p["name"] for p in proxies]
    for group in template.get("proxy-groups", []):
        if group.get("name") == "MAIN":
            group["proxies"] = proxy_names

    print("💾 Сохраняем конфиг в", OUTPUT_PATH)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(template, f, allow_unicode=True, sort_keys=False)

    print("✅ Готово!")

if __name__ == "__main__":
    main()
