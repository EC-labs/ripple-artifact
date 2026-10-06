{ pkgs ? import <nixpkgs> {} }:
let
    social-network = pkgs.callPackage ./social-network {};
    media-microservices = pkgs.callPackage ./media-microservices {};
    online-boutique = pkgs.callPackage ./online-boutique {};
in
{
    manifests = pkgs.symlinkJoin {
        name = "manifests";
        paths = [
            social-network.k8s
            media-microservices.k8s
            online-boutique.k8s
        ];
    };
}
