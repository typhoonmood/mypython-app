# AkShare HTTP 服务 + n8n 集成方案

## 📋 项目结构

```
workspace/
├── akshare_http_service.py    # AkShare HTTP 服务主程序
├── requirements.txt           # Python 依赖包
├── start_service.bat         # Windows 启动脚本
├── start_service.sh          # Linux/Mac 启动脚本
├── n8n_akshare_function.js   # n8n Function 节点代码
├── final_auto_system.py      # 原始自动化系统（保留）
└── README.md                 # 使用说明
```

## 🚀 快速开始

### 第1步：启动 AkShare HTTP 服务

#### Windows 用户：
```bash
双击 start_service.bat
```
或
```bash
start_service.bat
```

#### Linux/Mac 用户：
```bash
chmod +x start_service.sh
./start_service.sh
```

#### 手动启动：
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python akshare_http_service.py
```

### 第2步：验证服务运行
打开浏览器访问：http://localhost:5000

应该看到：
```json
{
  "status": "online",
  "service": "AkShare HTTP Service",
  "version": "1.0.0",
  "endpoints": {
    "/": "首页",
    "/health": "健康检查",
    "/north_funds": "北向资金数据",
    "/news": "财经新闻",
    "/sector_leaders": "板块龙头",
    "/stock/<symbol>": "股票数据",
    "/full_analysis": "完整分析报告"
  }
}
```

## 🔌 n8n 配置

### 第1步：在 n8n 中创建工作流

工作流结构：
```
[Cron 节点] → [Function 节点] → [HTTP Request 节点] → [飞书 Webhook]
```

### 第2步：配置 Function 节点

1. 在 n8n 中创建 Function 节点
2. 将 `n8n_akshare_function.js` 的内容复制到 Function 节点中
3. 保存节点

### 第3步：配置 Cron 节点
- 设置定时触发（如每天 9:00）
- 时区：Asia/Shanghai

### 第4步：配置飞书 Webhook
- 使用你原来的飞书 Webhook URL
- 方法：POST
- Headers: `Content-Type: application/json`

## 📊 API 接口说明

### 1. 完整分析报告
```
GET http://localhost:5000/full_analysis
```
返回完整的投资分析数据，包括：
- 北向资金流向
- 最新财经新闻
- 板块龙头股票
- 市场情绪分析

### 2. 北向资金数据
```
GET http://localhost:5000/north_funds
```
返回北向资金详细数据：
- 流入/流出板块数量
- 流入前10板块
- 流出前10板块

### 3. 财经新闻
```
GET http://localhost:5000/news?limit=10
```
参数：
- `limit`: 返回新闻数量（默认10）

### 4. 板块龙头
```
GET http://localhost:5000/sector_leaders
```
返回各板块龙头股票列表

### 5. 健康检查
```
GET http://localhost:5000/health
```
检查服务状态

## ⚙️ 配置说明

### 修改服务端口
编辑 `akshare_http_service.py`：
```python
app.run(host='0.0.0.0', port=5000, debug=False)  # 修改端口号
```

### 修改 n8n 中的服务地址
编辑 `n8n_akshare_function.js`：
```javascript
const CONFIG = {
    AKSHARE_SERVICE: 'http://localhost:5000',  // 修改为你的服务地址
    // ...
};
```

## 🔧 故障排除

### 问题1：服务启动失败
**症状**：`ModuleNotFoundError: No module named 'akshare'`
**解决**：
```bash
pip install akshare==1.12.75
```

### 问题2：n8n 连接失败
**症状**：`ECONNREFUSED` 或连接超时
**解决**：
1. 确认 AkShare 服务正在运行
2. 检查防火墙设置
3. 修改 n8n 中的服务地址

### 问题3：数据获取失败
**症状**：AkShare API 返回空数据
**解决**：
1. 检查网络连接
2. 等待一段时间重试
3. 查看服务日志

## 📈 数据更新频率

- **北向资金数据**：交易日实时更新
- **财经新闻**：实时抓取
- **板块龙头**：静态数据，可手动更新

## 🔄 自动运行

### Windows 计划任务
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置每天 9:00 运行 `start_service.bat`

### Linux/Mac cron 任务
```bash
# 编辑 crontab
crontab -e

# 添加每天 9:00 启动
0 9 * * * cd /path/to/workspace && ./start_service.sh
```

## 📞 支持

如有问题，请检查：
1. Python 版本（需要 3.8+）
2. 网络连接
3. 防火墙设置
4. 服务日志

## 📝 更新日志

### v1.0.0 (2024-03-22)
- 初始版本发布
- 支持 AkShare 数据获取
- 提供完整 HTTP API
- n8n 集成支持

---

**注意**：投资有风险，本系统提供的数据仅供参考，不构成投资建议。