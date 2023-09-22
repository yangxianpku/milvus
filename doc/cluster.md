# Docker Swarm集群管理


## 1. 集群初始化

### 1.1 主节点初始化集群


```bash
# 在 29.16.21.80上运行如下命令
[dcos@gp22aitppap3jmy-M3~]$docker swarm init --advertise-addr 29.16.21.80
Swarm initialized: current node (wx61lby7f5py1x9di21tig6d4) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-04tfg8tpsrj1zdxw9c98m0qbtfbiima14lr5y2kqmdlzhp0xpf-eoeqqa8sb94fr2mgq6ah2bc1a 29.16.21.80:2377

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.
```

此时我们在节点上初始化完成了docker swarm集群，docker为我们自动输出了以worker身份加入该集群的token。整个集群中，为了高可用，我们需要存在3个管理节点，我们使用如下命令来得到以管理员加入该集群的token信息：
```bash
[dcos@gp22aitppap3jmy-M3~]$docker swarm join-token manager
To add a manager to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-04tfg8tpsrj1zdxw9c98m0qbtfbiima14lr5y2kqmdlzhp0xpf-0gzylt5ed5ek4lqgclhz0imm1 29.16.21.80:2377
```


### 1.2 主节点加入
```bash
# 1. 在节点29.16.21.81上运行如下命令
[dcos@gp22aitppapvgr5-M3~]$docker swarm join --token SWMTKN-1-04tfg8tpsrj1zdxw9c98m0qbtfbiima14lr5y2kqmdlzhp0xpf-0gzylt5ed5ek4lqgclhz0imm1 29.16.21.80:2377
This node joined a swarm as a manager.

# 2. 在节点29.16.21.82上运行如下命令
[dcos@gp22aitppapvgr5-M3~]$docker swarm join --token SWMTKN-1-04tfg8tpsrj1zdxw9c98m0qbtfbiima14lr5y2kqmdlzhp0xpf-0gzylt5ed5ek4lqgclhz0imm1 29.16.21.80:2377
This node joined a swarm as a manager.

# 3.查看当前集群情况
[dcos@gp22aitppapjbfv-M3~]$docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS      ENGINE VERSION
wx61lby7f5py1x9di21tig6d4     gp22aitppap3jmy     Ready               Active              Leader              18.09.9
hp7jwyjryd12x8f66h9rawa4m *   gp22aitppapjbfv     Ready               Active              Reachable           18.09.9
qtihlj52m9v4jdjs44o9xvc30     gp22aitppapvgr5     Ready               Active              Reachable           18.09.9
```


### 1.3 工作节点加入
此时，我们已经在26个节点中，完成了三个管理节点的初始化。3个管理节点中，如果某一个节点出现故障，整个集群仍可以正常工作。但如果2个节点因为故障下线，集群则失效。接下来，我们将剩余的23个节点均与worker的身份加入集群。我们在剩余的23个节点上均运行如下命令:

