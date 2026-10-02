{ pkgs ? import <nixpkgs> {}}:
with builtins;
let
    vars = fromJSON (readFile ../../../../nixos/vars.json);
    mkDockerOnlineBoutique = (ipSelector:
        pkgs.stdenv.mkDerivation {
            name = "online-boutique-docker-${ipSelector}";

            buildInputs = with pkgs; [
                (python3.withPackages (py-pkgs: with py-pkgs; [pyyaml]))
            ];

            src = ./.;
            buildPhase = ''
                python configs-generate.py ${vars."k8s-master"."${ipSelector}"} ${vars."k8s-worker1"."${ipSelector}"} ${vars.k8s-worker2."${ipSelector}"}
                for vm in k8s-master k8s-worker1 k8s-worker2; do
                    sed -e "s|\$DNS_CONFIG_PATH|$out/dns-config.json|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                done
            '';

            installPhase = ''
                mkdir $out
                cp ./compose-k8s-master.yaml $out/
                cp ./compose-k8s-worker1.yaml $out/
                cp ./compose-k8s-worker2.yaml $out/
                cp ./dns-config.json $out
            '';
        }
    );
in
{
    internal = mkDockerOnlineBoutique "privateIP";
    external = mkDockerOnlineBoutique "publicIP";
}
