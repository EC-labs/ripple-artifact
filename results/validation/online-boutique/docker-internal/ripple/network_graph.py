import os
import duckdb
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict
from matplotlib.patches import Wedge
from pathlib import Path

machine_color = {
    1: "#1f77b4",
    2: "#ff7f0e",
    3: "#2ca02c",
    -1: "lightgray"
}

SERVICES = [
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
    "docker"
]

def draw_network(edges_df: pd.DataFrame, script_dir: Path):
    # Map services to machines
    machine_map = {}
    for _, row in edges_df.iterrows():
        machine_map[row['src']] = row['src_machine']
        machine_map[row['dst']] = row['dst_machine']

    # Group services by machine
    machine_to_services = defaultdict(list)
    for service, machine in machine_map.items():
        machine_to_services[machine].append(service)

    # Flatten services in order by machine
    clustered_services = []
    machine_angle_ranges = {}  # machine_id -> (start_idx, end_idx)
    angle_index = 0
    for machine in sorted(machine_to_services):
        services = sorted(set(machine_to_services[machine]))
        clustered_services.extend(services)
        machine_angle_ranges[machine] = (angle_index, angle_index + len(services) - 1)
        angle_index += len(services)

    # Assign positions on circle
    n = len(clustered_services)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pos = {}
    for i, service in enumerate(clustered_services):
        angle = angles[i]
        pos[service] = (np.cos(angle), np.sin(angle))

    # Build graph
    G = nx.Graph()
    edges = list(zip(edges_df['src'], edges_df['dst']))
    G.add_edges_from(edges)

    # Plot setup
    fig, ax = plt.subplots(figsize=(6, 6))

    # Parameters for node radius and slice padding
    node_radius = 0.08  # approximate node circle radius (half sqrt of node size)
    slice_outer_radius = 1.07  # slightly larger than node radius 1
    slice_inner_radius = 0  # small hole in the center

    # Draw filled pie slices for each machine
    for machine, (start_idx, end_idx) in machine_angle_ranges.items():
        theta_start = np.degrees(angles[start_idx]) - 6  # small padding on each side
        theta_end = np.degrees(angles[end_idx]) + 6
        # Handle wrap-around if needed
        if theta_end < theta_start:
            theta_end += 360

        # Draw the wedge (filled arc)
        wedge = Wedge(center=(0, 0),
                      r=slice_outer_radius,
                      theta1=theta_start,
                      theta2=theta_end,
                      width=slice_outer_radius - slice_inner_radius,
                      facecolor=machine_color[machine],
                      alpha=0.3,
                      edgecolor='gray',
                      linestyle="solid" if machine != -1 else "dashed",
                      linewidth=1.5)
        ax.add_patch(wedge)

        # Label in the middle of the arc, closer to the center
        mid_angle = (angles[start_idx] + angles[end_idx]) / 2
        label_radius = slice_inner_radius + (slice_outer_radius - slice_inner_radius) / 2
        label_x = label_radius * np.cos(mid_angle)
        label_y = label_radius * np.sin(mid_angle)
        ax.text(label_x, label_y, machine if machine != -1 else "?",
                fontsize=20, fontweight='bold',
                ha='center', va='center', color='gray')

    # Draw edges and nodes on top of slices
    # Separate edges by machine status
    intra_edges = []
    cross_or_unknown_edges = []

    for _, row in edges_df.iterrows():
        src = row['src']
        dst = row['dst']
        src_machine = row['src_machine']
        dst_machine = row['dst_machine']

        if src_machine != -1:
            intra_edges.append((src, dst))
        else:
            cross_or_unknown_edges.append((src, dst))

    # Draw intra-machine edges (solid)
    nx.draw_networkx_edges(G, pos, edgelist=intra_edges, ax=ax, width=1.5, style="solid", edge_color="black")

    # Draw cross-machine or unknown-machine edges (dashed)
    nx.draw_networkx_edges(G, pos, edgelist=cross_or_unknown_edges, ax=ax, width=1.5, style="dashed", edge_color="gray")

    # Split nodes by machine == -1
    nodes_unknown = [node for node in G.nodes if machine_map.get(node, -1) == -1]
    nodes_known = [node for node in G.nodes if machine_map.get(node, -1) != -1]

    # Draw known machine nodes (solid border)
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=nodes_known,
                           node_size=70, node_color="white", edgecolors="black", linewidths=1.2)

    # Manually draw nodes with machine == -1 using dashed edge
    for node in nodes_unknown:
        x, y = pos[node]
        circle = plt.Circle((x, y), radius=0.04,  # adjust radius as needed
                            facecolor='white',
                            edgecolor='black',
                            linewidth=1.2,
                            linestyle='dashed',
                            zorder=3)
        ax.add_patch(circle)

    # Radial labels outside nodes
    for node, (x, y) in pos.items():
        angle = np.arctan2(y, x)
        label_radius = 1.1  # outside slice radius now
        label_x = label_radius * np.cos(angle)
        label_y = label_radius * np.sin(angle)
        rotation = np.degrees(angle)
        if rotation < -90 or rotation > 90:
            rotation += 180
            ha = 'right'
        else:
            ha = 'left'
        ax.text(label_x, label_y, node, fontsize=9, rotation=rotation,
                ha=ha, va='center', rotation_mode='anchor')

    # Final plot tweaks
    ax.set_aspect('equal')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(script_dir.joinpath("network_graph.pdf"))
    plt.show()

