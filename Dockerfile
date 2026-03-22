FROM python:3.9

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgomp1 \
    libssl-dev \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# 暴露端口（和代码默认一致）
EXPOSE 5000

# ✅ 简化启动命令，去掉--port参数
CMD ["python", "professional_finance_service.py"]
