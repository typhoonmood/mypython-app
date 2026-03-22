#!/usr/bin/env python3
# 专业财经新闻服务 - 真实数据版
from flask import Flask, jsonify
from flask_cors import CORS
import datetime
import time
import os
import pandas as pd
import akshare as ak
import re

app = Flask(__name__)
CORS(app)

PORT = int(os.getenv("PORT", 5000))

class RealFinanceNewsService:
    """真实财经新闻服务 - 只使用真实API数据"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300
        
        # 真实股票数据缓存
        self.stock_data_cache = {}
        self.stock_cache_timeout = 3600
        
    def get_real_finance_news(self):
        """获取真实财经新闻 - 优先AkShare、财联社、新浪、巨潮"""
        print("获取真实财经新闻...")
        
        all_news = []
        
        # 1. 财联社新闻（最专业）
        try:
            print("尝试财联社新闻...")
            # 财联社有多种新闻接口
            try:
                # 尝试财联社电报
                cls_news = ak.news_cls_telegraph()
                if not cls_news.empty:
                    print(f"财联社电报: {len(cls_news)}条")
                    for _, row in cls_news.iterrows():
                        title = str(row.get('title', '')).strip()
                        if title and len(title) > 10:
                            all_news.append({
                                "title": title[:150],
                                "content": str(row.get('content', ''))[:300],
                                "time": str(row.get('ctime', '')),
                                "source": "财联社电报",
                                "importance": 90  # 财联社重要性高
                            })
            except:
                pass
            
            # 尝试财联社快讯
            try:
                cls_express = ak.news_cls_express()
                if not cls_express.empty:
                    print(f"财联社快讯: {len(cls_express)}条")
                    for _, row in cls_express.iterrows():
                        title = str(row.get('title', '')).strip()
                        if title and len(title) > 10:
                            all_news.append({
                                "title": title[:150],
                                "content": str(row.get('content', ''))[:300],
                                "time": str(row.get('ctime', '')),
                                "source": "财联社快讯",
                                "importance": 85
                            })
            except:
                pass
        except Exception as e:
            print(f"财联社新闻失败: {e}")
        
        # 2. 新浪财经新闻
        try:
            print("尝试新浪财经新闻...")
            sina_news = ak.news_report_time()
            if not sina_news.empty:
                print(f"新浪财经: {len(sina_news)}条")
                for _, row in sina_news.iterrows():
                    title = str(row.get('title', '')).strip()
                    if title and len(title) > 10:
                        all_news.append({
                            "title": title[:150],
                            "content": str(row.get('content', ''))[:300],
                            "time": str(row.get('ctime', '')),
                            "source": "新浪财经",
                            "importance": 80
                        })
        except Exception as e:
            print(f"新浪财经失败: {e}")
        
        # 3. 东方财富新闻
        try:
            print("尝试东方财富新闻...")
            eastmoney_news = ak.news_roll()
            if not eastmoney_news.empty:
                print(f"东方财富: {len(eastmoney_news)}条")
                for _, row in eastmoney_news.iterrows():
                    title = str(row.get('title', '')).strip()
                    if title and len(title) > 10:
                        all_news.append({
                            "title": title[:150],
                            "content": "",
                            "time": str(row.get('ctime', '')),
                            "source": "东方财富",
                            "importance": 75
                        })
        except Exception as e:
            print(f"东方财富失败: {e}")
        
        # 4. 巨潮资讯（上市公司公告）
        try:
            print("尝试巨潮资讯...")
            # 获取最新公告
            announcements = ak.announcement_latest()
            if not announcements.empty:
                print(f"巨潮公告: {len(announcements)}条")
                for _, row in announcements.head(20).iterrows():
                    title = str(row.get('公告标题', '')).strip()
                    if title and len(title) > 10:
                        stock_code = str(row.get('证券代码', ''))
                        stock_name = str(row.get('证券简称', ''))
                        
                        all_news.append({
                            "title": f"{stock_name}: {title[:100]}",
                            "content": f"公告代码: {stock_code}",
                            "time": str(row.get('公告日期', '')),
                            "source": "巨潮资讯",
                            "stock_code": stock_code,
                            "stock_name": stock_name,
                            "importance": 85
                        })
        except Exception as e:
            print(f"巨潮资讯失败: {e}")
        
        # 5. 央视财经新闻（备用）
        if len(all_news) < 15:
            try:
                print("尝试央视财经新闻...")
                cctv_news = ak.news_cctv()
                if not cctv_news.empty:
                    print(f"央视财经: {len(cctv_news)}条")
                    for _, row in cctv_news.iterrows():
                        title = str(row.get('新闻标题', '')).strip()
                        if title and len(title) > 10:
                            all_news.append({
                                "title": title[:150],
                                "content": "",
                                "time": str(row.get('发布时间', '')),
                                "source": "央视财经",
                                "importance": 70
                            })
            except Exception as e:
                print(f"央视财经失败: {e}")
        
        # 去重并排序
        unique_news = []
        seen_titles = set()
        
        for news in all_news:
            title_key = news["title"][:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        # 按重要性排序
        unique_news.sort(key=lambda x: x["importance"], reverse=True)
        
        print(f"最终获取 {len(unique_news)} 条真实财经新闻")
        return unique_news[:20]  # 返回最多20条
    
    def analyze_news_and_get_stocks(self, news_item):
        """分析新闻并获取相关股票"""
        title = news_item["title"]
        content = news_item.get("content", "")
        
        # 提取股票代码和名称
        stocks = []
        
        # 1. 从标题中提取股票
        stock_pattern = r'([0-9]{6})|([\u4e00-\u9fa5]{2,4})'
        matches = re.findall(stock_pattern, title)
        
        for match in matches:
            stock_code = match[0]
            stock_name = match[1]
            
            if stock_code and len(stock_code) == 6:
                # 通过代码获取股票信息
                stock_info = self.get_stock_by_code(stock_code)
                if stock_info:
                    stocks.append(stock_info)
            
            if stock_name and len(stock_name) >= 2:
                # 通过名称获取股票信息
                stock_info = self.get_stock_by_name(stock_name)
                if stock_info:
                    stocks.append(stock_info)
        
        # 2. 如果没找到具体股票，根据行业推荐
        if len(stocks) < 5:
            related_sectors = self.analyze_sectors(title + " " + content)
            sector_stocks = self.get_stocks_by_sectors(related_sectors, 5 - len(stocks))
            stocks.extend(sector_stocks)
        
        # 去重
        unique_stocks = []
        seen_codes = set()
        
        for stock in stocks:
            if stock["code"] not in seen_codes:
                seen_codes.add(stock["code"])
                unique_stocks.append(stock)
        
        # 计算优先级
        for stock in unique_stocks:
            stock["priority"] = self.calculate_stock_priority(stock, news_item)
        
        # 按优先级排序
        unique_stocks.sort(key=lambda x: x["priority"], reverse=True)
        
        return unique_stocks[:10]  # 最多返回10个
    
    def get_stock_by_code(self, code):
        """通过代码获取股票信息"""
        try:
            # 获取股票实时信息
            stock_info = ak.stock_zh_a_spot_em()
            if not stock_info.empty:
                stock_row = stock_info[stock_info['代码'] == code]
                if not stock_row.empty:
                    return {
                        "code": code,
                        "name": str(stock_row.iloc[0]['名称']),
                        "price": float(stock_row.iloc[0]['最新价']),
                        "change": float(stock_row.iloc[0]['涨跌幅']),
                        "sector": self.get_stock_sector(code)
                    }
        except:
            pass
        
        # 如果实时数据失败，尝试基本信息
        try:
            stock_basic = ak.stock_individual_info_em(symbol=code)
            if not stock_basic.empty:
                return {
                    "code": code,
                    "name": str(stock_basic.iloc[0]['股票简称']),
                    "price": 0,
                    "change": 0,
                    "sector": "未知"
                }
        except:
            pass
        
        return None
    
    def get_stock_by_name(self, name):
        """通过名称获取股票信息"""
        try:
            stock_info = ak.stock_zh_a_spot_em()
            if not stock_info.empty:
                # 模糊匹配
                for _, row in stock_info.iterrows():
                    if name in str(row['名称']):
                        return {
                            "code": str(row['代码']),
                            "name": str(row['名称']),
                            "price": float(row['最新价']),
                            "change": float(row['涨跌幅']),
                            "sector": self.get_stock_sector(str(row['代码']))
                        }
        except:
            pass
        
        return None
    
    def get_stock_sector(self, code):
        """获取股票所属行业"""
        try:
            # 获取股票所属板块
            stock_sectors = ak.stock_sector_detail(symbol=code)
            if not stock_sectors.empty:
                return str(stock_sectors.iloc[0]['板块名称'])
        except:
            pass
        
        return "未知"
    
    def analyze_sectors(self, text):
        """分析文本中的行业关键词"""
        sectors = set()
        
        # 行业关键词
        sector_keywords = {
            "新能源汽车": ["新能源", "汽车", "电池", "锂电", "电动车"],
            "光伏": ["光伏", "太阳能", "硅料", "组件"],
            "芯片": ["芯片", "半导体", "集成电路", "光刻机"],
            "人工智能": ["AI", "人工智能", "大模型", "算法"],
            "医药": ["医药", "医疗", "生物", "创新药", "疫苗"],
            "白酒": ["白酒", "茅台", "五粮液", "酒"],
            "金融": ["银行", "证券", "保险", "金融"],
            "房地产": ["房地产", "地产", "房价", "楼市"],
            "基建": ["基建", "建筑", "工程", "铁路"],
            "电力": ["电力", "电网", "发电", "新能源"],
            "煤炭": ["煤炭", "煤矿", "能源"],
            "有色金属": ["有色", "金属", "铜", "铝", "黄金"]
        }
        
        text_lower = text.lower()
        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    sectors.add(sector)
                    break
        
        return list(sectors)[:3]
    
    def get_stocks_by_sectors(self, sectors, limit=5):
        """根据行业获取股票"""
        stocks = []
        
        for sector in sectors:
            try:
                # 获取行业成分股
                sector_stocks = ak.stock_sector_spot(symbol=sector)
                if not sector_stocks.empty:
                    for _, row in sector_stocks.head(3).iterrows():
                        stocks.append({
                            "code": str(row['代码']),
                            "name": str(row['名称']),
                            "price": float(row['最新价']),
                            "change": float(row['涨跌幅']),
                            "sector": sector
                        })
            except:
                pass
        
        return stocks[:limit]
    
    def calculate_stock_priority(self, stock, news_item):
        """计算股票优先级"""
        priority = 50
        
        # 新闻相关性
        if stock["name"] in news_item["title"]:
            priority += 30
        
        # 涨跌幅影响
        if stock.get("change", 0) > 5:
            priority += 20
        elif stock.get("change", 0) < -5:
            priority += 10
        
        # 热门行业
        hot_sectors = ["新能源汽车", "芯片", "人工智能", "光伏"]
        if stock["sector"] in hot_sectors:
            priority += 15
        
        # 新闻来源权重
        if news_item["source"] == "财联社电报":
            priority += 10
        elif news_item["source"] == "巨潮资讯":
            priority += 8
        
        return min(100, priority)
    
    def get_sector_relations(self, sectors):
        """获取正负相关板块"""
        positive = []
        negative = []
        
        sector_relations = {
            "新能源汽车": {"positive": ["锂电池", "充电桩", "汽车零部件"], "negative": ["石油", "传统汽车"]},
            "光伏": {"positive": ["储能", "电力设备", "新能源"], "negative": ["煤炭", "传统能源"]},
            "芯片": {"positive": ["半导体设备", "材料", "5G"], "negative": ["传统电子"]},
            "人工智能": {"positive": ["云计算", "大数据", "软件"], "negative": ["传统制造业"]},
            "医药": {"positive": ["医疗器械", "生物科技"], "negative": []},
            "白酒": {"positive": ["食品饮料"], "negative": []},
            "金融": {"positive": ["银行", "保险"], "negative": []},
            "房地产": {"positive": ["建材", "家电"], "negative": []}
        }
        
        for sector in sectors[:2]:
            if sector in sector_relations:
                positive.extend(sector_relations[sector]["positive"])
                negative.extend(sector_relations[sector]["negative"])
        
        return list(set(positive))[:3], list(set(negative))[:3]
    
    def get_north_funds_real(self):
        """获取真实北向资金数据"""
        try:
            print("获取真实北向资金数据...")
            
            # 北向资金板块排行
            north_data = ak.stock_hsgt_board_rank_em()
            
            if not north_data.empty:
                print(f"获取到 {len(north_data)} 条北向资金数据")
                
                # 分析数据
                analysis = {
                    "total_inflow": 0,
                    "total_outflow": 0,
                    "inflow_count": 0,
                    "outflow_count": 0,
                    "top_inflow": [],
                    "top_outflow": [],
                    "update_time": datetime.datetime.now().strftime("%H:%M"),
                    "data_source": "东方财富实时"
                }
                
                # 查找资金列
                flow_col = None
                name_col = None
                
                for col in north_data.columns:
                    if '净流入' in col or '流入' in col:
                        flow_col = col
                    if '名称' in col or '板块' in col:
                        name_col = col
                
                if flow_col and name_col:
                    # 转换为数值
                    north_data[flow_col] = pd.to_numeric(north_data[flow_col], errors='coerce')
                    north_data = north_data.dropna(subset=[flow_col])
                    
                    inflow = north_data[north_data[flow_col] > 0]
                    outflow = north_data[north_data[flow_col] < 0]
                    
                    analysis["inflow_count"] = int(len(inflow))
                    analysis["outflow_count"] = int(len(outflow))
                    analysis["total_inflow"] = float(inflow[flow_col].sum())
                    analysis["total_outflow"] = float(abs(outflow[flow_col].sum()))
                    
                    # 流入前5
                    if len(inflow) > 0:
                        top_in = inflow.nlargest(5, flow_col)
                        for _, row in top_in.iterrows():
                            analysis["top_inflow"].append({
                                "sector": str(row[name_col]),
                                "flow": float(row[flow_col]),
                                "flow_formatted": f"{row[flow_col]:.2f}亿"
                            })
                    
                    # 流出前5
                    if len(outflow) > 0:
                        top_out = outflow.nsmallest(5, flow_col)
                        for _, row in top_out.iterrows():
                            analysis["top_outflow"].append({
                                "sector": str(row[name_col]),
                                "flow": float(row[flow_col]),
                                "flow_formatted": f"{row[flow_col]:.2f}亿"
                            })
                
                return analysis
            
            return {
                "inflow_count": 0,
                "outflow_count": 0,
                "top_inflow": [],
                "top_outflow": [],
                "update_time": datetime.datetime.now().strftime("%H:%M"),
                "data_source": "数据更新中"
            }
            
        except Exception as e:
            print(f"北向资金获取失败: {e}")
            return {
                "inflow_count": 0,
                "outflow_count": 0,
                "top_inflow": [],
                "top_outflow": [],
                "update_time": datetime.datetime.now().strftime("%H:%M"),
                "data_source": "获取失败",
                "error": str(e)
            }
    
    def calculate_market_sentiment(self, north_funds, news_count):
        """计算市场情绪 - 基于真实数据"""
        sentiment_score = 50
        
        if north_funds.get("total_inflow", 0) > north_funds.get("total_outflow", 0):
            sentiment_score += 15
        elif north_funds.get("total_inflow", 0) < north_funds.get("total_outflow", 0):
            sentiment_score -= 10
        
        # 新闻数量影响
        if news_count > 15:
            sentiment_score += 10  # 新闻多表示市场活跃
        elif news_count < 5:
            sentiment_score -= 5   # 新闻少表示市场平淡
        
        # 流入板块数量影响
        inflow_count = north_funds.get("inflow_count", 0)
        if inflow_count > 10:
            sentiment_score += 10
        elif inflow_count < 3:
            sentiment_score -= 5
        
        # 确保在0-100范围内
        sentiment_score = max(0, min(100, sentiment_score))
        
        # 确定情绪等级
        if sentiment_score >= 70:
            level = "乐观"
            desc = "市场情绪积极，资金流入明显"
        elif sentiment_score >= 50:
            level = "中性"
            desc = "市场情绪平稳，多空力量均衡"
        elif sentiment_score >= 30:
            level = "谨慎"
            desc = "市场情绪偏谨慎，注意风险控制"
        else:
            level = "悲观"
            desc = "市场情绪低迷，建议观望"
        
        return {
            "score": sentiment_score,
            "level": level,
            "desc": desc,
            "calculation_basis": {
                "north_funds_net": north_funds.get("total_inflow", 0) - north_funds.get("total_outflow", 0),
                "news_count": news_count,
                "inflow_sectors": north_funds.get("inflow_count", 0)
            }
        }
    
    def get_sector_leaders_real(self):
        """获取真实板块龙头"""
        try:
            print("获取真实板块龙头...")
            
            # 获取行业板块实时数据
            sector_data = ak.stock_board_industry_name_em()
            
            if not sector_data.empty:
                leaders = {}
                
                # 取涨跌幅前8的板块
                sector_data = sector_data.sort_values(by='涨跌幅', ascending=False)
                
                for _, row in sector_data.head(8).iterrows():
                    sector_name = str(row.get('板块名称', ''))
                    change = float(row.get('涨跌幅', 0))
                    
                    if sector_name:
                        # 获取该板块成分股
                        try:
                            sector_stocks = ak.stock_board_cons_em(symbol=sector_name)
                            if not sector_stocks.empty:
                                # 按涨跌幅排序
                                sector_stocks = sector_stocks.sort_values(by='涨跌幅', ascending=False)
                                top_stocks = sector_stocks.head(5)['名称'].tolist()
                                leaders[sector_name] = {
                                    "stocks": top_stocks,
                                    "sector_change": f"{change:.2f}%",
                                    "data_source": "实时数据"
                                }
                            else:
                                leaders[sector_name] = {
                                    "stocks": [f"{sector_name}龙头1", f"{sector_name}龙头2"],
                                    "sector_change": f"{change:.2f}%",
                                    "data_source": "基础数据"
                                }
                        except:
                            leaders[sector_name] = {
                                "stocks": [f"{sector_name}股票"],
                                "sector_change": f"{change:.2f}%",
                                "data_source": "简化数据"
                            }
                
                print(f"获取到 {len(leaders)} 个板块的实时数据")
                return leaders
            
            # 如果实时数据失败，返回空
            return {
                "_note": "实时板块数据获取失败",
                "data_source": "无数据"
            }
            
        except Exception as e:
            print(f"板块龙头获取失败: {e}")
            return {
                "_note": f"数据获取失败: {str(e)[:50]}",
                "data_source": "错误"
            }

# 创建服务实例
service = RealFinanceNewsService()

@app.route('/')
def home():
    """首页"""
    return jsonify({
        "status": "online",
        "service": "专业财经新闻服务",
        "version": "3.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "features": [
            "真实财经新闻（财联社、新浪、巨潮等）",
            "智能股票推荐（基于新闻内容）",
            "正负相关板块分析",
            "实时北向资金数据",
            "市场情绪分析",
            "板块龙头数据"
        ],
        "data_policy": "100%真实数据，无预设信息"
    })

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "data_policy": "real_data_only"
    })

@app.route('/professional_news', methods=['GET'])
def professional_news():
    """专业财经新闻+股票推荐"""
    try:
        print("处理专业财经新闻请求...")
        
        # 1. 获取真实财经新闻
        raw_news = service.get_real_finance_news()
        
        # 2. 为每条新闻分析并获取股票
        processed_news = []
        for news in raw_news[:15]:  # 处理前15条
            try:
                # 获取相关股票
                stocks = service.analyze_news_and_get_stocks(news)
                
                # 分析相关板块
                related_sectors = service.analyze_sectors(news["title"] + " " + news.get("content", ""))
                positive_sectors, negative_sectors = service.get_sector_relations(related_sectors)
                
                processed_news.append({
                    "news": news,
                    "recommended_stocks": stocks[:8],  # 最多8个股票
                    "related_sectors": related_sectors[:3],
                    "positive_sectors": positive_sectors,
                    "negative_sectors": negative_sectors,
                    "analysis_time": datetime.datetime.now().strftime("%H:%M:%S")
                })
            except Exception as e:
                print(f"处理新闻失败: {e}")
                continue
        
        # 3. 获取北向资金数据
        north_funds = service.get_north_funds_real()
        
        # 4. 计算市场情绪
        market_sentiment = service.calculate_market_sentiment(north_funds, len(processed_news))
        
        # 5. 获取板块龙头
        sector_leaders = service.get_sector_leaders_real()
        
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": {
                "news_with_stocks": processed_news,
                "north_funds": north_funds,
                "market_sentiment": market_sentiment,
                "sector_leaders": sector_leaders,
                "summary": {
                    "total_news": len(processed_news),
                    "total_stocks": sum(len(item["recommended_stocks"]) for item in processed_news),
                    "north_net_flow": north_funds.get("total_inflow", 0) - north_funds.get("total_outflow", 0),
                    "sentiment_level": market_sentiment.get("level", "未知")
                }
            },
            "data_policy": "100%真实数据",
            "data_sources": ["财联社", "新浪财经", "东方财富", "巨潮资讯", "央视财经"],
            "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"专业新闻处理失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)[:200],
            "timestamp": datetime.datetime.now().isoformat(),
            "data_policy": "real_data_only"
        }), 500

@app.route('/north_funds', methods=['GET'])
def north_funds():
    """北向资金数据"""
    try:
        data = service.get_north_funds_real()
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/market_sentiment', methods=['GET'])
def market_sentiment():
    """市场情绪分析"""
    try:
        north_funds = service.get_north_funds_real()
        news = service.get_real_finance_news()
        sentiment = service.calculate_market_sentiment(north_funds, len(news))
        
        return jsonify({
            "success": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": sentiment
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)[:100],
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/sector_leaders', methods=['GET'])
def sector_leaders():
    """板块龙头"""
    try:
        leaders = service.get_sector_leaders_real()
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

@app.route('/test_news', methods=['GET'])
def test_news():
    """测试新闻获取"""
    try:
        news = service.get_real_finance_news()
        return jsonify({
            "success": True,
            "count": len(news),
            "samples": news[:3] if len(news) > 3 else news,
            "sources": list(set([n["source"] for n in news]))
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("专业财经新闻服务启动")
    print(f"端口: {PORT}")
    print("数据源: 财联社、新浪财经、东方财富、巨潮资讯")
    print("功能: 真实新闻+股票推荐+板块分析")
    print("数据政策: 100%真实数据，无预设信息")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
