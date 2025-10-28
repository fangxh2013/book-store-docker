#!/bin/bash
# MySQL健康检查脚本

# 从secrets读取密码
MYSQL_PWD=$(cat /run/secrets/mysql_root_password)

# 执行健康检查
mysqladmin ping -h localhost -u root -p"${MYSQL_PWD}" >/dev/null 2>&1