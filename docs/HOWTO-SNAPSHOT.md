# スナップショットの設定とテスト方法

## 参考資料
https://github.com/kubernetes-csi/external-snapshotter


スナップショットを動作させるには、事前のスナップショッターの設定が必要となる。
設定ができていない場合、以下のようなエラーが発生する。

~~~
$ kubectl apply -f snapshotclass.yaml 
error: unable to recognize "snapshotclass.yaml": no matches for kind "VolumeSnapshotClass" in version "snapshot.storage.k8s.io/v1"
~~~




## スナップショッターのデプロイ

snapshotterのディレクトリに移動して、名前空間ceph-csiで、以下３種をデプロイする。

~~~
$ cd snapshotter
kubectl config use-context ceph
kubectl apply -f crd
kubectl apply -f snapshot-controller
kubectl apply -f csi-snapshotter/
~~~

スナップショットコントローラーのポッドが稼働していることを確認する

~~~
$ kubectl get po -n ceph-csi csi-snapshotter-0 
NAME                READY   STATUS    RESTARTS   AGE
csi-snapshotter-0   3/3     Running   0          105m
~~~

デプロイした結果、以下のAPIが追加されていることを確認する

~~~
$ kubectl api-resources --api-group=snapshot.storage.k8s.io
NAME                     SHORTNAMES   APIVERSION                   NAMESPACED   KIND
volumesnapshotclasses                 snapshot.storage.k8s.io/v1   false        VolumeSnapshotClass
volumesnapshotcontents                snapshot.storage.k8s.io/v1   false        VolumeSnapshotContent
volumesnapshots                       snapshot.storage.k8s.io/v1   true         VolumeSnapshot
~~~


