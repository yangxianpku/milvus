# Pulsar集群部署

本文档描述Pulsar集群的部署细节。Pulsar集群主要由ZooKeeper节点、BookKeeper节点和Broker节点组成。其中，因为资源限制原因，ZooKeeper节点与之前的etcd公用3个节点，Broker独占2个节点，BookKeeper独占3个。

## 1. ZooKeeper节点部署
### 1.1 准备工作

根据对26台主机的规划，ZooKeeper与etcd公用如下3个节点，详细信息如下：
```bash
=======================================================================
 hostname           ip                   id                   role 
-----------------------------------------------------------------------
gp22aitppapcsve  29.16.21.75  feat9cenkv7h5itauklaueqp6      zk1,etcd1
gp22aitppap92xg  29.16.21.76  lwzi92s62589xhej0y4o40xkk      zk2,etcd2
gp22aitppapch5z  29.16.21.77  u8n1y8aosgaaov2bhhmucdduh      zk3,etcd3
=======================================================================
```

我们在``/mnt/data``目录下建立相应的目录和文件供ZooKeeper节点使用。在``29.16.21.75~29.16.21.77``共3个节点上分别执行如下操作：
```bash
# 1. 在29.16.21.75上执行如下命令
mkdir -p /mnt/data/zookeeper/data
mkdir -p /mnt/data/zookeeper/logs
echo 1 > /mnt/data/zookeeper/data/myid


# 2. 在29.16.21.76上执行如下命令
mkdir -p /mnt/data/zookeeper/data
mkdir -p /mnt/data/zookeeper/logs
echo 2 > /mnt/data/zookeeper/data/myid


# 3. 在29.16.21.77上执行如下命令
mkdir -p /mnt/data/zookeeper/data
mkdir -p /mnt/data/zookeeper/logs
echo 3 > /mnt/data/zookeeper/data/myid
```

备注: 如果``/mnt/data``目录下已经存在``zookeeper``目录，建议先将其删除！！！


### 1.2 ZooKeeper配置文件
ZooKeeper默认的配置文件存储于Pulsar二进制包的下的``conf/zookeeper.conf``, 我们在其末尾添加如下内容:
```bash
server.1=zk1:2888:3888
server.2=zk2:2888:3888
server.3=zk3:2888:3888
```
这些信息主要用于定义ZooKeeper集群的节点和端口信息，其余部分保持不变，更改后的内容见本仓库下的[conf/pulsar/zookeeper.conf](../conf/pulsar/zookeeper.conf)文件. 将修改后的``zookeeper.conf``配置文件分别上传至``29.16.21.75~29.16.21.77``节点的``/home/dcos``目录下。


### 1.3 ZooKeeper服务部署
ZooKeeper服务我们也基于Docker Stack方式部署，其配置文件详见[/yaml/pulsar-zookeeper-2.yaml](../yaml/pulsar-zookeeper.yaml)。我们将该配置文件上传至``29.16.21.80``节点，执行如下命令:
```bash
# 1. 部署zookeeper服务
[dcos@gp22aitppap3jmy-M3~]$ docker stack deploy --compose-file pulsar-zookeeper.yaml milvus

# 2. 查看zookeeper服务状态
[dcos@gp22aitppap3jmy-M3~]$ docker stack ps  milvus --no-trunc
ID                          NAME                IMAGE               NODE                DESIRED STATE       CURRENT STATE         ERROR               PORTS
naloo1f4e3ysvvfkv13s7tj9e   milvus_zk3.1        pulsar:v3.1.0      gp22aitppapch5z     Running             Running 2 hours ago                       
95svbbgx6a1m6gtombj6xt8yq   milvus_zk2.1        pulsar:v3.1.0      gp22aitppap92xg     Running             Running 2 hours ago                       
m9b797mfudre8rvrch339pnz9   milvus_zk1.1        pulsar:v3.1.0      gp22aitppapcsve     Running             Running 2 hours ago  


# 3. 查看服务状态
[dcos@gp22aitppapjbfv-M3~]$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
72c943tp6b30        milvus_zk1          replicated          1/1                 pulsar:v3.1.0      
1zyoxwllkj7k        milvus_zk2          replicated          1/1                 pulsar:v3.1.0      
itmf2hf4uik1        milvus_zk3          replicated          1/1                 pulsar:v3.1.0
```

