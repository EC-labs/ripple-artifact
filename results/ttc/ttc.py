import duckdb
import pandas as pd


ONLINE_BOUTIQUE = [
    "loadgenerator",
    "frontend",
    "checkoutservice",
    "adservice",
    "recommendationservice",
    "paymentservice",
    "emailservice",
    "productcatalogservice",
    "shippingservice",
    "currencyservice",
    "cartservice",
    "redis-cart",
]

MEDIA = [
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

SOCIAL = [
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
    SELECT
        MIN(tcp.inserted_at) as inserted_at,
        tcp.local_machine_id, 
        lpids.pid as lpid,
        COALESCE(lk8s.pod_name, ldock.name, lpc.cgroup) as lcgroup,
        tcp.remote_machine_id,
        rpids.pid as rpid,
        COALESCE(rk8s.pod_name, rdock.name, rpc.cgroup) as rcgroup,
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
        lk8s.pod_name, 
        ldock.name, 
        lpc.cgroup,
        tcp.remote_machine_id,
        rk8s.pod_name, 
        rdock.name,
        rpc.cgroup,
        lpid,
        rpid
    ORDER BY
        lcgroup
"""

def part_of_app(name, app, prefix="", startswith=False):
    for service in app:
        service = f"{prefix}{service}"
        if startswith:
            if name.startswith(service):
                return service
        else: 
            if service in name:
                return service
    return None

def online():
    conn = duckdb.connect(database=':memory:')

    conn.execute("""ATTACH 'online/vm1.db3' as vm1""")
    conn.execute("""ATTACH 'online/vm2.db3' as vm2""")
    conn.execute("""ATTACH 'online/vm3.db3' as vm3""")

    edges = conn.execute(QUERY).df()

    table = edges.loc[:, ["lcgroup", "rcgroup", "inserted_at"]].rename(columns={"lcgroup": "src", "rcgroup": "dst"}).drop_duplicates()
    # print("service #:", len(table["src"].unique()), table.shape[0]/2)

    edges = []
    for (_, edge) in table.iterrows():
        
        src, dst, insert_ts = edge["src"], edge["dst"], edge["inserted_at"]
        src, dst = part_of_app(src, ONLINE_BOUTIQUE, "online-"), part_of_app(dst, ONLINE_BOUTIQUE, "online-")
        if src is None or dst is None:
            continue

        edges.append([src, dst, insert_ts])
        edges.append([dst, src, insert_ts])

    srcs, dsts, inserts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts, "inserted_at": inserts})\
        .drop_duplicates()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)

    online_ms = duckdb.sql("""SELECT 'online-' || src as src, 'online-' || dst as dst FROM read_csv('online.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM online_ms m
        LEFT JOIN edges e
            ON m.src = e.src AND m.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == online_ms.shape[0])
    ttc = res['inserted_at'].max() - res['inserted_at'].min()
    ttc = ttc.total_seconds()
    print(f"online: {ttc:.2f}")

def media():
    conn = duckdb.connect(database=':memory:')

    conn.execute("""ATTACH 'media/vm1.db3' as vm1""")
    conn.execute("""ATTACH 'media/vm2.db3' as vm2""")
    conn.execute("""ATTACH 'media/vm3.db3' as vm3""")

    edges = conn.execute(QUERY).df()

    table = edges.loc[:, ["lcgroup", "rcgroup", "inserted_at"]].rename(columns={"lcgroup": "src", "rcgroup": "dst"}).drop_duplicates()
    # print("service #:", len(table["src"].unique()), table.shape[0]/2)

    edges = []
    for (_, edge) in table.iterrows():
        
        src, dst, insert_ts = edge["src"], edge["dst"], edge["inserted_at"]
        src, dst = part_of_app(src, MEDIA, "media-"), part_of_app(dst, MEDIA, "media-")
        if src is None or dst is None:
            continue

        edges.append([src, dst, insert_ts])
        edges.append([dst, src, insert_ts])

    srcs, dsts, inserts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts, "inserted_at": inserts})\
        .drop_duplicates()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)

    media_ms = duckdb.sql("""SELECT 'media-' || src as src, 'media-' || dst as dst FROM read_csv('media.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM media_ms m
        LEFT JOIN edges e
            ON m.src = e.src AND m.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == media_ms.shape[0])
    ttc = res['inserted_at'].max() - res['inserted_at'].min()
    ttc = ttc.total_seconds()
    print(f"media: {ttc:.2f}")

def social():
    conn = duckdb.connect(database=':memory:')

    conn.execute("""ATTACH 'social/vm1.db3' as vm1""")
    conn.execute("""ATTACH 'social/vm2.db3' as vm2""")
    conn.execute("""ATTACH 'social/vm3.db3' as vm3""")

    edges = conn.execute(QUERY).df()

    table = edges.loc[:, ["lcgroup", "rcgroup", "inserted_at"]].rename(columns={"lcgroup": "src", "rcgroup": "dst"}).drop_duplicates()
    # print("service #:", len(table["src"].unique()), table.shape[0]/2)

    edges = []
    for (_, edge) in table.iterrows():
        
        src, dst, insert_ts = edge["src"], edge["dst"], edge["inserted_at"]
        src, dst = part_of_app(src, SOCIAL, "social-"), part_of_app(dst, SOCIAL, "social-")
        if src is None or dst is None:
            continue

        edges.append([src, dst, insert_ts])
        edges.append([dst, src, insert_ts])

    srcs, dsts, inserts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts, "inserted_at": inserts})\
        .drop_duplicates()\
        .groupby(["src", "dst"])\
        .min()\
        .reset_index()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)

    social_ms = duckdb.sql("""SELECT 'social-' || src as src, 'social-' || dst as dst FROM read_csv('social.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM social_ms m
        LEFT JOIN edges e
            ON m.src = e.src AND m.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == social_ms.shape[0])
    ttc = res['inserted_at'].max() - res['inserted_at'].min()
    ttc = ttc.total_seconds()
    print(f"social: {ttc:.2f}")

def online_media():
    conn = duckdb.connect(database=':memory:')

    conn.execute("""ATTACH 'online-media/vm1.db3' as vm1""")
    conn.execute("""ATTACH 'online-media/vm2.db3' as vm2""")
    conn.execute("""ATTACH 'online-media/vm3.db3' as vm3""")

    edges = conn.execute(QUERY).df()

    table = edges.loc[:, ["lcgroup", "rcgroup", "inserted_at"]].rename(columns={"lcgroup": "src", "rcgroup": "dst"}).drop_duplicates()
    # print("service #:", len(table["src"].unique()), table.shape[0]/2)

    edges = []
    for (_, edge) in table.iterrows():
        
        src, dst, insert_ts = edge["src"], edge["dst"], edge["inserted_at"]
        src = part_of_app(src, ONLINE_BOUTIQUE) or part_of_app(src, MEDIA)
        dst = part_of_app(dst, ONLINE_BOUTIQUE) or part_of_app(dst, MEDIA)
        if src is None or dst is None:
            continue

        edges.append([src, dst, insert_ts])
        edges.append([dst, src, insert_ts])

    srcs, dsts, inserts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts, "inserted_at": inserts})\
        .drop_duplicates()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)

    ms = duckdb.sql("""SELECT * FROM read_csv('online.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == ms.shape[0])
    online_min, online_max = res["inserted_at"].min(), res["inserted_at"].max()

    ms = duckdb.sql("""SELECT * FROM read_csv('media.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == ms.shape[0])
    media_min, media_max = res["inserted_at"].min(), res["inserted_at"].max()
    ttc = max(online_max, media_max) - min(online_min, media_min)
    ttc = ttc.total_seconds()
    print(f"online+media: {ttc:.2f}")

def online_social():
    conn = duckdb.connect(database=':memory:')

    conn.execute("""ATTACH 'online-social/vm1.db3' as vm1""")
    conn.execute("""ATTACH 'online-social/vm2.db3' as vm2""")
    conn.execute("""ATTACH 'online-social/vm3.db3' as vm3""")

    edges = conn.execute(QUERY).df()

    table = edges.loc[:, ["lcgroup", "rcgroup", "inserted_at"]].rename(columns={"lcgroup": "src", "rcgroup": "dst"}).drop_duplicates()
    # print("service #:", len(table["src"].unique()), table.shape[0]/2)

    edges = []
    for (_, edge) in table.iterrows():
        
        src, dst, insert_ts = edge["src"], edge["dst"], edge["inserted_at"]
        src = part_of_app(src, ONLINE_BOUTIQUE) or part_of_app(src, SOCIAL, prefix="social-")
        dst = part_of_app(dst, ONLINE_BOUTIQUE) or part_of_app(dst, SOCIAL, prefix="social-")
        if src is None or dst is None:
            continue

        edges.append([src, dst, insert_ts])
        edges.append([dst, src, insert_ts])

    srcs, dsts, inserts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts, "inserted_at": inserts})\
        .drop_duplicates()\
        .groupby(["src", "dst"])\
        .min()\
        .reset_index()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)

    ms = duckdb.sql("""SELECT * FROM read_csv('online.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == ms.shape[0])
    online_min, online_max = res["inserted_at"].min(), res["inserted_at"].max()

    ms = duckdb.sql("""SELECT 'social-' || src as src, 'social-' || dst as dst FROM read_csv('social.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == ms.shape[0])
    social_min, social_max = res["inserted_at"].min(), res["inserted_at"].max()
    ttc = max(online_max, social_max) - min(online_min, social_min)
    ttc = ttc.total_seconds()
    print(f"online+social: {ttc:.2f}")

def media_social():
    conn = duckdb.connect(database=':memory:')

    conn.execute("""ATTACH 'media-social/vm1.db3' as vm1""")
    conn.execute("""ATTACH 'media-social/vm2.db3' as vm2""")
    conn.execute("""ATTACH 'media-social/vm3.db3' as vm3""")

    edges = conn.execute(QUERY).df()

    table = edges.loc[:, ["lcgroup", "rcgroup", "inserted_at"]].rename(columns={"lcgroup": "src", "rcgroup": "dst"}).drop_duplicates()
    # print("service #:", len(table["src"].unique()), table.shape[0]/2)

    edges = []
    for (_, edge) in table.iterrows():
        
        src, dst, insert_ts = edge["src"], edge["dst"], edge["inserted_at"]
        src = part_of_app(src, MEDIA, startswith=True) or part_of_app(src, SOCIAL, prefix="social-")
        dst = part_of_app(dst, MEDIA, startswith=True) or part_of_app(dst, SOCIAL, prefix="social-")
        if src is None or dst is None:
            continue

        edges.append([src, dst, insert_ts])
        edges.append([dst, src, insert_ts])

    srcs, dsts, inserts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts, "inserted_at": inserts})\
        .drop_duplicates()\
        .groupby(["src", "dst"])\
        .min()\
        .reset_index()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)

    ms = duckdb.sql("""SELECT * FROM read_csv('media.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == ms.shape[0])
    media_min, media_max = res["inserted_at"].min(), res["inserted_at"].max()

    ms = duckdb.sql("""SELECT 'social-' || src as src, 'social-' || dst as dst FROM read_csv('social.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()

    assert(res.shape[0] == ms.shape[0])
    social_min, social_max = res["inserted_at"].min(), res["inserted_at"].max()
    ttc = max(media_max, social_max) - min(media_min, social_min)
    ttc = ttc.total_seconds()
    print(f"media+social: {ttc:.2f}")

def online_media_social():
    conn = duckdb.connect(database=':memory:')

    conn.execute("""ATTACH 'online-media-social/vm1.db3' as vm1""")
    conn.execute("""ATTACH 'online-media-social/vm2.db3' as vm2""")
    conn.execute("""ATTACH 'online-media-social/vm3.db3' as vm3""")

    edges = conn.execute(QUERY).df()

    table = edges.loc[:, ["lcgroup", "rcgroup", "inserted_at"]].rename(columns={"lcgroup": "src", "rcgroup": "dst"}).drop_duplicates()
    # print("service #:", len(table["src"].unique()), table.shape[0]/2)

    edges = []
    for (_, edge) in table.iterrows():
        
        src, dst, insert_ts = edge["src"], edge["dst"], edge["inserted_at"]
        src = part_of_app(src, MEDIA, startswith=True) or part_of_app(src, SOCIAL, prefix="social-") or part_of_app(src, ONLINE_BOUTIQUE, startswith=True)
        dst = part_of_app(dst, MEDIA, startswith=True) or part_of_app(dst, SOCIAL, prefix="social-") or part_of_app(dst, ONLINE_BOUTIQUE, startswith=True)
        if src is None or dst is None:
            continue

        edges.append([src, dst, insert_ts])
        edges.append([dst, src, insert_ts])

    srcs, dsts, inserts = zip(*edges)
    edges = pd.DataFrame({"src": srcs, "dst": dsts, "inserted_at": inserts})\
        .drop_duplicates()\
        .groupby(["src", "dst"])\
        .min()\
        .reset_index()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)

    ms = duckdb.sql("""SELECT * FROM read_csv('online.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()
    assert(res.shape[0] == ms.shape[0])
    online_min, online_max = res["inserted_at"].min(), res["inserted_at"].max()

    ms = duckdb.sql("""SELECT * FROM read_csv('media.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()
    assert(res.shape[0] == ms.shape[0])
    media_min, media_max = res["inserted_at"].min(), res["inserted_at"].max()

    ms = duckdb.sql("""SELECT 'social-' || src as src, 'social-' || dst as dst FROM read_csv('social.csv');""").df()
    res = duckdb.sql("""
        SELECT e.* 
        FROM ms
        LEFT JOIN edges e
            ON ms.src = e.src AND ms.dst = e.dst
        WHERE e.src IS NOT NULL
    """).df()
    assert(res.shape[0] == ms.shape[0])
    social_min, social_max = res["inserted_at"].min(), res["inserted_at"].max()

    ttc = max(online_max, media_max, social_max) - min(online_min, media_min, social_min)
    ttc = ttc.total_seconds()
    print(f"online+media+social: {ttc:.2f}")

if __name__ == "__main__":
    online()
    media()
    social()
    online_media() 
    online_social()
    media_social()
    online_media_social()
