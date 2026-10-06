import sys
import pandas as pd

from pathlib import Path


USAGE = f"""
Usage: python {sys.argv[0]} <directory-path>

Arguments: 
    directory-path: directory including a `nodes.csv` and `edges.csv` file exporting from caretta's grafana
"""

SERVICES = [
    'cast-info-mongodb',
    'cast-info-service',
    'compose-review-memcached',
    'compose-review-service',
    'movie-id-memcached',
    'movie-id-mongodb',
    'movie-id-service',
    'movie-info-mongodb',
    'movie-info-service',
    'movie-review-mongodb',
    'movie-review-redis',
    'movie-review-service',
    'nginx-web-server',
    'plot-mongodb',
    'plot-service',
    'rating-redis',
    'rating-service',
    'review-storage-mongodb',
    'review-storage-service',
    'text-service',
    'unique-id-service',
    'user-memcached',
    'user-mongodb',
    'user-review-mongodb',
    'user-review-redis',
    'user-review-service',
    'user-service'
]

def part_of_ob(name):
    for service in SERVICES:
        if name.startswith(service):
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
        src, dst = part_of_ob(src), part_of_ob(dst)
        if src is None or dst is None:
            continue

        edges.append([src, dst])
        edges.append([dst, src])

    srcs, dsts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts})\
        .drop_duplicates()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)
    print(edges)
    edges.to_csv(dir.joinpath("post.csv"), index=False)


if __name__ == "__main__":
    main(sys.argv)
