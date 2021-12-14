# CEPH CSIの起動とサンプルコード

元資料oは、git clone -b release-v3.4 https://github.com/ceph/ceph-csi でローカルにクローンできます。
詳しい検証を必要とする場合は、元資料をクローンしてご利用ください。



## 注意事項

* Cephのバージョン: ceph version 15.2.14 octopus (stable) 
* CSIのバージョン : Release-v3.4
* ディレクトリについて
deploy は cephfs, rbdのCSIドライバーをデプロイするためのファイルがあります。
これらは、example下のディレクトリ cephfs, rbd にある plugin-deploy.sh と plugin-teardown.shから利用されています。
そのため、デプロイ前に必ず deploy/cephfs と deploy/rbd の下にあるcsi-config-map.yamlを設定しなければなりません。
* 接続相手のCephクラスタは https://github.com/takara9/marmot-ceph を前提に記述しています。


## 共通準備作業

### Ceph CSI用名前空間の作成

Kubernetes上で、ceph の CSIを担うポッドを起動しなければならない。
専用の名前空間を作成して、cephfsとrbdのオブジェクトをまとめて管理する。

次のように名前空間ceph-csiを作成して、デフォルトの名前空間を切り替えておく。

~~~
kubectl create ns ceph-csi
kubectl config set-context ceph --namespace=ceph-csi --cluster=kubernetes --user=admin
kubectl config use-context ceph
kubectl config get-contexts
~~~

### Cephクラスタから接続情報の取得

cephクラスタのノードmon1へログインして、以下3つを取得する。

1. fsid
2. Cephモニターが動作するノードのIPアドレスとポート番号
3. クライアントのIDとKey


fsidとモニターのアドレスは、'ceph mon dump'で取得できる。

~~~
root@mon1:~# ceph mon dump
dumped monmap epoch 1
epoch 1
fsid e5687936-d583-445c-9ed6-dba05bb78eec
last_changed 2021-09-28T13:10:37.883933+0000
created 2021-09-28T13:10:37.883933+0000
min_mon_release 15 (octopus)
0: [v2:172.16.0.21:3300/0,v1:172.16.0.21:6789/0] mon.mon1
1: [v2:172.16.0.22:3300/0,v1:172.16.0.22:6789/0] mon.mon2
2: [v2:172.16.0.23:3300/0,v1:172.16.0.23:6789/0] mon.mon3
3: [v2:172.16.0.31:3300/0,v1:172.16.0.31:6789/0] mon.node1
4: [v2:172.16.0.32:3300/0,v1:172.16.0.32:6789/0] mon.node2
5: [v2:172.16.0.33:3300/0,v1:172.16.0.33:6789/0] mon.node3
6: [v2:172.16.0.34:3300/0,v1:172.16.0.34:6789/0] mon.node4
~~~

クライアントIDとKeyは、'ceph auth ls'で全登録ユーザーのリストを取得できる。
個別に習得する場合は、'ceph auth get client.ユーザーID'とする。

~~~
root@mon1:~# ceph auth get client.kubernetes
exported keyring for client.kubernetes
[client.kubernetes]
	key = AQAUFVNh0vs5ERAA9e7R/AbM5WlfZrWwb3bYkA==
	caps mgr = "profile rbd pool=kubernetes"
	caps mon = "profile rbd"
	caps osd = "profile rbd pool=kubernetes"
root@mon1:~# ceph auth get client.cephfs
exported keyring for client.cephfs
[client.cephfs]
	key = AQAYFVNhW6RhJhAARG41KC9E7uobGyPNmpV06g==
	caps mgr = "allow rw"
	caps mon = "allow r"
	caps osd = "allow rw tag cephfs metadata=*"
~~~

user_id と key はCeph側で設定しなければならない。
fsidは、Cephクラスタ構成時に生成されるので、クラスタの再構築の都度fsidは変わる。


コンフィグマップ ceph-csi-config は、Cephfsとrbdで共通であるが、それぞれのディレクトリに
同じファイルが存在するので、両方を設定しておかなければならない。

clusterIDにはfsidを設定。モニターのIPアドレスとポート番号6789を以下のように設定する。


### Cephクラスタの接続情報のコンフィグマップを作成

これが適切に設定されないと、Kubernetes上のプロビジョナーとCephクラスタが繋がらないため、
PVCが作成されないなどの問題が起こる。

