import sys
import pandas as pd
import json

from pathlib import Path


USAGE = f"""
Usage: python {sys.argv[0]} <directory-path>

Arguments: 
    directory-path: directory containing coroot's json request that constructs its service map page in the `services.json` file
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

def part_of_media(name):
    for service in SERVICES:
        if service in name:
            return service
    return None

def main(argv):
    if len(argv) != 2:
        print(USAGE)
        sys.exit(1)

    dir = Path(sys.argv[1])
    with open(dir.joinpath("services.json"), "r") as f:
        contents = json.load(f)

    edges = []

    for entry in contents["data"]["map"]: 
        src = part_of_media(entry["id"])
        if src is None:
            continue

        for downstream in entry["downstreams"]:
            dst = part_of_media(downstream["id"])
            if dst is None:
                continue
            edges.append([dst, src])
            edges.append([src, dst])

        for upstream in entry["upstreams"]:
            dst = part_of_media(upstream["id"])
            if dst is None:
                continue
            edges.append([src, dst])
            edges.append([dst, src])

    srcs, dsts = zip(*edges) or [], []
    edges = pd.DataFrame({"src": srcs, "dst": dsts}).drop_duplicates().sort_values(by=["src", "dst"]).reset_index(drop=True)
    print(edges)
    edges.to_csv(dir.joinpath("post.csv"), index=False)
    
if __name__ == "__main__":
    main(sys.argv)
