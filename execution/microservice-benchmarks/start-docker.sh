#!/usr/bin/env bash

set -euo pipefail

script="$(basename $0)"
script_d="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"

USAGE="
Usage: $script <microservice-benchmark> <run-type>

Positional parameters:
    microservice-benchmark: Enumerator for the type of microservice-benchmark
        being executed. Allowed values are 'social-network',
        'media-microservices', 'online-boutique'.
    run-type: Enumerator parameter to describe the type of execution. Allowed
        values are 'internal', and 'external'.
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

ssh.sh k8s-master  "docker compose -f /etc/${microservice_benchmark}/${run_type}.yaml up -d"
ssh.sh k8s-worker1 "docker compose -f /etc/${microservice_benchmark}/${run_type}.yaml up -d"
ssh.sh k8s-worker2 "docker compose -f /etc/${microservice_benchmark}/${run_type}.yaml up -d"


case "$microservice_benchmark" in
    "media-microservices")
        sleep 10
        worker2IP="$(jq -r --arg node "k8s-worker2" '.[$node].publicIP // empty' "$VARS_JSON")"
        ssh.sh k8s-worker2 "docker run --rm --name init -e PYTHONUNBUFFERED=1 dclandau/initmediamicroservices:bd75677 ${worker2IP}:3009"
        ;;
    "social-network")
        sleep 10
        worker2IP="$(jq -r --arg node "k8s-worker2" '.[$node].publicIP // empty' "$VARS_JSON")"
        ssh.sh k8s-worker2 "docker run --rm --name init -e PYTHONUNBUFFERED=1 dclandau/initsocialgraph:4181ebd --ip ${worker2IP} --port 3009"
        ;;
    *)
        ;;
esac

kubectl kustomize --enable-helm "${script_d}/${microservice_benchmark}/k8s/load" \
    | kubectl apply -f -

sleep 10