~~~
$ cd manifests/ceph-csi/deploy/cephfs/kubernetes
$ cat csi-config-map.yaml
---
apiVersion: v1
kind: ConfigMap
data:
  config.json: |-
    [
      {
        "clusterID": "e5687936-d583-445c-9ed6-dba05bb78eec",
        "monitors": [
          "172.16.0.21:6789",
          "172.16.0.22:6789",
          "172.16.0.23:6789",
          "172.16.0.31:6789",
          "172.16.0.32:6789",
          "172.16.0.33:6789",
          "172.16.0.34:6789"
        ]
      }
    ]
metadata:
  name: ceph-csi-config
~~~

以上で、cephfsとrbdの共通設定は完了となる。




## Cephfsの利用方法

Cephfsを利用するにあたっての環境設定は、シークレットとストレージクラスになる。
これらは、名前空間 ceph-csiに作成する。

ワーキングディレクトリは、gitからクローンしたディレクトリ下になるので確認しておく。

~~~
$ pwd
manifests/ceph-csi/examples/cephfs
~~~


### secretの設定

secret.yamlには、CephのユーザーIDとKeyを設定する。
ceph auth コマンドで、ユーザーIDには、client.kubernetesなどのようにプレフィックスが
付いているが、clientをつけてidをセットすると、認識されないので、必ず取り除かなければ
ならない。

~~~
---
apiVersion: v1
kind: Secret
metadata:
  name: csi-cephfs-secret
  namespace: ceph-csi
stringData:
  # Required for statically provisioned volumes
  userID: myfs
  userKey: AQCUMlNhtjLTOBAAuCXJ75r6iM/x8IAYfUwRjA==

  # Required for dynamically provisioned volumes
  adminID: myfs
  adminKey: AQCUMlNhtjLTOBAAuCXJ75r6iM/x8IAYfUwRjA==
~~~

CephにCSIでCephfsを利用するユーザーが設定されていない場合は、以下のコマンドで登録する。

~~~
root@mon1:~# ceph auth get-or-create client.myfs mon 'allow r' osd 'allow rw tag cephfs *=*' mgr 'allow rw' mds 'allow rw'
~~~


### ストレージクラスの設定

ストレージクラスは、ストレージの種類ごとに設定しなければならない。同じcephfsでも使用するプールが異なれば、
異なるストレージクラスを設定して、プロビジョナーにストレージクラスを通じてパラメーターを与える。

ストレージクラスは、名前空間ceph-csiで作成しても、defaultなど他の名前空間からでも参照できるので、ceph-csiに作成する。

~~~
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: csi-cephfs-sc
provisioner: cephfs.csi.ceph.com
parameters:
  clusterID: e5687936-d583-445c-9ed6-dba05bb78eec
  fsName: cephfs
  csi.storage.k8s.io/provisioner-secret-name: csi-cephfs-secret
  csi.storage.k8s.io/provisioner-secret-namespace: ceph-csi
  csi.storage.k8s.io/controller-expand-secret-name: csi-cephfs-secret
  csi.storage.k8s.io/controller-expand-secret-namespace: ceph-csi
  csi.storage.k8s.io/node-stage-secret-name: csi-cephfs-secret
  csi.storage.k8s.io/node-stage-secret-namespace: ceph-csi
reclaimPolicy: Delete
allowVolumeExpansion: true
mountOptions:
  - debug
~~~


## cephfsプラグインのデプロイ

次のワーキングディレクトリで'plugin-deploy.sh'を実行することで、
cephfsにアクセスするために必要なオブジェクトがプロビジョニングされる。

~~~
tkr@hv2:~/marmot-k8s/manifests/ceph-fs-csi/ceph-csi/examples/cephfs$ ./plugin-deploy.sh 
serviceaccount/cephfs-csi-provisioner created
clusterrole.rbac.authorization.k8s.io/cephfs-external-provisioner-runner created
clusterrolebinding.rbac.authorization.k8s.io/cephfs-csi-provisioner-role created
role.rbac.authorization.k8s.io/cephfs-external-provisioner-cfg created
rolebinding.rbac.authorization.k8s.io/cephfs-csi-provisioner-role-cfg created
serviceaccount/cephfs-csi-nodeplugin created
clusterrole.rbac.authorization.k8s.io/cephfs-csi-nodeplugin created
clusterrolebinding.rbac.authorization.k8s.io/cephfs-csi-nodeplugin created
configmap/ceph-csi-config created
service/csi-cephfsplugin-provisioner created
deployment.apps/csi-cephfsplugin-provisioner created
daemonset.apps/csi-cephfsplugin created
service/csi-metrics-cephfsplugin created
~~~

すべてのポッドがRunning状態になれば、PVCを作成できる環境が整ったことになる。

