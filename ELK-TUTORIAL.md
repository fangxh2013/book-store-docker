# 从0开始使用ELK Stack详细教程

本教程将指导您如何在Docker环境中从零开始部署和使用ELK Stack（Elasticsearch, Logstash, Kibana）来收集、分析和可视化日志数据。

## 目录

1. [ELK Stack简介](#elk-stack简介)
2. [环境准备](#环境准备)
3. [部署ELK Stack](#部署elk-stack)
4. [配置Filebeat日志收集](#配置filebeat日志收集)
5. [访问Kibana](#访问kibana)
6. [创建索引模式](#创建索引模式)
7. [日志分析](#日志分析)
8. [高级功能](#高级功能)
9. [故障排除](#故障排除)

## ELK Stack简介

ELK Stack是一套开源的日志分析解决方案，由以下三个组件组成：

- **Elasticsearch**: 一个分布式搜索和分析引擎，用于存储和索引日志数据
- **Logstash**: 一个数据处理管道，用于接收、转换和发送日志数据
- **Kibana**: 一个可视化平台，用于搜索、查看和交互式分析存储在Elasticsearch中的数据

在本教程中，我们将使用Filebeat作为轻量级日志收集器，直接将日志发送到Elasticsearch，跳过Logstash以简化架构。

## 环境准备

### 系统要求

- Docker Engine 20.10+
- Docker Compose 1.29+
- 至少4GB内存（推荐8GB以上）
- 至少20GB可用磁盘空间

### 安装Docker和Docker Compose

如果您尚未安装Docker和Docker Compose，请参考以下官方文档：

- [Docker安装指南](https://docs.docker.com/get-docker/)
- [Docker Compose安装指南](https://docs.docker.com/compose/install/)

## 部署ELK Stack

### 1. 创建项目目录结构

```bash
mkdir -p elk-tutorial/{elasticsearch,kibana,filebeat}
cd elk-tutorial
```

### 2. 创建docker-compose.yml文件

创建一个包含ELK Stack服务的docker-compose.yml文件：

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.10.0
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
      - elk-network
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
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - elk-network
    depends_on:
      - elasticsearch
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.3"

  filebeat:
    image: docker.elastic.co/beats/filebeat:7.10.0
    container_name: filebeat
    user: root
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - elk-network
    depends_on:
      - elasticsearch
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.2"

volumes:
  elasticsearch_data:

networks:
  elk-network:
    driver: bridge
```

### 3. 创建Filebeat配置文件

在filebeat目录下创建filebeat.yml配置文件：

```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/lib/docker/containers/*/*.log
    fields:
      service: docker
    fields_under_root: true
    multiline.pattern: '^\d{4}-\d{2}-\d{2}'
    multiline.negate: true
    multiline.match: after

processors:
  - add_docker_metadata:
      host: "unix:///var/run/docker.sock"

  - decode_json_fields:
      fields: ["message"]
      target: "json"
      overwrite_keys: true

  - drop_fields:
      fields: ["agent", "ecs", "input", "log", "host"]

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "filebeat-%{[agent.version]}-%{+yyyy.MM.dd}"
  bulk_max_size: 1024
  worker: 2

setup.template.name: "filebeat"
setup.template.pattern: "filebeat-*"
setup.kibana.host: "kibana:5601"

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

### 4. 启动ELK Stack

在项目根目录下运行以下命令启动所有服务：

```bash
docker-compose up -d
```

### 5. 验证服务状态

检查所有服务是否正常运行：

```bash
docker-compose ps
```

您应该看到所有服务都处于"Up"状态。

## 配置Filebeat日志收集

### 1. 创建示例应用以生成日志

创建一个简单的应用来生成日志数据：

```bash
# 创建应用目录
mkdir -p app/logs

# 创建一个简单的Python应用
cat > app/app.py << EOF
import logging
import time
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 生成日志
while True:
    log_level = random.choice([logging.INFO, logging.WARNING, logging.ERROR])
    if log_level == logging.INFO:
        logger.info("This is an info message")
    elif log_level == logging.WARNING:
        logger.warning("This is a warning message")
    else:
        logger.error("This is an error message")
    
    time.sleep(5)
EOF
```

### 2. 创建应用的Dockerfile

```bash
cat > app/Dockerfile << EOF
FROM python:3.9-slim

WORKDIR /app

COPY app.py .

CMD ["python", "app.py"]
EOF
```

### 3. 更新docker-compose.yml文件

将应用服务添加到docker-compose.yml文件中：

```yaml
  app:
    build: ./app
    container_name: sample-app
    volumes:
      - ./app/logs:/app/logs
    networks:
      - elk-network
```

### 4. 重新启动服务

```bash
docker-compose up -d
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

### 4. 磁盘空间不足

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

### 3. 安全性

- 启用安全功能并配置用户认证
- 使用TLS加密通信
- 定期更新组件版本

### 4. 监控和告警

- 设置关键指标的监控
- 配置告警规则
- 定期审查和优化告警策略

## 结论

通过本教程，您已经学会了如何从零开始部署和使用ELK Stack进行日志收集、分析和可视化。ELK Stack是一个强大的日志分析解决方案，可以帮助您更好地理解和监控应用程序和系统的运行状态。

随着您对ELK Stack的深入了解，您可以探索更多高级功能，如机器学习、安全分析、APM等，以进一步提升您的日志分析能力。