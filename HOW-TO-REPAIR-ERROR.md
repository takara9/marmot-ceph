# エラー発生時の修復

## CASE-1 HEALTH_ERR データを保管するpgブロックの破損

エラーのメッセージ Possible data damage

~~~
root@mon1:~# ceph status
  cluster:
    id:     2f31e764-2087-425f-9336-10369b4ad611
    health: HEALTH_ERR
            1 scrub errors
            Possible data damage: 1 pg inconsistent
~~~

詳細の表示と、修復対象箇所の特定

~~~
root@mon1:~# ceph health detail
HEALTH_ERR 1 scrub errors; Slow OSD heartbeats on back (longest 1468.955ms); Slow OSD heartbeats on front (longest 1468.993ms); Possible data damage: 1 pg inconsistent
[ERR] OSD_SCRUB_ERRORS: 1 scrub errors
[WRN] OSD_SLOW_PING_TIME_BACK: Slow OSD heartbeats on back (longest 1468.955ms)
    Slow OSD heartbeats on back from osd.7 [] to osd.4 [] 1468.955 msec
    Slow OSD heartbeats on back from osd.7 [] to osd.6 [] 1468.391 msec
    Slow OSD heartbeats on back from osd.7 [] to osd.0 [] 1464.605 msec
    Slow OSD heartbeats on back from osd.7 [] to osd.2 [] 1464.442 msec
    Slow OSD heartbeats on back from osd.0 [] to osd.7 [] 1303.725 msec
    Slow OSD heartbeats on back from osd.0 [] to osd.3 [] 1303.616 msec
    Slow OSD heartbeats on back from osd.0 [] to osd.1 [] 1303.513 msec
    Slow OSD heartbeats on back from osd.0 [] to osd.5 [] 1303.492 msec
[WRN] OSD_SLOW_PING_TIME_FRONT: Slow OSD heartbeats on front (longest 1468.993ms)
    Slow OSD heartbeats on front from osd.7 [] to osd.4 [] 1468.993 msec
    Slow OSD heartbeats on front from osd.7 [] to osd.6 [] 1468.576 msec
    Slow OSD heartbeats on front from osd.7 [] to osd.2 [] 1468.324 msec
    Slow OSD heartbeats on front from osd.7 [] to osd.0 [] 1464.737 msec
    Slow OSD heartbeats on front from osd.0 [] to osd.7 [] 1303.673 msec
    Slow OSD heartbeats on front from osd.0 [] to osd.5 [] 1303.559 msec
    Slow OSD heartbeats on front from osd.0 [] to osd.3 [] 1303.491 msec
    Slow OSD heartbeats on front from osd.0 [] to osd.1 [] 1303.479 msec
[ERR] PG_DAMAGED: Possible data damage: 1 pg inconsistent
    pg 8.c is active+clean+inconsistent, acting [6,4,7]
~~~


pg 8.c に対して、修復コマンド投入

~~~
root@mon1:~# ceph pg repair 8.c
instructing pg 8.c on osd.6 to repair
~~~

修復結果確認

~~~
root@mon1:~# ceph status
  cluster:
    id:     2f31e764-2087-425f-9336-10369b4ad611
    health: HEALTH_OK
~~~



## CASE-2 HEALTH_WARN モニタのダウン

エラーメッセージ 1/7 mons down, quorum mon1,mon2,mon3,node2,node3,node4
これから、ステータスでモニターの一つ node1 のモニターが落ちていることが解る。

~~~
root@mon1:~# ceph status
  cluster:
    id:     2f31e764-2087-425f-9336-10369b4ad611
    health: HEALTH_WARN
            1/7 mons down, quorum mon1,mon2,mon3,node2,node3,node4
 
  services:
    mon: 7 daemons, quorum mon1,mon2,mon3,node2,node3,node4 (age 15h), out of quorum: node1
    mgr: mon3(active, since 2w), standbys: mon2, mon1
    mds: cephfs:1 {0=mon1=up:active} 2 up:standby
    osd: 8 osds: 8 up (since 101m), 8 in (since 3w)
    rgw: 3 daemons active (mon1, mon2, mon3)
~~~


詳細を表示しても同様にnode1が止まっている。

~~~
root@mon1:~# ceph health detail
HEALTH_WARN 1/7 mons down, quorum mon1,mon2,mon3,node2,node3,node4
[WRN] MON_DOWN: 1/7 mons down, quorum mon1,mon2,mon3,node2,node3,node4
    mon.node1 (rank 3) addr [v2:172.16.0.31:3300/0,v1:172.16.0.31:6789/0] is down (out of quorum)
