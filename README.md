# 最小のCephクラスタのVagrant+Ansible


## 概要

これはパソコンのVagrant上で以下のノードを起動してCephクラスタの仕組みを理解する為のコードです。

~~~
1. node1    172.20.1.31  192.168.1.91  Cephノード1 兼 管理ノード
1. node2    172.20.1.32                Cephノード2
1. node3    172.20.1.33                Cephノード3
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

MacやWindowsのパソコン内で起動した場合は、https://172.20.1.31:8443/ にアクセスすることで、Cephダッシュボードが起動します。ユーザーとパスワードは、`admin` / `password` です。また、Linux 上のVagrantで起動した場合は、https://192.168.1.91:8443/ として、パソコン上のNICにIPアドレスを追加して起動します。利用者自身のLAN環境に合わせて、Vagrantfile のIPアドレスは変更してください。




## クライアントのセットアップ

Cephクラスタが提供するストレージを利用するための学習用クライアントは、[client](client) にありますので参考に利用方法を習得できます。



## 参考URL

* Cephクラスタの構築, https://docs.ceph.com/docs/master/start/quick-ceph-deploy/
* ダッシュボード設定, https://docs.ceph.com/docs/master/mgr/dashboard/#enabling
* ダッシュボード課題対応, https://stackoverflow.com/questions/56696819/ceph-nautilus-how-to-enable-the-ceph-mgr-dashboard
* ブロックストレージ, https://docs.ceph.com/docs/master/start/quick-rbd/
* CephFSアクセス、https://docs.ceph.com/docs/giant/cephfs/createfs/
* CephFSカーネルドライバによるアクセス、https://docs.ceph.com/docs/giant/cephfs/kernel/
* S3/Swiftオブジェクトストレージ,https://docs.ceph.com/docs/master/install/install-ceph-gateway/
