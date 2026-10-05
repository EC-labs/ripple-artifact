#!/usr/bin/env bash

set -euo pipefail

if (( $# != 2 )); then
    echo "Usage: $0 <source> <destination>" >&2
    exit 1
fi

resolve_remote() {
    local arg="$1"

    if [[ "$arg" == *:* ]]; then
        local node="${arg%%:*}"
        local path="${arg#*:}"

        local nodeIP
        nodeIP="$(jq -r --arg node "$node" '.[$node].publicIP // empty' "$VARS_JSON")"

        if [[ -z "$nodeIP" ]]; then
            echo "$node does not exist in vars.json" >&2
            exit 1
        fi

        printf 'root@%s:%s' "$nodeIP" "$path"
    else
        printf '%s' "$arg"
    fi
}

source="$(resolve_remote "$1")"
destination="$(resolve_remote "$2")"

set -x 
exec scp -i "$ED25519" "$source" "$destination"