~~~


node1 に入って、モニターデーモンを再起動してみる。

~~~
root@node1:/var/log/ceph# systemctl restart ceph-mon@node1.service
~~~

再起動結果の確認

~~~
root@node1:/var/log/ceph# systemctl status ceph-mon@node1.service
● ceph-mon@node1.service - Ceph cluster monitor daemon
   Loaded: loaded (/lib/systemd/system/ceph-mon@.service; indirect; vendor preset: enabled)
   Active: active (running) since Tue 2021-11-02 10:19:29 UTC; 347ms ago
 Main PID: 11816 (ceph-mon)
    Tasks: 26
   CGroup: /system.slice/system-ceph\x2dmon.slice/ceph-mon@node1.service
           └─11816 /usr/bin/ceph-mon -f --cluster ceph --id node1 --setuser ceph --setgroup ceph
~~~

一度、起動に成功したが、しばらくすると落ちてしまう。

~~~
root@node1:/var/log/ceph# systemctl status ceph-mon@node1.service
● ceph-mon@node1.service - Ceph cluster monitor daemon
   Loaded: loaded (/lib/systemd/system/ceph-mon@.service; indirect; vendor preset: enabled)
   Active: failed (Result: signal) since Tue 2021-11-02 10:20:09 UTC; 25s ago
  Process: 11906 ExecStart=/usr/bin/ceph-mon -f --cluster ${CLUSTER} --id node1 --setuser ceph --setgroup ceph (code=killed, signal=ABRT)
 Main PID: 11906 (code=killed, signal=ABRT)
~~~

原因を調べるために、/var/log/ceph/ceph-mon.node1.log を調べる。
行番号を付けて、less でerrorを検索する。　以下のように、Corruption:が見つかった。

~~~
root@node1:/var/log/ceph# cat -n /var/log/ceph/ceph-mon.node1.log |less
  9476     -13> 2021-11-02T09:04:55.964+0000 7f0cd6e20700  3 rocksdb: [db/db_impl_compaction_flush.cc:2660] Compaction error: Corruption: block checksum mismatch: expected 97447552, got 920580140  in /var/lib/ceph/mon/ceph-node1/store.db/057059.sst offset 12418567 size 27949
~~~


このエラーメッセージにあるモニターストアDBのファイル`/var/lib/ceph/mon/ceph-node1/store.db/057059.sst`が壊れている。壊れる原因が解らないが、修復しなければならない。


ここで、正常に動作するモニターデーモンの数が重要となり、以下の判断をしなければならない。
【判断】他のモニターが実行中で、quorum を形成できていれば、復旧できる。



壊れたモニターを削除する。今回 node1 なので、他のモニターが壊れた時は、node1を置き換えて読むこと。

~~~
root@mon1:~# ceph mon remove node1
removing mon.node1 at [v2:172.16.0.31:3300/0,v1:172.16.0.31:6789/0], there will be 6 monitors
~~~

削除されたことを確認

~~~
root@mon1:~# ceph mon stat
e2: 6 mons at {mon1=[v2:172.16.0.21:3300/0,v1:172.16.0.21:6789/0],mon2=[v2:172.16.0.22:3300/0,v1:172.16.0.22:6789/0],mon3=[v2:172.16.0.23:3300/0,v1:172.16.0.23:6789/0],node2=[v2:172.16.0.32:3300/0,v1:172.16.0.32:6789/0],node3=[v2:172.16.0.33:3300/0,v1:172.16.0.33:6789/0],node4=[v2:172.16.0.34:3300/0,v1:172.16.0.34:6789/0]}, election epoch 5466, leader 0 mon1, quorum 0,1,2,3,4,5 mon1,mon2,mon3,node2,node3,node4
~~~

もし/etc/cephにキーリングファイルが無い場合は、
node1でcephコマンドが動作するように、mon1のキーリングファイルをnode1の/etc/cephに置く

~~~
root@mon1:/etc/ceph# scp ceph.client.admin.keyring node1:/etc/ceph
~~~


ここからssh で node1に入って、操作する。

/var/lib/ceph/mon/ceph-node1の下にある壊れたデータセットは、ディレクトリごと削除して、新たにディレクトリを作る。

