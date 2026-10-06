#!/usr/bin/env python3

import sys
import os
import duckdb
import pandas as pd

from pathlib import Path
from jinja2 import Template


SERVICE_MAP_QUERY = os.getenv(
    "SERVICE_MAP_QUERY", 
    str(Path(__file__).resolve().parent / "service-map.sql")
)
GROUND_TRUTH = os.getenv(
    "GROUND_TRUTH", 
    str(Path(__file__).resolve().parent / "gt")
)

def services(db, is_k8s: bool, microservice_benchmark: str):
    template = Template((Path(SERVICE_MAP_QUERY)).read_text())
    if is_k8s:
        service_filter = f"(lsvc.namespace = '{microservice_benchmark}' AND rsvc.namespace = '{microservice_benchmark}')"
    else:
        service_filter = f"""(
                (service1 LIKE '/{microservice_benchmark}-%' OR service1 = 'docker-proxy') 
                AND (service2 LIKE '/{microservice_benchmark}-%' OR service2 = 'docker-proxy')
            )"""

    query = template.render({
        "service_filter": service_filter 
    }) 
    return db.execute(query).df().drop_duplicates()


def connect_docker_proxy(service_map):
    db = duckdb.connect(database=":memory:")
    regular = db.execute('''
        SELECT * FROM service_map 
        WHERE 'docker-proxy' NOT IN (service1, service2)
    ''').df()
    proxied = db.execute('''
        WITH 
            with_proxy_ AS (
                SELECT * FROM service_map 
                WHERE 'docker-proxy' IN (service1, service2)
            ),
            with_proxy AS (
                SELECT
                    CASE WHEN service1 = 'docker-proxy' THEN machine2 ELSE machine1 END machine1,
                    CASE WHEN service1 = 'docker-proxy' THEN pid2 ELSE pid1 END pid1,
                    CASE WHEN service1 = 'docker-proxy' THEN service2 ELSE service1 END service1,
                    CASE WHEN service1 = 'docker-proxy' THEN machine1 ELSE machine2 END machine2,
                    CASE WHEN service1 = 'docker-proxy' THEN pid1 ELSE pid2 END pid2,
                    CASE WHEN service1 = 'docker-proxy' THEN service1 ELSE service2 END service2
                FROM with_proxy_
            ),
            selfjoin AS (
                SELECT l.machine1 as machine1, l.pid1 as pid1, l.service1 as service1, r.machine1 as machine2, r.pid1 as pid2, r.service1 as service2
                FROM with_proxy l
                INNER JOIN with_proxy r
                    ON (((l.machine2, l.pid2, l.service2) = (r.machine2, r.pid2, r.service2))
                        AND ((l.machine1, l.pid1, l.service1) != (r.machine1, r.pid1, r.service1)))
                    
            )
        SELECT * FROM selfjoin
    ''').df()
    service_map = pd.concat([regular, proxied], axis=0).reset_index(drop=True)
    
    return service_map
    

def postprocess_docker(service_map, microservice_benchmark):
    service_map["service1"] = service_map["service1"].str.replace(f"/{microservice_benchmark}-(.*)-[0-9]+", r"\1", regex=True)
    service_map["service2"] = service_map["service2"].str.replace(f"/{microservice_benchmark}-(.*)-[0-9]+", r"\1", regex=True)


def postprocess_k8s(service_map):
    service_map["service1"] = service_map["service1"].str.replace(r"-[0-9a-z]+-[0-9a-z]+$", "", regex=True)
    service_map["service2"] = service_map["service2"].str.replace(r"-[0-9a-z]+-[0-9a-z]+$", "", regex=True)

def compare(microservice_benchmark, service_map):
    conn = duckdb.connect(database=':memory:')
    
    results = []
    gt_path = Path(GROUND_TRUTH) / f"{microservice_benchmark}.csv"
    gt = conn.execute(f"""
        SELECT * FROM '{gt_path}'
    """).df()
    inaccurate = conn.execute("""
        SELECT * FROM service_map
        EXCEPT ALL
        SELECT * FROM gt
    """).df()
    missing = conn.execute("""
        SELECT * FROM gt
        EXCEPT ALL
        SELECT * FROM service_map
    """).df()

    if len(inaccurate):
        print("=== INACCURATE ===")
        print(inaccurate)
    if len(missing):
        print("=== MISSING ===")
        print(missing)
    
    precision = (service_map.shape[0] - inaccurate.shape[0])/service_map.shape[0]
    recall = (gt.shape[0] - missing.shape[0])/gt.shape[0]
    f1 = 2 * ((precision*recall)/(precision + recall))
    results.append([precision, recall, f1])
    results = pd.DataFrame(data=results, columns=["precision", "recall", "f1score"])
    print(results)

def main():
    db = sys.argv[1]
    is_k8s = sys.argv[2] == "True"
    microservice_benchmark = sys.argv[3]
    db = duckdb.connect(db)
    service_map = services(db, is_k8s, microservice_benchmark)
    if is_k8s:
        postprocess_k8s(service_map)
    else:
        postprocess_docker(service_map, microservice_benchmark)
        service_map = connect_docker_proxy(service_map)

    service_map = pd.concat([
        service_map[["service1", "service2"]],
        service_map[["service1", "service2"]].rename(
            columns={"service1": "service2", "service2": "service1"}
        ),
    ], ignore_index=True)

    service_map = service_map.drop_duplicates().reset_index(drop=True)
    compare(microservice_benchmark, service_map)

if __name__ == "__main__":
    main()
