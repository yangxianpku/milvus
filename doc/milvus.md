# Milvus集群部署

到目前为止，Milvus服务相关的依赖服务我们都已经搭建好了，接下来我们搭建Milvus集群服务。Milvus集群内部有很多角色，比如协调器、工作节点等。协调器分为根协调器、数据协调器、索引协调器、查询协调器等，协调器负责安排具体的工作到对应的工作节点。工作节点又分为查询节点、索引节点和数据节点。 其中，工作节点使用过Etcd的方式进行服务发现的，因此工作节点向Etcd注册时，需要找到与其身份对应的协调节点。因此，我们先要将协调节点搭建好，然后再搭建工作节点，最后搭建整个Milvus服务的入口代理和负载均衡.

## 0. 配置文件准备
Milvus服务依赖于其它服务，自身内部又有各种角色，因此我们需要使用配置文件明确配置出这些角色的信息和相互之间的依赖关系。在Milvus的镜像路径中包含了其配置，但该配置需要根据集群的实际情况进行调整. 对于我们的集群，调整内容如下：

```yaml
etcd:
    endpoints: etcd-proxy:23790
    rootPath: cpic-milvus

metastore:
    type: etcd

minio:
    address: minio-proxy
    port: 9000
    accessKeyID: minioadmin
    secretAccessKey: minioadmin
    useSSL: false
    bucketName: milvus-bucket
    rootPath: file
    useIAM: false
    iamEndpoint: 

mq:
    type: pulsar

messageQueue: pulsar

pulsar:
    address: broker
    port: 6650
    maxMessageSize: 5242880

rootCoord:
    address: rootcoord
    port: 53100
    enableActiveStandby: false  # Enable active-standby

proxy:
    port: 19530
    internalPort: 19529
    http:
        enabled: true
    accessLog:
    localPath: /milvus/access-logs
    filename: milvus_access_log.log # Log filename, leave empty to disable file log.

queryCoord:
    address: querycoord
    port: 19531

    enableActiveStandby: false  # Enable active-standby

queryNode:
    port: 21123
    enableDisk: true # Enable querynode load disk index, and search on disk index

indexCoord:
    address: indexcoord
    port: 31000
    enableActiveStandby: false  # Enable active-standby

indexNode:
    port: 21121
    enableDisk: true # Enable index node build disk vector index

dataCoord:
    address: datacoord
    port: 13333
    enableActiveStandby: false  # Enable active-standby

dataNode:
    port: 21124

log:
    level: info
    file:
        rootPath: "/milvus/system-logs"
        maxSize: 300
        maxAge: 10
        maxBackups: 20
    format: text

common:
    chanNamePrefix:
        cluster: cpic-milvus
    storageType: minio
```


【备注】最终完整的配置文件参考：[./conf/milvus/milvus.yaml](./conf/milvus/milvus.yaml).

## 1. 协调节点服务搭建

协调器节点主要负责工作的安排而自己不作任何实际的工作，因此其对硬件资源的需求较低，所以我们可以将4个协调器角色的所有服务部署在2台机器上，实现一个高可用的状态。协调器角色的主机明细如下:

```bash
=======================================================================
 hostname           ip                   id                   role 
-----------------------------------------------------------------------
gp22aitppapwa92  29.16.21.73  twb7ul6y1uvk23th0yz5z9maw      coord
gp22aitppap9mtz  29.16.21.74  ms5me3log9re8ryb74aghf1p6      coord
=======================================================================
```

### 1.1 准备工作

我们在``/mnt/data``目录下建立相应的目录协调节点使用。在``29.16.21.73~29.16.21.74``共2个节点上分别执行如下操作：
```bash
# 1. 在29.16.21.73上执行如下命令
mkdir -p /mnt/data/milvus/system-logs

# 2. 在29.16.21.74上执行如下命令
mkdir -p /mnt/data/milvus/system-logs
```



### 1.2 服务部署
我们将``milvus.yaml``文件上传到``29.16.21.73~29.16.21.74``节点的``/home/dcos``目录，方便后续服务启动时映射到容器内部. 我们将Milvus协调节点的启动配置文件[./yaml/milvus-coord.yaml](./yaml/milvus-coord.yaml)上传到80节点，然后执行如下命令:
```bash
[dcos@gp22aitppap3jmy-M3~]$ docker stack deploy --compose-file  milvus-coord.yaml milvus
Creating service milvus_rootcoord
Creating service milvus_datacoord
Creating service milvus_querycoord
Creating service milvus_indexcoord
```

