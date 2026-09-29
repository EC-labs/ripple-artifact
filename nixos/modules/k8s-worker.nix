{ config, kubeletHostName, ... }: 
{
    imports = [ ./base-ami.nix ];

    services.kubernetes = {
        roles = [ "node" ];
        masterAddress = "k8s-master";
        clusterCidr = "10.42.0.0/16";
        apiserver.serviceClusterIpRange = "10.43.0.0/16";

        caFile = "${config.services.kubernetes.secretsPath}/ca.pem";
        pki = {
            enable = true;
            genCfsslCACert = false;
            genCfsslAPIToken = false;
        };

        kubelet = {
            hostname = kubeletHostName;
            extraOpts = "--fail-swap-on=false";
            kubeconfig.server = "https://k8s-master:6443";
        };
    };

    systemd.tmpfiles.rules = [
    #    Type | Destination                                              | Mode | User  | Group  | Age | Source
        "C      ${config.services.kubernetes.pki.caCertPathPrefix}.pem     0600   root    root     -     ${../secrets/root-ca.pem}"
        "C      ${config.services.cfssl.dataDir}/apitoken.secret           0600   root    root     -     ${../secrets/apitoken}"
    ];

    # For some reason, there is an issue when the SANs have colon's in their 
    # names, e.g., system:node:alcaraz. This led to requests to sign a 
    # certificates without the extra SANs. However, on re-inspection, certmgr 
    # would identify this mismatch and ask to sign another certificate, again
    # without the SAN. Ultimately, the repetition of this cycle caused kubelet
    # and the kube-apiserver to restart, and specified on the certmgr's 
    # configuration file.
    services.certmgr.specs.kubeProxyClient.request.hosts = [];
    services.certmgr.specs.kubeletClient.request.hosts = [];

    networking.firewall.allowedTCPPorts = [ 
        10250 # cadvisor
        9100 # node-exporter
    ];
}