```bash
# 1. 将剩余23个节点全部以worker身份加入集群
[dcos@gp22aitppaphhq1-M3~]$ docker swarm join --token SWMTKN-1-04tfg8tpsrj1zdxw9c98m0qbtfbiima14lr5y2kqmdlzhp0xpf-eoeqqa8sb94fr2mgq6ah2bc1a 29.16.21.80:2377

This node joined a swarm as a worker.

# 2. 在任意manager节点上运行如下命令，查看集群状态
[dcos@gp22aitppap3jmy-M3~]$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS    ENGINE VERSION
zeexprr05039cvnx6sfsbrsrg     gp22aitppap1a0m     Ready               Active                                  18.09.9  
qecn8tzfdol91lr2yxwbljeju     gp22aitppap3j1z     Ready               Active                                  18.09.9  
wx61lby7f5py1x9di21tig6d4 *   gp22aitppap3jmy     Ready               Active              Leader              18.09.9
qmq7uiblozdfkuwptvddppeoo     gp22aitppap7keb     Ready               Active                                  18.09.9 
ms5me3log9re8ryb74aghf1p6     gp22aitppap9mtz     Ready               Active                                  18.09.9 
966axvponin40bwccb4lp0bcp     gp22aitppap71ux     Ready               Active                                  18.09.9 
lwzi92s62589xhej0y4o40xkk     gp22aitppap92xg     Ready               Active                                  18.09.9 
svprh9iymqlbrbvsokr9uw79m     gp22aitppap224s     Ready               Active                                  18.09.9 
acok3zlmgico5juh63vciry5o     gp22aitppapa69j     Ready               Active                                  18.09.9  
ydt3d0592sagnc04ydrcv6tiw     gp22aitppapagzs     Ready               Active                                  18.09.9  
u8n1y8aosgaaov2bhhmucdduh     gp22aitppapch5z     Ready               Active                                  18.09.9 
feat9cenkv7h5itauklaueqp6     gp22aitppapcsve     Ready               Active                                  18.09.9 
mfnn5yjmu58y21w372emyhk09     gp22aitppapggck     Ready               Active                                  18.09.9  
f7yxfoh9xbrwlrcjhbirzlob9     gp22aitppaphhq1     Ready               Active                                  18.09.9 
hp7jwyjryd12x8f66h9rawa4m     gp22aitppapjbfv     Ready               Active              Reachable           18.09.9
e0rawfh1oxojy40s67x3i90tp     gp22aitppapkkpt     Ready               Active                                  18.09.9 
orn6cvg523jsrvflt45ae4j0w     gp22aitppapn50h     Ready               Active                                  18.09.9  
t2ka3dmgb9o30vynhdqzo35cd     gp22aitppapnch3     Ready               Active                                  18.09.9 
4j81h9dvxmiqu4boz7nkni036     gp22aitppapnha1     Ready               Active                                  18.09.9 
njke6pgg1n8vjgzeod72psp1g     gp22aitppapqbnp     Ready               Active                                  18.09.9 
zm7xddql5zetsovcauuditedf     gp22aitppapssw8     Ready               Active                                  18.09.9 
qtihlj52m9v4jdjs44o9xvc30     gp22aitppapvgr5     Ready               Active              Reachable           18.09.9
twb7ul6y1uvk23th0yz5z9maw     gp22aitppapwa92     Ready               Active                                  18.09.9 
w9qfcpvtfstnxsudcom2wj6ii     gp22aitppapwc2g     Ready               Active                                  18.09.9 
wbhf2nmlx3jrfekfq76l582d0     gp22aitppapxpeg     Ready               Active                                  18.09.9 
gp4eib4g19df825nj2upfnmak     gp22aitppapy9ku     Ready               Active                                  18.09.9 
```

## 2. 节点标签

