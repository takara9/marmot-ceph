#!/usr/bin/env python2

import boto.s3.connection
from boto.s3.key import Key

access_key = '33SHVNZYIEU393LR69S4'
secret_key = '9IrU9HvLVGYrd22MO5K8cLS4Vs24IjuLM6p5HttZ'

conn = boto.connect_s3 (
         aws_access_key_id=access_key,
         aws_secret_access_key=secret_key,
         host='172.20.1.31', 
         port=7480,
         is_secure=False, 
         calling_format=boto.s3.connection.OrdinaryCallingFormat(),
       )

bucket = conn.create_bucket('my-new-bucket')


k = Key(bucket)
k.key = 'foobar'
k.set_contents_from_string('This is a test of S3')


for bucket in conn.get_all_buckets():
    print "{name} {created}".format(
        name=bucket.name,
        created=bucket.creation_date,
    )