~~~
tkr@hv2:~/marmot-k8s/manifests$ kubectl get po
NAME                                            READY   STATUS    RESTARTS   AGE
csi-cephfsplugin-2w9wf                          3/3     Running   0          136m
csi-cephfsplugin-76j65                          3/3     Running   0          136m
csi-cephfsplugin-8w9fn                          3/3     Running   0          136m
csi-cephfsplugin-provisioner-76964cfb57-fjlts   6/6     Running   0          136m
csi-cephfsplugin-provisioner-76964cfb57-kjfsw   6/6     Running   0          136m
csi-cephfsplugin-provisioner-76964cfb57-kprsr   6/6     Running   0          136m
~~~

反対にCSIドライバーを削除するには、`plugin-teardown.sh'を実行する。



## CephFSのユーザーのテスト

ここから名前空間 default で実施する。アプリやプロジェクトごとに専用の名前空間を持つことが一般的なので、
ceph-csi以外の名前空間からアクセスできることを確認するためである。

~~~
tkr@hv2:~/marmot-k8s/manifests$ kubectl config use-context default
~~~


### CephfsのPVCデプロイ

次のマニフェストを適用することで、設定が適切ならば、CephfsのPVC,PVが作成される。

~~~
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cephfs-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
  storageClassName: csi-cephfs-sc
~~~

PVCの作成と実行結果の確認

~~~
tkr@hv2:~/marmot-k8s/manifests$ kubectl apply -f pvc.yaml
tkr@hv2:~/marmot-k8s/manifests$ kubectl get pvc cephfs-pvc
NAME         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
cephfs-pvc   Bound    pvc-8c34c01d-1112-447e-ac0a-fb1439d471a5   1Gi        RWX            csi-cephfs-sc   143m
tkr@hv2:~/marmot-k8s/manifests$ kubectl get pv pvc-8c34c01d-1112-447e-ac0a-fb1439d471a5
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                STORAGECLASS    REASON   AGE
pvc-8c34c01d-1112-447e-ac0a-fb1439d471a5   1Gi        RWX            Delete           Bound    default/cephfs-pvc   csi-cephfs-sc            143m
~~~


### ポッドからのマウント

ポッドからマウントするには、次のYAMLファイルのように、pvcの名前を指定する。

~~~
apiVersion: v1
kind: Pod
metadata:
  name: test-cephfs-1
spec:
  containers:
    - name: my-ubuntu
      image: maho/my-ubuntu:0.1
      command: ["tail", "-f", "/dev/null"]      
      volumeMounts:
        - name: mypvc
          mountPath: /mnt
  volumes:
    - name: mypvc
      persistentVolumeClaim:
        claimName: cephfs-pvc
        readOnly: false
~~~

実行結果の確認

~~~
tkr@hv2:~/marmot-k8s/manifests/ceph-fs-csi/ceph-csi/examples/cephfs$ kubectl apply -f pod1.yaml
pod/test-cephfs-1 created


tkr@hv2:~/marmot-k8s/manifests/ceph-fs-csi/ceph-csi/examples/cephfs$ kubectl get pod 
NAME            READY   STATUS    RESTARTS   AGE
test-cephfs-1   1/1     Running   0          10s
~~~


### ポッド内からCephfsへのアクセス

ポッド test-cephfs-1 のシェルから lsblk, df -h を実行してマウントされていることを確認する。
lsblk では、 rbd0 というデバイスが認識されている。
また df -h では /mnt が ceph-fuse としてマウントされていることが確認できる。

~~~
tkr@hv2:~/marmot-k8s/manifests/ceph-fs-csi/ceph-csi/examples/cephfs$ kubectl exec -it test-cephfs-1 -- bash

root@test-cephfs-1:/# lsblk
NAME   MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
rbd0   251:0    0   1G  0 disk 
vda    252:0    0  10G  0 disk 
|-vda1 252:1    0   1M  0 part 
`-vda2 252:2    0  10G  0 part /dev/termination-log
vdb    252:16   0  20G  0 disk /etc/resolv.conf


root@test-cephfs-1:/# df -h
Filesystem      Size  Used Avail Use% Mounted on
overlay          20G  2.7G   16G  15% /
tmpfs            64M     0   64M   0% /dev
tmpfs           3.9G     0  3.9G   0% /sys/fs/cgroup
ceph-fuse       1.0G     0  1.0G   0% /mnt
/dev/vda2       9.8G  3.6G  5.8G  38% /etc/hosts
/dev/vdb         20G  2.7G   16G  15% /etc/hostname
shm              64M     0   64M   0% /dev/shm
tmpfs           3.9G   12K  3.9G   1% /run/secrets/kubernetes.io/serviceaccount
tmpfs           3.9G     0  3.9G   0% /proc/acpi
tmpfs           3.9G     0  3.9G   0% /proc/scsi
tmpfs           3.9G     0  3.9G   0% /sys/firmware
~~~

