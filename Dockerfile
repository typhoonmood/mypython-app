# 用完整镜像，避免依赖缺失
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 安装系统依赖（解决akshare/pandas的底层依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgomp1 \
    libssl-dev \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露Railway的PORT环境变量（关键）
ENV PORT=5000

# 暴露端口
EXPOSE $PORT

# 启动命令（强制指定端口，确保和代码一致）
CMD ["sh", "-c", "python professional_finance_service.py --port $PORT"]
