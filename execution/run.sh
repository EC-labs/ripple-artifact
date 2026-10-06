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

run_type="$2"
case "$run_type" in
    "k8s")
        start-k8s.sh "${microservice_benchmark}"
        ;;
    "internal"|"external")
        start-docker.sh "${microservice_benchmark}" "${run_type}"
        ;;
    *)
        printf "invalid <run-type> argument: received ${run_type}\n"
        printf "$USAGE"
        exit 1
esac

start-load.sh "${microservice_benchmark}" "${run_type}"
start-ripple.sh "${microservice_benchmark}" "${run_type}"

case "$run_type" in
    "k8s")
        stop-k8s.sh "${microservice_benchmark}"
        ;;
    "internal"|"external")
        stop-docker.sh "${microservice_benchmark}" "${run_type}"
        ;;
esac
