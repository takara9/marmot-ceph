

## ブートストラップのオプション

oot@node1:/etc/ceph# cephadm bootstrap -hcephadm
usage: cephadm bootstrap [-h] [--config CONFIG] [--mon-id MON_ID] [--mon-addrv MON_ADDRV | --mon-ip MON_IP] [--mgr-id MGR_ID] [--fsid FSID] [--output-dir OUTPUT_DIR]
                         [--output-keyring OUTPUT_KEYRING] [--output-config OUTPUT_CONFIG] [--output-pub-ssh-key OUTPUT_PUB_SSH_KEY] [--skip-admin-label] [--skip-ssh]
                         [--initial-dashboard-user INITIAL_DASHBOARD_USER] [--initial-dashboard-password INITIAL_DASHBOARD_PASSWORD] [--ssl-dashboard-port SSL_DASHBOARD_PORT]
                         [--dashboard-key DASHBOARD_KEY] [--dashboard-crt DASHBOARD_CRT] [--ssh-config SSH_CONFIG] [--ssh-private-key SSH_PRIVATE_KEY]
                         [--ssh-public-key SSH_PUBLIC_KEY] [--ssh-user SSH_USER] [--skip-mon-network] [--skip-dashboard] [--dashboard-password-noupdate] [--no-minimize-config]
                         [--skip-ping-check] [--skip-pull] [--skip-firewalld] [--allow-overwrite] [--allow-fqdn-hostname] [--allow-mismatched-release] [--skip-prepare-host]
                         [--orphan-initial-daemons] [--skip-monitoring-stack] [--apply-spec APPLY_SPEC] [--shared_ceph_folder CEPH_SOURCE_FOLDER] [--registry-url REGISTRY_URL]
                         [--registry-username REGISTRY_USERNAME] [--registry-password REGISTRY_PASSWORD] [--registry-json REGISTRY_JSON] [--with-exporter]
                         [--exporter-config EXPORTER_CONFIG] [--cluster-network CLUSTER_NETWORK] [--single-host-defaults] [--log-to-file]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        ceph conf file to incorporate
  --mon-id MON_ID       mon id (default: local hostname)
  --mon-addrv MON_ADDRV
                        mon IPs (e.g., [v2:localipaddr:3300,v1:localipaddr:6789])
  --mon-ip MON_IP       mon IP
  --mgr-id MGR_ID       mgr id (default: randomly generated)
  --fsid FSID           cluster FSID
  --output-dir OUTPUT_DIR
                        directory to write config, keyring, and pub key files
  --output-keyring OUTPUT_KEYRING
                        location to write keyring file with new cluster admin and mon keys
  --output-config OUTPUT_CONFIG
                        location to write conf file to connect to new cluster
  --output-pub-ssh-key OUTPUT_PUB_SSH_KEY
                        location to write the cluster's public SSH key
  --skip-admin-label    do not create admin label for ceph.conf and client.admin keyring distribution
  --skip-ssh            skip setup of ssh key on local host
  --initial-dashboard-user INITIAL_DASHBOARD_USER
                        Initial user for the dashboard
  --initial-dashboard-password INITIAL_DASHBOARD_PASSWORD
                        Initial password for the initial dashboard user
  --ssl-dashboard-port SSL_DASHBOARD_PORT
                        Port number used to connect with dashboard using SSL
  --dashboard-key DASHBOARD_KEY
                        Dashboard key
  --dashboard-crt DASHBOARD_CRT
                        Dashboard certificate
  --ssh-config SSH_CONFIG
                        SSH config
  --ssh-private-key SSH_PRIVATE_KEY
                        SSH private key
  --ssh-public-key SSH_PUBLIC_KEY
                        SSH public key
  --ssh-user SSH_USER   set user for SSHing to cluster hosts, passwordless sudo will be needed for non-root users
  --skip-mon-network    set mon public_network based on bootstrap mon ip
  --skip-dashboard      do not enable the Ceph Dashboard
  --dashboard-password-noupdate
                        stop forced dashboard password change
  --no-minimize-config  do not assimilate and minimize the config file
  --skip-ping-check     do not verify that mon IP is pingable
  --skip-pull           do not pull the default image before bootstrapping
  --skip-firewalld      Do not configure firewalld
  --allow-overwrite     allow overwrite of existing --output-* config/keyring/ssh files
  --allow-fqdn-hostname
                        allow hostname that is fully-qualified (contains ".")
  --allow-mismatched-release
                        allow bootstrap of ceph that doesn't match this version of cephadm
  --skip-prepare-host   Do not prepare host
  --orphan-initial-daemons
                        Set mon and mgr service to `unmanaged`, Do not create the crash service
  --skip-monitoring-stack
                        Do not automatically provision monitoring stack (prometheus, grafana, alertmanager, node-exporter)
  --apply-spec APPLY_SPEC
                        Apply cluster spec after bootstrap (copy ssh key, add hosts and apply services)
  --shared_ceph_folder CEPH_SOURCE_FOLDER
                        Development mode. Several folders in containers are volumes mapped to different sub-folders in the ceph source folder
  --registry-url REGISTRY_URL
                        url for custom registry
  --registry-username REGISTRY_USERNAME
                        username for custom registry
  --registry-password REGISTRY_PASSWORD
                        password for custom registry
  --registry-json REGISTRY_JSON
                        json file with custom registry login info (URL, Username, Password)
  --with-exporter       Automatically deploy cephadm metadata exporter to each node
  --exporter-config EXPORTER_CONFIG
                        Exporter configuration information in JSON format (providing: key, crt, token, port information)
  --cluster-network CLUSTER_NETWORK
                        subnet to use for cluster replication, recovery and heartbeats (in CIDR notation network/mask)
  --single-host-defaults
                        adjust configuration defaults to suit a single-host cluster
  --log-to-file         configure cluster to log to traditional log files in /var/log/ceph/$fsid

