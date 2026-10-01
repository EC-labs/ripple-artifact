{
    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
    };
    outputs = { self, nixpkgs }@inputs:
        let 
            system = "x86_64-linux";
            pkgs = import nixpkgs {
                inherit system;
            };
            manifests = pkgs.callPackage ./manifests {};
        in
        {
            devShells.${system} = {
                default = pkgs.mkShell {
                    packages = with pkgs; [ 
                        jq
                    ];
                    NIX_SSHOPTS = "-i nixos/secrets/id_ed25519";
                };
                secrets = pkgs.mkShell {
                    packages = with pkgs; [
                        openssh
                        cfssl
                    ];
                };
                manifests = manifests.devShell;
            };
            nixosConfigurations = import ./nixos { inherit nixpkgs system inputs; };
        };
}
