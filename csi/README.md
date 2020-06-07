# CSIでKubernetesと連携する方法


## Ceph node1 の設定

プールを設定する。

~~~
root@node1:/root# ceph osd pool create kubernetes 4
pool 'kubernetes' created
root@node1:/root# rbd pool init kubernetes
~~~

認証情報を作成

~~~
root@node1:/root# ceph auth get-or-create client.kubernetes mon 'profile rbd' osd 'profile rbd pool=kubernetes' mgr 'profile rbd'
[client.kubernetes]
	key = AQDOHtxeW9GzNhAAYi7oyvBixY1jb+CBoUA7VA==
~~~


もし失敗したら、以下の方法で一旦消して、再度上記を実行

~~~
root@node1:/root# ceph auth rm client.kubernetes 
updated
~~~

fsidの表示

~~~
root@node1:/root# ceph mon dump
dumped monmap epoch 1
epoch 1
fsid 3ac56641-b273-42ab-afcf-218a34ad1924
last_changed 2020-06-06 03:25:22.430426
created 2020-06-06 03:25:22.430426
min_mon_release 14 (nautilus)
0: [v2:172.20.1.31:3300/0,v1:172.20.1.31:6789/0] mon.node1
1: [v2:172.20.1.32:3300/0,v1:172.20.1.32:6789/0] mon.node2
2: [v2:172.20.1.33:3300/0,v1:172.20.1.33:6789/0] mon.node3
~~~


## Kubernetes側 CSIの設定作業

Ceph CSI のコードをGitHubからクローンする。

~~~
$ git clone -b release-v1.2.0 https://github.com/ceph/ceph-csi
$ cd ceph-csi/deploy/rbd/kubernetes/v1.14+
~~~


file: csi-config-map.yaml

~~~
apiVersion: v1
kind: ConfigMap
data:
  config.json: |-
    [
      {
        "clusterID": "3ac56641-b273-42ab-afcf-218a34ad1924",
        "monitors": [
          "172.20.1.31:6789",
          "172.20.1.32:6789",
          "172.20.1.33:6789"
        ]
      }
    ]
metadata:
  name: ceph-csi-config
~~~


file: csi-rbd-secret.yaml

~~~
apiVersion: v1
kind: Secret
metadata:
  name: csi-rbd-secret
stringData:
  userID: kubernetes
  userKey: AQDOHtxeW9GzNhAAYi7oyvBixY1jb+CBoUA7VA==
~~~



~~~
$ kubectl apply -f csi-config-map.yaml
$ kubectl apply -f csi-rbd-secret.yaml
~~~


~~~
$ kubectl apply -f csi-nodeplugin-rbac.yaml 
$ kubectl apply -f csi-provisioner-rbac.yaml 
$ kubectl apply -f csi-rbdplugin-provisioner.yaml 
$ kubectl apply -f csi-rbdplugin.yaml 
~~~


起動の確認

~~~
$ kubectl get po
NAME                                         READY   STATUS    RESTARTS   AGE
csi-rbdplugin-5whkf                          3/3     Running   0          102m
csi-rbdplugin-h62hf                          3/3     Running   0          102m
csi-rbdplugin-provisioner-75dd6f9d54-68nnp   5/5     Running   0          102m
csi-rbdplugin-provisioner-75dd6f9d54-cv24g   5/5     Running   0          102m
csi-rbdplugin-provisioner-75dd6f9d54-pwv5m   5/5     Running   0          102m
~~~



## Kubernetes側 ストレージクラスの設定作業


csi-rbd-sc.yaml 

~~~
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
   name: csi-rbd-sc
provisioner: rbd.csi.ceph.com
parameters:
   clusterID: 3ac56641-b273-42ab-afcf-218a34ad1924
   pool: kubernetes
   csi.storage.k8s.io/provisioner-secret-name: csi-rbd-secret
   csi.storage.k8s.io/provisioner-secret-namespace: default
   csi.storage.k8s.io/node-stage-secret-name: csi-rbd-secret
   csi.storage.k8s.io/node-stage-secret-namespace: default
reclaimPolicy: Delete
mountOptions:
   - discard
~~~


~~~
$ kubectl apply -f csi-rbd-sc.yaml 
~~~

ストレージクラスの確認

~~~
$ kubectl get sc
NAME         PROVISIONER        RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
csi-rbd-sc   rbd.csi.ceph.com   Delete          Immediate           false                  101m
~~~


## 動作確認 PVCとPODの作成 


ブロックデバイスを作成するPVC

~~~raw-block-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: raw-block-pvc
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Block
  resources:
    requests:
      storage: 1Gi
  storageClassName: csi-rbd-sc
~~~

永続ボリュームクレームの適用

