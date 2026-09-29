id_ed25519
```bash
ssh-keygen -t ed25519 -f id_ed25519 -C "root"
```

root-ca
```bash
cfssl genkey -initca config/kube-pki-cacert-csr.json | cfssljson -bare root-ca
```

apitoken
```bash
head -c 16 /dev/urandom | od -An -t x | tr -d ' ' > apitoken
```

```bash
cfssl gencert -ca ./root-ca.pem -ca-key ./root-ca-key.pem config/cluster-admin-csr.json | cfssljson -bare ./cluster-admin
```

Generate cluster-admin kubeconfig:
```bash
nix-instantiate --json --eval -E "(let kubeconfig = import ./config/kubeconfig.nix; in kubeconfig)" | nix run nixpkgs#jq
```

