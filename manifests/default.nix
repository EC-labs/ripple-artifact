{ pkgs, ... }:
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
{
    devShell = pkgs.mkShell {
        packages = with pkgs; [
            kubectl
            kubernetes-helm
            k9s
        ];
        KUBECONFIG = kubeconfig;
    };
}
