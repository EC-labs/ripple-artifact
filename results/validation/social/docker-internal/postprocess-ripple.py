import sys
import pandas as pd
import duckdb

from pathlib import Path


USAGE = f"""
Usage: python {sys.argv[0]} <directory-path>

Arguments: 
    directory-path: directory including the metrics collected in the three different VMs `vm1.db3`, `vm2.db3` and `vm3.db3`
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

    dir = Path(argv[1])

    conn = duckdb.connect(database=':memory:')

    conn.execute(f"""ATTACH '{dir}/vm1.db3' as vm1""")
    conn.execute(f"""ATTACH '{dir}/vm2.db3' as vm2""")
    conn.execute(f"""ATTACH '{dir}/vm3.db3' as vm3""")

    edges = conn.execute("""
        WITH 
            tcp_discovery AS (
                SELECT * FROM vm1.tcp_discovery tcp
                WHERE tcp.remote_inode_id <> 0
                UNION ALL
                SELECT * FROM vm2.tcp_discovery tcp
                WHERE tcp.remote_inode_id <> 0
                UNION ALL
                SELECT * FROM vm3.tcp_discovery tcp
                WHERE tcp.remote_inode_id <> 0
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
            tcp.remote_machine_id,
            tcp.remote_inode_id, 
            rpids.pid as rpid,
            COALESCE(rk8s.pod_name, rdock.name, rpc.cgroup) as rcgroup,
            COUNT(*) as num_connections, 
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
        GROUP BY 
            tcp.local_machine_id, 
            lpids.pid,
            lk8s.pod_name, 
            ldock.name, 
            lpc.cgroup,
            tcp.remote_machine_id,
            tcp.remote_inode_id, 
            rpids.pid,
            rk8s.pod_name, 
            rdock.name,
            rpc.cgroup,
        ORDER BY
            lcgroup
    """).df()

    res = edges.loc[:, ["lpid", "lcgroup", "rpid", "rcgroup"]].rename(columns={"lcgroup": "src", "rcgroup": "dst"}).drop_duplicates()
    removed_proxy = duckdb.sql("""
        WITH
            proxy AS (
                SELECT 
                    * 
                FROM 
                    res
                WHERE 
                    src LIKE '%docker.service%' 
                    OR dst LIKE '%docker.service%'
            )
        SELECT l.src, r.dst
        FROM (SELECT * FROM proxy WHERE src NOT LIKE '%docker.service%') as l
        LEFT JOIN (SELECT * FROM proxy WHERE dst NOT LIKE '%docker.service%') as r
            ON l.rpid = r.lpid AND l.lpid <> r.rpid
    """).df()
    table = pd.concat([res.loc[:, ["src", "dst"]], removed_proxy])

    edges = []
    for (_, edge) in table.iterrows():
        src, dst = edge["src"], edge["dst"]
        src, dst = part_of_media(src), part_of_media(dst)
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
