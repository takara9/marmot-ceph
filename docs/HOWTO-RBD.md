# Ceph RBD の利用方法


~~~
$ pwd
manifests/ceph-csi/examples/rbd
~~~


## PVCをデプロイする

名前空間をdefaultに切り替えてpvc.yamlを適用する。

~~~
$ kubectl config use-context default
$ cat pvc.yaml
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
$ kubectl apply -f pvc.yaml
$ kubectl get pvc
NAME         STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
rbd-pvc      Bound     pvc-2f093ed0-b492-44a0-983c-27ced74acf77   1Gi        RWO            csi-rbd-sc      1h
~~~


## ポッドからのマウント

名前空間defaultからrbdのPVCをプロビジョニングする。

~~~
$ kubectl apply -f pod1.yaml
pod/test-rbd-1 created

$ kubectl get pod 
NAME            READY   STATUS              RESTARTS   AGE
test-rbd-1      1/1     Running             0          17s
~~~

ポッドでシェルを対話型で動かして、ブロック・ストレージがマウントされていることを確認する。

~~~
$ kubectl exec -it test-rbd-1 -- bash
root@test-rbd-1:/# lsblk
NAME   MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
rbd0   251:0    0   1G  0 disk /mnt
vda    252:0    0  10G  0 disk 
|-vda1 252:1    0   1M  0 part 
`-vda2 252:2    0  10G  0 part /dev/termination-log
vdb    252:16   0  20G  0 disk /etc/resolv.conf

# cd /mnt
# ls -la
total 24
drwxrwxrwx 3 root root  4096 Sep 29 01:57 .
drwxr-xr-x 1 root root  4096 Sep 29 01:56 ..
drwx------ 2 root root 16384 Sep 28 15:01 lost+found

# cp -fr /etc .
# ls
etc  lost+found
~~~



## PVCのクローン

永続ボリュームをクローンして、新たなポッドからマウントして利用できる

クローンのPVCを作成する

~~~
$ kubectl apply -f pvc-clone.yaml 
persistentvolumeclaim/rbd-pvc-clone created

$ kubectl get pvc
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
rbd-pvc         Bound    pvc-2f093ed0-b492-44a0-983c-27ced74acf77   1Gi        RWO            csi-rbd-sc      42h
rbd-pvc-clone   Bound    pvc-b9dd5121-86ca-4e9d-aab8-1d9fa1816b6f   1Gi        RWO            csi-rbd-sc      5s
~~~

pvc-clone.yamlのファイルでは、dataSourceに元になるPVCを設定して
metadata.nameにクローンのPVC名を設定して実行

~~~
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rbd-pvc-clone
spec:
  storageClassName: csi-rbd-sc
  dataSource:
    name: rbd-pvc
    kind: PersistentVolumeClaim
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
~~~

クローンのPVCをマウントするポッドを起動して、内容を確認する。

~~~
$ kubectl apply -f pod-clone.yaml 
pod/test-rbd-clone created

$ kubectl get po
NAME             READY   STATUS    RESTARTS   AGE
test-rbd-1       1/1     Running   0          31h
test-rbd-clone   1/1     Running   0          106s
~~~

ポッドの中から、内容を確認する。クローン元と同じ/mnt/etcが確認できる。

~~~
$ kubectl exec -it test-rbd-clone  -- bash
# ls -al /mnt
total 28
drwxrwxrwx  4 root root  4096 Sep 29 01:58 .
drwxr-xr-x  1 root root  4096 Sep 30 09:05 ..
drwxr-xr-x 35 root root  4096 Sep 29 01:58 etc
drwx------  2 root root 16384 Sep 28 15:01 lost+found
~~~

/mntの下、すなわち、Cephの永続ボリュームにディレクトリworkを作成する

~~~
# mkdir /mnt/work
# ls /mnt
etc  lost+found  work
~~~

クローン元のPVCをマウントするポッドから、影響がないことを確認する。

~~~
$ kubectl exec -it test-rbd-1  -- bash
# ls /mnt
etc  lost+found
~~~



## スナップショットの設定

事前準備は、HOWTO-SNAPSHOT.md に案内に従って、スナップショッターを設定する。

次に、以下のコマンドで、スナップショットクラスを設定

~~~
kubectl config use-context ceph
kubectl apply -f snapshotclass.yaml
~~~


## スナップショットの取得

スナップショットを取り、volumesnapshotを表示して確認する。この時点でPVCではない。

~~~
$ kubectl apply -f take-snapshot.yaml 
volumesnapshot.snapshot.storage.k8s.io/rbd-pvc-snapshot created
~~~

take-snapshot.yaml のファイルは、以下のとおり。
事前に登録しておいた Volume Snapshot Class を指定して、ソースとなるPVCを指定する。

~~~
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: rbd-pvc-snapshot
spec:
  volumeSnapshotClassName: csi-rbdplugin-snapclass
  source:
    persistentVolumeClaimName: rbd-pvc
~~~



## スナップショットの確認

~~~
$ kubectl get volumesnapshot
NAME               READYTOUSE   SOURCEPVC   SOURCESNAPSHOTCONTENT   RESTORESIZE   SNAPSHOTCLASS             SNAPSHOTCONTENT                                    CREATIONTIME   AGE
rbd-pvc-snapshot   true         rbd-pvc                             1Gi           csi-rbdplugin-snapclass   snapcontent-41a43480-6fcb-4f64-9f71-177a379a9409   15s            15s
~~~


## スナップショットをPVCへリストア

pvc-restore.yaml によりスナップショットからPVCを生成する。

~~~
$ kubectl get pvc
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE

$ kubectl apply -f pvc-restore.yaml 
persistentvolumeclaim/rbd-pvc-restore created

$ kubectl get pvc
NAME              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
rbd-pvc-restore   Bound    pvc-450e2e94-23b6-4ae9-8c48-d3e2dba0ddbe   1Gi        RWO            csi-rbd-sc      2s
~~~

pvc-restore.yaml では、元のスナップショットを指定して、metadata.nameに生成するPVCを指定する。

~~~
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rbd-pvc-restore
spec:
  storageClassName: csi-rbd-sc
  dataSource:
    name: rbd-pvc-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
~~~


生成したPVCをポッドでマウント

~~~
$ kubectl apply -f pod-restore.yaml 
pod/test-rbd-restore created

$ kubectl get pod
NAME               READY   STATUS    RESTARTS   AGE
test-rbd-restore   1/1     Running   0          7m38s
~~~


/mntの下に、元のPVCのデータが入っているのが解る。

~~~
$ kubectl exec -it test-rbd-restore -- bash
root@test-rbd-restore:/# ls /mnt
etc  lost+found
~~~

