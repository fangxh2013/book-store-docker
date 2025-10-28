#!/bin/bash
# Redis健康检查脚本

# 从secrets读取密码
REDIS_PWD=$(cat /run/secrets/redis_password)

# 执行健康检查
redis-cli -h localhost -p 6379 -a "${REDIS_PWD}" ping >/dev/null 2>&1