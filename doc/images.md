# Milvus集群镜像制作

## 1. 概述

无论在测试环境还是生产环境中，因为集群的节点太多，我们为了减少镜像构建的工作量，因此我们尽可能减少镜像的数量，把更多的工具融合在一起构建了一个体积更到的镜像文件。尽管这违背了镜像构建的基本原则(镜像体积应该尽可能小，功能单一，某个镜像完成具体的细分功能)，但是能为生产操作省下很多操作。

本项目中，由于Milvus相关组件的构建及其麻烦，因此对于Milvus服务我们直接使用官方提供的镜像，将其pull下来后，直接导出tar镜像文件，然后加载到内部的测试和生产环境。对于Milvus集群中的其它子集群，如元数据存储etcd，对象存储MinIO， 消息中间件Pulsar等，负载均衡等，我们将这些组件统一准备在一个镜像内，详细的内容参考下述小节。

## 2. Milvus镜像

```bash
# 1. 从官方仓库拉拉取镜像
docker pull milvusdb/milvus:v2.3.0

# 2. 将镜像导出为离线镜像文件
docker save milvusdb/milvus:v2.3.0 -o milvus-v2.3.0.tar

# 3. 将镜像导入weidocker image
docker load -i milvus-v2.3.0.tar
docker tag f8cef2947a8a milvus:v2.3.0
```



## 3. 其它组件镜像

### 3.1 基础环境
为了方便，我们直接使用ubuntu:20.04作为基础镜像，因为其gcc和glibc都具有比较高的版本，省去我们安装gcc特别是glibc的码放事情. 首先拉取官方官方镜像，然后启动一个容器:

```bash
docekr pull ubuntu:20.04
docker run --rm -itd --name minio-etcd-pulsar -v /Users/yangxianpku/Software:/mnt/data ubuntu:20.04 bash
```

##### 3.1.1 GCC环境

###### 3.1.1.1 源更新
```bash
root@1ae04f6fa728:/mnt/data# apt-get update
Get:1 http://archive.ubuntu.com/ubuntu  focal InRelease [265 kB]
Get:2 http://security.ubuntu.com/ubuntu focal-security InRelease [114 kB]
Get:3 http://security.ubuntu.com/ubuntu focal-security/restricted amd64 Packages [2761 kB]
Get:4 http://archive.ubuntu.com/ubuntu  focal-updates InRelease [114 kB]
Get:5 http://archive.ubuntu.com/ubuntu  focal-backports InRelease [108 kB]
Get:6 http://archive.ubuntu.com/ubuntu  focal/universe amd64 Packages [11.3 MB]
Get:7 http://security.ubuntu.com/ubuntu focal-security/multiverse amd64 Packages [29.3 kB]
Get:8 http://security.ubuntu.com/ubuntu focal-security/universe amd64 Packages [1099 kB]
Get:9 http://security.ubuntu.com/ubuntu focal-security/main amd64 Packages [3020 kB]
Get:10 http://archive.ubuntu.com/ubuntu focal/main amd64 Packages [1275 kB]
Get:11 http://archive.ubuntu.com/ubuntu focal/multiverse amd64 Packages [177 kB]
Get:12 http://archive.ubuntu.com/ubuntu focal/restricted amd64 Packages [33.4 kB]
Get:13 http://archive.ubuntu.com/ubuntu focal-updates/restricted amd64 Packages [2911 kB]
Get:14 http://archive.ubuntu.com/ubuntu focal-updates/main amd64 Packages [3507 kB]
Get:15 http://archive.ubuntu.com/ubuntu focal-updates/universe amd64 Packages [1401 kB]
Get:16 http://archive.ubuntu.com/ubuntu focal-updates/multiverse amd64 Packages [32.0 kB]
Get:17 http://archive.ubuntu.com/ubuntu focal-backports/universe amd64 Packages [28.6 kB]
Get:18 http://archive.ubuntu.com/ubuntu focal-backports/main amd64 Packages [55.2 kB]
Fetched 28.3 MB in 32s (885 kB/s)
Reading package lists... Done
```

###### 3.1.1.2 阿里源
```bash
root@1ae04f6fa728:/mnt/data# apt-get install vim
root@1ae04f6fa728:/mnt/data# mv  /etc/apt/sources.list /etc/apt/sources.list.bak
root@1ae04f6fa728:/mnt/data# vim /etc/apt/sources.list

deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse

root@1ae04f6fa728:/mnt/data# apt-get update
root@1ae04f6fa728:/mnt/data# apt-get install -f
root@1ae04f6fa728:/mnt/data# apt-get upgrade
```

