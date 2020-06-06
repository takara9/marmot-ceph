# Ceph学習用のクライアント



## 学習用クライアントの起動

起動する前に、必ず以下のコマンドでsshのための鍵ファイルのディレクトリを、このREADME.mdが存在するディレクトリへコピーしてください。Cephのノードからリモート操作で、クライアントモジュールをインストールするために使用されます。

~~~
cp -r ../ssh .
~~~

仮想サーバーを起動して`vagrant ssh`でログインして操作します。

~~~
vagrant up
vagrant ssh
~~~


## 学習用クライアントのセットアップ

もう一つターミナルを開いて、`vagrant node1` へログインして、Cephのツールをインストールします。 以下のコマンでは、`client`というホストに対して、Cephのバージョン Nautilus をリモートインストールします。そして、次のコマンドで、設定情報をコピーして、Cephクラスタにアクセスできるようにします。

~~~
$ vagrant ssh node1
Welcome to Ubuntu 18.04.3 LTS (GNU/Linux 4.15.0-72-generic x86_64)
<中略>

vagrant@node1:~$ sudo -s
root@node1:~# cd /root
root@node1:~# ceph-deploy install --release nautilus client
root@node1:~# ceph-deploy admin client
~~~

これらの操作によって、クライアントの仮想マシンから、cephのコマンドが実行できるようになります。




## Cephブロックストレージの利用

学習クライアントのターミナルから、ブロックデバイス RBD (RADOS Block Device) イメージを作成して、カーネルのデバイス名とマップすることで、ブロックデバイスとしてアクセスできるようになる。そして、ブロックデバイスにファイルシステムを作成してマウントする。

次のコマンドで、プール blk_data 上に イメージフィーチャーlayering、サイズ 4096 MB で、lv0 を作成する。

~~~
client:~ $ sudo -s
<中略>
client:~# rbd create lv0 --size 4096 --image-feature layering -p blk_data
~~~

Ceph上のブロックデバイスをカーネルのブロックデバイスとマッピング（対応づけ）る。

~~~
client:~# rbd map lv0 -p blk_data
/dev/rbd0
~~~

ファイルシステムでフォーマットする。 

~~~
client:~# mkfs.ext4 -m0 /dev/rbd0
~~~


マウントポイントのディレクトリを作成してマウントする。これで一般のプロセスからアクセス可能となった。

~~~
root@client:~# mkdir /mnt/blk
root@client:~# mount /dev/rbd0 /mnt/blk
root@client:~# df -h
Filesystem      Size  Used Avail Use% Mounted on
<中略>
/dev/rbd0       3.9G   16M  3.9G   1% /mnt/blk
~~~

再起動後は 'rbd map lv0 -p blk_data' により 再マップして 'mount /dev/rbd0 /mnt/blk' する。


#### RBDのリスト表示

次のプール上のRBDをリストできる。

~~~
# rbd ls blk_data
lv0

# rbd create lv1 --size 1024 --image-feature layering -p blk_data
# rbd ls blk_data
lv0
lv1
~~~


#### RBDの情報表示

`rbd info`は ブロックデバイスのサイズ、スナップショット数、作成日などを表示できる。

~~~
# rbd info lv1 -p blk_data
rbd image 'lv1':
	size 1 GiB in 256 objects
	order 22 (4 MiB objects)
	snapshot_count: 0
	id: 11b7171215c2
	block_name_prefix: rbd_data.11b7171215c2
	format: 2
	features: layering
	op_features: 
	flags: 
	create_timestamp: Sat Jun  6 07:03:37 2020
	access_timestamp: Sat Jun  6 07:03:37 2020
	modify_timestamp: Sat Jun  6 07:03:37 2020
~~~


#### RBDの削除

`rbd rm` によってデバイスの削除ができる。

~~~
# rbd rm lv1 -p blk_data
Removing image: 100% complete...done.

# rbd ls blk_data
lv0
~~~



#### 参考資料

* Ceph Basic Block Device Commands, https://docs.ceph.com/docs/master/rbd/rados-rbd-cmds/
* Ceph Kernel Module Operation, https://docs.ceph.com/docs/master/rbd/rbd-ko/






## Cephファイルシステムへのアクセス

こちらもcephfsのためのCephクラスタ側の設定は、AnsibleのPlaybookによって設定済みなので、クライアントだけの設定でマウントができます。

Cephfsにアクセスするためのキーを表示して、クライアント側にファイルを作成します。

~~~
tkr@luigi:~/vagrant-ceph$ vagrant ssh master -c "sudo cat ceph.client.admin.keyring"
[client.admin]
	key = AQCR9w9eyY/4EhAAPoVbB412QsC58KxzIv3ABg==
<以下省略>
~~~

ファイル名は特に何でも良いのですが、`admin.secret`としておきます。

