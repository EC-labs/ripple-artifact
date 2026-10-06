{ pkgs ? import <nixpkgs> {} }:
{
    devShell = pkgs.mkShell {
        packages = with pkgs; [
            terraform
            awscli
        ];
    };
}