## メモリの制限

root@node1:/# ceph orch ps
NAME                       HOST   PORTS        STATUS        REFRESHED  AGE  MEM USE  MEM LIM  VERSION  IMAGE ID      CONTAINER ID  
alertmanager.node1         node1  *:9093,9094  running (3d)     6m ago   3d    13.7M        -  0.23.0   ba2b418f427c  36c9e756db3c  
crash.node1                node1               running (3d)     6m ago   3d    7335k        -  16.2.12  921c4e969fff  29ef747d4ded  
crash.node2                node2               running (3d)     6m ago   3d    7824k        -  16.2.12  921c4e969fff  e83b8d9d3c8b  
crash.node3                node3               running (3d)     6m ago   3d    7352k        -  16.2.12  921c4e969fff  98bcf39a0dcb  
crash.node4                node4               running (3d)     6m ago   3d    7340k        -  16.2.12  921c4e969fff  b108066fc015  
crash.node5                node5               running (3d)     6m ago   3d    7228k        -  16.2.12  921c4e969fff  f009d4f4c927  
grafana.node1              node1  *:3000       running (3d)     6m ago   3d    48.0M        -  8.3.5    dad864ee21e9  8b43d1889bbe  
mds.meta_svr.node2.kicmda  node2               running (3d)     6m ago   3d    24.2M        -  16.2.12  921c4e969fff  8705a1c422a3  
mds.meta_svr.node5.zvthhm  node5               running (3d)     6m ago   3d    24.6M        -  16.2.12  921c4e969fff  867a790d48ac  
mgr.node1.wpghae           node1  *:9283       running (3d)     6m ago   3d     495M        -  16.2.12  921c4e969fff  29b5d82040e9  
mgr.node2.uoauna           node2  *:8443,9283  running (3d)     6m ago   3d     384M        -  16.2.12  921c4e969fff  91242f8589df  
mon.node1                  node1               running (3d)     6m ago   3d     430M    2048M  16.2.12  921c4e969fff  84e35dad046d  
mon.node2                  node2               running (3d)     6m ago   3d     270M    2048M  16.2.12  921c4e969fff  3bf8f005ca46  
mon.node3                  node3               running (3d)     6m ago   3d     273M    2048M  16.2.12  921c4e969fff  368bd51c97d6  
mon.node4                  node4               running (3d)     6m ago   3d     269M    2048M  16.2.12  921c4e969fff  e62cb04c9fb8  
mon.node5                  node5               running (3d)     6m ago   3d     268M    2048M  16.2.12  921c4e969fff  e2cbaeb27caa  
node-exporter.node1        node1  *:9100       running (3d)     6m ago   3d    10.8M        -  1.3.1    1dbe0e931976  1ac84bef2c77  
node-exporter.node2        node2  *:9100       running (3d)     6m ago   3d    10.3M        -  1.3.1    1dbe0e931976  4c3555489d49  
node-exporter.node3        node3  *:9100       running (3d)     6m ago   3d    10.9M        -  1.3.1    1dbe0e931976  52ec52f4f7f0  
node-exporter.node4        node4  *:9100       running (3d)     6m ago   3d    10.3M        -  1.3.1    1dbe0e931976  d7fccab9d08a  
node-exporter.node5        node5  *:9100       running (3d)     6m ago   3d    10.8M        -  1.3.1    1dbe0e931976  ebb098e3edcd  
osd.0                      node1               running (3d)     6m ago   3d    49.7M    4096M  16.2.12  921c4e969fff  10c287b14412  
osd.1                      node2               running (3d)     6m ago   3d    48.3M    4096M  16.2.12  921c4e969fff  e4b665b61b2b  
osd.2                      node3               running (3d)     6m ago   3d    45.7M    4096M  16.2.12  921c4e969fff  9df495d36716  
osd.3                      node4               running (3d)     6m ago   3d    46.0M    4096M  16.2.12  921c4e969fff  aa1e745454b6  
osd.4                      node5               running (3d)     6m ago   3d    46.5M    4096M  16.2.12  921c4e969fff  6ccbe6b54145  
prometheus.node1           node1  *:9095       running (3d)     6m ago   3d    89.7M        -  2.33.4   514e6a882f6e  e55e98dd4baa  


