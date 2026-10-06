{ 
    pkgs ? import <nixpkgs> {},
    stdenv ? pkgs.stdenv,
    rippleScripts,
    kubeconfig
}:
let
    social-network = pkgs.callPackage ./social-network {};
    media-microservices = pkgs.callPackage ./media-microservices {};
    online-boutique = pkgs.callPackage ./online-boutique {};
in
rec {
    manifests = stdenv.mkDerivation {
        name = "manifests";
        dontUnpack = true;
        installPhase = ''
            mkdir -p $out
            cp -r ${social-network.k8s}/social-network $out
            cp -r ${media-microservices.k8s}/media-microservices $out
            cp -r ${online-boutique.k8s}/online-boutique $out
        '';
    };
    scripts = with pkgs; stdenv.mkDerivation {
        name = "execution-scripts";
        dontUnpack = true;
        buildInputs = with pkgs; [
           makeWrapper
           bash
        ];
        installPhase = ''
            mkdir -p $out/bin

            install -Dm555 ${./start-docker.sh} $out/bin/start-docker.sh
            wrapProgram $out/bin/start-docker.sh \
                --set VARS_JSON "${./../../nixos/vars.json}" \
                --set MANIFESTS_DIR "${manifests}" \
                --set KUBECONFIG "${kubeconfig}" \
                --prefix PATH : ${lib.makeBinPath [
                    rippleScripts 
                    coreutils 
                    jq
                    kubectl
                    kubernetes-helm
                ]}


            install -Dm555 ${./start-k8s.sh} $out/bin/start-k8s.sh
            wrapProgram $out/bin/start-k8s.sh \
                --set MANIFESTS_DIR "${manifests}" \
                --set KUBECONFIG "${kubeconfig}" \
                --prefix PATH : ${lib.makeBinPath [
                    coreutils
                    kubectl
                    kubernetes-helm
                ]}

            install -Dm555 ${./start-load.sh} $out/bin/start-load.sh
            wrapProgram $out/bin/start-load.sh \
                --set KUBECONFIG "${kubeconfig}" \
                --set VARS_JSON "${./../../nixos/vars.json}" \
                --prefix PATH : ${lib.makeBinPath [
                    curl
                    coreutils
                    kubectl
                    kubernetes-helm
                    jq
                ]}

            install -Dm555 ${./stop-docker.sh} $out/bin/stop-docker.sh
            wrapProgram $out/bin/stop-docker.sh \
                --set MANIFESTS_DIR "${manifests}" \
                --set KUBECONFIG "${kubeconfig}" \
                --prefix PATH : ${lib.makeBinPath [
                    rippleScripts 
                    coreutils 
                    kubectl
                    kubernetes-helm
                ]}


            install -Dm555 ${./stop-k8s.sh} $out/bin/stop-k8s.sh
            wrapProgram $out/bin/stop-k8s.sh \
                --set MANIFESTS_DIR "${manifests}" \
                --set KUBECONFIG "${kubeconfig}" \
                --prefix PATH : ${lib.makeBinPath [
                    coreutils 
                    kubectl
                    kubernetes-helm
                ]}

        '';
    };
}