~~~
$ kubectl apply -f raw-block-pvc.yaml

$ kubectl get pvc
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
raw-block-pvc   Bound    pvc-a09369d1-53ec-4198-b39d-64a23f2fcf97   1Gi        RWO            csi-rbd-sc     110m

$ kubectl get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                   STORAGECLASS   REASON   AGE
pvc-a09369d1-53ec-4198-b39d-64a23f2fcf97   1Gi        RWO            Delete           Bound    default/raw-block-pvc   csi-rbd-sc              110m
~~~


前述のPVCをマウントするポッド起動の起動

~~~
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-raw-block-volume
spec:
  containers:
    - name: my-container
      image: maho/my-ubuntu:0.1
      command: ["/bin/sh", "-c"]
      args: ["tail -f /dev/null"]
      volumeDevices:
        - name: data
          devicePath: /dev/xvda
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: raw-block-pvc
~~~


コンテナに入って確認する。ファイルシステムなしで、ブロックデバイスとして認識されている。

~~~
$ kubectl exec -it pod-with-raw-block-volume -- bash

root@pod-with-raw-block-volume:/# lsblk
NAME   MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
loop0    7:0    0   1G  0 loop 
sda      8:0    0  10G  0 disk 
`-sda1   8:1    0  10G  0 part /etc/resolv.conf
sdb      8:16   0  10M  0 disk 
rbd0   252:0    0   1G  0 disk 

root@pod-with-raw-block-volume:/# ls -al /dev/xvda
brw-rw-rw- 1 root disk 252, 0 Jun  6 23:02 /dev/xvda
~~~


## 動作確認 PVCとPODの作成２

ブロックデバイスをファイルシステムとしてマウントするケース

fs-block-pvc.yaml

~~~
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: fs-block-pvc
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Filesystem
  resources:
    requests:
      storage: 1Gi
  storageClassName: csi-rbd-sc
~~~

raw-block-pod.yaml

~~~
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-raw-block-volume
spec:
  containers:
    - name: my-container
      image: maho/my-ubuntu:0.1
      command: ["/bin/sh", "-c"]
      args: ["tail -f /dev/null"]
      volumeDevices:
        - name: data
          devicePath: /dev/xvda
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: raw-block-pvc
~~~


~~~
$ kubectl apply -f fs-block-pod.yaml

$ kubectl get pvc
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
fs-block-pvc    Bound    pvc-96e9aff9-6b1f-4ee0-a5e2-d4c72ec73df9   1Gi        RWO            csi-rbd-sc     2m12s
raw-block-pvc   Bound    pvc-a09369d1-53ec-4198-b39d-64a23f2fcf97   1Gi        RWO            csi-rbd-sc     122m
~~~


~~~
vagrant@bootnode:/vagrant/csi$ kubectl get pod
NAME                                         READY   STATUS    RESTARTS   AGE
csi-rbd-demo-pod                             1/1     Running   0          58s
csi-rbdplugin-5whkf                          3/3     Running   0          123m
csi-rbdplugin-h62hf                          3/3     Running   0          123m
csi-rbdplugin-provisioner-75dd6f9d54-68nnp   5/5     Running   0          123m
csi-rbdplugin-provisioner-75dd6f9d54-cv24g   5/5     Running   0          123m
csi-rbdplugin-provisioner-75dd6f9d54-pwv5m   5/5     Running   0          123m
pod-with-raw-block-volume                    1/1     Running   0          118m
~~~



~~~
vagrant@bootnode:/vagrant/csi$ kubectl exec -it csi-rbd-demo-pod -- bash

root@csi-rbd-demo-pod:/# df -h
Filesystem      Size  Used Avail Use% Mounted on
overlay         9.7G  3.9G  5.8G  41% /
tmpfs            64M     0   64M   0% /dev
tmpfs           3.9G     0  3.9G   0% /sys/fs/cgroup
shm              64M     0   64M   0% /dev/shm
/dev/sda1       9.7G  3.9G  5.8G  41% /etc/hosts
/dev/rbd1       976M  2.6M  958M   1% /var/lib/www/html
tmpfs           3.9G   12K  3.9G   1% /run/secrets/kubernetes.io/serviceaccount
tmpfs           3.9G     0  3.9G   0% /proc/acpi
tmpfs           3.9G     0  3.9G   0% /proc/scsi
tmpfs           3.9G     0  3.9G   0% /sys/firmware

root@csi-rbd-demo-pod:/# lsblk -f
NAME   FSTYPE LABEL UUID FSAVAIL FSUSE% MOUNTPOINT
loop0                                   
sda                                     
`-sda1                      5.8G    40% /etc/resolv.conf
sdb                                     
rbd0                                    
rbd1                      957.4M     0% /var/lib/www/html
~~~


