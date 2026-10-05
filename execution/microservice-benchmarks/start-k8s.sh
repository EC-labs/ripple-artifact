#!/usr/bin/env bash

set -euo pipefail

script_d="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"

kubectl kustomize --enable-helm "${script_d}/${microservice_benchmark}/k8s" \
    | kubectl apply -f -
