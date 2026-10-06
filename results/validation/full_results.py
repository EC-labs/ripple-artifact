import pandas as pd


def main():
    records = []
    
    for app in ["social", "media", "online-boutique"]:
        for env in ["k8s", "docker-internal", "docker-external"]:
            df = pd.read_csv(f"{app}/{env}/results.csv")
            df.set_index("tool", inplace=True)
            
            # Add a row-level index for app and env
            records.append(((app, env), df))
    
    # Build the final dataframe
    all_data = {}
    for (app, env), df in records:
        for tool in df.index:
            for metric in df.columns:
                all_data.setdefault((tool, metric), {})[(app, env)] = df.loc[tool, metric]
    
    # Create MultiIndex DataFrame
    final_df = pd.DataFrame.from_dict(all_data, orient="columns")
    final_df.index = pd.MultiIndex.from_tuples(final_df.index, names=["app", "env"])
    final_df.columns = pd.MultiIndex.from_tuples(final_df.columns, names=["tool", "metric"])

    print(final_df.transpose().to_latex(index_names=False, float_format="%.2f"))

if __name__ == "__main__":
    main()
