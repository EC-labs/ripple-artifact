{ config, pkgs, inputs, lib, ... }:
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

    dockerSocialNetwork = pkgs.callPackage ../../execution/microservice-benchmarks/social-network {};
    dockerOnlineBoutique = pkgs.callPackage ../../execution/microservice-benchmarks/online-boutique {};
in
{
    imports = [
        "${inputs.nixpkgs}/nixos/modules/virtualisation/amazon-image.nix"
    ];
    environment.systemPackages = [ inputs.prism.outputs.packages.${pkgs.system}.prism ];
    systemd.tmpfiles.rules = [
        "f /run/resolv.conf 0664 root resolvconf -"
    ];

    networking.firewall.extraCommands = ''
        iptables -t filter -I INPUT -s 172.0.0.0/8 -j ACCEPT
    '';

    virtualisation.docker.enable = true;

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

    # Add docker compose experiment files
    environment.etc."social-network/internal.yaml".source = "${dockerSocialNetwork.internal}/compose-${config.services.kubernetes.kubelet.hostname}.yaml";
    environment.etc."social-network/external.yaml".source = "${dockerSocialNetwork.external}/compose-${config.services.kubernetes.kubelet.hostname}.yaml";
    environment.etc."online-boutique/internal.yaml".source = "${dockerOnlineBoutique.internal}/compose-${config.services.kubernetes.kubelet.hostname}.yaml";
    environment.etc."online-boutique/external.yaml".source = "${dockerOnlineBoutique.external}/compose-${config.services.kubernetes.kubelet.hostname}.yaml";

}
