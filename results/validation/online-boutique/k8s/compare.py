import duckdb
import pandas as pd

def main():
    conn = duckdb.connect(database=':memory:')

    results = []
    for tool in ["caretta", "coroot", "deepflow", "ripple"]:
        print(tool)
        gt = conn.execute(f"""
            SELECT * FROM 'gt.csv'
        """).df()
        tool_rows = conn.execute(f"""
            SELECT * FROM '{tool}/post.csv'
        """).df()
        inaccurate = conn.execute(f"""
            SELECT * FROM '{tool}/post.csv'
            EXCEPT ALL
            SELECT * FROM 'gt.csv'
        """).df()
        missing = conn.execute(f"""
            SELECT * FROM 'gt.csv'
            EXCEPT ALL
            SELECT * FROM '{tool}/post.csv'
        """).df()

        precision = (tool_rows.shape[0] - inaccurate.shape[0])/tool_rows.shape[0]
        recall = (gt.shape[0] - missing.shape[0])/gt.shape[0]
        f1 = 2 * ((precision*recall)/(precision + recall))
        results.append([tool, precision, recall, f1])
    
    pd.DataFrame(data=results, columns=["tool", "precision", "recall", "f1score"]).to_csv("results.csv", index=False)




if __name__ == "__main__":
    main()
