{
    imports = [
        ../modules/base-ami.nix
        ../modules/k8s-master.nix
    ];
    
    services.kubernetes.kubelet.hostname = "k8s-master";
}
