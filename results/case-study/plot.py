import duckdb
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt

matplotlib.style.use("bmh")
font = {'size': 13}
matplotlib.rc('font', **font)

QUERY = """
WITH 
    _tcp_discovery AS (
        SELECT * FROM vm1.tcp_discovery tcp
        WHERE tcp.remote_inode_id <> 0
        UNION ALL
        SELECT * FROM vm2.tcp_discovery tcp
        WHERE tcp.remote_inode_id <> 0
        UNION ALL
        SELECT * FROM vm3.tcp_discovery tcp
        WHERE tcp.remote_inode_id <> 0
    ),
    tcp_discovery AS (
        SELECT * FROM _tcp_discovery
        UNION ALL 
        SELECT 
            remote_machine_id as local_machine_id,
            remote_inode_id as local_inode_id,
            local_machine_id as remote_machine_id,
            local_inode_id as remote_inode_id,
            inserted_at,
        FROM 
            _tcp_discovery
    ),
    process_context AS (
        SELECT 1 as machine_id, * FROM vm1.process_context
        UNION ALL
        SELECT 2 as machine_id, * FROM vm2.process_context
        UNION ALL
        SELECT 3 as machine_id, * FROM vm3.process_context
    ),
    docker AS (
        SELECT 1 as machine_id, * FROM vm1.docker
        UNION ALL
        SELECT 2 as machine_id, * FROM vm2.docker
        UNION ALL
        SELECT 3 as machine_id, * FROM vm3.docker
    ),
    k8s AS (
        SELECT 1 as machine_id, * FROM vm1.k8s
        UNION ALL
        SELECT 2 as machine_id, * FROM vm2.k8s
        UNION ALL
        SELECT 3 as machine_id, * FROM vm3.k8s
    ),
    pids AS (
        SELECT DISTINCT
            1 as machine_id,
            pid, 
            inode_id,
        FROM 
            vm1.vfs vfs
        WHERE 
            vfs.fs_magic = 1397703499
        UNION ALL
        SELECT DISTINCT
            2 as machine_id,
            pid, 
            inode_id,
        FROM 
            vm2.vfs vfs
        WHERE 
            vfs.fs_magic = 1397703499
        UNION ALL
        SELECT DISTINCT
            3 as machine_id,
            pid, 
            inode_id,
        FROM 
            vm3.vfs vfs
        WHERE 
            vfs.fs_magic = 1397703499
    )
SELECT DISTINCT
    tcp.local_machine_id, 
    lpids.pid as lpid,
    COALESCE(lk8s.pod_name, ldock.name, lpc.cgroup) as lcgroup,
    tcp.local_inode_id,
    tcp.remote_machine_id,
    rpids.pid as rpid,
    COALESCE(rk8s.pod_name, rdock.name, rpc.cgroup) as rcgroup,
    tcp.remote_inode_id,
FROM
    tcp_discovery tcp
LEFT JOIN
    pids as lpids
    ON lpids.inode_id = tcp.local_inode_id
    AND lpids.machine_id = tcp.local_machine_id
LEFT JOIN 
    process_context lpc
    ON lpc.pid = lpids.pid
    AND lpc.machine_id = tcp.local_machine_id
LEFT JOIN
    docker ldock
    ON ldock.cgroup = lpc.cgroup
    AND ldock.machine_id = tcp.local_machine_id
LEFT JOIN
    k8s lk8s
    ON lk8s.cgroup = lpc.cgroup
    AND lk8s.machine_id = tcp.local_machine_id
LEFT JOIN
    pids as rpids
    ON rpids.inode_id = tcp.remote_inode_id
    AND rpids.machine_id = tcp.remote_machine_id
LEFT JOIN 
    process_context rpc
    ON rpc.pid = rpids.pid
    AND rpc.machine_id = tcp.remote_machine_id
LEFT JOIN 
    docker rdock
    ON rdock.cgroup = rpc.cgroup
    AND rdock.machine_id = tcp.remote_machine_id
LEFT JOIN 
    k8s rk8s
    ON rk8s.cgroup = rpc.cgroup
    AND rk8s.machine_id = tcp.remote_machine_id
WHERE 
    lpids.pid IS NOT NULL 
    AND rpids.pid IS NOT NULL
    AND (
        lcgroup LIKE '%frontend%' 
        OR lcgroup LIKE '%checkout%'
        OR lcgroup LIKE '%ad%'
        OR lcgroup LIKE '%recommendation%'
        OR lcgroup LIKE '%payment%'
        OR lcgroup LIKE '%email%'
        OR lcgroup LIKE '%productcatalog%'
        OR lcgroup LIKE '%shipping%'
        OR lcgroup LIKE '%currency%'
        OR lcgroup LIKE '%cart%'
        OR lcgroup LIKE '%redis%'
    )
    AND NOT starts_with(rcgroup, '/')
ORDER BY
    lcgroup, rcgroup
"""

conn = duckdb.connect(database=':memory:')
conn.execute("""ATTACH 'online/vm1.db3' as vm1""")
conn.execute("""ATTACH 'online/vm2.db3' as vm2""")
conn.execute("""ATTACH 'online/vm3.db3' as vm3""")

print(conn.execute(QUERY).df())

conn = duckdb.connect(database='online/vm3.db3')

# Write activity to the recommendation service
QUERY = """
SELECT DISTINCT
    ts_s, SUM(total_requests) as total_requests
FROM vfs
WHERE inode_id = 121847460 AND op = 0
GROUP BY ts_s
ORDER BY ts_s
"""

df = conn.execute(QUERY).df()

plt.figure(figsize=(8, 4))
plt.plot(df["ts_s"], df["total_requests"])

QUERY = """
SELECT DISTINCT
    tid
FROM taskstats_view
WHERE pid = 1390867
"""

plt.figure(figsize=(5,4))
for tid in conn.execute(QUERY).df()["tid"]:
    QUERY = f"""
        SELECT ts, rq_share FROM taskstats_view WHERE tid = {tid} ORDER BY ts
    """
    df = conn.execute(QUERY).df()
    plt.plot((df["ts"] - df["ts"].min()).dt.total_seconds(), pd.Series.ewm(df['rq_share'], span=20).mean())
plt.xlabel("Timestamp (s)")
plt.ylabel("Runqueue Time (s/s)")
plt.tight_layout()
plt.savefig("rqtime.pdf", bbox_inches='tight', pad_inches=0)

QUERY = """
SELECT DISTINCT
    ts_s, SUM(total_requests) as total_requests
FROM vfs
WHERE inode_id = 106838211 AND op = 0
GROUP BY ts_s
ORDER BY ts_s
"""

conn = duckdb.connect(database='online/vm2.db3')
df = conn.execute(QUERY).df()

plt.figure(figsize=(8, 4))
plt.plot(df["ts_s"], df["total_requests"])

target = duckdb.sql("""
    SELECT 
        make_timestamp(Timestamp * 1000000) as "Timestamp", "Requests/s"
    FROM read_csv('results/load_stats_history.csv')
    WHERE Name = 'Aggregated'
""").df()
print(target.columns)

plt.figure(figsize=(5, 4))
plt.plot((target["Timestamp"] - target["Timestamp"].min()).dt.total_seconds(), target["Requests/s"])
plt.xlabel("Timestamp (s)")
plt.ylabel("Throughput (req/s)")
plt.tight_layout()
plt.savefig("throughput.pdf", bbox_inches='tight', pad_inches=0)
plt.show()

print(target["Timestamp"] - target["Timestamp"].min())
