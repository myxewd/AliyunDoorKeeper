# AliyunDoorKeeper

​		本项目基于阿里云API与阿里云ECS安全组功能，实现了对云服务器的访问权限的简单自动化控制与维护。

## 环境依赖

- Python 3.7 +
- Redis
- RabbitMQ
- 互联网访问

## 配置详解

| 配置项名           | 解释                                                         |
| ------------------ | ------------------------------------------------------------ |
| behind_proxy       | 应用是否被反向代理<br />如果未被，则直接通过`remote_addr`取用户IP<br />如果被，则通过`X-Forwarded-For`头取用户IP<br />该项非常重要，若配置不当，可能导致应用无法正常运行，或IP被用户随意篡改. |
| server             | 被控制权限应用的简称                                         |
| sg_id              | 进行权限授予的安全组ID                                       |
| sg_region_id       | 进行权限授予的安全组地域ID                                   |
| rule_priority      | ACCEPT权限的优先级<br />请将该值配置为小于全局REFUSE规则的优先级 |
| api.endpoint       | 需要操作的阿里云API的端点                                    |
| api.ak_id          | 你的阿里云AccessKey-ID<br />请确保该AK具有访问上面设置的安全组的权限 |
| api.ak_secret      | API密钥                                                      |
| max_whitelist_size | 由于阿里云对单个安全组所能创建的规则条数做了限制，当被授予权限的用户数达到该值后再有新的授权出现，最先被授予权限的用户将被提前撤销权限。 |
| expiry_time        | 权限有效期，单位为秒                                         |
| redis.*            | Redis配置                                                    |
| rabbitmq.*         | RabbitMQ配置<br />需要注意的是，该RabbitMQ需要支持通过WebAPI进行管理。 |
| bluebird.max_retry | 阿里云API重试次数。                                          |

