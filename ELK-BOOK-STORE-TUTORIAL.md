# Book Store项目ELK日志分析系统使用教程

本教程将指导您如何在当前的Book Store项目中使用ELK Stack（Elasticsearch, Logstash, Kibana）来收集、分析和可视化各个微服务组件的日志数据。

## 目录

1. [项目日志架构概述](#项目日志架构概述)
2. [环境准备](#环境准备)
3. [启动ELK Stack服务](#启动elk-stack服务)
4. [验证服务状态](#验证服务状态)
5. [访问Kibana](#访问kibana)
6. [创建索引模式](#创建索引模式)
7. [日志分析](#日志分析)
8. [各组件日志说明](#各组件日志说明)
9. [故障排除](#故障排除)
10. [最佳实践](#最佳实践)

## 项目日志架构概述

Book Store项目使用ELK Stack + Filebeat作为日志收集和分析解决方案：

- **Elasticsearch**: 存储和索引所有微服务的日志数据
- **Kibana**: 提供日志数据的可视化界面
- **Filebeat**: 轻量级日志收集器，收集各容器的日志并发送到Elasticsearch

当前项目中收集日志的组件包括：
- MySQL
- Redis
- Nacos
- RabbitMQ
- RocketMQ Broker
- RocketMQ Name Server

## 环境准备

### 系统要求

- Docker Engine 20.10+
- Docker Compose 1.29+
- 至少8GB内存（推荐16GB以上）
- 至少20GB可用磁盘空间

### 项目结构

确保您的项目目录结构如下：

```
book-store/
├── docker-compose.yml
├── logging/
│   └── filebeat.yml
├── mysql/
│   ├── logs/
│   └── ...
├── redis/
│   ├── data/
│   └── ...
├── nacos/
│   ├── logs/
│   └── ...
├── rabbitmq/
│   ├── logs/
│   └── ...
├── rocketmq/
│   ├── broker/
│   │   ├── logs/
│   │   └── ...
│   └── namesrv/
│       ├── logs/
│       └── ...
└── ...
```

## 启动ELK Stack服务

### 1. 确保所有服务都已配置

检查docker-compose.yml文件中的ELK相关配置：

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:7.10.0
  platform: linux/amd64
  container_name: elasticsearch
  environment:
    - discovery.type=single-node
    - ES_JAVA_OPTS=-Xms512m -Xmx512m
  ports:
    - "9200:9200"
    - "9300:9300"
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data
  networks:
    - backend-network
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: "0.5"
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 3

kibana:
  image: docker.elastic.co/kibana/kibana:7.10.0
  platform: linux/amd64
  container_name: kibana
  ports:
    - "5601:5601"
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
  networks:
    - backend-network
  depends_on:
    - elasticsearch
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: "0.3"

filebeat:
  image: docker.elastic.co/beats/filebeat:7.10.0
  platform: linux/amd64
  container_name: filebeat
  user: root
  volumes:
    - ./logging/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
    # macOS配置
    - ./nacos/logs:/var/log/containers/nacos:ro
    - ./mysql/logs:/var/log/containers/mysql:ro
    - ./redis/data:/var/log/containers/redis:ro
    - ./rabbitmq/logs:/var/log/containers/rabbitmq:ro
    - ./rocketmq/broker/logs:/var/log/containers/rocketmq-broker:ro
    - ./rocketmq/namesrv/logs:/var/log/containers/rocketmq-namesrv:ro
  networks:
    - backend-network
  depends_on:
    - elasticsearch
  deploy:
    resources:
      limits:
        memory: 256M
        cpus: "0.2"
```

### 2. 启动所有服务

在项目根目录下运行以下命令启动所有服务：

```bash
# 启动完整版（包含ELK日志系统）
docker-compose up -d
```

## 验证服务状态

### 1. 检查所有服务状态

```bash
docker-compose ps
```

您应该看到所有服务都处于"Up"状态，包括elasticsearch、kibana和filebeat。

### 2. 检查ELK服务健康状态

```bash
# 检查Elasticsearch健康状态
curl -X GET "localhost:9200/_cluster/health?pretty"

# 检查Elasticsearch节点信息
curl -X GET "localhost:9200/_nodes?pretty"
```

## 访问Kibana

### 1. 打开Kibana

在浏览器中访问 http://localhost:5601

首次访问时，Kibana会显示欢迎页面。

### 2. 检查Elasticsearch连接

在Kibana左侧导航栏中，点击"Management" > "Stack Monitoring"，确保Elasticsearch连接正常。

## 创建索引模式

### 1. 导航到索引模式创建页面

在Kibana中：

1. 点击左侧导航栏的"Analytics" > "Discover"
2. 点击"Create index pattern"

### 2. 创建索引模式

1. 在"Index pattern"字段中输入：`filebeat-*`
2. 点击"Next step"
3. 选择时间字段：`@timestamp`
4. 点击"Create index pattern"

### 3. 验证索引模式

创建完成后，您可以在"Analytics" > "Discover"中查看收集到的日志数据。

## 日志分析

### 1. 使用Discover功能

在"Analytics" > "Discover"页面中，您可以：

- 搜索特定的日志条目
- 使用过滤器缩小搜索范围
- 按时间范围查看日志
- 添加字段到表格中进行比较

常用搜索示例：
```
# 搜索包含"error"的日志
error

# 搜索特定服务的日志
service: mysql

# 搜索特定时间范围的日志
@timestamp > "2023-01-01T00:00:00" AND @timestamp < "2023-01-02T00:00:00"

# 组合搜索
service: redis AND error
```

### 2. 创建可视化图表

在"Analytics" > "Dashboard"中，您可以：

1. 点击"Create new"
2. 选择"Visualization"
3. 选择图表类型（如柱状图、饼图等）
4. 选择数据源（之前创建的索引模式）
5. 配置图表参数
6. 保存并添加到仪表板

### 3. 创建仪表板

1. 在"Analytics" > "Dashboard"中点击"Create new"
2. 点击"Add from library"
3. 选择之前创建的可视化图表
4. 调整布局
5. 保存仪表板

## 各组件日志说明

### 1. MySQL日志

MySQL日志包含：
- 错误日志
- 慢查询日志
- 通用查询日志

日志路径：`./mysql/logs/`

### 2. Redis日志

Redis日志包含：
- 启动和关闭日志
- 连接日志
- 慢查询日志

日志路径：`./redis/data/`

### 3. Nacos日志

Nacos日志包含：
- 服务注册/注销日志
- 配置变更日志
- 认证日志

日志路径：`./nacos/logs/`

### 4. RabbitMQ日志

RabbitMQ日志包含：
- 启动日志
- 连接日志
- 消息投递日志
- 错误日志

日志路径：`./rabbitmq/logs/`

### 5. RocketMQ日志

RocketMQ日志包含：
- Name Server日志
- Broker日志
- 消息发送/消费日志

日志路径：
- Name Server: `./rocketmq/namesrv/logs/`
- Broker: `./rocketmq/broker/logs/`

## 故障排除

### 1. 服务无法启动

检查Docker资源限制，确保有足够的内存和CPU资源。

```bash
# 检查服务日志
docker-compose logs elasticsearch
docker-compose logs kibana
docker-compose logs filebeat
```

### 2. Filebeat无法收集日志

检查Filebeat配置文件和挂载的卷：

```bash
# 检查Filebeat配置
docker-compose exec filebeat filebeat test config

# 检查Filebeat连接
docker-compose exec filebeat filebeat test output
```

### 3. Kibana无法连接Elasticsearch

检查网络连接和Elasticsearch状态：

```bash
# 检查Elasticsearch健康状态
curl -X GET "localhost:9200/_cluster/health?pretty"

# 检查Kibana日志
docker-compose logs kibana
```

### 4. 日志未显示在Kibana中

1. 检查Filebeat是否正常收集日志
2. 检查Elasticsearch索引是否创建
3. 确认Kibana索引模式配置正确
4. 检查时间筛选范围

```bash
# 检查Elasticsearch中的索引
curl -X GET "localhost:9200/_cat/indices?v"

# 检查特定索引的内容
curl -X GET "localhost:9200/filebeat-*/_search?pretty"
```

### 5. 磁盘空间不足

定期清理旧的索引数据：

```bash
# 在Kibana中设置索引生命周期管理(ILM)
# 或使用Elasticsearch API删除旧索引
curl -X DELETE "localhost:9200/old-index-name"
```

## 最佳实践

### 1. 资源管理

- 为每个服务设置合理的资源限制
- 监控服务的内存和CPU使用情况
- 根据实际需求调整JVM堆大小

### 2. 数据管理

- 配置索引生命周期管理(ILM)策略
- 定期备份重要数据
- 设置适当的日志轮转策略

当前Filebeat配置已设置日志轮转：
```yaml
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

### 3. 安全性

- 启用安全功能并配置用户认证
- 使用TLS加密通信
- 定期更新组件版本

### 4. 监控和告警

- 设置关键指标的监控
- 配置告警规则
- 定期审查和优化告警策略

### 5. 性能优化

- 调整Elasticsearch的JVM参数
- 优化Filebeat的批量发送大小
- 合理配置索引刷新间隔

## 高级功能

### 1. 设置告警

在"Management" > "Stack Management" > "Alerts and Insights" > "Rules"中，您可以：

1. 创建新的告警规则
2. 设置告警条件（如错误日志数量超过阈值）
3. 配置通知方式（如邮件、Slack等）

### 2. 使用机器学习功能

Elastic Stack提供了机器学习功能，可以自动检测异常和异常模式：

1. 在"Analytics" > "Machine Learning"中
2. 创建新的机器学习作业
3. 选择数据源和分析类型
4. 配置参数并启动作业

### 3. 配置安全功能

为了保护您的ELK Stack，可以配置以下安全功能：

1. 启用Elasticsearch安全功能
2. 配置用户认证和授权
3. 设置TLS加密通信
4. 配置审计日志

## 结论

通过本教程，您已经学会了如何在Book Store项目中使用ELK Stack进行日志收集、分析和可视化。ELK Stack是一个强大的日志分析解决方案，可以帮助您更好地理解和监控应用程序和系统的运行状态。

随着您对ELK Stack的深入了解，您可以探索更多高级功能，如机器学习、安全分析、APM等，以进一步提升您的日志分析能力。

## 附录

### 服务访问地址

| 服务 | 访问地址 | 端口 |
|------|----------|------|
| Kibana | http://localhost:5601 | 5601 |
| Elasticsearch | http://localhost:9200 | 9200/9300 |

### 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs [service_name]

# 重启特定服务
docker-compose restart [service_name]
```

### Filebeat配置说明

当前Filebeat配置文件(`./logging/filebeat.yml`)包含以下输入配置：

1. 通用日志收集
2. MySQL日志收集
3. Nacos日志收集
4. Redis日志收集
5. RabbitMQ日志收集
6. RocketMQ Broker日志收集
7. RocketMQ Name Server日志收集

每个输入配置都包含：
- 服务标识字段
- 多行日志处理
- JSON字段解码
- 不必要的字段移除