import pandas as pd

results = []

for ms in ["online-boutique", "social", "media"]:
    for approach in ["baseline", "caretta", "coroot", "deepflow", "ripple"]:
        experiments = pd.read_csv(f"{ms}/{approach}.csv").iloc[:, 0]
        results.append([ms, approach, experiments.mean(), experiments.std()])

df = pd.DataFrame(results, columns=["benchmark", "approach", "avg", "std"])
# df["latency"] = df["avg"].round(2).astype(str) + " ± " + df["std"].round(2).astype(str)
df["latency"] = df.apply(lambda row: f"{row['avg']:.2f} ± {row['std']:.2f}", axis=1)
# df: pd.DataFrame = df.loc[:, ["latency", "approach", "benchmark"]]
# print(df)
table = df.pivot(values=["latency"], index=["approach"], columns=["benchmark"])
print(table.to_latex(escape=False))