其中, ``REPLICAS``字段的``1/1``表示该service共1个副本，其中1个副本为正常状态，如果为非正常状态，则小于该service总副本的数量。为了保险起见，我们可以依次进入每个service所在的节点，使用docker ps命令查看镜像，如下：
```bash
# 1. 登陆到3个zookeeper节点上查看正在运行的docer容器
[dcos@gp22aitppapcsve-M3~]$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS                 PORTS               NAMES
adc893c76160        pulsar:v3.1.0      "bash -c 'bin/apply-…"   2 hours ago         Up 2 hours (healthy)                       milvus_zk1.1.m9b797mfudre8rvrch339pnz9

# 2. 进入zookeeper容器
[dcos@gp22aitppapcsve-M3~]$ docker exec -it adc893c76160 bash
root@zk1:/pulsar# 


# 3. 运行如下命令查看zookeeper运行状态，发现当前zookeeper上只有一个zookeeper节点
root@zk1:/pulsar# ./bin/pulsar zookeeper-shell
Connecting to localhost:2181
...                                                                      # 此处省去n个字
Welcome to ZooKeeper!
JLine support is disabled

WATCHER::

WatchedEvent state:SyncConnected type:None path:null
ls /
[zookeeper]

```


### 1.4 Pulsar集群初始化
我们登陆3个zookeeper节点的任何一个，使用``docker exec -it``进入对应的容器，执行如下命令对Pulsar集群进行初始化：
```bash
./bin/pulsar initialize-cluster-metadata   \
    --zookeeper zk1:2181                   \
    --cluster pulsar-cluster               \
    --configuration-store zk1:2181         \
    --web-service-url http://broker:8080                      \
    --web-service-url-tls https://broker:8443                 \
    --broker-service-url pulsar://broker:6650                 \
    --broker-service-url-tls pulsar+ssl://broker:6651
```


### 1.5 ZooKeeper集群验证
对Pulsar集群初始化完成后，我们进入其中任何一个zookeeper的容器，再进行zookeeper节点信息查看，可以得到如下内容：


```bash
root@zk1:/pulsar# ./bin/pulsar zookeeper-shell
Connecting to localhost:2181
...                                                                      # 此处省去n个字
Welcome to ZooKeeper!

WATCHER::

WatchedEvent state:SyncConnected type:None path:null
ls /
[admin, bookies, ledgers, managed-ledgers, namespace, pulsar, stream, zookeeper]

```

注意：在3个zookeeper中均应该看到如上内容，此时表示zookeeper集群搭建成功，并成功完成对Pulsar集群的初始化！


## 2. Bookie节点部署

### 2.1 准备工作
根据对26台主机的规划，Bookie独占如下3个节点，详细信息如下：
```bash
=======================================================================
 hostname           ip                   id                   role 
-----------------------------------------------------------------------
gp22aitppaphhq1  29.16.21.87  f7yxfoh9xbrwlrcjhbirzlob9        bookie1
gp22aitppapssw8  29.16.21.88  zm7xddql5zetsovcauuditedf        bookie2
gp22aitppap71ux  29.16.21.89  966axvponin40bwccb4lp0bcp        bookie3
=======================================================================
```

我们在``/mnt/data``目录下建立相应的目录和文件共ZooKeeper节点使用。在``29.16.21.87~29.16.21.89``共3个节点上分别执行如下操作：
```bash
# 1. 在29.16.21.87上执行如下命令
mkdir -p /mnt/data/bookkeeper/journal
mkdir -p /mnt/data/bookkeeper/ledgers
mkdir -p /mnt/data/bookkeeper/logs


# 2. 在29.16.21.88上执行如下命令
mkdir -p /mnt/data/bookkeeper/journal
mkdir -p /mnt/data/bookkeeper/ledgers
mkdir -p /mnt/data/bookkeeper/logs


# 3. 在29.16.21.89上执行如下命令
mkdir -p /mnt/data/bookkeeper/journal
mkdir -p /mnt/data/bookkeeper/ledgers
mkdir -p /mnt/data/bookkeeper/logs
```

备注: 如果``/mnt/data``目录下已经存在``bookkeeper``目录，建议先将其删除！！！


### 2.2 配置文件

BookKeeper所有的配置项我们通过环境变量进行配置，详细参考:[./yaml/pulsar-bookie.yaml](./yaml/pulsar-bookie.yaml). 

【备注】 这种通过环境变量配置的方式是该镜像的特性，其采用一个脚本将容器启动时将环境变量的值覆盖配置文件的方式来配置，从而我们无需将配置文件写好然后在容器启动时从宿主机挂载到容器内，这样我们需要将该配置文件分别上传到所有要运行该容器的主机，相对麻烦.


### 2.3 服务部署

