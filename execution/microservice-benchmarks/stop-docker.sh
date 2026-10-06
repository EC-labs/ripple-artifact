#!/usr/bin/env bash

set -euo pipefail

script="$(basename $0)"

USAGE="
Usage: $script <microservice-benchmark> <run-type>

Positional parameters:
    microservice-benchmark: Enumerator for the type of microservice-benchmark
        being executed. Allowed values are 'social-network',
        'media-microservices', 'online-boutique'.
    run-type: Enumerator parameter to describe the type of execution. Allowed
        values are 'internal', and 'external'.

Required environment variables:
    KUBECONFIG: Path to kubeconfig to reach the k8s cluster
    MANIFESTS_DIR: Path to microservice-benchmark manifests directory
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

run_type="$2"
case "$run_type" in
    "internal"|"external")
        ;;
    *)
        printf "invalid <run-type> argument: received ${run_type}\n"
        printf "$USAGE"
        exit 1
esac


ssh.sh k8s-master  "docker compose -f /etc/${microservice_benchmark}/${run_type}.yaml down -v"
ssh.sh k8s-worker1 "docker compose -f /etc/${microservice_benchmark}/${run_type}.yaml down -v"
ssh.sh k8s-worker2 "docker compose -f /etc/${microservice_benchmark}/${run_type}.yaml down -v"


kubectl delete -f "${MANIFESTS_DIR}/${microservice_benchmark}/load.yaml"