書込みのテストとして、/usr 以下のディレクトリを/mntへ書き込んでみる。
以下の結果では、正常に描き終えた。

~~~
root@test-cephfs-1:/# cd /mnt 
root@test-cephfs-1:/mnt# ls -la
total 5
drwxrwxrwx 2 root root    0 Sep 28 22:14 .
drwxr-xr-x 1 root root 4096 Sep 28 22:17 ..
root@test-cephfs-1:/mnt# cp -fr /usr . 
root@test-cephfs-1:/mnt# ls -la
total 5
drwxrwxrwx  3 root root 4195095 Sep 28 22:17 .
drwxr-xr-x  1 root root    4096 Sep 28 22:17 ..
drwxr-xr-x 10 root root 4195095 Sep 28 22:17 usr
~~~

### 他のポッドからPVCを共有してアクセス

同じPVCを他のポッドからアクセスするテストを実施する。

~~~
apiVersion: v1
kind: Pod
metadata:
  name: test-cephfs-2
spec:
  containers:
    - name: my-ubuntu
      image: maho/my-ubuntu:0.1
      command: ["tail", "-f", "/dev/null"]      
      volumeMounts:
        - name: mypvc
          mountPath: /mnt
  volumes:
    - name: mypvc
      persistentVolumeClaim:
        claimName: cephfs-pvc
        readOnly: false
~~~


2番目のポッドを起動して共有したcephfsへのアクセスする。
次の結果のように、Cepfsが共有されていることが確認できる。

~~~
tkr@hv2:~/marmot-k8s/manifests/ceph-fs-csi/ceph-csi/examples/cephfs$ kubectl apply -f pod2.yaml
pod/test-cephfs-2 created


Ctkr@hv2:~/marmot-k8s/manifests/ceph-fs-csi/ceph-csi/examples/cephfs$ kubectl get pod
NAME            READY   STATUS    RESTARTS   AGE
test-cephfs-1   1/1     Running   0          2m50s
test-cephfs-2   1/1     Running   0          31s


