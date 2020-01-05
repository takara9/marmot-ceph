# Vagrantノード上にCephクラスタを構築するAnsible


## 概要

これはパソコンのVagrant上で以下のノードを起動してCephクラスタの仕組みを理解する為のコードです。

~~~
1. master   172.20.1.30  192.168.1.90  管理ノード
1. node1    172.20.1.31　              ストレージノード
1. node2    172.20.1.32                ストレージノード
1. node3    172.20.1.33                ストレージノード
1. client   172.20.1.229               テスト用クライアント
~~~


## このクラスタを起動するために必要なソフトウェア

このコードを利用するためには、次のソフトウェアを必要とします。

* Vagrant (https://www.vagrantup.com/)
* VirtualBox (https://www.virtualbox.org/)
* kubectl (https://kubernetes.io/docs/tasks/tools/install-kubectl/)
* git (https://kubernetes.io/docs/tasks/tools/install-kubectl/)


## 仮想マシンのホスト環境

Vagrant と VirtualBox が動作するOSが必要です。

* Windows10　
* MacOS
* Linux

推奨ハードウェアとして、必要なリソースは以下です。

* RAM: 16GB 以上
* ストレージ: 空き領域 10GB 以上
* CPU: Intel Core i5 以上


## Cephクラスタの起動手順

GitHubからクローンして、Vagrantで仮想マシンを起動すると、Ansibleで自動設定します。その内容は、クラスタのノード同士が、sshで連携できる様にします。そして、ceph-deployを管理ノードにインストールして、ceph-deployのコマンドで、クラスタを構築していきます。また、ダッシュボードも自動設定します。

アクセステストのために、クライアントをセットアップして、ブロックストレージ、ファイルストレージ、オブジェクトストレージをアクセスする部分は、自動化していませんから、自身で作業する必要があります。

```
$ git clone https://github.com/takara9/vagrant-ceph
$ cd vagrant-ceph
$ vagrant up
```


## Cephダッシュボードのアクセス

MacやWindowsのパソコン内で起動した場合は、https://172.20.1.30:8443/ にアクセスすることで、Cephダッシュボードが起動します。ユーザーとパスワードは、`admin` / `password` です。また、Linux 上のVagrantで起動した場合は、https://192.168.1.90:8443/ として、パソコン上のNICにIPアドレスを追加して起動します。利用者自身のLAN環境に合わせて、Vagrantfile のIPアドレスは変更してください。


## 検証用クライアントのセットアップ

既にsshで連携する為の、鍵ファイルやsshの設定は完了しているので、管理用ノードにログインして、deploy-cephでリモートインストールするだけです。

以下のコマンでは、`client`というホストに対して、Cephのバージョン Nautilus をリモートインストールします。そして、次のコマンドで、設定情報をコピーして、Cephクラスタにアクセスできるようにします。

~~~
maho:cepf maho$ vagrant ssh master
Welcome to Ubuntu 18.04.3 LTS (GNU/Linux 4.15.0-72-generic x86_64)
<中略>

vagrant@master:~$ sudo -s
root@master:~# ceph-deploy install --release nautilus client
root@master:~# ceph-deploy admin client
~~~

これらのコマンドによって、クライアントのノードから、cephのコマンドが実行できるようになります。とっても簡単ですね。



## Cephブロックストレージの利用

Cephはパソコンやサーバーなどの内臓ディスクと同じようにアクセスする手段を提供します。その為のブロックストレージをアクセスする為のOSDとプールは作成済みなので、ここではクライアントにログインして、マウントする為のコマンドを実行するだけです。以下の操作の前に`vagrant ssh client`でクライアント役の仮想マシンにログインして、`sudo -s`で root で作業します。

論理ボリュームの作成lv0は、既に作成済みのプール blk_dataを指定して作成した後、ローカルマシンのデバイスとして対応づけます。次に、ファイルシステムとしてフォーマットして準備完了です。

~~~
maho:cepf maho$ vagrant ssh client
Welcome to Ubuntu 18.04.3 LTS (GNU/Linux 4.15.0-72-generic x86_64)
<中略>

vagrant@client:~$ sudo -s
root@client:~# rbd create lv0 --size 4096 --image-feature layering -p blk_data
root@client:~# rbd map lv0 -p blk_data
/dev/rbd0
root@client:~# mkfs.ext4 -m0 /dev/rbd/blk_data/lv0
~~~

マウントポイントのディレクトリを作成して、マウントします。これでアクセス可能となりました。

~~~
root@client:~# mkdir /mnt/blk
root@client:~# mount /dev/rbd/blk_data/lv0 /mnt/blk
root@client:~# df -h
Filesystem      Size  Used Avail Use% Mounted on
<中略>
/dev/rbd0       3.9G   16M  3.9G   1% /mnt/blk
~~~

## Cephファイルシステムへのアクセス

こちらもcephfsのためのCephクラスタ側の設定は、AnsibleのPlaybookによって設定済みなので、クライアントだけの設定でマウントができます。

Cephfsにアクセスするためのキーを表示して、クライアント側にファイルを作成します。

~~~
tkr@luigi:~/vagrant-ceph$ vagrant ssh master -c "cat ceph.client.admin.keyring"
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
