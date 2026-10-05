#!/usr/bin/env bash

set -euo pipefail

script=$(basename "$0")
script_d="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"

if ! [[ -d "${DATA_DIR}" ]]; then
    mkdir "${DATA_DIR}"
fi
USAGE="
Usage: $script <microservice-benchmark> <run-type>

Positional parameters:
    microservice-benchmark: Enumerator for the type of microservice-benchmark
        being executed. Allowed values are 'social-network',
        'media-microservices', 'online-boutique'.
    run-type: Enumerator parameter to describe the type of execution. Allowed
        values are 'k8s', 'internal', and 'external'.
"

if (( $# != 2 )); then
    printf "${script} expects exactly 2 positional arguments\n"
    printf "$USAGE"
    exit 1
fi

microservice_benchmark="$1"
case "$microservice_benchmark" in
    "online-boutique"|"social-network"|"media-microservices")
        ;;
    *)
        printf "invalid <microservice-benchmark> argument: received ${microservice_benchmark}\n"
        printf "$USAGE"
        exit 1
esac

bootstrap_option=""
run_type="$2"
case "$run_type" in
    "k8s")
        bootstrap_option="--containerd-container-filters \"labels.io.kubernetes.pod.namespace==${microservice_benchmark}\""
        ;;
    "internal"|"external")
        bootstrap_option="--docker-container-names \".*${microservice_benchmark}.*\""
        ;;
    *)
        printf "invalid <run-type> argument: received ${run_type}\n"
        printf "$USAGE"
        exit 1
esac

ssh.sh k8s-master 'RUST_LOG=info metric-collector --duckdb-directory /var/lib/prism >/dev/null 2>&1 & disown'
ssh.sh k8s-worker1 'RUST_LOG=info metric-collector --duckdb-directory /var/lib/prism >/dev/null 2>&1 & disown'

sleep 10

ssh.sh k8s-worker2 "RUST_LOG=info metric-collector --duckdb-directory /var/lib/prism ${bootstrap_option} >/dev/null 2>&1 & disown"

sleep 30

for vm in k8s-master k8s-worker1 k8s-worker2; do
    ssh.sh "$vm" 'pkill -TERM metric-collec'
done

sleep 10

for vm in k8s-master k8s-worker1 k8s-worker2; do
    last_file="$(ssh.sh "$vm" "ls -Art /var/lib/prism | tail -n 1")"
    single-scp.sh "${vm}:/var/lib/prism/${last_file}" "${DATA_DIR}"
    prism_files+=("${DATA_DIR}/${last_file}")
done

combine-dbs --dbs "${prism_files[0]},${prism_files[1]},${prism_files[2]}" --result-file "${DATA_DIR}/${run_type}-${microservice_benchmark}.db3"
rm "${prism_files[@]}"
