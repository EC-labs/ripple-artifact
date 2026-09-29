{
    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
    };
    outputs = { self, nixpkgs }@inputs:
        let 
            system = "x86_64-linux";
            pkgs = import nixpkgs { inherit system; };
        in
        {
            devShells.${system} = {
                nixos = pkgs.mkShell {
                    packages = with pkgs; [ 
                        jq
                    ];
                    NIX_SSHOPTS = "-i secrets/id_ed25519";
                };
                secrets = pkgs.mkShell {
                    packages = with pkgs; [
                        openssh
                        cfssl
                    ];
                };
            };
            nixosConfigurations = import ./nixos { inherit nixpkgs system inputs; };
        };
}
