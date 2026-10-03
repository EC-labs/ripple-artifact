WITH
  pid_sock AS (
    SELECT DISTINCT machine_id, pid, inode_id
    FROM vfs
    LEFT JOIN linux_consts lc ON vfs.fs_magic = lc.value and lc.const_type = 'fs_magic'
    WHERE lc.const_name = 'SOCKFS_MAGIC'
        AND true
  ),

  tcp_sock_map AS (
      SELECT DISTINCT
        CASE WHEN (local_machine_id, local_inode_id) <= (remote_machine_id, remote_inode_id) THEN local_machine_id ELSE remote_machine_id END AS machine1,
        CASE WHEN (local_machine_id, local_inode_id) <= (remote_machine_id, remote_inode_id) THEN local_inode_id   ELSE remote_inode_id   END AS sock1,
        CASE WHEN (local_machine_id, local_inode_id) > (remote_machine_id, remote_inode_id)  THEN local_machine_id ELSE remote_machine_id END AS machine2,
        CASE WHEN (local_machine_id, local_inode_id) > (remote_machine_id, remote_inode_id)  THEN local_inode_id   ELSE remote_inode_id   END AS sock2,
      FROM tcp_discovery
      WHERE remote_machine_id <> 0
  ),
  -- enhance tcp socket map data with information on the pids interacting with the socket
  tcp_sock_pids AS (
    SELECT
      ts.machine1 lmachine, pid1.pid lpid, ts.sock1,
      ts.machine2 rmachine, pid2.pid rpid, ts.sock2
    FROM tcp_sock_map ts
    INNER JOIN pid_sock pid1 ON ts.machine1 = pid1.machine_id and ts.sock1 = pid1.inode_id
    INNER JOIN pid_sock pid2 ON ts.machine2 = pid2.machine_id and ts.sock2 = pid2.inode_id
  ),
  -- get the number of tcp connections between 2 pids
  pid_map_tcp_connections AS (
    SELECT
        CASE WHEN (lmachine, lpid) <= (rmachine, rpid) THEN lmachine ELSE rmachine END AS machine1,
        CASE WHEN (lmachine, lpid) <= (rmachine, rpid) THEN lpid     ELSE rpid     END AS pid1,
        CASE WHEN (lmachine, lpid) >  (rmachine, rpid) THEN lmachine ELSE rmachine END AS machine2,
        CASE WHEN (lmachine, lpid) >  (rmachine, rpid) THEN lpid     ELSE rpid     END AS pid2,
        COUNT(*) connections
    FROM tcp_sock_pids
    GROUP BY 1,2,3,4
  ),

  pid_connections AS (
    SELECT *, 'tcp' as connection_type FROM pid_map_tcp_connections
  ),
  service_context AS (
    SELECT DISTINCT
        COALESCE(k.pod_name, d.name, tv.comm) AS service_name,
        COALESCE(pc.machine_id, tv.machine_id) machine_id,
        COALESCE(pc.pid, tv.pid) pid,
        k.namespace,
        pc.exe
    FROM process_context pc
    LEFT JOIN docker d USING (machine_id, cgroup)
    LEFT JOIN k8s k USING(machine_id, cgroup)
    RIGHT JOIN (
        SELECT DISTINCT machine_id, pid, tid, comm FROM (
            SELECT
                machine_id,
                pid,
                tid,
                comm,
                ROW_NUMBER() OVER(PARTITION BY machine_id, pid, tid ORDER BY ts DESC) AS rn
            FROM (
                SELECT
                    machine_id, pid, tid, comm, max(ts) AS ts
                FROM taskstats
                WHERE pid = tid
                GROUP BY machine_id, pid, tid, comm
            )
        )
        WHERE rn = 1
    ) tv
        ON (pc.pid = tv.pid) and (pc.pid = tv.tid) and (pc.machine_id = tv.machine_id)
  )
SELECT DISTINCT
    machine1, pid1, lsvc.service_name service1,
    machine2, pid2, rsvc.service_name service2
FROM pid_connections pc
LEFT JOIN service_context lsvc
    ON lsvc.machine_id = pc.machine1 AND lsvc.pid = pc.pid1
LEFT JOIN service_context rsvc
    ON rsvc.machine_id = pc.machine2 AND rsvc.pid = pc.pid2
WHERE
    -- FILTERS
    -- (service1 LIKE '/media-microservices%' OR service2 LIKE '/media-microservices%')
    -- (lsvc.namespace = 'media-microservices' or rsvc.namespace = 'media-microservices')
    {{ service_filter }}
;