### 2.1 集群关系
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
-----------------------------------------------------------------------
gp22aitppapcsve  29.16.21.75  feat9cenkv7h5itauklaueqp6      zk1,etcd1
gp22aitppap92xg  29.16.21.76  lwzi92s62589xhej0y4o40xkk      zk2,etcd2
gp22aitppapch5z  29.16.21.77  u8n1y8aosgaaov2bhhmucdduh      zk3,etcd3
-----------------------------------------------------------------------
gp22aitppapy9ku  29.16.21.78  gp4eib4g19df825nj2upfnmak       broker
gp22aitppapkkpt  29.16.21.79  e0rawfh1oxojy40s67x3i90tp       broker
-----------------------------------------------------------------------
gp22aitppap3jmy  29.16.21.80  wx61lby7f5py1x9di21tig6d4
gp22aitppapvgr5  29.16.21.81  qtihlj52m9v4jdjs44o9xvc30
gp22aitppapjbfv  29.16.21.82  hp7jwyjryd12x8f66h9rawa4m
-----------------------------------------------------------------------
gp22aitppapwc2g  29.16.21.83  w9qfcpvtfstnxsudcom2wj6ii        minio1
gp22aitppapxpeg  29.16.21.84  wbhf2nmlx3jrfekfq76l582d0        minio2
gp22aitppap7keb  29.16.21.85  qmq7uiblozdfkuwptvddppeoo        minio3
gp22aitppapnch3  29.16.21.86  t2ka3dmgb9o30vynhdqzo35cd        minio4
-----------------------------------------------------------------------
gp22aitppaphhq1  29.16.21.87  f7yxfoh9xbrwlrcjhbirzlob9        bookie1
gp22aitppapssw8  29.16.21.88  zm7xddql5zetsovcauuditedf        bookie2
gp22aitppap71ux  29.16.21.89  966axvponin40bwccb4lp0bcp        bookie3
=======================================================================
```



### 2.2 节点标签

docker node update --label-add query1=true 29.16.21.64
```bash
docker node update --label-add query1=true  orn6cvg523jsrvflt45ae4j0w
docker node update --label-add query2=true  qecn8tzfdol91lr2yxwbljeju
docker node update --label-add query3=true  svprh9iymqlbrbvsokr9uw79m
docker node update --label-add query4=true  njke6pgg1n8vjgzeod72psp1g
docker node update --label-add query5=true  mfnn5yjmu58y21w372emyhk09


docker node update --label-add index1=true  ydt3d0592sagnc04ydrcv6tiw 
docker node update --label-add index2=true  4j81h9dvxmiqu4boz7nkni036
docker node update --label-add index3=true  zeexprr05039cvnx6sfsbrsrg
docker node update --label-add index4=true  acok3zlmgico5juh63vciry5o


docker node update --label-add coord=true   twb7ul6y1uvk23th0yz5z9maw
docker node update --label-add coord=true   ms5me3log9re8ryb74aghf1p6


docker node update --label-add zk1=true     feat9cenkv7h5itauklaueqp6
docker node update --label-add zk2=true     lwzi92s62589xhej0y4o40xkk
docker node update --label-add zk3=true     u8n1y8aosgaaov2bhhmucdduh

docker node update --label-add etcd1=true   feat9cenkv7h5itauklaueqp6
docker node update --label-add etcd2=true   lwzi92s62589xhej0y4o40xkk
docker node update --label-add etcd3=true   u8n1y8aosgaaov2bhhmucdduh


docker node update --label-add broker=true  gp4eib4g19df825nj2upfnmak
docker node update --label-add broker=true  e0rawfh1oxojy40s67x3i90tp

docker node update --label-add minio1=true  w9qfcpvtfstnxsudcom2wj6ii
docker node update --label-add minio2=true  wbhf2nmlx3jrfekfq76l582d0
docker node update --label-add minio3=true  qmq7uiblozdfkuwptvddppeoo
docker node update --label-add minio4=true  t2ka3dmgb9o30vynhdqzo35cd


docker node update --label-add bookie1=true f7yxfoh9xbrwlrcjhbirzlob9
docker node update --label-add bookie2=true zm7xddql5zetsovcauuditedf
docker node update --label-add bookie3=true 966axvponin40bwccb4lp0bcp
```


至此，集群搭建和节点角色的划分就完成了。我们通过如下命令查看节点的标签信息:

```bash
# 其中 t2ka3dmgb9o30vynhdqzo35cd为节点的ID
[dcos@gp22aitppap3jmy-M3~]$ docker node inspect --format '{{ .Spec.Labels }}' t2ka3dmgb9o30vynhdqzo35cd
map[minio4:true]
```

## 参考文档
1. Docker可视化工具Portainer: https://www.bilibili.com/video/BV1gr4y1U7CY?p=87
2. Docker监控工具:  https://www.bilibili.com/video/BV1gr4y1U7CY?p=90
3. Docker Swarm部署MinIO集群: https://www.cnblogs.com/lenovo_tiger_love/p/13050511.html
4. Docker外部负载均衡: https://docs.docker.com/engine/swarm/ingress/#/configure-an-external-load-balancer