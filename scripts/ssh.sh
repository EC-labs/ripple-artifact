#!/usr/bin/env bash

set -euo pipefail

if (( $# < 1 )); then
    echo "Usage: $0 <node> [command...]" >&2
    exit 1
fi

node="$1"
shift

nodeIP="$(jq -r --arg node "$node" '.[$node].publicIP // empty' nixos/vars.json)"

if [[ -z "$nodeIP" ]]; then
    echo "$node does not exist in vars.json" >&2
    exit 1
fi

set -x
exec ssh -o LogLevel=ERROR -i ./nixos/secrets/id_ed25519 "root@$nodeIP" "$@"
