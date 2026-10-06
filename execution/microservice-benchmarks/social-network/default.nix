{ pkgs ? import <nixpkgs> {}, stdenv ? pkgs.stdenv, lib ? pkgs.lib }:
let
    docker = pkgs.callPackage ./docker {};
in
{
    inherit (docker) internal external;
    k8s = stdenv.mkDerivation {
        name = "social-network-k8s";
        src = ./.;
        dontBuild = true;
        buildInputs = with pkgs; [ kubectl kubernetes-helm ];
        outputHashAlgo = "sha256";
        outputHashMode = "recursive";
        # outputHash = lib.fakeHash;
        outputHash = "sha256-RhyTSc5gBbyV5LmzwkGbEIKXkx/WivJAkKN4ff5T6Ts=";

        installPhase = ''
            mkdir -p $out/social-network

            kubectl kustomize --enable-helm ./k8s/application > $out/social-network/application.yaml
            kubectl kustomize --enable-helm ./k8s/load > $out/social-network/load.yaml
        '';
    };
}
