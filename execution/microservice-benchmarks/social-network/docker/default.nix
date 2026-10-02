{ pkgs ? import <nixpkgs> {}}:
with builtins;
let
    vars = fromJSON (readFile ../../../../nixos/vars.json);
    mkDockerCompose = (ipSelector:
        pkgs.stdenv.mkDerivation {
            name = "social-network-docker-${ipSelector}";

            buildInputs = with pkgs; [
                (python3.withPackages (py-pkgs: with py-pkgs; [pyyaml]))
            ];

            src = ./.;

            buildPhase = ''
                python configs-generate.py ${vars."k8s-master"."${ipSelector}"} ${vars."k8s-worker1"."${ipSelector}"} ${vars.k8s-worker2."${ipSelector}"} config-compose/service-config.json
                for vm in k8s-master k8s-worker1 k8s-worker2; do
                    sed -e "s|\$DNS_CONFIG_PATH|$out/dns-config.json|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                    sed -e "s|\$CONFIG_COMPOSE_PATH|$out/config-compose|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                    sed -e "s|\$MEDIA_FRONTEND_PATH|$out/media-frontend|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                    sed -e "s|\$NGINX_WEB_SERVER_COMPOSE_PATH|$out/nginx-web-server-compose|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                    sed -e "s|\$GEN_LUA_PATH|$out/gen-lua|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                    sed -e "s|\$LUA_THRIFT_PATH|$out/lua-thrift|g" < compose-$vm.yaml > compose-$vm.yaml.tmp
                    mv compose-$vm.yaml.tmp compose-$vm.yaml
                done
            '';

            installPhase = ''
                mkdir $out
                cp ./compose-k8s-master.yaml $out/
                cp ./compose-k8s-worker1.yaml $out/
                cp ./compose-k8s-worker2.yaml $out/
                cp ./dns-config.json $out
                cp -r ./config-compose $out
                cp -r ./media-frontend $out
                cp -r ./nginx-web-server-compose $out
                cp -r ./gen-lua $out
                cp -r ./lua-thrift $out
            '';
        }
    );
in
{
    package = {
        internal = mkDockerCompose "privateIP";
        external = mkDockerCompose "publicIP";
    };
}
