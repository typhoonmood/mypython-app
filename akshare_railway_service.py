#!/usr/bin/env python3
# AkShare Railway 服务 - 专为Railway优化
from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import time
import random
import os
import json
import pandas as pd
import akshare as ak

app = Flask(__name__)
CORS(app)

# Railway环境变量
PORT = int(os.getenv("PORT", 5000))
RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "production")

class AkShareRailwayService:
    """AkShare Railway服务类"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        
    def get_north_funds(self):
        """获取北向资金数据（带缓存）"""
        cache_key = "north_funds"
        
        # 检查缓存
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                print("使用缓存的北向资金数据")
                return cached_data
        
        print("获取实时北向资金数据...")
        
        try:
            for attempt in range(2):  # Railway环境减少重试次数
                try:
                    data = ak.stock_hsgt_board_rank_em()
                    if not data.empty:
                        print(f"成功! 获取到 {len(data)} 个板块数据")
                        analyzed_data = self.analyze_north_funds(data)
                        
                        # 更新缓存
                        self.cache[cache_key] = (analyzed_data, time.time())
                        return analyzed_data
                except Exception as e:
                    print(f"尝试 {attempt+1}/2 失败")
                    if attempt < 1:
                        time.sleep(1)
            
        except Exception as e:
            print(f"最终失败: {e}")
        
        # 返回空数据而不是失败
        return {"inflow_count": 0, "outflow_count": 0, "top_inflow": [], "top_outflow": []}
    
    def analyze_north_funds(self, data):
        """分析北向资金数据"""
        if data.empty:
            return {"inflow_count": 0, "outflow_count": 0, "top_inflow": [], "top_outflow": []}
        
        analysis = {
            "inflow_count": 0,
            "outflow_count": 0,
            "top_inflow": [],
            "top_outflow": []
        }
        
        # 查找列
        flow_column = None
        name_column = None
        
        for col in data.columns:
            if '净流入' in col or '流入' in col:
                flow_column = col
            if '名称' in col or '板块' in col:
                name_column = col
        
        if flow_column and name_column:
            inflow = data[data[flow_column] > 0]
            outflow = data[data[flow_column] < 0]
            
            analysis["inflow_count"] = int(len(inflow))
            analysis["outflow_count"] = int(len(outflow))
            
            # 流入前5（Railway环境减少数据量）
            if len(inflow) > 0:
                top_inflow = inflow.nlargest(5, flow_column)
                for _, row in top_inflow.iterrows():
                    analysis["top_inflow"].append({
                        "sector": str(row[name_column]),
                        "flow": float(row[flow_column])
                    })
            
            # 流出前5
            if len(outflow) > 0:
                top_outflow = outflow.nsmallest(5, flow_column)
                for _, row in top_outflow.iterrows():
                    analysis["top_outflow"].append({
                        "sector": str(row[name_column]),
                        "flow": float(row[flow_column])
                    })
        
        return analysis
    
    def get_finance_news(self, limit=5):
        """获取财经新闻（Railway优化版）"""
        print("获取财经新闻...")
        
        try:
            # 使用轻量级新闻源
            news_data = ak.news_cctv()
            
            if not news_data.empty:
                news_list = []
                for _, row in news_data.head(limit).iterrows():
                    news_list.append({
                        "title": str(row.get("新闻标题", ""))[:100],  # 限制长度
                        "time": str(row.get("发布时间", "")),
                        "source": "央视新闻"
                    })
                return news_list
        except Exception as e:
            print(f"获取新闻失败: {e}")
        
        # 返回精简的备用新闻
        return [
            {"title": "财经新闻数据更新中", "source": "系统", "time": datetime.datetime.now().strftime("%H:%M")}
        ]
    
    def get_sector_leaders(self):
        """获取板块龙头股票（精简版）"""
        return {
            "新能源汽车": ["宁德时代", "比亚迪", "亿纬锂能"],
            "人工智能": ["科大讯飞", "海康威视", "大华股份"],
            "医药": ["恒瑞医药", "药明康德", "迈瑞医疗"],
            "半导体": ["中芯国际", "韦尔股份", "兆易创新"],
            "光伏": ["隆基绿能", "通威股份", "阳光电源"]
        }

# 创建服务实例
service = AkShareRailwayService()

@app.route('/')
def home():
    """首页"""
    return jsonify({
        "status": "online",
        "service": "AkShare Railway Service",
        "environment": RAILWAY_ENVIRONMENT,
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoints": {
            "/": "首页",
            "/health": "健康检查",
            "/north_funds": "北向资金数据",
            "/news": "财经新闻",
            "/sector_leaders": "板块龙头",
            "/full_analysis": "完整分析报告"
        }
    })

@app.route('/health')
def health_check():
    """健康检查（Railway需要）"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": RAILWAY_ENVIRONMENT
    })

@app.route('/north_funds', methods=['GET'])
def north_funds():
    """获取北向资金数据"""
    try:
        data = service.get_north_funds()
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],  # 限制错误信息长度
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/news', methods=['GET'])
def finance_news():
    """获取财经新闻"""
    try:
        limit = min(int(request.args.get('limit', 5)), 10)  # 限制最大数量
        news = service.get_finance_news(limit=limit)
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": news
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/sector_leaders', methods=['GET'])
def sector_leaders():
    """获取板块龙头"""
    try:
        leaders = service.get_sector_leaders()
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": leaders
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/full_analysis', methods=['GET'])
def full_analysis():
    """获取完整分析报告（Railway优化版）"""
    try:
        # 获取所有数据
        north_funds = service.get_north_funds()
        news = service.get_finance_news(limit=5)
        leaders = service.get_sector_leaders()
        
        # 简化情绪分析
        sentiment_score = 50
        if north_funds["inflow_count"] > north_funds["outflow_count"]:
            sentiment_score = 65
        elif north_funds["inflow_count"] < north_funds["outflow_count"]:
            sentiment_score = 35
        
        sentiment = {
            "score": sentiment_score,
            "level": "乐观" if sentiment_score >= 60 else "中性" if sentiment_score >= 40 else "谨慎",
            "desc": "数据更新正常"
        }
        
        # 构建精简报告
        analysis = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "north_funds": north_funds,
            "news": news,
            "sector_leaders": leaders,
            "market_sentiment": sentiment
        }
        
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": analysis
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print(f"AkShare Railway 服务启动 - {RAILWAY_ENVIRONMENT}环境")
    print(f"端口: {PORT}")
    print("=" * 60)
    
    # Railway使用0.0.0.0绑定
    app.run(host='0.0.0.0', port=PORT, debug=False)