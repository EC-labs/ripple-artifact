{ pkgs ? import <nixpkgs> {}}:
with builtins;
let
    vars = fromJSON (readFile ../../../../nixos/vars.json);
    mkDockerCompose = (ipSelector:
        pkgs.stdenv.mkDerivation {
            name = "media-microservices-docker-${ipSelector}";

            buildInputs = with pkgs; [
                (python3.withPackages (py-pkgs: with py-pkgs; [pyyaml]))
            ];

            src = ./.;

            buildPhase = ''
                python configs-generate.py ${vars."k8s-master"."${ipSelector}"} ${vars."k8s-worker1"."${ipSelector}"} ${vars.k8s-worker2."${ipSelector}"} compose-service-config.json
                for vm in k8s-master k8s-worker1 k8s-worker2; do
                    sed -e "s|\$DNS_CONFIG_PATH|$out/dns-config.json|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                    sed -e "s|\$COMPOSE_SERVICE_CONFIG_PATH|$out/compose-service-config.json|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                    sed -e "s|\$NGINX_WEB_SERVER_DISTRIBUTED_DOCKER_PATH|$out/nginx-web-server-distributed-docker|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                    sed -e "s|\$GEN_LUA_PATH|$out/gen-lua|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                done
            '';

            installPhase = ''
                mkdir $out
                cp ./compose-k8s-master.yaml $out/
                cp ./compose-k8s-worker1.yaml $out/
                cp ./compose-k8s-worker2.yaml $out/
                cp ./dns-config.json $out
                cp ./compose-service-config.json $out
                cp -r ./nginx-web-server-distributed-docker $out
                cp -r ./gen-lua $out
            '';
        }
    );
in
{
    internal = mkDockerCompose "privateIP";
    external = mkDockerCompose "publicIP";
}
