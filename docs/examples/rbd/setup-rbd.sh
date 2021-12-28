#!/bin/bash


kubectl create ns ceph-csi
kubectl config set-context ceph --namespace=ceph-csi --cluster=kubernetes --user=admin
kubectl config use-context ceph
kubectl config get-contexts

kubectl apply -f secret.yaml
kubectl apply -f storageclass.yaml
./plugin-deploy.sh

kubectl get po

echo "kubectl patch storageclass csi-rbd-sc -p \'{\"metadata\": {\"annotations\":{\"storageclass.kubernetes.io\/is-default-class\":\"true\"}}}'\""
kubectl patch storageclass csi-rbd-sc -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
