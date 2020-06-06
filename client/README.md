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

もう一つターミナルを開いて、`vagrant node1` へログインして、Cephのツールをリモート・インストールします。 以下のコマンでは、`client`というホストに対して、Cephのバージョン Nautilus をリモートインストールします。そして、次のコマンドで、設定情報をコピーして、Cephクラスタにアクセスできるようにします。

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




# Cephブロックストレージの利用

学習クライアントのターミナルから、ブロックデバイス RBD (RADOS Block Device) イメージを作成して、カーネルのデバイス名とマップすることで、ブロックデバイスとしてアクセスできるようになる。そして、ブロックデバイスにファイルシステムを作成してマウントする。

#### RBDの作成

次のコマンドで、プール blk_data 上に イメージフィーチャーlayering、サイズ 4096 MB で、lv0 を作成する。

~~~
client:~ $ sudo -s
<中略>
client:~# rbd create lv0 --size 4096 --image-feature layering -p blk_data
~~~


#### カーネルデバイスとのマッピング

Ceph上のブロックデバイスをカーネルのブロックデバイスとマッピング（対応づけ）る。

~~~
client:~# rbd map lv0 -p blk_data
/dev/rbd0
~~~


#### ファイルシステムのマウント

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






# CephFSの利用

#### 認証情報の取得

CephFSにアクセスするためにvagrant ホストからnode1を指定してキーを表示して、クライアント側にファイルを作成する。

~~~
$ vagrant ssh node1 -c "sudo cat /root/ceph.client.admin.keyring"
[client.admin]
	key = AQC0DNte1MCaNhAAU2nqHMw5bO+xIULhBgf2wg==
	caps mds = "allow *"
	caps mgr = "allow *"
	caps mon = "allow *"
	caps osd = "allow *"
<以下省略>
~~~


ファイル名はmountコマンドのオプションとして指定するので、後で分かり易い名前`admin.secret`にしておく。

~~~
$ vagrant ssh client
$ sudo -s
# cat - > admin.secret
AQCR9w9eyY/4EhAAPoVbB412QsC58KxzIv3ABg==
ctrl-D
~~~

マウントポイントを作成して、マウントする。

~~~
# mkdir /mnt/fs
# mount -t ceph node1:6789:/ /mnt/fs -o name=admin,secretfile=admin.secret

# df -h
Filesystem          Size  Used Avail Use% Mounted on
<中略>
/dev/rbd0           3.9G   16M  3.9G   1% /mnt/blk
172.20.1.31:6789:/   93G     0   93G   0% /mnt/fs
~~~


アンマウントは 'umount' コマンドを利用する。


参考資料
* Ceph Mount CephFS using Kernel Driver, https://docs.ceph.com/docs/master/cephfs/mount-using-kernel-driver/





# オブジェクトストレージ

Ceph オブジェクト・ゲートウェイは Amazon S3 互換API、OpenStack Swift互換APIを提供する。


#### アクセスキーの生成

クライアントからのアクセスのまに、node1にログインしてアクセスキーを生成する。このコマンドではS3互換のアクセスキーとシークレットキーが生成される。

~~~
$ vagrant ssh node1
$ sudo -s
root@node1:~# radosgw-admin user create --uid="testuser" --display-name="First User"
{
    "user_id": "testuser",
    "display_name": "First User",
    "email": "",
    "suspended": 0,
    "max_buckets": 1000,
    "subusers": [],
    "keys": [
        {
            "user": "testuser",
            "access_key": "33SHVNZYIEU393LR69S4",
            "secret_key": "9IrU9HvLVGYrd22MO5K8cLS4Vs24IjuLM6p5HttZ"
        }
    ],
    "swift_keys": [],
    <以下省略>
}
~~~

次のコマンドではSWIFT互換のキーを生成できる


~~~
root@node1:~# radosgw-admin subuser create --uid=testuser --subuser=testuser:swift --access=full
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
    "keys": [
        {
            "user": "testuser",
            "access_key": "33SHVNZYIEU393LR69S4",
            "secret_key": "9IrU9HvLVGYrd22MO5K8cLS4Vs24IjuLM6p5HttZ"
        }
    ],
    "swift_keys": [
        {
            "user": "testuser:swift",
            "secret_key": "FQLP4X6nK46a08BReIrQOTsjZ7LuQAITfYdLH5Wj"
        }
    ],
    <以下省略>    
}
~~~




#### AWS S3 APIアクセス


ディレクトリclientの下、sample-codeにAWS S3にアクセスするためのサンプルコードを置いておく。

~~~
client/
├── README.md
├── Vagrantfile
├── playbooks
│   ├── hosts
│   └── install_node.yaml
└── sample-code
    ├── boto-create-bucket.py
    ├── boto3-create-bucket.py
    └── credentials.json
~~~



## OpenStack Swift API アクセス

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
