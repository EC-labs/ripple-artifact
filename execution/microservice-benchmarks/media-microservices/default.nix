{ pkgs ? import <nixpkgs> {}, stdenv ? pkgs.stdenv }:
let
    docker = pkgs.callPackage ./docker {};
in
{
    inherit (docker) internal external;
    k8s = stdenv.mkDerivation {
        name = "media-microservices-k8s";
        src = ./.;
        dontBuild = true;
        installPhase = ''
            mkdir $out/media-microservices
            cp -r ./k8s $out/media-microservices/
        '';
    };
}
