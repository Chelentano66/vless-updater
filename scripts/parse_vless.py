import requests
import base64
import yaml

SUBSCRIPTION_URL = "https://xeovo.com/proxy/pw/MGEpOQtBnz1iN6SPxCCSUOoUCefQx8Ao/plain/config/"
output_config = "output_config.yaml"

def parse_vless(line):
    from urllib.parse import urlparse, parse_qs
    if not line.startswith("vless://"):
        return None

    uri = line.strip()[8:]
    if '#' in uri:
        uri, tag = uri.split('#', 1)
    else:
        tag = "Unnamed"

    userinfo, rest = uri.split('@', 1)
    uuid = userinfo
    server, params = rest.split('?', 1)
    host, port = server.split(':')

    qs = parse_qs(params)

    return {
        'name': tag,
        'type': 'vless',
        'server': host,
        'port': int(port),
        'uuid': uuid,
        'udp': True,
        'tls': True,
        'sni': qs.get('sni', [host])[0],
        'skip-cert-verify': False,
        'network': qs.get('type', ['ws'])[0],
        'ws-opts': {
            'path': qs.get('path', ['/'])[0],
            'headers': {
                'Host': qs.get('host', [host])[0]
            }
        }
    }

def main():
    print("🔄 Скачиваем подписку...")
    response = requests.get(SUBSCRIPTION_URL)
    data = base64.b64decode(response.text).decode("utf-8")

    lines = data.strip().splitlines()
    proxies = []

    for line in lines:
        line = line.strip()
        if line.startswith("vless://"):
            proxy = parse_vless(line)
            if proxy:
                # ❌ Исключаем Украину
                if ".ua" in proxy['server']:
                    continue
                proxies.append(proxy)
        else:
            print(f"⛔ Пропущен неподдерживаемый протокол: {line[:30]}...")

    config = {
        'proxies': proxies,
        'proxy-groups': [{
            'name': 'MAIN',
            'type': 'url-test',
            'proxies': [p['name'] for p in proxies],
            'url': "http://www.gstatic.com/generate_204",
            'interval': 1200
        }],
        'rules': [
            "MATCH,DIRECT"
        ]
    }

    with open(output_config, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    print(f"✅ Готово: сохранено {len(proxies)} прокси в {output_config}")

if __name__ == "__main__":
    main()
