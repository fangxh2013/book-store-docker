# Book Store 服务消息通信环境

该项目基于RocketMQ和Nacos构建微服务消息通信环境，支持分布式系统下的消息发布与订阅、服务注册与配置管理。适用于微服务架构中的异步通信与服务治理场景。

## 技术栈

- **消息中间件**: RocketMQ
- **服务注册与配置中心**: Nacos
- **容器编排**: Docker Compose
- **数据库**: MySQL (存储Nacos配置数据)
- **缓存**: Redis
- **对象存储**: MinIO
- **日志管理**: ELK Stack (Elasticsearch, Logstash, Kibana) + Filebeat
- **消息队列**: RabbitMQ

## 目录结构

```
.
├── docker-compose.yml          # 容器编排配置（完整版，包含ELK日志系统）
├── docker-compose-simple.yml   # 简化版容器编排配置（仅核心服务）
├── README.md                   # 项目说明文档
├── ELK-BOOK-STORE-TUTORIAL.md  # ELK日志分析系统使用教程
├── gen_token.py                # 安全令牌生成脚本
├── secrets/                    # 敏感信息存储目录
├── mysql/                      # MySQL配置和数据目录
├── redis/                      # Redis配置和数据目录
├── nacos/                      # Nacos配置和日志目录
├── rocketmq/                   # RocketMQ配置和日志目录
├── rabbitmq/                   # RabbitMQ配置和数据目录
├── minio/                      # MinIO数据目录
└── logging/                    # 日志收集配置目录
    └── filebeat.yml            # Filebeat配置文件
```

## 环境要求

- Docker Engine 20.10+
- Docker Compose 1.29+
- 至少8GB内存

## 系统兼容性说明

本项目支持macOS和Linux系统，但在docker-compose.yml中有一些针对不同系统的配置差异：

### macOS系统配置（默认）
- Filebeat日志收集使用特定的卷挂载路径
- RocketMQ服务移除了Linux特定的platform配置
- 为Apple Silicon (M1/M2)芯片的macOS系统添加了platform: linux/amd64配置以解决架构兼容性问题

### Linux系统配置
- 如果在Linux系统上运行，请根据docker-compose.yml中的注释调整配置
- 取消注释Linux特定的配置行
- 注释掉macOS特定的配置行

## 部署步骤

### 1. 准备工作

确保已安装Docker和Docker Compose，并且Docker服务正在运行。

### 2. 选择部署版本

本项目提供两个版本的部署配置：

1. **完整版** (`docker-compose.yml`)：包含所有服务和ELK日志系统
2. **简化版** (`docker-compose-simple.yml`)：仅包含核心服务（MySQL、Redis、Nacos、RocketMQ）

如果遇到镜像拉取问题或资源限制，建议先使用简化版进行部署。

### 3. 创建secrets文件（完整版需要）

在项目根目录下创建secrets目录并添加必要的密码文件（仅完整版需要）：

```bash
mkdir -p secrets

# 创建各服务的密码文件
echo "root8888" > secrets/mysql_root_password
echo "nacos8888" > secrets/nacos_db_password
echo "minioadmin" > secrets/minio_password
echo "rabbitmq" > secrets/rabbitmq_password
echo "redis8888" > secrets/redis_password
```

### 4. 启动服务

根据需要选择部署版本：

```bash
# 启动简化版（推荐用于初次部署或资源有限环境）
docker-compose -f docker-compose-simple.yml up -d

# 启动完整版（包含ELK日志系统）
docker-compose up -d
```

### 5. 验证服务状态

检查所有服务是否正常运行：

```bash
# 检查简化版服务
docker-compose -f docker-compose-simple.yml ps

# 检查完整版服务
docker-compose ps
```

## 服务访问地址

| 服务 | 访问地址 | 端口 |
|------|----------|------|
| Nacos | http://localhost:8848/nacos | 8848 |
| MySQL | localhost | 3306 |
| Redis | localhost | 6379 |
| MinIO Console | http://localhost:9001 | 9000/9001 |
| RocketMQ Name Server | localhost | 9876 |
| RabbitMQ Management | http://localhost:15672 | 5672/15672 |
| Kibana | http://localhost:5601 | 5601 |
| Elasticsearch | http://localhost:9200 | 9200/9300 |

## 日志管理

本项目集成了ELK Stack进行日志收集和分析，所有关键组件的日志都会被收集：

### 收集的日志类型

