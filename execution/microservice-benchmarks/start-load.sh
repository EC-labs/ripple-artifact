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
    VARS_JSON: Path to host to public and private IPs map
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
host_option=""
case "$run_type" in
    "k8s")
        ;;
    "internal"|"external")
        if [[ "${microservice_benchmark}" == "online-boutique" ]]; then
            frontendIP="$(jq -r --arg node "k8s-master"  '.[$node].publicIP // empty' "$VARS_JSON")"
            host_option="&host=http://${frontendIP}:80"
        else
            frontendIP="$(jq -r --arg node "k8s-worker2" '.[$node].publicIP // empty' "$VARS_JSON")"
            host_option="&host=http://${frontendIP}:3009"
        fi
        ;;
    *)
        printf "invalid <run-type> argument: received ${run_type}\n"
        printf "$USAGE"
        exit 1
esac

kubectl port-forward \
    -n "load-generators-${microservice_benchmark}" \
    svc/locust 8089:8089 >/dev/null 2>&1 &
pf_pid=$!

curl "http://localhost:8089/swarm" \
    --retry-connrefused \
    --connect-timeout 5 \
    --max-time 10 \
    --retry 5 \
    --retry-delay 0 \
    --retry-max-time 40 \
    -H 'content-type: application/x-www-form-urlencoded' \
    --data-raw "user_count=5&spawn_rate=5${host_option}"

kill -SIGTERM "$pf_pid"
