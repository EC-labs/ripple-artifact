#!/usr/bin/env bash

set -euo pipefail

script=$(basename "$0")
script_d="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
scripts="${script_d}/../../scripts"
data_d="${script_d}/../../data"

if ! [[ -d "${data_d}" ]]; then
    mkdir "${data_d}"
fi
USAGE="
Usage: $script <microservice-benchmark> <run-type>

Positional parameters:
    microservice-benchmark: Enumerator for the type of microservice-benchmark being executed. Allowed values (social-network, media-microservices, online-boutique).
    run-type: Enumerator parameter to describe the type of execution. Allowed values are 'k8s', 'internal', and 'external'.
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

"${scripts}/ssh.sh" k8s-master 'RUST_LOG=info metric-collector --duckdb-directory /var/lib/prism >/dev/null 2>&1 & disown'
"${scripts}/ssh.sh" k8s-worker1 'RUST_LOG=info metric-collector --duckdb-directory /var/lib/prism >/dev/null 2>&1 & disown'

sleep 10

"${scripts}/ssh.sh" k8s-worker2 "RUST_LOG=info metric-collector --duckdb-directory /var/lib/prism ${bootstrap_option} >/dev/null 2>&1 & disown"

sleep 30

for vm in k8s-master k8s-worker1 k8s-worker2; do
    "${scripts}/ssh.sh" "$vm" 'pkill -TERM metric-collec'
done

sleep 10

for vm in k8s-master k8s-worker1 k8s-worker2; do
    last_file="$("${scripts}/ssh.sh" "$vm" "ls -Art /var/lib/prism | tail -n 1")"
    "${scripts}/scp.sh" "${vm}:/var/lib/prism/${last_file}" "${data_d}"
    prism_files+=("${data_d}/${last_file}")
done

combine-dbs --dbs "${prism_files[0]},${prism_files[1]},${prism_files[2]}" --result-file "${data_d}/k8s-$1.db3"
rm "${prism_files[@]}"
