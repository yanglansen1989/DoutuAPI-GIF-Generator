# 使用官方轻量级 Python 3.10 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 1. 安装系统依赖和中文字体
# fonts-noto-cjk 是 Google 的开源中日韩字体库，解决中文乱码问题
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 复制项目代码
COPY . .

# 4. 创建字体目录（为了方便挂载自定义字体）
RUN mkdir -p fonts

# 5. 暴露端口
EXPOSE 8066

# 6. 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8066"]
