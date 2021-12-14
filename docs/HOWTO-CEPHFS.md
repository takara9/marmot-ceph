# Cephfs の利用方法

## CephfsのPVCデプロイ

Cephfs のYAMLを格納しているディレクトリは、marmot-k8s/manifests/ceph-csi/examples/cephfs である。

pvc.yamlは、ストレージクラスに csi-cephfs-sc を指定する。

~~
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
~~

PVCの作成と実行結果の確認

~~
$ kubectl apply -f pvc.yaml
persistentvolumeclaim/cephfs-pvc created

$ kubectl get pvc
NAME              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
cephfs-pvc        Bound    pvc-674480e7-c482-4e95-806b-8b8eaabc044b   1Gi        RWX            csi-cephfs-sc   7s
~~


## ポッドからのマウント

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
$ kubectl apply -f pod.yaml
pod/test-cephfs-1 created

$ kubectl get pod 
NAME            READY   STATUS    RESTARTS   AGE
test-cephfs-1   1/1     Running   0          10s
~~~


## 複数ポッドからのマウント

~~~
$ kubectl apply -f pod2.yaml 
pod/test-cephfs-2 created

$ kubectl get po
NAME               READY   STATUS    RESTARTS   AGE
test-cephfs-1      1/1     Running   0          6m51s
test-cephfs-2      1/1     Running   0          11s

~~~

~~~
$ kubectl exec -it test-cephfs-1 -- bash
root@test-cephfs-1:/# ls /mnt
root@test-cephfs-1:/# tar cf /mnt/test.dat /usr
root@test-cephfs-1:/# md5sum /mnt/test.dat 
dbac22ba62f319196aec44b988862f9a  /mnt/test.dat
~~~

md5sumの結果は同じことが確認できたことから、２つのポッドから一つのPVCがマウントされていることが確認できる。

~~~
$ kubectl apply -f pod2.yaml 
pod/test-cephfs-2 created

$ kubectl get po
NAME               READY   STATUS    RESTARTS   AGE
test-cephfs-1      1/1     Running   0          6m51s
test-cephfs-2      1/1     Running   0          11s

$ kubectl exec -it test-cephfs-2 -- bash
root@test-cephfs-2:/# ls /mnt
test.dat
root@test-cephfs-2:/# md5sum /mnt/test.dat 
dbac22ba62f319196aec44b988862f9a  /mnt/test.dat
root@test-cephfs-2:/# 
~~~


## PVCクローン

~~~
$ kubectl apply -f pvc-clone.yaml 
persistentvolumeclaim/cephfs-pvc-clone created

$ kubectl apply -f pod-clone.yaml 
pod/pod-cephfs-clone created

$ kubectl exec -it pod-cephfs-clone -- bash
root@pod-cephfs-clone:/# ls -al /mnt
total 104775
drwxrwxrwx 2 root root 107284480 Oct  1 15:02 .
drwxr-xr-x 1 root root      4096 Oct  1 15:10 ..
-rw-r--r-- 1 root root 107284480 Oct  1 15:02 test.dat
root@pod-cephfs-clone:/# md5sum /mnt/test.dat 
dbac22ba62f319196aec44b988862f9a  /mnt/test.dat
~~~


## スナップショットの作成

PVCのスナップショットを取得するには、APIを記述したYAMLを適用する。

~~~
$ kubectl apply -f take-snapshot.yaml 
volumesnapshot.snapshot.storage.k8s.io/cephfs-pvc-snapshot created

$ kubectl get volumesnapshot
NAME                  READYTOUSE   SOURCEPVC    SOURCESNAPSHOTCONTENT   RESTORESIZE   SNAPSHOTCLASS                SNAPSHOTCONTENT                                    CREATIONTIME   AGE
cephfs-pvc-snapshot   true         cephfs-pvc                           1Gi           csi-cephfsplugin-snapclass   snapcontent-2a453898-5592-4f21-b262-c97c9aafc596   5s             5s
~~~


take-snapshot.yamlの内容は、以下のとおり、volumeSnapshotClassNameが事前に設定されていなければならない。

~~~
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: cephfs-pvc-snapshot
spec:
  volumeSnapshotClassName: csi-cephfsplugin-snapclass
  source:
    persistentVolumeClaimName: cephfs-pvc
~~~

スナップショットを取得しても、次の結果のようにPVCは生成されない。

~~~
$ kubectl get pvc
NAME               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
cephfs-pvc         Bound    pvc-674480e7-c482-4e95-806b-8b8eaabc044b   1Gi        RWX            csi-cephfs-sc   19m
~~~



## スナップショットからPVCの生成


PVCを取得するには、次の例のようにpvc-restore.yaml適用することで、cephfs-pvc-restoreを得られる

~~~
$ kubectl apply -f pvc-restore.yaml 
persistentvolumeclaim/cephfs-pvc-restore created

$ kubectl get pvc
NAME                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
cephfs-pvc           Bound    pvc-674480e7-c482-4e95-806b-8b8eaabc044b   1Gi        RWX            csi-cephfs-sc   19m
cephfs-pvc-restore   Bound    pvc-9717eba4-91e1-4fa5-9982-749ee558e007   1Gi        RWX            csi-cephfs-sc   5s
~~~


スナップショットを元に、PVCを生成する。

~~~
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cephfs-pvc-restore
spec:
  storageClassName: csi-cephfs-sc
  dataSource:
    name: cephfs-pvc-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
~~~
