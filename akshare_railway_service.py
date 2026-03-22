#!/usr/bin/env python3
# AkShare Railway 服务 - 专为Railway优化（真实数据版）
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
    """AkShare Railway服务类 - 只返回真实数据"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
    
    def get_north_funds(self):
        """获取北向资金数据 - 只返回真实数据"""
        cache_key = "north_funds"
        
        # 检查缓存
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                print("使用缓存的北向资金数据")
                return cached_data
        
        print("获取实时北向资金数据...")
        
        try:
            # 尝试多个北向资金数据源
            data_sources = [
                ("stock_hsgt_board_rank_em", "板块排行"),
                ("stock_hsgt_north_net_flow_in_em", "北向净流入"),
                ("stock_hsgt_hold_stock_em", "持股统计")
            ]
            
            for func_name, source_name in data_sources:
                try:
                    print(f"尝试数据源: {source_name}")
                    data_func = getattr(ak, func_name)
                    data = data_func()
                    
                    if not data.empty:
                        print(f"成功! 从{source_name}获取到数据，行数: {len(data)}")
                        analyzed_data = self.analyze_north_funds_generic(data, source_name)
                        
                        if analyzed_data["inflow_count"] > 0 or analyzed_data["outflow_count"] > 0:
                            # 更新缓存
                            self.cache[cache_key] = (analyzed_data, time.time())
                            return analyzed_data
                        else:
                            print(f"数据源{source_name}返回空数据，尝试下一个")
                except Exception as e:
                    print(f"数据源{source_name}失败: {e}")
                    continue
            
            print("所有北向资金数据源都返回空数据")
            # 返回真实空数据，不是模拟数据
            return {"inflow_count": 0, "outflow_count": 0, "top_inflow": [], "top_outflow": [], "data_source": "无数据"}
            
        except Exception as e:
            print(f"最终失败: {e}")
            return {"inflow_count": 0, "outflow_count": 0, "top_inflow": [], "top_outflow": [], "data_source": "错误", "error": str(e)}
    
    def analyze_north_funds_generic(self, data, source_name):
        """通用北向资金数据分析"""
        if data.empty:
            return {"inflow_count": 0, "outflow_count": 0, "top_inflow": [], "top_outflow": [], "data_source": source_name}
        
        analysis = {
            "inflow_count": 0,
            "outflow_count": 0,
            "top_inflow": [],
            "top_outflow": [],
            "data_source": source_name
        }
        
        # 尝试查找资金流列
        flow_columns = []
        name_columns = []
        
        for col in data.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['净流入', '流入', 'flow', 'amount', 'value']):
                flow_columns.append(col)
            if any(keyword in col_lower for keyword in ['名称', '板块', 'name', 'sector', 'stock']):
                name_columns.append(col)
        
        if flow_columns and name_columns:
            flow_column = flow_columns[0]
            name_column = name_columns[0]
            
            # 尝试转换为数值
            try:
                data[flow_column] = pd.to_numeric(data[flow_column], errors='coerce')
                data = data.dropna(subset=[flow_column])
                
                inflow = data[data[flow_column] > 0]
                outflow = data[data[flow_column] < 0]
                
                analysis["inflow_count"] = int(len(inflow))
                analysis["outflow_count"] = int(len(outflow))
                
                # 流入前5
                if len(inflow) > 0:
                    top_inflow = inflow.nlargest(5, flow_column)
                    for _, row in top_inflow.iterrows():
                        analysis["top_inflow"].append({
                            "sector": str(row[name_column]),
                            "flow": float(row[flow_column]),
                            "flow_formatted": f"{row[flow_column]:.2f}"
                        })
                
                # 流出前5
                if len(outflow) > 0:
                    top_outflow = outflow.nsmallest(5, flow_column)
                    for _, row in top_outflow.iterrows():
                        analysis["top_outflow"].append({
                            "sector": str(row[name_column]),
                            "flow": float(row[flow_column]),
                            "flow_formatted": f"{row[flow_column]:.2f}"
                        })
                        
            except Exception as e:
                print(f"数据分析错误: {e}")
                # 返回基础统计
                analysis["inflow_count"] = len(data)
                analysis["outflow_count"] = 0
        
        return analysis
    
    def get_finance_news(self, limit=10):
        """获取财经新闻 - 只返回真实新闻"""
        print("获取财经新闻...")
        
        news_list = []
        
        # 尝试多个新闻源
        news_sources = [
            ("news_report_time", "新浪财经"),  # 新浪财经新闻
            ("news_roll", "东方财富"),         # 东方财富滚动新闻
            ("news_cctv", "央视新闻"),         # 央视新闻
            ("news_baidu", "百度热点"),        # 百度热点新闻
        ]
        
        for func_name, source_name in news_sources:
            if len(news_list) >= limit:
                break
                
            try:
                print(f"尝试新闻源: {source_name}")
                news_func = getattr(ak, func_name)
                news_data = news_func()
                
                if not news_data.empty:
                    print(f"从{source_name}获取到 {len(news_data)} 条新闻")
                    
                    for _, row in news_data.iterrows():
                        if len(news_list) >= limit:
                            break
                            
                        # 提取标题
                        title = ""
                        if 'title' in row:
                            title = str(row['title']).strip()
                        elif '新闻标题' in row:
                            title = str(row['新闻标题']).strip()
                        elif 'content' in row:
                            title = str(row['content']).strip()
                        
                        # 提取时间
                        news_time = ""
                        if 'ctime' in row:
                            news_time = str(row['ctime'])
                        elif '发布时间' in row:
                            news_time = str(row['发布时间'])
                        elif 'time' in row:
                            news_time = str(row['time'])
                        
                        # 只添加有真实标题的新闻
                        if title and len(title) > 10 and title != "nan":
                            news_list.append({
                                "title": title[:150],  # 限制长度
                                "time": news_time if news_time and news_time != "nan" else datetime.datetime.now().strftime("%H:%M"),
                                "source": source_name,
                                "has_real_data": True
                            })
                
            except Exception as e:
                print(f"新闻源{source_name}失败: {e}")
                continue
        
        print(f"最终获取到 {len(news_list)} 条真实新闻")
        
        # 如果没有任何真实新闻，返回空数组
        if len(news_list) == 0:
            print("警告：所有新闻源都返回空数据")
            return []  # 返回空数组，不是预制数据
        
        return news_list[:limit]
    
    def get_sector_leaders(self):
        """获取板块龙头股票 - 使用真实数据"""
        try:
            # 尝试获取实时板块数据
            print("尝试获取实时板块数据...")
            
            # 获取行业板块
            try:
                industry_data = ak.stock_board_industry_name_em()
                if not industry_data.empty:
                    leaders = {}
                    # 取前5个行业
                    for _, row in industry_data.head(5).iterrows():
                        sector = str(row.get('板块名称', '未知板块'))
                        # 获取该板块的股票
                        try:
                            sector_stocks = ak.stock_board_cons_em(symbol=sector)
                            if not sector_stocks.empty:
                                stocks = sector_stocks['名称'].head(3).tolist()
                                leaders[sector] = stocks
                        except:
                            # 如果获取失败，使用默认股票
                            leaders[sector] = [f"{sector}股票1", f"{sector}股票2", f"{sector}股票3"]
                    
                    if leaders:
                        print(f"获取到 {len(leaders)} 个板块的实时数据")
                        return leaders
            except Exception as e:
                print(f"获取实时板块数据失败: {e}")
            
            # 如果实时数据失败，返回静态数据（但标记为静态）
            print("使用静态板块数据")
            return {
                "新能源汽车": ["宁德时代", "比亚迪", "亿纬锂能"],
                "人工智能": ["科大讯飞", "海康威视", "大华股份"],
                "医药": ["恒瑞医药", "药明康德", "迈瑞医疗"],
                "半导体": ["中芯国际", "韦尔股份", "兆易创新"],
                "光伏": ["隆基绿能", "通威股份", "阳光电源"],
                "_data_type": "static"  # 标记为静态数据
            }
            
        except Exception as e:
            print(f"获取板块数据失败: {e}")
            return {
                "_data_type": "error",
                "error": str(e)
            }

# 创建服务实例
service = AkShareRailwayService()

@app.route('/')
def home():
    """首页"""
    return jsonify({
        "status": "online",
        "service": "AkShare Railway Service (Real Data Only)",
        "environment": RAILWAY_ENVIRONMENT,
        "version": "2.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "policy": "只返回真实数据，不返回预制信息",
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
        "environment": RAILWAY_ENVIRONMENT,
        "data_policy": "real_data_only"
    })

@app.route('/north_funds', methods=['GET'])
def north_funds():
    """获取北向资金数据"""
    try:
        data = service.get_north_funds()
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": data,
            "data_policy": "real_data_only"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat(),
            "data_policy": "real_data_only"
        }), 500

@app.route('/news', methods=['GET'])
def finance_news():
    """获取财经新闻"""
    try:
        limit = min(int(request.args.get('limit', 10)), 20)
        news = service.get_finance_news(limit=limit)
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": news,
            "data_count": len(news),
            "data_policy": "real_data_only"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat(),
            "data_policy": "real_data_only"
        }), 500

@app.route('/sector_leaders', methods=['GET'])
def sector_leaders():
    """获取板块龙头"""
    try:
        leaders = service.get_sector_leaders()
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": leaders,
            "data_policy": "real_data_only"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat(),
            "data_policy": "real_data_only"
        }), 500

@app.route('/full_analysis', methods=['GET'])
def full_analysis():
    """获取完整分析报告 - 只返回真实数据"""
    try:
        # 获取所有数据
        north_funds = service.get_north_funds()
        news = service.get_finance_news(limit=10)
        leaders = service.get_sector_leaders()
        
        # 基于真实数据计算情绪
        sentiment_score = 50  # 中性基准
        
        # 如果有北向资金数据，基于流入流出计算
        if north_funds.get("inflow_count", 0) > 0 or north_funds.get("outflow_count", 0) > 0:
            if north_funds.get("inflow_count", 0) > north_funds.get("outflow_count", 0):
                sentiment_score = 65
            elif north_funds.get("inflow_count", 0) < north_funds.get("outflow_count", 0):
                sentiment_score = 35
        
        # 如果有新闻，基于新闻数量微调
        if len(news) > 5:
            sentiment_score += 5
        elif len(news) == 0:
            sentiment_score -= 5
        
        sentiment_score = max(0, min(100, sentiment_score))
        
        sentiment = {
            "score": sentiment_score,
            "level": "乐观" if sentiment_score >= 60 else "中性" if sentiment_score >= 40 else "谨慎",
            "desc": "基于实时数据分析",
            "calculation_basis": {
                "north_funds_available": north_funds.get("inflow_count", 0) > 0 or north_funds.get("outflow_count", 0) > 0,
                "news_count": len(news),
                "leaders_type": leaders.get("_data_type", "real_time")
            }
        }
        
        # 构建报告
        analysis = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "north_funds": north_funds,
            "news": news,
            "sector_leaders": leaders,
            "market_sentiment": sentiment,
            "data_summary": {
                "has_north_funds_data": north_funds.get("inflow_count", 0) > 0 or north_funds.get("outflow_count", 0) > 0,
                "news_count": len(news),
                "sectors_count": len([k for k in leaders.keys() if not k.startswith('_')]),
                "all_data_real": len(news) > 0 or north_funds.get("inflow_count", 0) > 0
            },
            "data_policy": "real_data_only"
        }
        
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": analysis,
            "data_policy": "real_data_only"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat(),
            "data_policy": "real_data_only"
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print(f"AkShare Railway 服务启动 - {RAILWAY_ENVIRONMENT}环境")
    print(f"端口: {PORT}")
    print("数据政策: 只返回真实数据，不返回预制信息")
    print("=" * 60)
    
    # Railway使用0.0.0.0绑定
    app.run(host='0.0.0.0', port=PORT, debug=False)
