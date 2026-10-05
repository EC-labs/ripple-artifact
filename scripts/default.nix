{ pkgs ? import <nixpkgs> {}, lib ? pkgs.lib }:
rec {
    default = pkgs.symlinkJoin {
        name = "scripts";
        paths = [
            combine-dbs
            wrapped-ssh
            wrapped-scp
            wrapped-nixos-rebuild
        ];
    };
    combine-dbs = pkgs.stdenv.mkDerivation {
        name = "combine-dbs";
        dontUnpack = true;
        
        buildInputs = with pkgs; [
            (python3.withPackages (py-pkgs: with py-pkgs; [ click duckdb ]))
        ];

        installPhase = ''
            install -Dm555 ${./combinedbs.py} $out/bin/combine-dbs
        ''; 
    };
    wrapped-ssh = pkgs.stdenv.mkDerivation {
        name = "ssh.sh";
        dontUnpack = true;
        
        buildInputs = with pkgs; [
            bash 
            makeWrapper
        ];

        installPhase = ''
            install -Dm555 ${./ssh.sh} $out/bin/ssh.sh
            wrapProgram $out/bin/ssh.sh \
                --prefix PATH : ${lib.makeBinPath [ pkgs.openssh pkgs.jq ]} \
                --set VARS_JSON ${../nixos/vars.json} \
                --set ED25519 ${../nixos/secrets/id_ed25519}
        '';
    };
    wrapped-scp = pkgs.stdenv.mkDerivation {
        name = "single-scp.sh";
        dontUnpack = true;
        
        buildInputs = with pkgs; [
            bash 
            makeWrapper
        ];

        installPhase = ''
            install -Dm555 ${./single-scp.sh} $out/bin/single-scp.sh
            wrapProgram $out/bin/single-scp.sh \
                --prefix PATH : ${lib.makeBinPath [ pkgs.openssh pkgs.jq ]} \
                --set VARS_JSON ${../nixos/vars.json} \
                --set ED25519 ${../nixos/secrets/id_ed25519}
        '';
    };
    wrapped-nixos-rebuild = pkgs.stdenv.mkDerivation {
        name = "nixos-rebuild.sh";
        dontUnpack = true;
        
        buildInputs = with pkgs; [
            bash 
            makeWrapper
        ];

        installPhase = ''
            install -Dm555 ${./nixos-rebuild.sh} $out/bin/nixos-rebuild.sh
            wrapProgram $out/bin/nixos-rebuild.sh \
                --prefix PATH : ${lib.makeBinPath [ pkgs.openssh pkgs.nixos-rebuild pkgs.jq ]} \
                --set VARS_JSON ${../nixos/vars.json} \
                --set ED25519 ${../nixos/secrets/id_ed25519}
        '';
    };
}
