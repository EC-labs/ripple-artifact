import sys
import pandas as pd
import json

from pathlib import Path


USAGE = f"""
Usage: python {sys.argv[0]} <directory-path>

Arguments: 
    directory-path: directory containing coroot's json request that constructs its service map page in the `services.json` file
"""

def main(argv):
    if len(argv) != 2:
        print(USAGE)
        sys.exit(1)

    dir = Path(sys.argv[1])
    with open(dir.joinpath("services.json"), "r") as f:
        contents = json.load(f)

    edges = []

    for entry in contents["data"]["map"]: 
        src = entry["id"]
        if not src.startswith("default"):
            continue
        src = src.split(":")[2]

        for downstream in entry["downstreams"]:
            dst = downstream["id"]
            if not dst.startswith("default"):
                continue
            dst = dst.split(":")[2]
            edges.append([dst, src])
            edges.append([src, dst])

        for upstream in entry["upstreams"]:
            dst = upstream["id"]
            if not dst.startswith("default"):
                continue
            dst = dst.split(":")[2]
            edges.append([src, dst])
            edges.append([dst, src])

    srcs, dsts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts}).drop_duplicates().sort_values(by=["src", "dst"]).reset_index(drop=True)
    edges.to_csv(dir.joinpath("post.csv"), index=False)
    
if __name__ == "__main__":
    main(sys.argv)