~~~
root@node1:~# cd /var/lib/ceph/mon/
root@node1:/var/lib/ceph/mon# ls
ceph-node1
root@node1:/var/lib/ceph/mon# rm -fr ceph-node1/
root@node1:/var/lib/ceph/mon# mkdir  ceph-node1/
root@node1:/var/lib/ceph/mon# chown ceph:ceph ceph-node1/
~~~

キーリングファイルとマップファイルを一時的に置く場所を作る。

~~~
root@node1:/var/lib/ceph/mon# mkdir tmp
~~~

キーリングファイルを書き出す。

~~~
root@node1:/var/lib/ceph/mon# ceph auth get mon. -o tmp/ceph.keyring
exported keyring for mon.
~~~

マップファイルを書き出す。

~~~
root@node1:/var/lib/ceph/mon# ceph mon getmap -o tmp/mapfile
got monmap epoch 2
~~~

node1のモニターを作成する。

~~~
root@node1:/var/lib/ceph/mon# ceph-mon -i node1 --mkfs --monmap tmp/mapfile --keyring tmp/ceph.keyring
~~~

Cephクラスタのメンバーに作成したnode1のモニターを開始する。

~~~
root@node1:/var/lib/ceph/mon# ceph-mon -i node1 --public-addr 172.16.0.31
~~~

これで、モニターが復活していることを、ダッシュボードや 'ceph status' から確認する。この状態は、コマンドラインから直接モニターデーモンを起動したことになるので、'ceph mon ok-to-stop node1'で停止させる。そして、'systemctl start ceph-mon@node1' でスタートさせる。そして、'systemctl status ceph-mon@node1' のコマンドで正常に稼働していることを確認する。



## CASE-3 insufficient standby MDS daemons available

mdsデーモンが複数ダウンして、警告が出る。

~~~
# ceph status
  cluster:
    id:     2f31e764-2087-425f-9336-10369b4ad611
    health: HEALTH_WARN
            insufficient standby MDS daemons available
            1/7 mons down, quorum mon1,mon2,mon3,node2,node3,node4
            34 daemons have recently crashed
 
  services:
    mon: 7 daemons, quorum mon1,mon2,mon3,node2,node3,node4 (age 11m), out of quorum: node1
    mgr: mon3(active, since 2d), standbys: mon1, mon2
    mds: cephfs:1 {0=mon3=up:active}
    osd: 8 osds: 8 up (since 16h), 8 in (since 4w)
    rgw: 3 daemons active (mon1, mon2, mon3)

~~~

mdsデーモンが落ちているノードで、リスタートを実行する。

~~~
# systemctl restart ceph-mds@mon1
~~~



## CASE-4 daemons have recently crashed

以下の状態をクリアする方法

~~~
root@node1:/var/lib/ceph/mon# ceph status
  cluster:
    id:     2f31e764-2087-425f-9336-10369b4ad611
    health: HEALTH_WARN
            28 daemons have recently crashed
~~~

以下のようにクラッシュのリストを表示して、詳細を確認、個別に消すか、全部を一度に消す

~~~
ceph crash ls
ceph crash info 2021-11-09T17:19:54.048597Z_442ccb50-c02f-4be0-978c-7540f87128c7
ceph crash archive 2021-11-09T17:19:54.048597Z_442ccb50-c02f-4be0-978c-7540f87128c7
または
ceph crash archive-all
~~~


## CASE-5 PVCは出来るが、PodがContainerCreating から何時間経過しても進まない。

以下の様な状態になり、先へ進まなくなる。

~~~
maho:rbd maho$ kubectl get pod
NAME                          READY   STATUS              RESTARTS   AGE
test-rbd-1                    0/1     ContainerCreating   0          25s
~~~

'kubectl describe pod' でEventログを表示すると、以下のようなエラーメッセージが表示される。

~~~
Events:
  Type     Reason                  Age               From                     Message
  ----     ------                  ----              ----                     -------
  Warning  FailedMount             1s (x6 over 33s)  kubelet                  MountVolume.MountDevice failed for volume "pvc-ffa8a9de-6fed-4663-9279-a03441df1f84" : rpc error: code = Aborted desc = an operation with the given Volume ID 0001-0024-2f31e764-2087-425f-9336-10369b4ad611-0000000000000008-436bdf6e-4375-11ec-a9c0-225c7abf2bb3 already exists
~~~

Cephのモニターノードにログインして、ヘルスチュックしてもOKとなる場合、CSIプラグインに問題があると判別できる。

~~~
root@mon1:~# ceph health
HEALTH_OK
~~~


