#! bash

set -euo pipefail

if (( $# != 1 )); then
    echo "Usage: $0 <node>" >&2
    exit 1
fi

node="$1"

nodeIP="$(jq -r --arg node "$node" '.[$node].publicIP // empty' "$VARS_JSON")"

if [[ -z "$nodeIP" ]]; then
    echo "$node does not exist in vars.json" >&2
    exit 1
fi

export NIX_SSHOPTS="-i ${ED25519}";
exec nixos-rebuild \
    --flake ".#${node}" \
    --target-host "root@${nodeIP}" \
    switch
