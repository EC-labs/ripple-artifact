{ inputs, lib, ... }:
with builtins; with lib;
let
    # hosts = map () (attrNames (import ../vars.nix));
    vars = fromJSON (readFile ../vars.json);

    hosts = listToAttrs (mapAttrsToList
        (name: host: {
            name = host.privateIP;
            value = [ name ];
        })
        vars
    );
in
{
    imports = [
        "${inputs.nixpkgs}/nixos/modules/virtualisation/amazon-image.nix"
    ];

    networking.hosts = hosts;

    services.openssh = {
        enable = true;
        hostKeys = [{
            path = "/etc/ssh/ssh_host_ed25519_key";
            type = "ed25519";
        }];
    };

    # system.hostPlatform = "x86_64-linux";
    system.stateVersion = "25.11";

    nix.settings.experimental-features = [ "flakes" "nix-command" ];

}