対応方法は、CSIプラグインのポッドを削除して再スタートさせる。

~~~
maho:rbd maho$ kubectl get pod -n ceph-csi
NAME                                            READY   STATUS    RESTARTS   AGE
csi-rbdplugin-4j8pf                             3/3     Running   0          27d
csi-rbdplugin-fdvs9                             3/3     Running   3          27d
csi-rbdplugin-provisioner-56f98557c8-lcd7p      7/7     Running   0          9m58s
csi-rbdplugin-provisioner-56f98557c8-nvxkj      7/7     Running   0          6m21s
csi-rbdplugin-provisioner-56f98557c8-xr6xt      7/7     Running   0          6m49s
csi-rbdplugin-w9gqk                             3/3     Running   0          27d
maho:rbd maho$ kubectl delete pod -n ceph-csi csi-rbdplugin-4j8pf 
pod "csi-rbdplugin-4j8pf" deleted
maho:rbd maho$ kubectl delete pod -n ceph-csi csi-rbdplugin-fdvs9 
pod "csi-rbdplugin-fdvs9" deleted
maho:rbd maho$ kubectl delete pod -n ceph-csi csi-rbdplugin-w9gqk  
pod "csi-rbdplugin-w9gqk" deleted
~~~

これで、再度デプロイを行ってみると、Podの生成とPVCのマウントに成功した。




## CASE-6 ceph statusが応答しない。 ブラウザのCeph consoleにアクセスできない。

Cephのモニターノードにログインして、'ceph status' を実行しても応答がない。
ブラウザで、Cephコンソールにアクセスしても、応答がない。

原因は、ファイルシステムに空きスペースが無くなり、書き込みが出来なくなっている。

~~~
root@mon1:~# df -h
Filesystem      Size  Used Avail Use% Mounted on
udev            1.9G     0  1.9G   0% /dev
tmpfs           395M   41M  355M  11% /run
/dev/vda2        12G   12G     0 100% /
tmpfs           2.0G     0  2.0G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           2.0G     0  2.0G   0% /sys/fs/cgroup
tmpfs           395M     0  395M   0% /run/user/1000
root@mon1:~# du / |sort -rn |less
12300540        /
9395984 /var
8015296 /var/log
7293312 /var/log/ceph
2122288 /usr
1287536 /var/lib
1090020 /var/lib/ceph
1089912 /var/lib/ceph/mon
1089908 /var/lib/ceph/mon/ceph-mon1
1089892 /var/lib/ceph/mon/ceph-mon1/store.db
846224  /usr/lib
719664  /var/log/journal
686880  /var/log/journal/b40e439c277f11ec9662c766898227f6
686572  /usr/bin
625248  /lib
~~~

対策として、ノードのログを別のサーバーに転送したあとログを削除して、再起動する。

~~~
root@mon1:/var/log/ceph# rm *.gz
root@mon1:/var/log/ceph# df -h
Filesystem      Size  Used Avail Use% Mounted on
udev            1.9G     0  1.9G   0% /dev
tmpfs           395M   41M  355M  11% /run
/dev/vda2        12G   12G     0 100% /
tmpfs           2.0G     0  2.0G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           2.0G     0  2.0G   0% /sys/fs/cgroup
tmpfs           395M     0  395M   0% /run/user/1000

root@mon1:/var/log/ceph# rm ceph.log.1
root@mon1:/var/log/ceph# df -h
Filesystem      Size  Used Avail Use% Mounted on
udev            1.9G     0  1.9G   0% /dev
tmpfs           395M   41M  355M  11% /run
/dev/vda2        12G  4.8G  6.4G  44% /
tmpfs           2.0G     0  2.0G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           2.0G     0  2.0G   0% /sys/fs/cgroup
tmpfs           395M     0  395M   0% /run/user/1000
~~~

すべてのノードの対処が完了したら、ceph status のコマンドが正常に戻る。


## 参考資料

1. Red Hat Ceph Storage 初期のトラブルシューティングガイド
https://access.redhat.com/documentation/ja-jp/red_hat_ceph_storage/2/html/troubleshooting_guide/initial-troubleshooting#diagnosing-the-health-of-a-ceph-storage-cluster

2. Ceph Troubleshooting PGs
https://docs.ceph.com/en/octopus/rados/troubleshooting/troubleshooting-pg/?highlight=repair#troubleshooting-pgs

3. Ceph Troubleshooting Monitors
https://docs.ceph.com/en/octopus/rados/troubleshooting/troubleshooting-mon/