def part_of_app(name):
    for service in SERVICES:
        if service in name:
            return service if service != "docker" else "docker-proxy"
    return None

def ripple_connections(dir: Path):
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

    table = edges.loc[:, ["lpid", "lcgroup", "local_machine_id", "rpid", "rcgroup", "remote_machine_id"]].rename(columns={"lcgroup": "src", "rcgroup": "dst", "local_machine_id": "src_machine", "remote_machine_id": "dst_machine"}).drop_duplicates()
    print(table)

    edges = []
    for (_, edge) in table.iterrows():
        
        src, dst = edge["src"], edge["dst"]
        src, dst = part_of_app(src), part_of_app(dst)
        if src is None or dst is None:
            continue
        src_machine, dst_machine = edge["src_machine"], edge["dst_machine"]
        spid, dpid = edge["lpid"], edge["rpid"]
        edges.append([spid, src, src_machine, dpid, dst, dst_machine])
        edges.append([dpid, dst, dst_machine, spid, src, src_machine])

    spids, srcs, src_machines, dpids, dsts, dst_machines = zip(*edges)
    return pd.DataFrame({"spid": spids, "src": srcs, "src_machine": src_machines, "dpid": dpids, "dst": dsts, "dst_machine": dst_machines})\
        .drop_duplicates()\
        .sort_values(by=["src", "dst"]).reset_index(drop=True)

def missing_connections(ripple_post: Path, gt: Path):
    ripple = pd.read_csv(ripple_post)
    gt = pd.read_csv(gt)
    df_diff = gt.merge(ripple, how='outer', indicator=True)
    missing = df_diff[df_diff['_merge'] == 'left_only'].loc[:, ["src", "dst"]]
    missing["src_machine"] = -1
    missing["dst_machine"] = -1
    return missing
    # Optional: drop the '_merge' column if not needed
    # df_exclusive = df_exclusive.drop(columns=['_merge'])


if __name__ == "__main__":
    script_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    edges_df = ripple_connections(Path(script_dir))
    print(edges_df)
    edges_df["src"] = edges_df.apply(lambda row: row['src'] + (("\n" + str(row["spid"])) if row["src"] == "docker-proxy" else ""), axis=1)
    edges_df["dst"] = edges_df.apply(lambda row: row['dst'] + (("\n" + str(row["dpid"])) if row["dst"] == "docker-proxy" else ""), axis=1)
    print(edges_df)
    draw_network(edges_df, script_dir)