```bash
# 1. 部署zookeeper服务
[dcos@gp22aitppap3jmy-M3~]$ docker stack deploy --compose-file pulsar-bookie.yaml milvus
Creating service milvus_bookie1
Creating service milvus_bookie2
Creating service milvus_bookie3


# 2. 查看zookeeper服务状态
[dcos@gp22aitppap3jmy-M3~] $docker stack ps  milvus --no-trunc
ID                          NAME                IMAGE               NODE                DESIRED STATE       CURRENT STATE             ERROR               PORTS
un0dtacyuhwo1vu1qmugtw9y2   milvus_bookie3.1    pulsar:v3.1.0      gp22aitppap71ux     Running             Starting 21 seconds ago                       
9jb9giu9p6eglo5jdz9qls4eq   milvus_bookie2.1    pulsar:v3.1.0      gp22aitppapssw8     Running             Starting 22 seconds ago                       
w9lqmdxaal8lfixlo5peza0hq   milvus_bookie1.1    pulsar:v3.1.0      gp22aitppaphhq1     Running             Starting 22 seconds ago                       
naloo1f4e3ysvvfkv13s7tj9e   milvus_zk3.1        pulsar:v3.1.0      gp22aitppapch5z     Running             Running 3 hours ago                           
95svbbgx6a1m6gtombj6xt8yq   milvus_zk2.1        pulsar:v3.1.0      gp22aitppap92xg     Running             Running 3 hours ago                           
m9b797mfudre8rvrch339pnz9   milvus_zk1.1        pulsar:v3.1.0      gp22aitppapcsve     Running             Running 3 hours ago 

# 3. 查看服务运行成功情况
[dcos@gp22aitppapjbfv-M3~]$docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
bxsq56qc4ik4        milvus_bookie1      replicated          1/1                 pulsar:v3.1.0      
gqr70oej6788        milvus_bookie2      replicated          1/1                 pulsar:v3.1.0      
qehd69cgtrnq        milvus_bookie3      replicated          1/1                 pulsar:v3.1.0      
72c943tp6b30        milvus_zk1          replicated          1/1                 pulsar:v3.1.0      
1zyoxwllkj7k        milvus_zk2          replicated          1/1                 pulsar:v3.1.0      
itmf2hf4uik1        milvus_zk3          replicated          1/1                 pulsar:v3.1.0 
```

### 2.4 服务日志查看
我们使用service id查看服务的日志情况，如下:
```bash
[dcos@gp22aitppapjbfv-M3~]$ docker service logs bxsq56qc4ik4 | grep Adding 
...                                                       # 此处省去n个字
milvus_bookie1.1.w9lqmdxaal8l@gp22aitppaphhq1    | 06:10:02.765 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie3:3181
milvus_bookie1.1.w9lqmdxaal8l@gp22aitppaphhq1    | 06:09:41.837 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie2:3181
milvus_bookie1.1.w9lqmdxaal8l@gp22aitppaphhq1    | 06:09:42.049 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie1:3181



[dcos@gp22aitppapjbfv-M3~]$ docker service logs gqr70oej6788 | grep Adding 
...                                                       # 此处省去n个字
milvus_bookie2.1.9jb9giu9p6eg@gp22aitppapssw8    | 06:10:22.089 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie2:3181
milvus_bookie2.1.9jb9giu9p6eg@gp22aitppapssw8    | 06:10:02.064 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie1:3181
milvus_bookie2.1.9jb9giu9p6eg@gp22aitppapssw8    | 06:10:22.089 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie3:3181



[dcos@gp22aitppapjbfv-M3~]$ docker service logs qehd69cgtrnq | grep Adding 
...                                                       # 此处省去n个字
milvus_bookie3.1.un0dtacyuhwo@gp22aitppap71ux    | 06:09:41.898 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie2:3181
milvus_bookie3.1.un0dtacyuhwo@gp22aitppap71ux    | 06:10:02.084 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie1:3181
milvus_bookie3.1.un0dtacyuhwo@gp22aitppap71ux    | 06:10:02.094 [BookKeeperClientScheduler-OrderedScheduler-0-0] INFO  org.apache.bookkeeper.net.NetworkTopologyImpl - Adding a new node: /default-rack/bookie3:3181
```

### 2.5 集群验证
我们在3个BookKeeper节点上，进入对应的容器，使用如下命令验证节点是否正常工作：
```bash
# 1. 简单验证
# 该命令在bookkeeper集群中写入数据，然后删除测试数据
root@bookie1:/pulsar# ./bin/bookkeeper shell bookiesanity 
...                                                       # 此处省去n个字             
07:03:06.749 [main] INFO  org.apache.bookkeeper.tools.cli.commands.bookie.SanityTestCommand - Bookie sanity test succeeded

# 看到Bookie sanity test succeeded就是表示环境没有问题
# 2. 指定bookie节点数量
root@bookie1:/pulsar#  ./bin/bookkeeper shell simpletest --ensemble 2 --writeQuorum 2 --ackQuorum 2 --numEntries 3
```

到此，BookKeeper服务部署成功！


## 3. Broker节点部署
### 3.1 准备工作

