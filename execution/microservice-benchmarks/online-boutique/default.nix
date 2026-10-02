{ pkgs ? import <nixpkgs> {} }:
let
    docker = pkgs.callPackage ./docker {};
in
{
    inherit (docker) internal external;
}