1. **MySQL**: 错误日志、慢查询日志、通用查询日志
2. **Nacos**: 服务注册/注销日志、配置变更日志、认证日志
3. **Redis**: 慢查询日志、内存使用日志、连接日志
4. **RabbitMQ**: 消息投递日志、连接日志、错误日志
5. **RocketMQ**: 消息发送/消费日志、Broker日志、Namesrv日志

### Filebeat配置

Filebeat会自动收集所有容器的日志并发送到Elasticsearch。

### 访问Kibana

1. 打开浏览器访问 http://localhost:5601
2. 在Kibana中创建索引模式：
   - 进入"Management" > "Stack Management" > "Kibana" > "Index Patterns"
   - 创建新的索引模式，使用`filebeat-*`作为模式
   - 选择`@timestamp`作为时间字段
3. 在"Analytics" > "Discover"中查看日志数据

### 详细使用教程

请参考 [ELK-BOOK-STORE-TUTORIAL.md](ELK-BOOK-STORE-TUTORIAL.md) 文件获取完整的ELK日志分析系统使用教程。

### 日志分析建议

- 设置告警规则监控错误日志
- 定期分析慢查询日志优化数据库性能
- 监控服务注册/注销日志确保服务稳定性
- 分析消息队列日志优化消息处理流程

## 安全配置

所有敏感信息都通过Docker secrets管理，不会在配置文件中暴露明文密码。

## 资源限制

为各个服务设置了合理的资源限制，防止某个服务占用过多资源影响其他服务：

- MySQL和Nacos: 1GB内存，0.5个CPU
- Redis、MinIO和RocketMQ Name Server: 512MB内存，0.3个CPU
- RocketMQ Broker: 1GB内存，0.5个CPU
- RabbitMQ: 512MB内存，0.3个CPU
- Elasticsearch: 1GB内存，0.5个CPU
- Kibana: 512MB内存，0.3个CPU
- Filebeat: 256MB内存，0.2个CPU

## 健康检查

所有关键服务都配置了健康检查，确保服务完全就绪后再启动依赖服务。

## 常见问题

### 1. 服务启动失败

检查Docker资源限制，确保有足够的内存和CPU资源。

### 2. 无法访问Nacos控制台

确认Nacos服务已完全启动，可以通过`docker-compose logs nacos`查看日志。

### 3. 日志无法在Kibana中显示

确认Filebeat、Elasticsearch和Kibana服务都正常运行，并正确配置了索引模式。

### 4. Apple Silicon (M1/M2)芯片macOS系统兼容性问题

如果遇到"no matching manifest for linux/arm64/v8"错误，请确保docker-compose.yml中所有服务都添加了`platform: linux/amd64`配置。

### 5. 镜像拉取失败或超时

如果遇到镜像拉取失败或超时问题，可以尝试以下解决方案：

1. **使用国内镜像源**：
   - 配置Docker使用国内镜像加速器（如阿里云、腾讯云等）
   - 在Docker Desktop中设置：Preferences > Docker Engine，添加镜像加速器配置

2. **手动拉取镜像**：
   ```bash
   # 拉取基础镜像
   docker pull mysql:8.0
   docker pull redis:7.0
   docker pull nacos/nacos-server:v2.2.3
   # 等等...
   ```

3. **使用替代镜像版本**：
   - 如果特定版本拉取困难，可以尝试使用其他版本
   - 在docker-compose.yml中修改镜像标签

4. **网络问题**：
   - 检查网络连接是否正常
   - 尝试使用VPN或代理

5. **使用简化版配置**：
   - 如果完整版部署遇到问题，可以先使用简化版进行部署
   - 简化版仅包含核心服务，镜像更容易获取且资源占用更少

## 维护命令

### 停止所有服务

```bash
# 停止简化版服务
docker-compose -f docker-compose-simple.yml down

# 停止完整版服务
docker-compose down
```

### 查看服务日志

```bash
# 查看简化版服务日志
docker-compose -f docker-compose-simple.yml logs [service_name]

# 查看完整版服务日志
docker-compose logs [service_name]
```

### 重启特定服务

```bash
# 重启简化版服务
docker-compose -f docker-compose-simple.yml restart [service_name]

# 重启完整版服务
docker-compose restart [service_name]
```

### 扩展服务实例

```bash
# 扩展简化版服务
docker-compose -f docker-compose-simple.yml up -d --scale [service_name]=n

# 扩展完整版服务
docker-compose up -d --scale [service_name]=n
```

## 注意事项

1. 请勿将secrets目录提交到版本控制系统
2. 定期清理日志文件，避免占用过多磁盘空间
3. 生产环境部署时，请根据实际需求调整资源配置