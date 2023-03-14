# ceph pacific の設定メモ

Ceph Pacific では主要モジュールがコンテナで稼働しているので、
アクセス方法も異なる。
参考URL　https://docs.ceph.com/en/pacific/


## セットアップ
~~~
tkr@hmc:~/marmot-ceph$ mactl create
tkr@hmc:~/marmot-ceph$ ansible -i hosts_kvm -m ping all
tkr@hmc:~/marmot-ceph$ ansible-playbook -i hosts_kvm playbook/install.yaml
tkr@hmc:~/marmot-ceph$ ansible-playbook -i hosts_kvm playbook/step2.yaml
tkr@hmc:~/marmot-ceph$ ansible-playbook -i hosts_kvm playbook/step3.yaml
tkr@hmc:~/marmot-ceph$ ansible-playbook -i hosts_kvm playbook/step4.yaml
~~~

* install.yaml Linuxの設定
* setup2.yaml Cephベースの設定
* setup3.yaml ブロックストレージの設定
* setup4.yaml ファイルストレージの設定
* setup5.yaml オブジェクトストレージの設定（途上）



## 起動後の状態確認など


### クラスタの状態確認

~~~
ubuntu@node1:~$ sudo cephadm shell -- ceph status
Inferring fsid dbb9d7ba-c1f9-11ed-830a-41bcb1024539
Using recent ceph image quay.io/ceph/ceph@sha256:748387ea347157fb9df9bb2620d873ac633ff80d0308bcc82a74a821df0d0cfa
  cluster:
    id:     dbb9d7ba-c1f9-11ed-830a-41bcb1024539
    health: HEALTH_ERR
            1 filesystem is offline
            1 filesystem is online with fewer MDS than max_mds

  services:
    mon: 5 daemons, quorum node1,node2,node5,node3,node4 (age 94m)
    mgr: node1.vegtdo(active, since 98m), standbys: node2.gyzdja
    mds: 0/0 daemons up
    osd: 5 osds: 5 up (since 93m), 5 in (since 94m)

  data:
    volumes: 1/1 healthy
    pools:   5 pools, 65 pgs
    objects: 1 objects, 19 B
    usage:   31 MiB used, 500 GiB / 500 GiB avail
    pgs:     65 active+clean
~~~


### ノードのリストとクラスタID

~~~
ubuntu@node1:~$ sudo cephadm shell -- ceph mon dump
Inferring fsid dbb9d7ba-c1f9-11ed-830a-41bcb1024539
Using recent ceph image quay.io/ceph/ceph@sha256:748387ea347157fb9df9bb2620d873ac633ff80d0308bcc82a74a821df0d0cfa
epoch 5
fsid dbb9d7ba-c1f9-11ed-830a-41bcb1024539
last_changed 2023-03-13T23:55:42.193406+0000
created 2023-03-13T23:51:07.455033+0000
min_mon_release 16 (pacific)
election_strategy: 1
0: [v2:172.16.0.31:3300/0,v1:172.16.0.31:6789/0] mon.node1
1: [v2:172.16.0.32:3300/0,v1:172.16.0.32:6789/0] mon.node2
2: [v2:172.16.0.35:3300/0,v1:172.16.0.35:6789/0] mon.node5
3: [v2:172.16.0.33:3300/0,v1:172.16.0.33:6789/0] mon.node3
4: [v2:172.16.0.34:3300/0,v1:172.16.0.34:6789/0] mon.node4
dumped monmap epoch 5
~~~

### Cephブロックストレージのアクセスキー

~~~
ubuntu@node1:~$ sudo cephadm shell -- ceph auth get client.kubernetes
Inferring fsid dbb9d7ba-c1f9-11ed-830a-41bcb1024539
Using recent ceph image quay.io/ceph/ceph@sha256:748387ea347157fb9df9bb2620d873ac633ff80d0308bcc82a74a821df0d0cfa
[client.kubernetes]
	key = AQCtuA9kFap9KhAArc4K4iG4S/v/bJnJMIbNcQ==
	caps mgr = "profile rbd pool=kubernetes"
	caps mon = "profile rbd"
	caps osd = "profile rbd pool=kubernetes"
exported keyring for client.kubernetes
~~~


### CephFSのアクセスキー

~~~
ubuntu@node1:~$ sudo cephadm shell -- ceph auth get client.cephfs
Inferring fsid dbb9d7ba-c1f9-11ed-830a-41bcb1024539
Using recent ceph image quay.io/ceph/ceph@sha256:748387ea347157fb9df9bb2620d873ac633ff80d0308bcc82a74a821df0d0cfa
[client.cephfs]
	key = AQA7yg9kixu1IhAAqJV9wyesJR+ZEso7/7sTDA==
	caps mds = "allow rw"
	caps mgr = "allow rw"
	caps mon = "allow r"
	caps osd = "allow rw tag cephfs *=*"
exported keyring for client.cephfs
~~~


~~~
ubuntu@node1:~$ sudo cephadm shell -- ceph auth get client.cephfs2
Inferring fsid dbb9d7ba-c1f9-11ed-830a-41bcb1024539
Using recent ceph image quay.io/ceph/ceph@sha256:748387ea347157fb9df9bb2620d873ac633ff80d0308bcc82a74a821df0d0cfa
[client.cephfs2]
	key = AQBByg9k0nViIBAAb4x8H1YuQcNi8qqcCdQsnQ==
	caps mds = "allow rw fsname=cephfs"
	caps mon = "allow r fsname=cephfs"
	caps osd = "allow rw tag cephfs data=cephfs"
exported keyring for client.cephfs2
~~~


### エンドポイントのアドレスの確認

~~~
ubuntu@node1:~$ sudo cephadm shell -- ceph mgr services 
Inferring fsid dbb9d7ba-c1f9-11ed-830a-41bcb1024539
Using recent ceph image quay.io/ceph/ceph@sha256:748387ea347157fb9df9bb2620d873ac633ff80d0308bcc82a74a821df0d0cfa
{
    "dashboard": "https://172.16.0.32:8443/",
    "prometheus": "http://172.16.0.32:9283/"
}
~~~


## CSIドライバーとストレージクラスの設定

docs/README.md


