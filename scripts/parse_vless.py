import requests
import yaml
import ipaddress

URL = "https://xeovo.com/proxy/pw/MGEpOQtBnz1iN6SPxCCSUOoUCefQx8Ao/plain/config/"
OUTPUT_PATH = "output/vless.yaml"

UKR_IP_RANGES = [
    "5.8.0.0/16", "31.28.0.0/16", "31.184.0.0/13", "46.5.0.0/17",
    "46.110.0.0/16", "46.113.0.0/16", "77.111.0.0/16", "78.24.0.0/13",
    "91.200.16.0/20", "91.213.8.0/21", "92.63.0.0/16", "93.184.192.0/18",
    "185.81.24.0/21", "185.125.48.0/20", "188.163.0.0/19", "193.109.0.0/17",
    "194.44.0.0/16", "195.2.0.0/16", "195.211.0.0/16", "217.23.32.0/19",
]

def ip_in_ukraine(ip_str):
    ip = ipaddress.ip_address(ip_str)
    for net in UKR_IP_RANGES:
        if ip in ipaddress.ip_network(net):
            return True
    return False

def main():
    r = requests.get(URL)
    r.raise_for_status()
    data = r.text
    config = yaml.safe_load(data)
    print("DEBUG: Тип config =", type(config))
    print("DEBUG: Содержимое config:\n", config)
    proxies = config.get("proxies", [])
    filtered = []

    for p in proxies:
        if p.get("type") == "vless":
            server = p.get("server")
            try:
                if not ip_in_ukraine(server):
                    filtered.append(p)
            except ValueError:
                filtered.append(p)

    new_config = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "debug",
        "ipv6": False,
        "proxies": filtered,
        "proxy-groups": [
            {
                "name": "MAIN",
                "type": "url-test",
                "proxies": [p["name"] for p in filtered],
                "url": "http://www.gstatic.com/generate_204",
                "interval": 1200,
            }
        ],
        "rules": [
            "DOMAIN-SUFFIX,ua,MAIN",
            "MATCH,DIRECT"
        ]
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(new_config, f, allow_unicode=True)

if __name__ == "__main__":
    main()
