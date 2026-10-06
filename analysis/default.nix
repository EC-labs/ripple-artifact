{ pkgs ? import <nixpkgs> {}, stdenv ? pkgs.stdenv }:
{
    devShell = pkgs.mkShell {
        packages = [];
    };
    package = stdenv.mkDerivation {
        name = "ripple-analysis";
        dontUnpack = true;
        dontBuild = true;
        buildInputs = with pkgs; [
            (python3.withPackages (py-pkgs: with py-pkgs; [
                jinja2 
                duckdb 
                numpy 
                pandas 
            ]))
            makeWrapper
        ];

        installPhase = ''
            mkdir -p $out/bin
            cp ${./service-map.sql} $out/service-map.sql
            cp -r ${./gt} $out/gt

            install -Dm555 ${./ripple.py} $out/bin/ripple-analysis;
            wrapProgram $out/bin/ripple-analysis \
                --set SERVICE_MAP_QUERY $out/service-map.sql \
                --set GROUND_TRUTH $out/gt
        '';
    };
}
