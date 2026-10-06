{ pkgs ? import <nixpkgs> {}, stdenv ? pkgs.stdenv, lib ? pkgs.lib }:
let
    docker = pkgs.callPackage ./docker {};
in
{
    inherit (docker) internal external;
    k8s = stdenv.mkDerivation {
        name = "online-boutique-k8s";
        src = ./.;
        dontBuild = true;
        buildInputs = with pkgs; [ kubectl kubernetes-helm ];
        outputHashAlgo = "sha256";
        outputHashMode = "recursive";
        # outputHash = lib.fakeHash;
        outputHash = "sha256-fbm67UYsff8KeftoQceu1VC+aswgOKIFFlbm7o5bG7Y=";

        installPhase = ''
            mkdir -p $out/online-boutique

            kubectl kustomize --enable-helm ./k8s/application > $out/online-boutique/application.yaml
            kubectl kustomize --enable-helm ./k8s/load > $out/online-boutique/load.yaml
        '';
    };
}
