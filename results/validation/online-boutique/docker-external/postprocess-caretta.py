import sys
import pandas as pd

from pathlib import Path


USAGE = f"""
Usage: python {sys.argv[0]} <directory-path>

Arguments: 
    directory-path: directory including a `nodes.csv` and `edges.csv` file exporting from caretta's grafana
"""

def main(argv):
    if len(argv) != 2:
        print(USAGE)
        sys.exit(1)

    dir = Path(argv[1])

    nodes = pd.read_csv(dir.joinpath("nodes.csv"))
    nodes = nodes.loc[
        nodes["title"].str.startswith("ip-172") | nodes["title"].str.startswith("ec2-"), 
        ["id", "title"]
    ] 
    edges = pd.read_csv(dir.joinpath("edges.csv")).loc[:, ["source", "target"]]

    res = pd.merge(edges, nodes, how="left", left_on="source", right_on="id")
    res = pd.merge(res, nodes, how="left", left_on="target", right_on="id")
    res = res.loc[:, ["title_x", "title_y"]]\
        .rename(columns={"title_x": "src", "title_y": "dst"})
    reverse = res.rename(columns={"src": "dst", "dst": "src"})
    res = pd.concat([res, reverse])\
        .drop_duplicates()\
        .sort_values(by=["src", "dst"])\
        .dropna()\
        .reset_index(drop=True)

    print(res)
    # print(list(res["src"].unique()))
    res.to_csv(dir.joinpath("post.csv"), index=False)

if __name__ == "__main__":
    main(sys.argv)
