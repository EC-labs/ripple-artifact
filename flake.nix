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
            analysis = pkgs.callPackage ./analysis {};
            execution = pkgs.callPackage ./execution {
                scripts = scripts.default;
                analysis = analysis.package;
            };
            scripts = pkgs.callPackage ./scripts {};
            social-network = pkgs.callPackage ./execution/microservice-benchmarks/social-network {};
        in
        {
            packages.${system} = {
                inherit scripts;
                inherit social-network;
                execution = execution.packages;
                analysis = analysis.package;
            };

            devShells.${system} = {
                default = pkgs.mkShell {
                    packages = with pkgs; [ 
                        jq
                        duckdb
                        self.packages.${system}.scripts.combine-dbs
                        scripts.default
                        (python3.withPackages (py-pkgs: with py-pkgs; [ 
                            jinja2 
                            duckdb 
                            numpy 
                            pandas 
                        ]))
                    ];
                    NIX_SSHOPTS = "-i nixos/secrets/id_ed25519";
                };
                secrets = pkgs.mkShell {
                    packages = with pkgs; [
                        openssh
                        cfssl
                    ];
                };
                execution = execution.devShell;
            };
            nixosConfigurations = import ./nixos { inherit nixpkgs system inputs; };
        };
}