~~~
tkr@luigi:~/vagrant-ceph$ vagrant ssh client
vagrant@client:~$ sudo -
root@client:~# vi admin.secret
root@client:~# cat admin.secret 
AQCR9w9eyY/4EhAAPoVbB412QsC58KxzIv3ABg==
~~~

次は、鍵ファイルを指定してマウントすることができます。node1は予め/etc/hostsに登録してあるので、他に設定は必要ありません。

~~~
root@client:~# mkdir /mnt/fs
root@client:~# mount -t ceph node1:6789:/ /mnt/fs -o name=admin,secretfile=admin.secret

root@client:~# df -h
Filesystem          Size  Used Avail Use% Mounted on
<中略>
/dev/rbd0           3.9G   16M  3.9G   1% /mnt/blk
172.20.1.31:6789:/   93G     0   93G   0% /mnt/fs
~~~


## Amazon S3互換API、OpenStack Swift互換API のオブジェクトストレージアクセス

こちらも`vagrant up`で、Cephクラスタの設定が完了しているので、アクセス用のユーザーを作成して、アクセスするだけです。

管理用ノードにログインして、以下のコマンドでユーザーを作成して、キーを生成します。

~~~
root@master:~# radosgw-admin user create --uid="testuser" --display-name="First User"
root@master:~# radosgw-admin subuser create --uid=testuser --subuser=testuser:swift --access=full
{
    "user_id": "testuser",
    "display_name": "First User",
    "email": "",
    "suspended": 0,
    "max_buckets": 1000,
    "subusers": [
        {
            "id": "testuser:swift",
            "permissions": "full-control"
        }
    ],
    "keys": [　　<-- S3互換
        {
            "user": "testuser",
            "access_key": "APHPYEEV1BFOCXOFYV95",
            "secret_key": "1G2cDndryMZlkhNJDKra7R9CXEsJtPWjE5L6QMmW"
        }
    ],
    "swift_keys": [
        {
            "user": "testuser:swift",
            "secret_key": "hVkJtBBTxxBNUImI4CXAZ1xTvCz59gWfWV96TPPH"
        }
    ],
＜以下省略＞
~~~

### S3 APIでのアクセス

S3 APIのアクセスは、Pythonから実行します。そのためのモジュールをインストールしておきます。

~~~
root@client:~# apt-get install python-boto
~~~

Pythonの後述のコードをコピペで作成しておき、実行して、バケットが作成されたことで確認します。

~~~
root@client:~# vi s3test.py
root@client:~# python s3test.py 
my-new-bucket 2020-01-04T22:39:22.195Z
~~~

以下がS3アクセス用のコードです。IPアドレスは、node1のIPアドレスで、２つのキーを前述のユーザー生成時の応答からコピペして利用すます。

~~~
root@client:~# cat s3test.py 
import boto.s3.connection

access_key = 'APHPYEEV1BFOCXOFYV95'
secret_key = '1G2cDndryMZlkhNJDKra7R9CXEsJtPWjE5L6QMmW'
conn = boto.connect_s3(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        host='172.20.1.31', port=7480,
        is_secure=False, calling_format=boto.s3.connection.OrdinaryCallingFormat(),
       )

bucket = conn.create_bucket('my-new-bucket')
for bucket in conn.get_all_buckets():
    print "{name} {created}".format(
        name=bucket.name,
        created=bucket.creation_date,
    )
~~~

## Swift API でのアクセス

先ほど作成したバケットをSwiftオブジェクトストレージから見えることを確認します。

必要なモジュールをインストールしてきます。

~~~
apt-get install python-setuptools python-pip
pip install --upgrade setuptools
pip install --upgrade python-swiftclient
~~~

swiftコマンドに、キーをユーザーと鍵文字列を設定して、バケットをリストして、確認します。

~~~
root@client:~# swift -V 1 -A http://172.20.1.31:7480/auth -U testuser:swift -K 'hVkJtBBTxxBNUImI4CXAZ1xTvCz59gWfWV96TPPH' list
my-new-bucket
~~~


## 参考URL

* Cephクラスタの構築, https://docs.ceph.com/docs/master/start/quick-ceph-deploy/
* ダッシュボード設定, https://docs.ceph.com/docs/master/mgr/dashboard/#enabling
* ダッシュボード課題対応, https://stackoverflow.com/questions/56696819/ceph-nautilus-how-to-enable-the-ceph-mgr-dashboard
* ブロックストレージ, https://docs.ceph.com/docs/master/start/quick-rbd/
* CephFSアクセス、https://docs.ceph.com/docs/giant/cephfs/createfs/
* CephFSカーネルドライバによるアクセス、https://docs.ceph.com/docs/giant/cephfs/kernel/
* S3/Swiftオブジェクトストレージ,https://docs.ceph.com/docs/master/install/install-ceph-gateway/
