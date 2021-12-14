# オブジェクトストレージの利用方法

Cephをインストールした直後では、オブジェクトストレージを利用できない。
RADOSGWを追加でインストール、インスタンスを起動したあと、
ユーザーを設定して、Webダッシュボードからアクセスできるようにすることで、
オブジェクトストレージが本格的に利用できるようになる。


## オブジェクトストレージの設定

Cephのmon1にログインして、ceph-deploy, radosgw-admin, cephコマンドを実行して設定する。

(1) RADOSGWのインストールと起動を次のコマンドで実行する

~~~
ceph-deploy install --rgw mon1 mon2 mon3
ceph-deploy admin mon1 mon2 mon3
ceph-deploy rgw create mon1 mon2 mon3
~~~


(2) radosgwのユーザーを作成する

~~~
# radosgw-admin user create --uid=tkr --display-name="Maho Takara" --system
~~~


(3) access-keyとsecret-keyを取得して、ファイルに保存する

~~~
# radosgw-admin user info --uid=tkr|jq '.keys' |jq '.[0]' |jq '.access_key' |sed s/\"//g | tee access-key
X3X9FQM1N0JUVGWBMU36

# radosgw-admin user info --uid=tkr|jq '.keys' |jq '.[0]' |jq '.secret_key' |sed s/\"//g | tee secret-key
6teO7BwloiBAlJyKjxVOAH6ybJSvnCcFCV4D1UTH
~~~


(4) Webのダッシュボードから、RADOSGWをアクセスできるようにキーをセットする

~~~
# ceph dashboard set-rgw-api-access-key -i access-key
Option RGW_API_ACCESS_KEY updated

# ceph dashboard set-rgw-api-secret-key -i secret-key
Option RGW_API_SECRET_KEY updated
~~~

(5) 動作確認として、mon1, mon2, mon3 のIPアドレスをcurlでアクセスしてレスポンスを確認する。

~~~
$ curl http://192.168.1.227:7480;echo
<?xml version="1.0" encoding="UTF-8"?><ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner><ID>anonymous</ID><DisplayName></DisplayName></Owner><Buckets></Buckets></ListAllMyBucketsResult>
~~~



## AWS S3クライアントからのアクセス

botoは、AWSのサービスを利用するためのPythonのAPIライブラリである。
これを利用したCephをオブジェクトストレージを利用するコードを開示する。

Pythonを実行できる環境で以下を実行することで、
Ceph S3互換 オブジェクトストレージを利用できる。

~~~
##
## Ceph RADOSGW Test
## 機能
##  1 バケットを作成
##  2 オブジェクトを作成して文字列の書き込み
##  3 文字列の書かれたオブジェクトをローカルのファイルにダウンロード
##  4 ファイルのアップロードとダウンロード

## このPythonのコードを実行する前に、botoのモジュールをインストール
## pip install boto
##  botoは、AWS S3 をアクセスするためのライブラリで、次のリンクにドキュメントがある。
##  http://boto.cloudhackers.com/
##
import boto.s3.connection

## Ceph RADOSGWのユーザーに付与されたアクセスキーとシークレット
## 取得方法は、Cephのモニターノードにログインして以下を実行
##   radosgw-admin user info --uid=<user_id>
## ユーザーの作成は、以下で良い
##   radosgw-admin user create --uid=<user_id> --display-name="Your Name" --system
##
access_key = 'X3X9FQM1N0JUVGWBMU36'
secret_key = '6teO7BwloiBAlJyKjxVOAH6ybJSvnCcFCV4D1UTH'

## host_name は、Ceph モニターノードのホスト名やIPアドレスを設定（文字列）
## host_port は、RADOSGW のポート番号 (数値)
##
host_name  = '192.168.1.227'
host_port  = 7480

## S3サーバーへ接続
##
conn = boto.connect_s3(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    host=host_name,
    port=host_port,
    is_secure=False,
    calling_format=boto.s3.connection.OrdinaryCallingFormat(),
)

## バケットを作成
##
bucket = conn.create_bucket('my-new-bucket')

## パケットのリスト表示
##
for bucket in conn.get_all_buckets():
    print "{name} {created}".format(
        name=bucket.name,
        created=bucket.creation_date,
    )


## バケットにテキストのデータを出力
##
bucket = conn.get_bucket('my-new-bucket')
key = bucket.new_key('hello.txt')
key.set_contents_from_string('Hello World!')

## ファイルとしてダウンロード
##
key.get_contents_to_filename('/hello.txt')


## 新たなキーを作成
key2 = bucket.new_key('test.dat')

## ローカルのデータをアップロード
key2.set_contents_from_filename('test.dat')

## オブジェクトをダウンロード
key2.get_contents_to_filename('download.dat')
~~

