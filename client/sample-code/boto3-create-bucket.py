#!/usr/bin/env python3

import os
import sys
import json
import boto3


if __name__ == '__main__':

    #
    # 認証情報の読み取り
    #
    with open('credentials.json', 'r') as fd:
        credentials = json.loads(fd.read())

    #
    # バケットの作成
    #
    s3r = boto3.resource('s3',
                        endpoint_url=credentials['endpoint_url'],
                        aws_access_key_id=credentials['access_key'],
                        aws_secret_access_key=credentials['secret_key'])
    
    bucket = s3r.Bucket('my_bucket')
    bucket.create()

    #
    # アップロード
    #
    bucket.upload_file(Filename='s3test.py',
                       Key='s3test.py')

    #
    # バケット内オブジェクトのリスト
    #
    s3c = boto3.client('s3',
                      endpoint_url=credentials['endpoint_url'],
                      aws_access_key_id=credentials['access_key'],
                      aws_secret_access_key=credentials['secret_key'])
    
    response = s3c.list_objects_v2(Bucket='my_bucket')
    for item in response['Contents']:
        print(item['Key'])
    

    #
    # ダウンロード
    #
    bucket = s3r.Bucket('my_bucket')
    io = open("/tmp/s3test.py", "wb") 
    bucket.download_fileobj(Fileobj=io, Key='s3test.py')
    
        
    #
    # バケットのリスト
    #
    s3 = boto3.client('s3',
                      endpoint_url=credentials['endpoint_url'],
                      aws_access_key_id=credentials['access_key'],
                      aws_secret_access_key=credentials['secret_key'])
    
    response = s3.list_buckets()
    for item in response['Buckets']:
        print(item['CreationDate'], item['Name'])    
    

