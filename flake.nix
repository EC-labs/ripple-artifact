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
                config.allowUnfree = true;
            };
            analysis = pkgs.callPackage ./analysis {};
            execution = pkgs.callPackage ./execution {
                scripts = scripts.default;
                analysis = analysis.package;
            };
            scripts = pkgs.callPackage ./scripts {};
            terraform = pkgs.callPackage ./terraform {};
        in
        {
            packages.${system} = {
                inherit scripts;
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
                terraform = terraform.devShell;
            };
            nixosConfigurations = import ./nixos { inherit nixpkgs system inputs; };
        };
}
