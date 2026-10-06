{ pkgs ? import <nixpkgs> {}, stdenv ? pkgs.stdenv, lib ? pkgs.lib }:
let
    docker = pkgs.callPackage ./docker {};
in
{
    inherit (docker) internal external;
    k8s = stdenv.mkDerivation {
        name = "media-microservices-k8s";
        src = ./.;
        dontBuild = true;
        buildInputs = with pkgs; [ kubectl kubernetes-helm ];
        outputHashAlgo = "sha256";
        outputHashMode = "recursive";
        # outputHash = lib.fakeHash;
        outputHash = "sha256-CShOkYY1gDoudoxO7jMZzOI0ypj2ReG0IUUK6WlgMi8=";

        installPhase = ''
            mkdir -p $out/media-microservices

            kubectl kustomize --enable-helm ./k8s/application > $out/media-microservices/application.yaml
            kubectl kustomize --enable-helm ./k8s/load > $out/media-microservices/load.yaml

        '';
    };
}