### 1.3 服务验证
我们到``coord``节点上进入协调节点服务的任意容器，使用如下命令查看服务的健康性:
```bash
root@rootcoord:/milvus# curl -i http://localhost:9091/healthz
HTTP/1.1 200 OK
Date: Thu, 21 Sep 2023 08:07:43 GMT
Content-Length: 2
Content-Type: text/plain; charset=utf-8

root@datacoord:/milvus# curl -i http://localhost:9091/healthz
HTTP/1.1 200 OK
Date: Thu, 21 Sep 2023 08:07:43 GMT
Content-Length: 2
Content-Type: text/plain; charset=utf-8


root@querycoord:/milvus# curl -i http://localhost:9091/healthz
HTTP/1.1 200 OK
Date: Thu, 21 Sep 2023 08:07:43 GMT
Content-Length: 2
Content-Type: text/plain; charset=utf-8


root@indexcoord:/milvus# curl -i http://localhost:9091/healthz
HTTP/1.1 200 OK
Date: Thu, 21 Sep 2023 08:07:43 GMT
Content-Length: 2
Content-Type: text/plain; charset=utf-8
```

发现返回200的状态码，则表明服务已经成功启动。


## 2. 工作节点服务搭建

接下来我们搭建Milvus的工作节点服务。Milvus的工作节点共3个角色，分别为查询节点、索引节点和数据节点。其中，数据节点因为资源要求较低，我们与协调节点公用硬件资源。查询节点和索引节点各自拥有独立的资源，如下：
```bash
=======================================================================
 hostname           ip                   id                   role 
-----------------------------------------------------------------------
gp22aitppapn50h  29.16.21.64  orn6cvg523jsrvflt45ae4j0w      query1
gp22aitppap3j1z  29.16.21.65  qecn8tzfdol91lr2yxwbljeju      query2
gp22aitppap224s  29.16.21.66  svprh9iymqlbrbvsokr9uw79m      query3
gp22aitppapqbnp  29.16.21.67  njke6pgg1n8vjgzeod72psp1g      query4
gp22aitppapggck  29.16.21.68  mfnn5yjmu58y21w372emyhk09      query5
-----------------------------------------------------------------------
gp22aitppapagzs  29.16.21.69  ydt3d0592sagnc04ydrcv6tiw      index1
gp22aitppapnha1  29.16.21.70  4j81h9dvxmiqu4boz7nkni036      index2
gp22aitppap1a0m  29.16.21.71  zeexprr05039cvnx6sfsbrsrg      index3
gp22aitppapa69j  29.16.21.72  acok3zlmgico5juh63vciry5o      index4
-----------------------------------------------------------------------
gp22aitppapwa92  29.16.21.73  twb7ul6y1uvk23th0yz5z9maw      coord
gp22aitppap9mtz  29.16.21.74  ms5me3log9re8ryb74aghf1p6      coord
=======================================================================
```

### 2.1 准备工作

我们为各个节点在宿主机上创建相应的目录，以便服务保存日志和数据信息。我们在``/mnt/data``目录下建立相应的目录供工作节点使用。在``29.16.21.69~29.16.21.72``共4个节点上分别执行如下操作：
```bash
# 1. 在29.16.21.69上执行如下命令
mkdir -p /mnt/data/milvus/index-node/data
mkdir -p /mnt/data/milvus/system-logs

# 2. 在29.16.21.70上执行如下命令
mkdir -p /mnt/data/milvus/index-node/data
mkdir -p /mnt/data/milvus/system-logs

# 3. 在29.16.21.71上执行如下命令
mkdir -p /mnt/data/milvus/index-node/data
mkdir -p /mnt/data/milvus/system-logs

# 4. 在29.16.21.72上执行如下命令
mkdir -p /mnt/data/milvus/index-node/data
mkdir -p /mnt/data/milvus/system-logs
```

在``29.16.21.64~29.16.21.68``共5个节点上分别执行如下操作：
```bash
# 1. 在29.16.21.64上执行如下命令
mkdir -p /mnt/data/milvus/query-node/data
mkdir -p /mnt/data/milvus/system-logs

# 2. 在29.16.21.65上执行如下命令
mkdir -p /mnt/data/milvus/query-node/data
mkdir -p /mnt/data/milvus/system-logs

# 3. 在29.16.21.66上执行如下命令
mkdir -p /mnt/data/milvus/query-node/data
mkdir -p /mnt/data/milvus/system-logs

# 4. 在29.16.21.67上执行如下命令
mkdir -p /mnt/data/milvus/query-node/data
mkdir -p /mnt/data/milvus/system-logs

# 5. 在29.16.21.68上执行如下命令
mkdir -p /mnt/data/milvus/query-node/data
mkdir -p /mnt/data/milvus/system-logs
```

在``29.16.21.73~29.16.21.74``共2个节点上分别执行如下操作：
```bash
# 1. 在29.16.21.64上执行如下命令
mkdir -p /mnt/data/milvus/data-node/data
mkdir -p /mnt/data/milvus/system-logs

# 2. 在29.16.21.65上执行如下命令
mkdir -p /mnt/data/milvus/data-node/data
mkdir -p /mnt/data/milvus/system-logs
```

### 2.2 服务部署

