#!/bin/bash

# 设置脚本和日志路径
SCRIPT_PATH="/home/zhengqiushi/trustbees-search/app.py"
CONFIG_PATH="/home/zhengqiushi/trustbees-search/config.env"
PYTHON_PATH="/home/zhengqiushi/miniconda3/envs/myenv/bin/python"

# 查找当前运行的 python 进程
PID=$(ps aux | grep "$SCRIPT_PATH" | grep -v grep | awk '{print $2}')

# 如果找到了进程，结束它
if [ ! -z "$PID" ]; then
  echo "Stopping the current APP server process (PID: $PID)..."
  kill -9 $PID
  echo "Process stopped."
else
  echo "No running process found for APP server."
fi

# 启动脚本
echo "Starting APP server..."
nohup $PYTHON_PATH $SCRIPT_PATH --config $CONFIG_PATH > /dev/null 2>&1 &
echo "Spider server restarted successfully!"