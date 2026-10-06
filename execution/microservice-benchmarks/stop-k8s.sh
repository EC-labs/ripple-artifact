#!/usr/bin/env bash

set -euo pipefail

script="$(basename $0)"

USAGE="
Usage: $script <microservice-benchmark>

Positional parameters:
    microservice-benchmark: Enumerator for the type of microservice-benchmark
        being executed. Allowed values are 'social-network',
        'media-microservices', 'online-boutique'.

Required environment variables:
    KUBECONFIG: Path to kubeconfig to reach the k8s cluster
    MANIFESTS_DIR: Path to microservice-benchmark manifests directory
"

microservice_benchmark="$1"
case "$microservice_benchmark" in
    "online-boutique"|"social-network"|"media-microservices")
        ;;
    *)
        printf "invalid <microservice-benchmark> argument: received ${microservice_benchmark}\n"
        printf "$USAGE"
        exit 1
esac


kubectl delete -f "${MANIFESTS_DIR}/${microservice_benchmark}"
