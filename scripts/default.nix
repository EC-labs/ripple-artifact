{ pkgs ? import <nixpkgs> {} }:
{
    packages = {
        combine-dbs = pkgs.stdenv.mkDerivation {
            name = "combined-dbs";
            dontUnpack = true;
            
            buildInputs = with pkgs; [
                (python3.withPackages (py-pkgs: with py-pkgs; [ click duckdb ]))
            ];

            installPhase = ''
                install -Dm555 ${./combinedbs.py} $out/bin/combine-dbs
            '';
        };
    };
}
