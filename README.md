# 大乐透数据分析系统 (DLT Analyzer)

大乐透数据分析系统是一个用于中国超级大乐透彩票的历史数据分析、号码推荐和复盘查询的Web应用系统。

## 项目简介

本系统提供完整的大乐透历史数据管理、号码频率统计分析、智能推荐号码、抽奖验证等功能，帮助彩民更好地分析号码走势。

## 功能特性

### 📊 数据管理
- 自动抓取大乐透历史开奖数据
- 本地数据持久化存储
- 支持CSV/TXT格式导出

### 📈 统计分析
- 号码出现频率统计
- 可自定义分析期数范围（最近N期）
- 前区+后区综合分析

### 🎯 号码推荐
- **智能推荐**：基于历史频率分析的智能选号
- **随机推荐**：自定义范围的真随机号码生成

### 🔍 复盘验证
- 输入期号和选号进行复盘
- 自动计算命中情况
- 查看历史复盘记录

### 💰 奖项查询
- 中奖判断（支持任意选号对比）
- 奖项规则说明
- 开奖期号选择

## 技术栈

- **后端**: Python Flask + FastAPI
- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **数据存储**: JSON本地文件

## 目录结构

```
.
├── app.py                  # Flask Web应用入口
├── dlt_core.py             # 核心业务逻辑模块
├── dlt/                    # FastAPI版本后端
│   ├── app.py              # FastAPI应用
│   └── dlt_core.py         # 核心逻辑
├── templates/
│   └── index.html          # 前端页面
├── requirements.txt        # Python依赖
└── .dlt_data/              # 数据存储目录
    ├── history.json        # 历史开奖数据
    ├── raw_history.json    # 原始完整数据
    ├── predictions.json    # 推荐数据
    └── latest_stats.json   # 最新统计
```

## 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

**方式一：Flask版本**
```bash
python app.py
```

**方式二：FastAPI版本**
```bash
cd dlt
uvicorn app:app --reload --port 8000
```

访问 `http://localhost:5000` (Flask) 或 `http://localhost:8000` (FastAPI)

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/latest` | GET | 获取最新开奖信息 |
| `/api/history` | GET | 获取历史开奖列表 |
| `/api/history/raw` | GET | 获取完整原始数据 |
| `/api/stats` | GET/POST | 号码频率统计 |
| `/api/recommend` | GET/POST | 生成推荐号码 |
| `/api/review` | POST | 复盘验证 |
| `/api/prize-check` | POST | 中奖检查 |
| `/api/prize-rules` | GET | 奖项规则 |
| `/api/all-combos` | GET | 全部组合查询 |
| `/api/appeared-combos` | GET | 已出现组合 |
| `/api/random-unopened` | GET | 随机未开组合 |
| `/api/export/csv` | GET | 导出CSV |
| `/api/export/txt` | GET | 导出TXT |
| `/api/fetch` | POST | 抓取最新数据 |
| `/api/archive` | GET | 复盘历史记录 |

## 奖项规则

大乐透中奖规则：
- **一等奖**：前区5个+后区2个全中 (浮动奖金)
- **二等奖**：前区5个+后区中1个 (浮动奖金)
- **三等奖**：前区5个全中 (10000元)
- **四等奖**：前区4个+后区2个 (3000元)
- **五等奖**：前区4个+后区中1个 (300元)
- **六等奖**：前区4个全中 (200元)
- **七等奖**：前区3个+后区2个 (100元)
- **八等奖**：前区3个+后区中1个 (15元)
- **九等奖**：前区中3个 或 后区中2个 (5元)

## 使用说明

1. **首次使用**：点击"抓取数据"按钮获取最新开奖历史
2. **查看分析**：在"统计分析"标签页查看号码频率
3. **获取推荐**：在"号码推荐"标签页获取智能推荐号码
4. **复盘验证**：选择期号，输入选号进行复盘
5. **导出数据**：导出历史数据进行离线分析

##  License

本项目仅供学习和研究使用，请遵守相关法律法规。彩票投注有风险，请理性消费。