###### 3.1.1.3 安装GCC
```bash
# 1. 安装gcc与g++
root@1ae04f6fa728:/mnt/data# apt-get install gcc g++
root@1ae04f6fa728:/mnt/data# gcc -v
Using built-in specs.
COLLECT_GCC=gcc
COLLECT_LTO_WRAPPER=/usr/lib/gcc/x86_64-linux-gnu/9/lto-wrapper
OFFLOAD_TARGET_NAMES=nvptx-none:hsa
OFFLOAD_TARGET_DEFAULT=1
Target: x86_64-linux-gnu
Configured with: ../src/configure -v --with-pkgversion='Ubuntu 9.4.0-1ubuntu1~20.04.2' --with-bugurl=file:///usr/share/doc/gcc-9/README.Bugs --enable-languages=c,ada,c++,go,brig,d,fortran,objc,obj-c++,gm2 --prefix=/usr --with-gcc-major-version-only --program-suffix=-9 --program-prefix=x86_64-linux-gnu- --enable-shared --enable-linker-build-id --libexecdir=/usr/lib --without-included-gettext --enable-threads=posix --libdir=/usr/lib --enable-nls --enable-clocale=gnu --enable-libstdcxx-debug --enable-libstdcxx-time=yes --with-default-libstdcxx-abi=new --enable-gnu-unique-object --disable-vtable-verify --enable-plugin --enable-default-pie --with-system-zlib --with-target-system-zlib=auto --enable-objc-gc=auto --enable-multiarch --disable-werror --with-arch-32=i686 --with-abi=m64 --with-multilib-list=m32,m64,mx32 --enable-multilib --with-tune=generic --enable-offload-targets=nvptx-none=/build/gcc-9-9QDOt0/gcc-9-9.4.0/debian/tmp-nvptx/usr,hsa --without-cuda-driver --enable-checking=release --build=x86_64-linux-gnu --host=x86_64-linux-gnu --target=x86_64-linux-gnu
Thread model: posix
gcc version 9.4.0 (Ubuntu 9.4.0-1ubuntu1~20.04.2)

root@1ae04f6fa728:/mnt/data# ldd --version
ldd (Ubuntu GLIBC 2.31-0ubuntu9.12) 2.31
Copyright (C) 2020 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
Written by Roland McGrath and Ulrich Drepper.

# 2. 安装其它编译工具
root@1ae04f6fa728:/mnt/data# apt-get install make
root@1ae04f6fa728:/mnt/data# apt-get install cmake
root@1ae04f6fa728:/mnt/data# cmake --version
cmake version 3.16.3

CMake suite maintained and supported by Kitware (kitware.com/cmake).
```


##### 3.1.2 工具库
```bash
root@1ae04f6fa728:/mnt/data# apt-get install wget
root@1ae04f6fa728:/mnt/data# apt-get install curl
root@1ae04f6fa728:/mnt/data# apt-get install net-tools
root@1ae04f6fa728:/mnt/data# apt-get install iputils-ping
root@1ae04f6fa728:/mnt/data# apt-get install htop
```


##### 3.1.3 Java环境
```bash
root@1ae04f6fa728:/mnt/data# apt install openjdk-17-jdk
root@1ae04f6fa728:/mnt/data# java --version
openjdk 17.0.8.1 2023-08-24
OpenJDK Runtime Environment (build 17.0.8.1+1-Ubuntu-0ubuntu120.04)
OpenJDK 64-Bit Server VM (build 17.0.8.1+1-Ubuntu-0ubuntu120.04, mixed mode, sharing)
```


### 3.2 MinIO安装
```bash
# 1. MinIO Server
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod a+x minio
mv minio /usr/bin

# 2. MinIO Client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod a+x mc
mv mc /usr/bin
```



### 3.3 etcd安装
```bash
# 1. etcd下载 https://github.com/etcd-io/etcd/releases/download/v3.5.9/etcd-v3.5.9-linux-amd64.tar.gz

tar -zvxf etcd-v3.5.9-linux-amd64.tar.gz
cd etcd-v3.5.9-linux-amd64
chmod a+x etcd
chmod a+x etcdctl
chmod a+x etcdutl

mv etcd /usr/bin
mv etcdctl /usr/bin
mv etcdutl /usr/bin
```


