import requests
import yaml
import os
from urllib.parse import parse_qs, unquote

# 🔧 Настройки
TEMPLATE_PATH = "scripts/template.yaml"
OUTPUT_DIR = "output"

# 📦 Список подписок: имя → URL
subscriptions = {
    "Sub1": "https://xeovo.com/proxy/pw/MGкаOQtBnz1iN6SPxCCSUOoUCefQx8Ao/plain/config/",
    "Sub2": "https://xeovo.com/proxy/pw/PjYJкаXGS1adWJJJ9tbL3V24eonExf/plain/config/",
    "Sub2": "https://xeovo.com/proxy/pw/PjYJкаXGS1adWJJJ9tbL3V24eonExf/plain/config/",
    # Добавляй сколько нужно...
}


def parse_vless(url, used_names):
    if not url.startswith("vless://"):
        return None

    url_ = url[len("vless://"):]

    try:
        user_uuid, rest = url_.split("@", 1)
    except ValueError:
        return None

    if "#" in rest:
        rest, remark = rest.split("#", 1)
    else:
        remark = ""

    if "?" in rest:
        hostport_path, query_string = rest.split("?", 1)
    else:
        hostport_path = rest
        query_string = ""

    if ":" not in hostport_path:
        return None
    host, port_path = hostport_path.split(":", 1)

    port = ""
    path = "/"
    for i, ch in enumerate(port_path):
        if ch.isdigit():
            port += ch
        else:
            path = port_path[i:]
            break
    else:
        path = "/"

    if port == "":
        return None
    port = int(port)

    query = parse_qs(query_string)

    # Уникальное имя прокси
    base_name = remark or f"{host}:{port}"
    base_name = unquote(base_name)
    name = base_name
    suffix = 1
    while name in used_names:
        suffix += 1
        name = f"{base_name}-{suffix}"
    used_names.add(name)

    proxy = {
        "name": name,
        "type": "vless",
        "server": host,
        "port": port,
        "uuid": user_uuid,
        "tls": query.get("security", ["tls"])[0] == "tls",
        "network": query.get("type", ["tcp"])[0],
        "udp": True,
    }

    if proxy["network"] == "ws":
        ws_path = query.get("path", [path])[0]
        ws_path = unquote(ws_path)
        ws_host = query.get("host", [""])[0]
        proxy["ws-opts"] = {
            "path": ws_path,
        }
        if ws_host:
            proxy["ws-opts"]["headers"] = {"Host": ws_host}

    return proxy


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for name, url in subscriptions.items():
        print(f"\n🔄 Обработка подписки: {name}")
        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Ошибка при скачивании подписки '{name}': {e}")
            continue

        decoded = response.text
        used_names = set()
        proxies = []

        for line in decoded.splitlines():
            line = line.strip()
            if line.startswith("vless://"):
                proxy = parse_vless(line, used_names)
                if proxy:
                    proxies.append(proxy)

        print(f"✅ Найдено VLESS-прокси: {len(proxies)}")

        try:
            with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
                template = yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки шаблона: {e}")
            continue

        template["proxies"] = proxies
        proxy_names = [p["name"] for p in proxies]
        for group in template.get("proxy-groups", []):
            if group.get("name") == "MAIN":
                group["proxies"] = proxy_names

        output_file = f"{OUTPUT_DIR}/{name}.yaml"
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(template, f, allow_unicode=True, sort_keys=False)

        print(f"💾 Сохранено: {output_file}")


if __name__ == "__main__":
    main()