根据对26台主机的规划，Broker独占如下2个节点，详细信息如下：
```bash
=======================================================================
 hostname           ip                   id                   role 
-----------------------------------------------------------------------
gp22aitppapy9ku  29.16.21.78  gp4eib4g19df825nj2upfnmak       broker
gp22aitppapkkpt  29.16.21.79  e0rawfh1oxojy40s67x3i90tp       broker
=======================================================================
```

我们在``/mnt/data``目录下建立相应的目录和文件共broker节点使用。在``29.16.21.78~29.16.21.79``共3个节点上分别执行如下操作：
```bash
# 1. 在29.16.21.78上执行如下命令
mkdir -p /mnt/data/broker/logs


# 2. 在29.16.21.79上执行如下命令
mkdir -p /mnt/data/broker/logs
```

备注: 如果``/mnt/data``目录下已经存在``broker``目录，建议先将其删除！！！

### 3.2 配置文件


Broker所有的配置项我们通过环境变量进行配置，详细参考:[./yaml/pulsar-broker.yaml](./yaml/pulsar-broker.yaml). 

### 3.3 服务部署

```bash
# 1. 部署zookeeper服务
[dcos@gp22aitppap3jmy-M3~]$ docker stack deploy --compose-file pulsar-broker.yaml milvus
Creating service milvus_broker1
Creating service milvus_broker2


# 2. 查看zookeeper服务状态
[dcos@gp22aitppap3jmy-M3~]$ docker stack ps  milvus --no-trunc
ID                          NAME                IMAGE               NODE                DESIRED STATE       CURRENT STATE            ERROR               PORTS
30vgtu1ir1e0hfg3f4tky8sly   milvus_broker1.1    pulsar:v3.1.0      gp22aitppapy9ku     Running             Running 2 seconds ago                        
z9255hh24gx8y1m4y7bwt5ugm   milvus_broker2.1    pulsar:v3.1.0      gp22aitppapkkpt     Running             Running 2 seconds ago                        
qf1avl83k6kyfqd5xkdud41g5   milvus_bookie3.1    pulsar:v3.1.0      gp22aitppap71ux     Running             Running 34 minutes ago                       
t2bp7qm5ky5x71rhmdeyts2g0   milvus_bookie2.1    pulsar:v3.1.0      gp22aitppapssw8     Running             Running 34 minutes ago                       
v8gxy2bcvo99tbn60uqlq3iyz   milvus_bookie1.1    pulsar:v3.1.0      gp22aitppaphhq1     Running             Running 34 minutes ago                       
sf9vxqhnjfxw2zicsna23ej1i   milvus_zk3.1        pulsar:v3.1.0      gp22aitppapch5z     Running             Running 37 minutes ago                       
sht3ppwgag6xebedwqh3urbd3   milvus_zk2.1        pulsar:v3.1.0      gp22aitppap92xg     Running             Running 37 minutes ago                       
z2w8na4qklxkhurty3jkjb3oh   milvus_zk1.1        pulsar:v3.1.0      gp22aitppapcsve     Running             Running 37 minutes ago 


# 3. 查看服务运行成功情况
[dcos@gp22aitppapjbfv-M3~]$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
slbr3sz7a0sy        milvus_bookie1      replicated          1/1                 pulsar:v3.1.0      
74urj21c8as3        milvus_bookie2      replicated          1/1                 pulsar:v3.1.0      
czoenue1d5l6        milvus_bookie3      replicated          1/1                 pulsar:v3.1.0      
st7xdqvge9oz        milvus_broker1      replicated          1/1                 pulsar:v3.1.0      
kc1v5e8ppukv        milvus_broker2      replicated          1/1                 pulsar:v3.1.0      
bc202de5yofe        milvus_zk1          replicated          1/1                 pulsar:v3.1.0      
q7uvn2mb3y5t        milvus_zk2          replicated          1/1                 pulsar:v3.1.0      
oc9ybjwxk838        milvus_zk3          replicated          1/1                 pulsar:v3.1.0
```

### 3.4 服务验证
使用``docker exec``的方式进入任意一个Pulsar镜像的容器，运行如下命令查看broker的可用性：
```bash
# 查看默认的pulsar租户下有哪些命令空间
root@bookie1:/pulsar# ./bin/pulsar-admin  --admin-url http://broker:8080 namespaces list pulsar
pulsar/systems
```

如果能够正确输出该内容，则表明broker服务搭建成功。


## 参考文档
1. Pulsar官方文档：     https://pulsar.apache.org/docs/3.1.x/
2. Pulsar官方仓库:      https://github.com/apache/pulsar
3. Kubernets中文文档：  https://kubernetes.io/zh-cn/docs/home/
4.《深入理解Kafka与Pulsar消息流平台的实践与剖析》， 梁国斌， 中国工信出版集团，电子工业出版社