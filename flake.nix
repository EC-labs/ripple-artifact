{
    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
        prism.url = "github:ec-labs/prism";
    };
    outputs = { self, nixpkgs, ... }@inputs:
        let 
            system = "x86_64-linux";
            pkgs = import nixpkgs {
                inherit system;
            };
            manifests = pkgs.callPackage ./manifests {};
            scripts = pkgs.callPackage ./scripts {};
            social-network = pkgs.callPackage ./execution/microservice-benchmarks/social-network {};
        in
        {
            packages.${system} = {
                inherit (scripts.packages) combine-dbs;
                inherit social-network;
            };

            devShells.${system} = {
                default = pkgs.mkShell {
                    packages = with pkgs; [ 
                        jq
                        duckdb
                        self.packages.${system}.combine-dbs
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
