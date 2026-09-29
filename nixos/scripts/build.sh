
set -euo pipefail

if [[ $# -ne 1 ]]; then
    exit 1    
fi

node="$1"
nodeIP="$(jq -r '."'"$node"'".publicIP' < vars.json)"

if [[ "$nodeIP" =~ "null" ]]; then
    echo "$node does not exist in vars.json"
    exit 1
fi

set -o xtrace
nixos-rebuild --flake ".#${node}" --target-host "root@${nodeIP}" switch
