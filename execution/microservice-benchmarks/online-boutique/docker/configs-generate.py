import json
import yaml
import sys


USAGE = f"""
Usage: {sys.argv[0]} <ip-vm1> <ip-vm2> <ip-vm3>

Args:
    ip-vm1: vm1's IP address
    ip-vm2: vm2's IP address
    ip-vm3: vm3's IP address
"""

SERVICE_MAP = {
    "productcatalogservice": "PRODUCT_CATALOG_SERVICE_ADDR",
    "shippingservice": "SHIPPING_SERVICE_ADDR",
    "paymentservice": "PAYMENT_SERVICE_ADDR",
    "emailservice": "EMAIL_SERVICE_ADDR",
    "currencyservice": "CURRENCY_SERVICE_ADDR",
    "cartservice": "CART_SERVICE_ADDR",
    "recommendationservice": "RECOMMENDATION_SERVICE_ADDR",
    "checkoutservice": "CHECKOUT_SERVICE_ADDR",
    "adservice": "AD_SERVICE_ADDR",
    "redis-cart": "REDIS_ADDR",
    "frontend": "FRONTEND_ADDR",
}

def main(argv):
    if len(argv) != 4:
        print(USAGE)
        sys.exit(1)

    vmips = {"k8s-master": argv[1], "k8s-worker1": argv[2], "k8s-worker2": argv[3]}

    vmservices = {}
    service_envs = set()
    for vm in ["k8s-master", "k8s-worker1", "k8s-worker2"]:
        compose_file = f"compose-{vm}.yaml"

        with open(compose_file, "r") as f:
            compose = yaml.safe_load(f)

        for service, value in compose["services"].items():
            service_env = SERVICE_MAP.get(service)
            if service_env is None:
                continue
            port = value["ports"][0].split(":")[0]
            service_envs.add(f"{service_env}={service}:{port}")
            vmservices.setdefault(vm, []).append(service)

    for vm in ["k8s-master", "k8s-worker1", "k8s-worker2"]:
        compose_file = f"compose-{vm}.yaml"
        with open(compose_file, "r") as f:
            compose = yaml.safe_load(f)

        for service, value in compose["services"].items():
            volumes = set(value.setdefault("volumes", []))
            volumes.add("/run/resolv.conf:/etc/resolv.conf")
            volumes = list(volumes)
            volumes.sort()
            value["volumes"] = volumes
            
            if "microservices-demo" not in value["image"]:
                continue

            environment = set(value.setdefault("environment", []))
            environment.update(service_envs)
            environment = list(environment)
            environment.sort()
            value["environment"] = environment

        with open(compose_file, "w") as f:
            yaml.dump(compose, f, indent=2)


    dns_proxy_config = {
        "version" : 2,
        "activeEnv" : "",
        "remoteDnsServers" : [],
        "envs" : [{
            "name": "",
            "hostnames": []
        }]
    }
    id = 1
    for key, services in vmservices.items():
        for service in services:
            host = service.split(":")[0]
            dns_proxy_config["envs"][0]["hostnames"].append({
                "id" : id,
                "hostname" : host,
                "ip" : vmips[key],
                "ttl" : 60,
                "type" : "A"
            })
            id += 1
    with open(f"dns-config.json", "w") as f:
        json.dump(dns_proxy_config, f, indent=4)

if __name__ == "__main__":
    main(sys.argv)