我们将``milvus.yaml``文件上传到上述11个节点的``/home/dcos``目录(因为部署协调器服务时，两个coord的机器上已经有了该配置文件，可以不用再传)，方便后续服务启动时映射到容器内部. 我们将Milvus工作节点的启动配置文件[./yaml/milvus-worker.yaml](./yaml/milvus-worker.yaml)上传到80节点，然后执行如下命令:

```bash
[dcos@gp22aitppap3jmy-M3~]$ docker stack deploy --compose-file  milvus-worker.yaml milvus
Creating service milvus_index1
Creating service milvus_index2
Creating service milvus_index3
Creating service milvus_index4
Creating service milvus_data1
Creating service milvus_data2
Creating service milvus_query1
Creating service milvus_query2
Creating service milvus_query3
Creating service milvus_query4
Creating service milvus_query5
```

### 2.3 服务验证

我们到``worker``节点上进入协调节点服务的任意容器，使用如下命令查看服务的健康性:
```bash
root@query1:/milvus# curl -i http://localhost:9091/healthz
HTTP/1.1 200 OK
Date: Thu, 21 Sep 2023 08:07:43 GMT
Content-Length: 2
Content-Type: text/plain; charset=utf-8

root@data1:/milvus# curl -i http://localhost:9091/healthz
HTTP/1.1 200 OK
Date: Thu, 21 Sep 2023 08:07:43 GMT
Content-Length: 2
Content-Type: text/plain; charset=utf-8


root@index1:/milvus# curl -i http://localhost:9091/healthz
HTTP/1.1 200 OK
Date: Thu, 21 Sep 2023 08:07:43 GMT
Content-Length: 2
Content-Type: text/plain; charset=utf-8

# ... 内容较多，不列出所有了！
```

发现返回200的状态码，则表明服务已经成功启动。

## 3. Milvus代理服务搭建

Milvus集群需要配置代理作为集群的访问入口，同其余服务一样，我们将Milvus的代理也部署在管理节点，因此我们需要将``milvus.yaml``上传至3个管理节点。

### 3.1 准备工作
我们为各个节点在宿主机上创建相应的目录，以便服务保存日志和数据信息。我们在``/mnt/data``目录下建立相应的目录供工作节点使用。在``29.16.21.80~29.16.21.82``共3个节点上分别执行如下操作：
```bash
# 1. 在29.16.21.80上执行如下命令
mkdir -p /mnt/data/milvus/proxy-node/access-logs
mkdir -p /mnt/data/milvus/system-logs

# 2. 在29.16.21.81上执行如下命令
mkdir -p /mnt/data/milvus/proxy-node/access-logs
mkdir -p /mnt/data/milvus/system-logs

# 2. 在29.16.21.82上执行如下命令
mkdir -p /mnt/data/milvus/proxy-node/access-logs
mkdir -p /mnt/data/milvus/system-logs
```

### 3.2 服务部署
我们将Milvus代理节点的启动配置文件[./yaml/milvus-proxy.yaml](./yaml/milvus-proxy.yaml)上传到80节点，然后执行如下命令:

```bash
[dcos@gp22aitppap3jmy-M3~]$ docker stack deploy --compose-file  etcd-proxy.yaml milvus
Creating service milvus_milvus-proxy
```

### 3.3 服务验证
我们已经将代理的19530端口映射到管理节点的宿主机，因此我们可以在客户端使用如下方式验证Milvus代理也即整个Milvus集群的可用性:
```python
from pymilvus import connections
from pymilvus import Collection
from pymilvus import utility
from pymilvus import CollectionSchema, FieldSchema, DataType

connections.connect(
  alias="default",     # 链接别名
  host='29.16.21.80',  # 服务端主机
  port='19530'         # 服务端端口
)

book_id    = FieldSchema(name="book_id",     dtype=DataType.INT64,  is_primary=True,)
book_name  = FieldSchema(name="book_name",   dtype=DataType.VARCHAR, max_length=200,)
word_count = FieldSchema(name="word_count",  dtype=DataType.INT64, )
book_intro = FieldSchema(name="book_intro",  dtype=DataType.FLOAT_VECTOR, dim=2)

schema          = CollectionSchema(fields=[book_id, book_name, word_count, book_intro], description="Test book search")
collection_name = "book"

collection = Collection(name=collection_name, schema=schema, using='default', shards_num=2)
collection.set_properties(properties={"collection.ttl.seconds": 1800})

has = utility.has_collection("book")
ls  = utility.list_collections()
suc = utility.drop_collection("book")

print(has, ls, suc)

connections.disconnect("default")
```

至此，整个Milvus集群搭建完成，服务已经可用！


## 参考文档
1.  向量数据库产品比较：  https://baijiahao.baidu.com/s?id=1770637201988677681&wfr=spider&for=pc
2.  Milvus官方文档:      https://milvus.io/docs
3.  Milvus版本更新Notes: https://milvus.io/docs/release_notes.md
4.  Milvus中文论坛：     https://www.slidestalk.com/Milvus/     