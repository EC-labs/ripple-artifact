{ pkgs ? import <nixpkgs> {}, stdenv ? pkgs.stdenv }:
let
    docker = pkgs.callPackage ./docker {};
in
{
    inherit (docker) internal external;
    k8s = stdenv.mkDerivation {
        name = "online-boutique-k8s";
        src = ./.;
        dontBuild = true;
        installPhase = ''
            mkdir $out/online-boutique
            cp -r ./k8s $out/online-boutique
        '';
    };
}
