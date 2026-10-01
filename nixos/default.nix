{ nixpkgs, system, inputs, ... }:
{
    k8s-master = nixpkgs.lib.nixosSystem {
        inherit system;

        specialArgs = {
            inherit inputs;
            kubeletHostName = "k8s-master";
        };
        modules = [
            ./modules/k8s-master.nix
            ({ ... }: { nixpkgs.config.permittedInsecurePackages = [ "docker-28.5.2" ];})
        ];
    }; 
    k8s-worker1 = nixpkgs.lib.nixosSystem {
        inherit system;

        specialArgs = {
            inherit inputs;
            kubeletHostName = "k8s-worker1";
        };
        modules = [
            ./modules/k8s-worker.nix
            ({ ... }: { nixpkgs.config.permittedInsecurePackages = [ "docker-28.5.2" ];})
        ];
    }; 
    k8s-worker2 = nixpkgs.lib.nixosSystem {
        inherit system;

        specialArgs = { 
            inherit inputs;
            kubeletHostName = "k8s-worker2"; 
        };
        modules = [
            ./modules/k8s-worker.nix
            ({ ... }: { nixpkgs.config.permittedInsecurePackages = [ "docker-28.5.2" ];})
        ];
    }; 
}
