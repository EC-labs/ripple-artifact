# Overview

The following repository contains the instructions to reproduce the results obtained for "Seeing Through NAT with Ripple: Retrofitting Service Dependency Discovery in Networked Distributed Systems". This repository is aimed for the Artifact Reproducible badge, whereas the source code targets the Artifact Available and Functional badges.

We include the instructions to reproduce our main results in Section 6.1. These instructions run Ripple on the 3 different microservice benchmarks, when they're running on the 3 different networking environments, for a total of 9 configurations. For the remainder of the experiments, we report our procedure in each respective section, and provide the raw data and analysis scripts in this repository's `./results` directory.

# Experiment 1: Validation

## Pre-requisites

Install the `nix` package manager on a machine that will coordinate the VMs.

## Setup

**We have provided default secrets, however these can be changed by executing commands similar to those shown in the `nixos/secrets/README.md` file.**

Clone this repository and make sure your current directory is the root directory of the repository:

```bash
git clone https://github.com/ec-labs/ripple-artifact
cd ripple-artifact
nix --extra-experimental-features 'nix-command flakes' develop .#terraform
```

Configure your AWS credentials with:
```bash
aws configure
```

Enter the terraform directory of the repository and you should now be able to create the required infrastructure with:
```bash
cd terraform
terraform init
terraform apply
terraform output -json vars > ../nixos/vars.json
```

Exit the current development shell, which should bring you back to the root directory of the repository:
```bash
exit
```

Configure the 3 virtual machines, by first configuring the shell environment:
```bash
nix --extra-experimental-features 'nix-command flakes' develop .#
```

followed by building and switching each virtual machine's nixos generation. Building and copying might take a while, so you can run these commands in parallel:
```bash
nixos-rebuild.sh k8s-master
nixos-rebuild.sh k8s-worker1
nixos-rebuild.sh k8s-worker2
```

The result of the switching might report a `systemctl` start error, which should autocorrect itself, after all systemd services are up and running. If not, it is possible that you might have to manually restart the systemd services in the VMs. To `ssh` into a VM you can use the helper `ssh.sh` script we provide, by running:
```bash
ssh.sh <node-name>
# where <node-name> can be "k8s-master", "k8s-worker1", and "k8s-worker2"
# E.g.:
ssh.sh k8s-worker1
```

Please reach out to `d.landau@uu.nl` if you're having issues.

After the previous 3 commands have completed, this should have installed a 3 node kubernetes cluster, and prepared each VM for the experiments that are to be executed. You can check whether the installation has been successful by running:
```bash
nix --extra-experimental-features 'nix-command flakes' develop .#execution

kubectl get nodes
# Which should output something like:
# NAME          STATUS   ROLES    AGE   VERSION
# k8s-master    Ready    <none>   62m   v1.34.3
# k8s-worker1   Ready    <none>   62m   v1.34.3
# k8s-worker2   Ready    <none>   62m   v1.34.3
```

This completes the setup stage.

## Execution

To execute an experiment, enter the execution shell environment with:
```bash
nix --extra-experimental-features 'nix-command flakes' develop .#execution
```

And then run an experiment. Don't forget to change the parameterised arguments `<microservice-benchmark> <run-type>`:
```bash
DATA_DIR=./data run.sh <microservice-benchmark> <run-type>
# For example:
DATA_DIR=./data run.sh media-microservices external
```

This command will perform a full experiment with ripple, ranging from setting up the microservice benchmark ("social-network", "media-microservices", or "online-boutique") in the expected network configuration (`<run-type>`). `<run-type>` can assume 3 values: 
    
* `internal`: which refers to the network configuration where the microservice benchmark is deployed with docker compose, and the services communicate with one another via the VMs privateIPs.
* `external`: which refers to the network configuration where the microservice benchmark is deployed with docker compose, and the services communicate with one another via the VMs publicIPs.
* `k8s`: refers to the network configuration where the microservice benchmark is deployed with k8s, and pods communicate and discover each other using standard kubernetes dns resolution and the flannel cni.

As such, with this command you can run Ripple in the 9 network configurations reported in the paper. 

The `run.sh` script then starts the load generator, followed by starting ripple. Finally, after 30s running ripple, the data is copied and analysed against the ground truth. For example, the following output is expected when running the online-boutique internal experiment:
```bash
DATA_DIR=./data run.sh online-boutique internal
# + exec ssh -o LogLevel=ERROR -i /nix/store/bffcc74cwfiq3si34m5yz5vh831r70wj-id_ed25519 root@18.195.37.79 'docker compose -f /etc/online-boutique/internal.yaml up -d'
# ...
# ...
#    precision  recall  f1score
# 0        1.0     1.0      1.0
```

The database for the experiment can be found in the `DATA_DIR` directory passed in as an environment variable in the command line (which in the previous command was `./data`).

*Note 1: The results might differ slightly depending on the context they are executed in, as a result of over-discovering services related to the microservice benchmark initialisation scripts.*

*Note 2: If the execution reports a very low fscore (lower than 0.8), then the load generator might not have run as expected. Run the experiment again with the same parameters, and if it still persists, reach out to `d.landau@uu.nl`.*


## Related Work

Extracting the results from the related works is non-standard, and hard to automate due to the requirement to interact with the interfaces they provide. 

**We provide the raw data and resulting service dependency graphs for all tools in the `./results/validation` directory.**

# Experiment 2: Overhead

Deploy the microservice application using the k8s instructions from Experiment 1. For each application, make sure you start the metric collection tool before running the workloads. After deploying the k8s microservice benchmark, and the metric collection tool, run the workload generator for a total of 30s, and collect the microservice benchmark average response time. This should be repeated 30 times. 

**The raw data and processing is available in `./results/overhead`.**

# Experiment 3: Time to Completion

1. Start a microservice application using any of the methods described above.
1. Start a long-running workload generator. I.e. If using online-boutique the workload generator already executes without termination, however, media and social both need to receive a duration parameter. We used -d 500 for these applications.
1. Make sure you start ripple on a pid of each application.
1. Copy the data from all VMs and store them in the same directory.
1. Analyse the data using the data/ttc.py script.

**The raw data and analysis scripts for the paper are included in `./results/ttc`.**

# Experiment 4: Case Study

1. Start the online boutique k8s microservice benchmark. 
1. Bootstrap Ripple with the namespace=online-boutique containerd-filter.
1. Run a stress-ng cpu intensive workload on the productcatalog container.
1. Analyse the data collected by the Prism agents.

**The raw data and analysis scripts for the paper are included in `./results/case-study`.**
