import sys
import pandas as pd

from pathlib import Path


USAGE = f"""
Usage: python {sys.argv[0]} <directory-path>

Arguments: 
    directory-path: directory including a `nodes.csv` and `edges.csv` file exporting from caretta's grafana
"""

SERVICES = [
    'compose-post-service',
    'home-timeline-redis',
    'home-timeline-service',
    'media-service',
    'nginx-thrift',
    'post-storage-mongodb',
    'post-storage-service',
    'social-graph-mongodb',
    'social-graph-redis',
    'social-graph-service',
    'text-service',
    'unique-id-service',
    'url-shorten-mongodb',
    'url-shorten-service',
    'user-memcached',
    'user-mention-service',
    'user-mongodb',
    'user-service',
    'user-timeline-mongodb',
    'user-timeline-redis',
    'user-timeline-service'
]

def part_of_app(name):
    for service in SERVICES:
        if service in name:
            return service
    return None

def main(argv):
    if len(argv) != 2:
        print(USAGE)
        sys.exit(1)

    dir = Path(argv[1]);
    table = pd.read_csv(dir.joinpath("services.csv")).loc[:, ["client_resource", "server_resource"]].rename(columns={"client_resource": "src", "server_resource": "dst"})
    
    edges = []
    for (_, edge) in table.iterrows():
        src, dst = edge["src"], edge["dst"]
        src, dst = part_of_app(src), part_of_app(dst)
        if src is None or dst is None:
            continue

        edges.append([src, dst])
        edges.append([dst, src])

    srcs, dsts = zip(*edges) or [], []
    edges = pd.DataFrame({"src": srcs, "dst": dsts})\
        .drop_duplicates()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)
    print(edges)
    edges.to_csv(dir.joinpath("post.csv"), index=False)


if __name__ == "__main__":
    main(sys.argv)
