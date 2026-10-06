{ pkgs, lib, stdenv, scripts, analysis }:
with builtins;
let
    masterPublicIP = (fromJSON (readFile ../nixos/vars.json))."k8s-master".publicIP;
    kubeconfig = pkgs.writeText "cluster-admin-kubeconfig" (
      builtins.toJSON {
        apiVersion = "v1";
        kind = "Config";
        clusters = [
          {
            name = "local";
            cluster.certificate-authority = ../nixos/secrets/root-ca.pem;
            cluster.server = "https://${masterPublicIP}:6443";
          }
        ];
        users = [
          {
            name = "cluster-admin";
            user = {
              client-certificate = ../nixos/secrets/cluster-admin.pem;
              client-key = ../nixos/secrets/cluster-admin-key.pem;
            };
          }
        ];
        contexts = [
          {
            context = {
              cluster = "local";
              user = "cluster-admin";
            };
            name = "local";
          }
        ];
        current-context = "local";
      }
    );
in
rec {
    devShell = pkgs.mkShell {
        packages = with pkgs; [
            kubectl
            kubernetes-helm
            k9s
            scripts
            packages.microservice-benchmarks.scripts
            jq
        ];
        KUBECONFIG = kubeconfig;
        MANIFESTS_DIR = "${packages.microservice-benchmarks.manifests}";
        VARS_JSON = "${./../nixos/vars.json}";
    };
    packages = {
        ripple = stdenv.mkDerivation {
            name = "ripple-distributed";
            dontUnpack = true;
            buildInputs = with pkgs; [ 
                makeWrapper
                bash
                scripts
            ];
            installPhase = ''
                mkdir $out
                install -Dm555 ${./ripple/start-ripple.sh} $out/bin/start-ripple.sh
                wrapProgram $out/bin/start-ripple.sh --prefix PATH : ${lib.makeBinPath [ scripts ]}
            '';
        };
        microservice-benchmarks = pkgs.callPackage ./microservice-benchmarks {
            inherit kubeconfig; 
            rippleScripts = scripts;
        };
        run = with pkgs; stdenv.mkDerivation {
            name = "run";
            dontUnpack = true;
            buildInputs = [
                makeWrapper
                bash
            ];
            installPhase = ''
                mkdir $out
                install -Dm555 ${./run.sh} $out/bin/run.sh
                wrapProgram $out/bin/run.sh --prefix PATH : "${lib.makeBinPath [
                    packages.microservice-benchmarks.scripts 
                    packages.ripple
                    coreutils
                    analysis
                ]}"
            '';
        };
    };
}