tkr@hv2:~/marmot-k8s/manifests/ceph-fs-csi/ceph-csi/examples/cephfs$ kubectl exec -it test-cephfs-2 -- bash
root@test-cephfs-2:/# lsblk
NAME   MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
vda    252:0    0  10G  0 disk 
|-vda1 252:1    0   1M  0 part 
`-vda2 252:2    0  10G  0 part /dev/termination-log
vdb    252:16   0  20G  0 disk /etc/resolv.conf


root@test-cephfs-2:/# df -h
Filesystem      Size  Used Avail Use% Mounted on
overlay          20G  2.7G   16G  15% /
tmpfs            64M     0   64M   0% /dev
tmpfs           3.9G     0  3.9G   0% /sys/fs/cgroup
ceph-fuse       1.0G  100M  924M  10% /mnt
/dev/vda2       9.8G  3.5G  5.8G  38% /etc/hosts
/dev/vdb         20G  2.7G   16G  15% /etc/hostname
shm              64M     0   64M   0% /dev/shm
tmpfs           3.9G   12K  3.9G   1% /run/secrets/kubernetes.io/serviceaccount
tmpfs           3.9G     0  3.9G   0% /proc/acpi
tmpfs           3.9G     0  3.9G   0% /proc/scsi
tmpfs           3.9G     0  3.9G   0% /sys/firmware


root@test-cephfs-2:/# cd /mnt
root@test-cephfs-2:/mnt# ls -la
total 5
drwxrwxrwx  3 root root 107371593 Sep 28 22:17 .
drwxr-xr-x  1 root root      4096 Sep 28 22:19 ..
drwxr-xr-x 10 root root 107371593 Sep 28 22:17 usr
~~~



## RBDの利用方法

プロックストレージとしてポッドにマウントする方法をみていく。
作業は、名前空間ceph-csiで実行する。

~~~
$ pwd
manifests/ceph-csi/examples/rbd
~~~


### secretの設定

secret.yamlには、CephのユーザーIDとKeyを設定する。これは利用するストレージのタイプにより
secretは異なるので、rbd用に設定する。IDとKeyはモニターノードの'ceph auth get client.kubernetes'の結果からセットする。

~~~
apiVersion: v1
kind: Secret
metadata:
  name: csi-rbd-secret
  namespace: ceph-csi
stringData:
  userID: kubernetes
  userKey: AQAUFVNh0vs5ERAA9e7R/AbM5WlfZrWwb3bYkA==

  # Encryption passphrase
  encryptionPassphrase: test_passphrase
~~~

以下を実行して、ceph-csiにシークレット csi-rbd-secretをデプロイする。

~~~
kubectl apply -f secret.yaml
~~~


### ストレージクラスの設定

ClusterIDにfsidの値を、poolに Ceph構築時に設定した専用プールの名前をセットする。

~~~
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
   name: csi-rbd-sc
provisioner: rbd.csi.ceph.com
parameters:
   clusterID: e5687936-d583-445c-9ed6-dba05bb78eec
   pool: kubernetes
   thickProvision: "false"
   imageFeatures: layering
   csi.storage.k8s.io/provisioner-secret-name: csi-rbd-secret
   csi.storage.k8s.io/provisioner-secret-namespace: ceph-csi
   csi.storage.k8s.io/controller-expand-secret-name: csi-rbd-secret
   csi.storage.k8s.io/controller-expand-secret-namespace: ceph-csi
   csi.storage.k8s.io/node-stage-secret-name: csi-rbd-secret
   csi.storage.k8s.io/node-stage-secret-namespace: ceph-csi

   csi.storage.k8s.io/fstype: ext4

reclaimPolicy: Delete
allowVolumeExpansion: true
mountOptions:
   - discard
~~~


こちらもceph-csiにデプロイする。

~~~
kubectl apply -f storageclass.yaml
~~~

次に、デプロイするためのシェルを実行する。

~~~
plugin-deploy.sh
~~~

ポッドが起動していることを確認して、名前空間をdefaultに切り替え、PVCのテストを実施する。

~~~
$ kubectl get po
csi-rbdplugin-gq6w5                             3/3     Running   0          10h
csi-rbdplugin-llgz9                             3/3     Running   0          10h
csi-rbdplugin-provisioner-56f98557c8-gl6mh      7/7     Running   0          10h
csi-rbdplugin-provisioner-56f98557c8-pwl2n      7/7     Running   0          10h
csi-rbdplugin-provisioner-56f98557c8-tbzhl      7/7     Running   0          10h
csi-rbdplugin-qpzwv                             3/3     Running   0          10h
~~~

削除する際は'plugin-teardown.sh'を利用する。


名前空間をdefaultに切り替えてpvc.yamlを適用する。

~~~
tkr@hv2:~/marmot-k8s/manifests/ceph-csi/examples/rbd$ kubectl config use-context default
tkr@hv2:~/marmot-k8s/manifests/ceph-csi/examples/rbd$ cat pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rbd-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: csi-rbd-sc
~~~

結果はすぐに出るので、pendingになれば、問題判別を実施する。

~~~
tkr@hv2:~/marmot-k8s/manifests/ceph-csi/examples/rbd$ kubectl apply -f pvc.yaml

tkr@hv2:~/marmot-k8s/manifests/ceph-csi/examples/rbd$ kubectl get pvc
NAME         STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
rbd-pvc      Bound     pvc-2f093ed0-b492-44a0-983c-27ced74acf77   1Gi        RWO            csi-rbd-sc      1h
~~~


## ポッドからのマウント

名前空間defaultからrbdのPVCをプロビジョニングする。

~~~
tkr@hv2:~/marmot-k8s/manifests/ceph-csi/examples/rbd$ kubectl apply -f pod1.yaml
pod/test-rbd-1 created

tkr@hv2:~/marmot-k8s/manifests/ceph-csi/examples/rbd$ kubectl get pod 
NAME            READY   STATUS              RESTARTS   AGE
test-rbd-1      1/1     Running             0          17s
~~~

ポッドでシェルを対話型で動かして、ブロック・ストレージがマウントされていることを確認する。

~~~
tkr@hv2:~/marmot-k8s/manifests/ceph-csi/examples/rbd$ kubectl exec -it test-rbd-1 -- bash
root@test-rbd-1:/# lsblk
NAME   MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
rbd0   251:0    0   1G  0 disk /mnt
vda    252:0    0  10G  0 disk 
|-vda1 252:1    0   1M  0 part 
`-vda2 252:2    0  10G  0 part /dev/termination-log
vdb    252:16   0  20G  0 disk /etc/resolv.conf
root@test-rbd-1:/# cd /mnt
root@test-rbd-1:/mnt# ls -la
total 24
drwxrwxrwx 3 root root  4096 Sep 29 01:57 .
drwxr-xr-x 1 root root  4096 Sep 29 01:56 ..
drwx------ 2 root root 16384 Sep 28 15:01 lost+found
root@test-rbd-1:/mnt# cp -fr /etc .
root@test-rbd-1:/mnt# ls
etc  lost+found
~~~


以上