### 3.4 Pulsar安装
```bash
# 1. 安装包下载: https://pulsar.apache.org/download/

tar -zvxf apache-pulsar-3.0.0-bin.tar.gz
cp -r apache-pulsar-3.0.0 /usr/local

# 添加环境变量
vim /etc/profile  添加如下内容：

export PATH=/usr/local/apache-pulsar-3.0.0/bin:$PATH
source /etc/profile
```


### 3.5 Nginx安装
```bash
root@1ae04f6fa728: apt-get install nginx

root@1ae04f6fa728:/mnt/data# nginx -v
nginx version: nginx/1.18.0 (Ubuntu)

# 配置文件路径: /usr/local/nginx/conf/nginx.conf
```


### 3.6 KeepAlived
```bash
root@1ae04f6fa728:/mnt/data# apt install keepalived

root@1ae04f6fa728:/mnt/data# keepalived --version
Keepalived v2.0.19 (10/19,2019)

Copyright(C) 2001-2019 Alexandre Cassen, <acassen@gmail.com>

Built with kernel headers for Linux 5.4.166
Running on Linux 5.10.104-linuxkit #1 SMP Thu Mar 17 17:08:06 UTC 2022

# 配置文件路径: /etc/keepalived/keepalived.conf
```


### 3.7 Premetheus
```bash
# 1.下载Premetheus安装包
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
#解压
tar xvf prometheus-2.45.0.linux-amd64.tar.gz -C /usr/local/
#建立软连接
ln -s /usr/local/prometheus-2.45.0.linux-amd64/prometheus /usr/bin/prometheus


# 2. 下载alertmanager安装包
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
#解压
tar xvf alertmanager-0.26.0.linux-amd64.tar.gz -C /usr/local/
#建立软连接
ln -s /usr/local/alertmanager-0.26.0.linux-amd64/alertmanager /usr/bin/alertmanager


# 3. 下载node_exporter安装包
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.0/node_exporter-1.6.0.linux-amd64.tar.gz
#解压
tar xvf node_exporter-1.6.0.linux-amd64.tar.gz -C /usr/local/
#建立软连接
ln -s /usr/local/node_exporter-1.6.0.linux-amd64/node_exporter/usr/bin/node_exporter
```


### 3.8 Grafana安装
```bash
#下载grafana安装包
wget https://dl.grafana.com/enterprise/release/grafana-enterprise-10.0.0.linux-amd64.tar.gz
#解压
tar xvf grafana-enterprise-10.0.0.linux-amd64.tar.gz -C /usr/local/
#建立软连接
ln -s /usr/local/grafana-enterprise-10.0.0.linux-amd64/bin/grafana /usr/bin/grafana 
```


### 3.9 其它
#### 3.9.1 redis
```bash
apt install lsb-release curl gpg

curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/redis.list

apt-get update
apt-get install redis

# 查看安装的版本信息
root@1ae04f6fa728:/mnt/data# redis-server --version
Redis server v=7.2.1 sha=00000000:0 malloc=jemalloc-5.3.0 bits=64 build=95712a67f5005c28

root@1ae04f6fa728:/mnt/data# redis-cli --version
redis-cli 7.2.1
```


#### 3.9.2 elastic search
```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg

apt-get install apt-transport-https

echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list

apt-get update 
apt-get install elasticsearch
```


### 3.10 容器导出 

```bash
docker export container_id -o etcd-minio-pulsar-nginx-redis-es.tar
docker import etcd-minio-pulsar-nginx-redis-es.tar etcd-minio-pulsar-nginx-redis-es:v23.09

rm -rf etcd-minio-pulsar-nginx-redis-es.tar
docker save etcd-minio-pulsar-nginx-redis-es:v23.09 -o etcd-minio-pulsar-nginx-redis-es.tar
docker rmi etcd-minio-pulsar-nginx-redis-es:v23.09
docker load -i etcd-minio-pulsar-nginx-redis-es.tar
docker tag 7e85392ea2da etcd-minio-pulsar-nginx-redis-es:v23.09
```

## 参考文档
1. MinIO安装: https://min.io/download#/linux
2. etcd下载: https://github.com/etcd-io/etcd/releases
3. Grafana安装教程: https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/#install-from-apt-repository