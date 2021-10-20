# エラー発生時の修復

## HEALTH_ERR

エラーのメッセージ

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

