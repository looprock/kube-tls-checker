# kube-tls-checker
Validate all TLS ingress endpoints

ssl-checker.py is meant to run inside a kubernetes cluster and validate certificats for all TLS terminated ingress endpoints.

# Usage

The script expects to be run inside a container containing a kubernetes configuration file and used the kubernetes module to read ingresses from the cluster. It provides output to prometheus on port 18080.

## Environment variables

kubeconfig - kubernetes configuration file (default: /k8s/kubeconfig)

context - the context to read endpoints from (default: None)

notify - the number of days before a certificate expiration to start warning (default: 30)

## Important

/k8s/kubeconfig isn't provided or references in the Dockerfile. Apply that in a different container and make this the base for it with the command: 

    CMD /usr/bin/python3 /usr/local/bin/ssl-checker.py
