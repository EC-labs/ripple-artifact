{ pkgs ? import <nixpkgs> {}, stdenv ? pkgs.stdenv }:
let
    docker = pkgs.callPackage ./docker {};
in
{
    inherit (docker) internal external;
    k8s = stdenv.mkDerivation {
        name = "social-network-k8s";
        src = ./.;
        dontBuild = true;
        installPhase = ''
            mkdir $out/social-network
            cp -r ./k8s $out/social-network
        '';
    };
}
