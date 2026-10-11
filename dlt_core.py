#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透核心业务逻辑模块
功能: 数据抓取、统计分析、推荐生成、开奖复盘
"""

import json
import math
import os
import random
import time
from datetime import datetime
from pathlib import Path
from collections import Counter
from itertools import combinations

try:
    import requests
except ImportError:
    requests = None

# ── 常量 ──────────────────────────────────────────────

FRONT_MIN, FRONT_MAX = 1, 35
FRONT_PICK = 5
BACK_MIN, BACK_MAX = 1, 12
BACK_PICK = 2

TOTAL_COMBOS = math.comb(35, 5) * math.comb(12, 2)
ANALYZE_WINDOW = 30
RECOMMEND_N = 5

DATA_DIR = Path(__file__).parent / ".dlt_data"
HIST_FILE = DATA_DIR / "history.json"
RAW_HIST_FILE = DATA_DIR / "raw_history.json"
STATS_FILE = DATA_DIR / "latest_stats.json"
ARCHIVE_FILE = DATA_DIR / "predictions.json"

EXPORT_FIELDS = [
    "期号", "开奖日期", "前区号码", "后区号码",
    "销售额", "奖池奖金",
    "一等奖注数", "一等奖地区", "二等奖注数", "三等奖注数"
]

NO_PROXY = {"http": "", "https": ""}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/147.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://static.sporttery.cn/",
}

# ── 本地 txt 文件路径（同级目录）──────────────────────
SCRIPT_DIR = Path(__file__).parent
DLT_LIST_FILE = SCRIPT_DIR / "dlt_list.txt"

WEEKDAY_MAP = {
    0: "星期一", 1: "星期二", 2: "星期三", 3: "星期四",
    4: "星期五", 5: "星期六", 6: "星期日",
}

LOCAL_FILE_HEADER = "期号,开奖日期,星期,前区号码,后区号码"


# ── 奖级判定 ──────────────────────────────────────────

def judge_prize(hit_front, hit_back):
    """根据前区命中数和后区命中数判定奖级"""
    if hit_front == 5 and hit_back == 2:
        return "一等奖"
    if hit_front == 5 and hit_back == 1:
        return "二等奖"
    if hit_front == 5 and hit_back == 0:
        return "三等奖"
    if hit_front == 4 and hit_back == 2:
        return "四等奖"
    if hit_front == 4 and hit_back == 1:
        return "五等奖"
    if hit_front == 3 and hit_back == 2:
        return "六等奖"
    if hit_front == 4 and hit_back == 0:
        return "七等奖"
    if (hit_front == 3 and hit_back == 1) or (hit_front == 2 and hit_back == 2):
        return "八等奖"
    if (hit_front == 3 and hit_back == 0) or (hit_front == 1 and hit_back == 2) or (hit_front == 0 and hit_back == 2):
        return "九等奖"
    return "未中奖"


# ── 本地 txt 文件操作 ─────────────────────────────────

def get_weekday_cn(date_str):
    """从日期字符串 (YYYY-MM-DD) 获取中文星期"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return WEEKDAY_MAP[dt.weekday()]
    except Exception:
        return ""


def load_local_history():
    """从同级目录下的 dlt_list.txt 加载历史数据，返回新到旧的列表"""
    if not DLT_LIST_FILE.exists():
        return []

    records = []
    lines = DLT_LIST_FILE.read_text(encoding="utf-8-sig").strip().split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("期号"):
            continue
        parts = line.split(",")
        if len(parts) >= 5:
            try:
                records.append({
                    "period": parts[0],
                    "draw_date": parts[1],
                    "weekday": parts[2],
                    "front": [int(x) for x in parts[3].split()],
                    "back": [int(x) for x in parts[4].split()],
                })
            except (ValueError, IndexError):
                continue

    records.sort(key=lambda x: x["period"], reverse=True)
    return records


def save_local_history(records):
    """
    保存历史数据到本地 txt 文件。
    流程: 写入 dlt_list_YYYYMMDD.txt → 删除旧 dlt_list.txt → 重命名
    """
    sorted_records = sorted(records, key=lambda x: x["period"])

    timestamp = datetime.now().strftime("%Y%m%d")
    temp_file = SCRIPT_DIR / f"dlt_list_{timestamp}.txt"

    lines = [LOCAL_FILE_HEADER]
    for r in sorted_records:
        front_str = " ".join(f"{n:02d}" for n in r["front"])
        back_str = " ".join(f"{n:02d}" for n in r["back"])
        weekday = r.get("weekday", "")
        if not weekday and r.get("draw_date"):
            weekday = get_weekday_cn(r["draw_date"])
        lines.append(f"{r['period']},{r.get('draw_date','')},{weekday},{front_str},{back_str}")

    temp_file.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    if DLT_LIST_FILE.exists():
        DLT_LIST_FILE.unlink()

    temp_file.rename(DLT_LIST_FILE)
    return True


def create_mock_data():
    """创建虚拟测试数据（大乐透每周一三五日开奖）"""
    mock = [
        ("25001", "2025-01-01", [1, 5, 12, 18, 25], [3, 8]),
        ("25002", "2025-01-04", [2, 7, 14, 21, 30], [5, 11]),
        ("25003", "2025-01-06", [3, 9, 15, 22, 31], [1, 9]),
        ("25004", "2025-01-08", [4, 10, 17, 24, 33], [2, 7]),
        ("25005", "2025-01-11", [6, 11, 19, 26, 35], [4, 10]),
        ("25006", "2025-01-13", [8, 13, 20, 27, 28], [6, 12]),
        ("25007", "2025-01-15", [1, 8, 16, 23, 32], [3, 9]),
        ("25008", "2025-01-18", [5, 10, 18, 25, 34], [5, 8]),
        ("25009", "2025-01-20", [2, 9, 17, 24, 29], [1, 11]),
        ("25010", "2025-01-22", [3, 7, 14, 21, 30], [4, 7]),
    ]
    records = []
    for period, date, front, back in mock:
        records.append({
            "period": period,
            "draw_date": date,
            "weekday": get_weekday_cn(date),
            "front": front,
            "back": back,
        })
    return records


def get_local_history_data():
    """从本地 txt 加载历史数据，文件不存在则创建虚拟数据"""
    records = load_local_history()
    if not records:
        records = create_mock_data()
        save_local_history(records)
        records = load_local_history()
    return records


def get_latest_from_local():
    """从本地 txt 文件获取最新一期"""
    records = get_local_history_data()
    if not records:
        return {"error": "无历史数据"}
    return records[0]


# ── 数据加载/保存 ─────────────────────────────────────

def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_history():
    if HIST_FILE.exists():
        return json.loads(HIST_FILE.read_text(encoding="utf-8"))
    return []


def save_history(data):
    _ensure_data_dir()
    HIST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_raw():
    if RAW_HIST_FILE.exists():
        return json.loads(RAW_HIST_FILE.read_text(encoding="utf-8"))
    return []


def save_raw(data):
    _ensure_data_dir()
    RAW_HIST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_archive():
    if ARCHIVE_FILE.exists():
        return json.loads(ARCHIVE_FILE.read_text(encoding="utf-8"))
    return []


def save_archive(data):
    _ensure_data_dir()
    ARCHIVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_stats():
    if STATS_FILE.exists():
        return json.loads(STATS_FILE.read_text(encoding="utf-8"))
    return None


def save_stats(data):
    _ensure_data_dir()
    STATS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 数据抓取 ──────────────────────────────────────────

def fetch_from_sporttery_all(timeout=20, max_pages=None):
    """
    从体彩官网 API 分页抓取全部历史数据（含奖金信息）
    返回所有记录列表
    """
    if requests is None:
        raise RuntimeError("缺少 requests 库，请运行: pip install requests")

    url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
    all_records = []
    page_no = 1
    page_size = 100

    while True:
        params = {
            "gameNo": "85",
            "provinceId": "0",
            "pageSize": str(page_size),
            "isVerify": "1",
            "pageNo": str(page_no),
        }
        try:
            resp = requests.get(url, params=params, headers=HEADERS,
                                timeout=timeout, proxies=NO_PROXY)
            data = resp.json()
            if data.get("errorCode") != "0":
                raise Exception(data.get("errorMsg", "API 返回异常"))

            items = data.get("value", {}).get("list", [])
            if not items:
                break

            for item in items:
                period = item.get("lotteryDrawNum", "")
                result_str = item.get("lotteryDrawResult", "")
                nums = [int(x) for x in result_str.split() if x.isdigit()]
                if len(nums) != 7:
                    continue

                prize_list = item.get("prizeLevelList", [])
                first_count = first_area = second_count = third_count = ""
                for p in prize_list:
                    level = p.get("prizeLevel", "")
                    if "一等奖" in level:
                        first_count = p.get("winningNumber", "")
                        area = p.get("winningArea", "")
                        first_area = ",".join(area) if isinstance(area, list) else str(area)
                    elif "二等奖" in level:
                        second_count = p.get("winningNumber", "")
                    elif "三等奖" in level:
                        third_count = p.get("winningNumber", "")

                all_records.append({
                    "period": period,
                    "draw_time": item.get("lotteryDrawTime", ""),
                    "front": sorted(nums[:5]),
                    "back": sorted(nums[5:]),
                    "sales": item.get("sales", ""),
                    "prize_pool": item.get("prizePool", ""),
                    "first_win_count": first_count,
                    "first_area": first_area,
                    "second_win_count": second_count,
                    "third_win_count": third_count,
                })

            print(f"  已抓取第 {page_no} 页，共 {len(items)} 条，累计 {len(all_records)} 条")

            if len(items) < page_size:
                break
            if max_pages and page_no >= max_pages:
                break
            page_no += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"  第 {page_no} 页抓取失败: {e}")
            break

    return all_records


def do_fetch(max_pages=None):
    """
    执行数据抓取并保存。
    返回 dict: {success, total, new_count, latest}
    """
    records = fetch_from_sporttery_all(timeout=100, max_pages=max_pages)
    if not records:
        return {"success": False, "error": "网络请求失败或 API 返回异常"}

    # 精简版
    existing = load_history()
    exist_set = {r["period"] for r in existing}
    new_n = 0
    for r in records:
        simple = {"period": r["period"], "front": r["front"], "back": r["back"]}
        if r["period"] not in exist_set:
            existing.append(simple)
            new_n += 1
    existing.sort(key=lambda x: x["period"], reverse=True)
    save_history(existing)

    # 完整版
    raw_existing = load_raw()
    raw_set = {r["period"] for r in raw_existing}
    new_raw = 0
    for r in records:
        if r["period"] not in raw_set:
            raw_existing.append(r)
            new_raw += 1
    raw_existing.sort(key=lambda x: x["period"], reverse=True)
    save_raw(raw_existing)

    latest = existing[0] if existing else None

    # 自动复盘
    if new_n > 0 and len(existing) > 1:
        _auto_review(latest)

    # 保存到本地 txt 文件
    try:
        local_records = []
        for r in raw_existing:
            draw_date = r.get("draw_time", "").split()[0] if r.get("draw_time") else ""
            weekday = get_weekday_cn(draw_date)
            local_records.append({
                "period": r["period"],
                "draw_date": draw_date,
                "weekday": weekday,
                "front": r["front"],
                "back": r["back"],
            })
        save_local_history(local_records)
        print(f"  本地文件已更新，共 {len(local_records)} 期")

        # 更新已开奖组合
        try:
            update_appeared_combos(local_records)
            print(f"  已开奖组合已更新")
        except Exception as e:
            print(f"  更新已开奖组合失败: {e}")
    except Exception as e:
        print(f"  保存本地文件失败: {e}")

    return {
        "success": True,
        "total": len(existing),
        "new_count": new_n,
        "latest": latest,
    }


# ── 统计分析 ──────────────────────────────────────────

def compute_stats(history=None, window=ANALYZE_WINDOW, start_date=None, end_date=None):
    """
    对指定范围的数据进行统计分析。
    - window: 取最近 N 期（仅当无日期筛选时生效）
    - start_date/end_date: 日期范围筛选 (YYYY-MM-DD)
    返回统计结果 dict。
    """
    if history is None:
        history = load_history()

    if not history:
        history = get_local_history_data()

    if not history:
        return {"error": "无历史数据"}

    # 按日期范围筛选
    date_filtered = False
    if start_date or end_date:
        date_filtered = True
        filtered = []
        for r in history:
            d = r.get("draw_date", "")
            if start_date and d < start_date:
                continue
            if end_date and d > end_date:
                continue
            filtered.append(r)
        recent = filtered
    else:
        recent = history[:window]

    recent.reverse()  # 按时间正序排列

    # 前区号码频率
    front_counter = Counter()
    back_counter = Counter()
    front_odd_count = []
    front_sum_list = []
    front_span_list = []
    back_sum_list = []
    consecutive_count = 0

    for draw in recent:
        front = draw["front"]
        back = draw["back"]
        front_counter.update(front)
        back_counter.update(back)

        odds = sum(1 for n in front if n % 2 == 1)
        front_odd_count.append(odds)
        front_sum_list.append(sum(front))
        front_span_list.append(max(front) - min(front))
        back_sum_list.append(sum(back))

        # 检查前区连号
        sorted_front = sorted(front)
        for i in range(len(sorted_front) - 1):
            if sorted_front[i + 1] - sorted_front[i] == 1:
                consecutive_count += 1
                break

    # 前区频率详情
    front_freq = []
    for num in range(FRONT_MIN, FRONT_MAX + 1):
        count = front_counter.get(num, 0)
        front_freq.append({"number": num, "count": count})

    # 后区频率详情
    back_freq = []
    for num in range(BACK_MIN, BACK_MAX + 1):
        count = back_counter.get(num, 0)
        back_freq.append({"number": num, "count": count})

    # 热号（出现次数最多）
    front_hot = front_counter.most_common(8)
    back_hot = back_counter.most_common(5)

    # 冷号（出现次数最少，包括 0 次）
    front_cold = sorted(
        [(num, front_counter.get(num, 0)) for num in range(FRONT_MIN, FRONT_MAX + 1)],
        key=lambda x: x[1]
    )[:8]
    back_cold = sorted(
        [(num, back_counter.get(num, 0)) for num in range(BACK_MIN, BACK_MAX + 1)],
        key=lambda x: x[1]
    )[:5]

    # 奇偶比统计
    odd_even_dist = Counter(front_odd_count)

    # 和值统计
    front_sum_avg = sum(front_sum_list) / len(front_sum_list) if front_sum_list else 0
    back_sum_avg = sum(back_sum_list) / len(back_sum_list) if back_sum_list else 0

    # 跨度统计
    front_span_avg = sum(front_span_list) / len(front_span_list) if front_span_list else 0

    # 连号出现概率
    consecutive_ratio = consecutive_count / len(recent) if recent else 0

    # 大小比（前区以18为界，1-17为小，18-35为大）
    big_small_dist = []
    for draw in recent:
        front = draw["front"]
        big = sum(1 for n in front if n >= 18)
        big_small_dist.append(big)

    stats = {
        "window": len(recent),
        "total_history": len(history),
        "date_filtered": date_filtered,
        "start_date": start_date or "",
        "end_date": end_date or "",
        "latest_period": recent[-1]["period"] if recent else "",
        "earliest_period": recent[0]["period"] if recent else "",
        "front_freq": front_freq,
        "back_freq": back_freq,
        "front_hot": [{"number": n, "count": c} for n, c in front_hot],
        "back_hot": [{"number": n, "count": c} for n, c in back_hot],
        "front_cold": [{"number": n, "count": c} for n, c in front_cold],
        "back_cold": [{"number": n, "count": c} for n, c in back_cold],
        "odd_even_dist": {str(k): v for k, v in sorted(odd_even_dist.items())},
        "front_sum_avg": round(front_sum_avg, 1),
        "back_sum_avg": round(back_sum_avg, 1),
        "front_span_avg": round(front_span_avg, 1),
        "consecutive_ratio": round(consecutive_ratio, 2),
        "big_small_dist": {str(k): v for k, v in sorted(Counter(big_small_dist).items())},
        "computed_at": datetime.now().isoformat(),
    }

    save_stats(stats)
    return stats


def do_analyze(window=ANALYZE_WINDOW, start_date=None, end_date=None):
    """执行分析，返回统计结果"""
    return compute_stats(window=window, start_date=start_date, end_date=end_date)


# ── 推荐生成 ──────────────────────────────────────────

def _weighted_pick(candidates, weights, n):
    """带权随机选择 n 个不重复的数"""
    selected = []
    pool = list(zip(candidates, weights))
    for _ in range(n):
        if not pool:
            break
        total = sum(w for _, w in pool)
        if total <= 0:
            # 全部权重为 0 时均匀随机
            pick = random.choice(pool)
        else:
            r = random.uniform(0, total)
            acc = 0
            pick = pool[-1]
            for item, w in pool:
                acc += w
                if r <= acc:
                    pick = (item, w)
                    break
        selected.append(pick[0])
        pool.remove(pick)
    return sorted(selected)


def generate_recommendations(stats=None, n=RECOMMEND_N):
    """
    基于统计分析生成 n 组推荐号码。
    策略: 热号为主 + 冷号回补 + 随机扰动
    """
    if stats is None:
        stats = load_stats()
    if not stats:
        history = load_history()
        if not history:
            history = get_local_history_data()
        if not history:
            return {"error": "无历史数据，请先抓取数据"}
        stats = compute_stats(history)
        if "error" in stats:
            return stats

    recommendations = []
    front_hot_nums = [item["number"] for item in stats.get("front_hot", [])]
    front_cold_nums = [item["number"] for item in stats.get("front_cold", [])]
    back_hot_nums = [item["number"] for item in stats.get("back_hot", [])]
    back_cold_nums = [item["number"] for item in stats.get("back_cold", [])]

    all_front = list(range(FRONT_MIN, FRONT_MAX + 1))
    all_back = list(range(BACK_MIN, BACK_MAX + 1))

    # 加载历史数据用于匹配检查
    history = load_history()
    if not history:
        history = get_local_history_data()

    for i in range(n):
        # 前区: 3热号 + 1冷号 + 1随机
        front_picks = set()

        # 从热号中选 2-3 个
        hot_pool = [n for n in front_hot_nums if n not in front_picks]
        hot_count = min(random.choice([2, 3]), len(hot_pool))
        if hot_pool:
            chosen = random.sample(hot_pool, hot_count)
            front_picks.update(chosen)

        # 从冷号中选 1-2 个
        cold_pool = [n for n in front_cold_nums if n not in front_picks]
        cold_count = min(random.choice([1, 2]), len(cold_pool))
        if cold_pool:
            chosen = random.sample(cold_pool, cold_count)
            front_picks.update(chosen)

        # 补齐剩余
        remaining = [n for n in all_front if n not in front_picks]
        while len(front_picks) < FRONT_PICK:
            front_picks.add(random.choice(remaining))

        # 后区: 1热号 + 1冷号/随机
        back_picks = set()
        if back_hot_nums:
            back_picks.add(random.choice(back_hot_nums))
        back_remaining = [n for n in all_back if n not in back_picks]
        if back_cold_nums:
            cold_back = [n for n in back_cold_nums if n not in back_picks]
            if cold_back:
                back_picks.add(random.choice(cold_back))
        while len(back_picks) < BACK_PICK:
            back_picks.add(random.choice(back_remaining))

        front_sorted = sorted(front_picks)
        back_sorted = sorted(back_picks)

        # 计算推荐特征
        odd_count = sum(1 for n in front_sorted if n % 2 == 1)
        big_count = sum(1 for n in front_sorted if n >= 18)
        front_sum = sum(front_sorted)

        # 检查历史匹配
        front_set = set(front_sorted)
        back_set = set(back_sorted)
        matched_periods = []
        for rec in history:
            rec_front_set = set(rec.get("front", []))
            rec_back_set = set(rec.get("back", []))
            if front_set == rec_front_set and back_set == rec_back_set:
                matched_periods.append(rec.get("period", ""))

        recommendations.append({
            "idx": i + 1,
            "front": front_sorted,
            "back": back_sorted,
            "odd_count": odd_count,
            "even_count": FRONT_PICK - odd_count,
            "big_count": big_count,
            "small_count": FRONT_PICK - big_count,
            "sum": front_sum,
            "span": max(front_sorted) - min(front_sorted),
            "history_match": matched_periods,
        })

    archive_entry = {
        "generated_at": datetime.now().isoformat(),
        "predictions": recommendations,
        "review": None,
        "actual": None,
    }

    arch = load_archive()
    arch.append(archive_entry)
    save_archive(arch)

    return {
        "recommendations": recommendations,
        "generated_at": archive_entry["generated_at"],
        "stats_ref": stats.get("computed_at"),
    }


def do_recommend(n=RECOMMEND_N):
    """生成推荐"""
    result = generate_recommendations(n=n)
    if isinstance(result, dict) and "recommendations" in result:
        result["logic"] = get_recommendation_logic()
    return result


# ── 开奖复盘 ──────────────────────────────────────────

def do_review(period):
    """
    复盘: 根据期号从历史数据查找实际开奖号码，对比最近一组推荐。
    """
    # 从历史数据查找该期开奖号码
    history = load_history()
    if not history:
        history = get_local_history_data()

    actual = None
    for r in history:
        if r.get("period") == period:
            actual = r
            break

    if not actual:
        return {"error": "未找到该期号的历史数据"}

    actual_front = actual.get("front", [])
    actual_back = actual.get("back", [])

    if len(actual_front) != FRONT_PICK or len(actual_back) != BACK_PICK:
        return {"error": f"前区需 {FRONT_PICK} 个号码，后区需 {BACK_PICK} 个号码"}

    arch = load_archive()
    if not arch:
        return {"error": "无推荐记录，请先生成推荐"}

    target = None
    for entry in reversed(arch):
        if entry.get("review") is None and entry.get("actual") is None:
            target = entry
            break

    if not target:
        return {"error": "没有未复盘的推荐记录"}

    act_front_set = set(actual_front)
    act_back_set = set(actual_back)

    results = []
    for p in target["predictions"]:
        hf = len(set(p["front"]) & act_front_set)
        hb = len(set(p["back"]) & act_back_set)
        pz = judge_prize(hf, hb)
        results.append({
            "idx": p["idx"],
            "front": p["front"],
            "back": p["back"],
            "hit_front": hf,
            "hit_back": hb,
            "prize": pz,
        })

    target["actual"] = {
        "period": period,
        "front": sorted(actual_front),
        "back": sorted(actual_back),
    }
    target["review"] = results
    save_archive(arch)

    return {
        "period": period,
        "actual_front": sorted(actual_front),
        "actual_back": sorted(actual_back),
        "recommendations": target["predictions"],
        "results": results,
    }


def _auto_review(latest_draw):
    """自动复盘最新一期"""
    arch = load_archive()
    if not arch:
        return

    period = latest_draw["period"]
    act_front = latest_draw["front"]
    act_back = latest_draw["back"]

    target = None
    for entry in reversed(arch):
        if entry.get("review") is None and entry.get("actual") is None:
            target = entry
            break
    if not target:
        return

    results = []
    for p in target["predictions"]:
        hf = len(set(p["front"]) & set(act_front))
        hb = len(set(p["back"]) & set(act_back))
        pz = judge_prize(hf, hb)
        results.append({
            "idx": p["idx"],
            "front": p["front"],
            "back": p["back"],
            "hit_front": hf,
            "hit_back": hb,
            "prize": pz,
        })

    target["actual"] = {"period": period, "front": act_front, "back": act_back}
    target["review"] = results
    save_archive(arch)


def get_archive():
    """获取所有推荐及复盘记录"""
    return load_archive()


# ── 开奖兑奖 ──────────────────────────────────────────

PRIZE_INFO = {
    "一等奖": {"amount": "浮动（最高1000万）", "fixed": False, "hit": (5, 2)},
    "二等奖": {"amount": "浮动（约几十万到百万）", "fixed": False, "hit": (5, 1)},
    "三等奖": {"amount": "10,000 元", "fixed": True, "hit": (5, 0)},
    "四等奖": {"amount": "3,000 元", "fixed": True, "hit": (4, 2)},
    "五等奖": {"amount": "300 元", "fixed": True, "hit": (4, 1)},
    "六等奖": {"amount": "200 元", "fixed": True, "hit": (3, 2)},
    "七等奖": {"amount": "100 元", "fixed": True, "hit": (4, 0)},
    "八等奖": {"amount": "15 元", "fixed": True, "hit": None},
    "九等奖": {"amount": "5 元", "fixed": True, "hit": None},
}

BET_PRICE = 2  # 每注2元


def do_prize_check(period, user_front, user_back):
    """
    开奖兑奖: 根据期号查找实际开奖号码，与用户选号对比。
    支持复式投注（前区选超过5个或后区选超过2个）。
    """
    history = load_history()
    if not history:
        history = get_local_history_data()

    actual = None
    for r in history:
        if r.get("period") == period:
            actual = r
            break

    if not actual:
        return {"error": "未找到该期号的历史数据"}

    actual_front = set(actual.get("front", []))
    actual_back = set(actual.get("back", []))

    user_front_set = set(user_front)
    user_back_set = set(user_back)

    is_front_multi = len(user_front) > FRONT_PICK
    is_back_multi = len(user_back) > BACK_PICK
    is_multi = is_front_multi or is_back_multi

    # 计算注数
    from itertools import combinations
    front_combos = list(combinations(sorted(user_front), FRONT_PICK))
    back_combos = list(combinations(sorted(user_back), BACK_PICK))
    total_bets = len(front_combos) * len(back_combos)
    total_cost = total_bets * BET_PRICE

    # 遍历所有组合，统计中奖
    prize_summary = {}
    total_prize = 0
    all_results = []

    for fc in front_combos:
        for bc in back_combos:
            hf = len(set(fc) & actual_front)
            hb = len(set(bc) & actual_back)
            pz = judge_prize(hf, hb)
            if pz != "未中奖":
                if pz not in prize_summary:
                    prize_summary[pz] = {"count": 0, "amount_text": PRIZE_INFO[pz]["amount"]}
                prize_summary[pz]["count"] += 1
                if PRIZE_INFO[pz]["fixed"]:
                    fixed_amount = int(PRIZE_INFO[pz]["amount"].replace(",", "").replace(" 元", ""))
                    total_prize += fixed_amount
                all_results.append({
                    "front": sorted(fc),
                    "back": sorted(bc),
                    "hit_front": hf,
                    "hit_back": hb,
                    "prize": pz,
                })

    hit_front_count = len(user_front_set & actual_front)
    hit_back_count = len(user_back_set & actual_back)

    return {
        "period": period,
        "actual_front": sorted(actual_front),
        "actual_back": sorted(actual_back),
        "user_front": sorted(user_front),
        "user_back": sorted(user_back),
        "is_multi": is_multi,
        "total_bets": total_bets,
        "total_cost": total_cost,
        "hit_front": hit_front_count,
        "hit_back": hit_back_count,
        "prize_summary": prize_summary,
        "total_prize": total_prize,
        "all_results": all_results,
        "net_profit": total_prize - total_cost,
    }


def get_prize_rules():
    """返回大乐透玩法规则信息"""
    return {
        "game_name": "中国体育彩票超级大乐透",
        "rules": [
            {"section": "玩法说明", "content": "前区从01-35中选5个号码，后区从01-12中选2个号码，组成一注。"},
            {"section": "投注方式", "content": "单式投注：前区选5个+后区选2个；复式投注：前区选超过5个或后区选超过2个，系统自动组合；胆拖投注：前区胆码必选+拖码补充。"},
            {"section": "投注金额", "content": "每注2元。可追加投注（额外1元），追加后一等奖/二等奖奖金翻倍。"},
            {"section": "开奖时间", "content": "每周一、三、六开奖。"},
        ],
        "prize_levels": [
            {"level": "一等奖", "condition": "前5+后2", "amount": "浮动（最高1000万，追加1500万）"},
            {"level": "二等奖", "condition": "前5+后1", "amount": "浮动（追加翻倍）"},
            {"level": "三等奖", "condition": "前5+后0", "amount": "10,000 元"},
            {"level": "四等奖", "condition": "前4+后2", "amount": "3,000 元"},
            {"level": "五等奖", "condition": "前4+后1", "amount": "300 元"},
            {"level": "六等奖", "condition": "前3+后2", "amount": "200 元"},
            {"level": "七等奖", "condition": "前4+后0", "amount": "100 元"},
            {"level": "八等奖", "condition": "前3+后1 或 前2+后2", "amount": "15 元"},
            {"level": "九等奖", "condition": "前3+后0 或 前1+后2 或 前2+后1 或 前0+后2", "amount": "5 元"},
        ],
    }


# ── 已开奖组合管理 ────────────────────────────────────

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPEARED_FILE = os.path.join(_BASE_DIR, 'dlt_appeared.txt')

_ALL_FRONT_COMBOS = None
_ALL_BACK_COMBOS = None


def _get_all_combos_cache():
    """缓存所有前区/后区组合"""
    global _ALL_FRONT_COMBOS, _ALL_BACK_COMBOS
    if _ALL_FRONT_COMBOS is None:
        _ALL_FRONT_COMBOS = list(combinations(range(1, 36), 5))
        _ALL_BACK_COMBOS = list(combinations(range(1, 13), 2))
    return _ALL_FRONT_COMBOS, _ALL_BACK_COMBOS


def _combo_key(front, back):
    """生成组合的唯一标识"""
    return tuple(sorted(front) + sorted(back))


def load_appeared_combos():
    """从 txt 加载已开奖组合"""
    combos = {}
    if not os.path.exists(APPEARED_FILE):
        return combos
    with open(APPEARED_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 7:
                try:
                    front = [int(x) for x in parts[:5]]
                    back = [int(x) for x in parts[5:7]]
                except ValueError:
                    continue
                key = _combo_key(front, back)
                if len(parts) >= 10 and parts[7] == '1':
                    date_compact = parts[9] if len(parts) > 9 else ''
                    date_display = date_compact
                    if len(date_compact) == 8:
                        date_display = f'{date_compact[:4]}-{date_compact[4:6]}-{date_compact[6:]}'
                    combos[key] = {
                        'period': parts[8] if len(parts) > 8 else '',
                        'date': date_display,
                        'date_compact': date_compact,
                        'weekday': parts[10] if len(parts) > 10 else ''
                    }
    return combos


def update_appeared_combos(history):
    """根据历史数据更新已开奖组合 txt"""
    existing = load_appeared_combos()
    changed = False

    for r in history:
        front = sorted(r.get('front', []))
        back = sorted(r.get('back', []))
        if len(front) < FRONT_PICK or len(back) < BACK_PICK:
            continue
        key = _combo_key(front, back)

        if key not in existing:
            draw_date = r.get('draw_date', '')
            date_compact = draw_date.replace('-', '') if draw_date else ''
            weekday = r.get('weekday', '')
            if not weekday and draw_date:
                weekday = get_weekday_cn(draw_date)
            existing[key] = {
                'period': str(r.get('period', '')),
                'date_compact': date_compact,
                'weekday': weekday
            }
            changed = True

    if changed:
        with open(APPEARED_FILE, 'w', encoding='utf-8') as f:
            for key, info in existing.items():
                nums = list(key)
                f.write(','.join(str(n) for n in nums[:5]) + ',' +
                        ','.join(str(n) for n in nums[5:7]) + ',1,' +
                        info['period'] + ',' + info['date_compact'] + ',' + info['weekday'] + '\n')

    return existing


def get_all_combos(page=1, page_size=20, filter_type='all'):
    """分页获取所有组合"""
    appeared = load_appeared_combos()
    all_front, all_back = _get_all_combos_cache()
    total_back = len(all_back)

    if filter_type == 'appeared':
        items = []
        for key, info in sorted(appeared.items()):
            front = list(key[:5])
            back = list(key[5:7])
            items.append({
                'front': front, 'back': back,
                'appeared': True,
                'period': info.get('period', ''),
                'date': info.get('date', ''),
                'weekday': info.get('weekday', '')
            })
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {'data': items[start:end], 'page': page, 'page_size': page_size,
                'total': total, 'total_pages': (total + page_size - 1) // page_size}
    else:
        total = len(all_front) * total_back
        start = (page - 1) * page_size
        end = min(start + page_size, total)

        items = []
        for i in range(start, end):
            fi = i // total_back
            bi = i % total_back
            front = list(all_front[fi])
            back = list(all_back[bi])
            key = _combo_key(front, back)
            info = appeared.get(key)
            items.append({
                'front': front, 'back': back,
                'appeared': info is not None,
                'period': info['period'] if info else '',
                'date': info['date'] if info else '',
                'weekday': info['weekday'] if info else ''
            })

        return {'data': items, 'page': page, 'page_size': page_size,
                'total': total, 'total_pages': (total + page_size - 1) // page_size}


def get_appeared_combos_list():
    """获取已开奖组合列表"""
    appeared = load_appeared_combos()
    items = []
    for key, info in sorted(appeared.items()):
        items.append({
            'front': list(key[:5]),
            'back': list(key[5:7]),
            'key': ','.join(str(n) for n in key),
            'period': info.get('period', ''),
            'date': info.get('date', ''),
            'weekday': info.get('weekday', '')
        })
    return {'total': len(items), 'data': items}


def get_random_unopened(n=5, front_min=1, front_max=35, back_min=1, back_max=12):
    """从未开奖组合中随机选取 n 注"""
    appeared = load_appeared_combos()
    front_pool = list(range(front_min, front_max + 1))
    back_pool = list(range(back_min, back_max + 1))

    if len(front_pool) < FRONT_PICK:
        return {'error': '前区范围至少需要5个号码'}
    if len(back_pool) < BACK_PICK:
        return {'error': '后区范围至少需要2个号码'}

    results = []
    seen = set()
    attempts = 0
    max_attempts = n * 200

    while len(results) < n and attempts < max_attempts:
        front = sorted(random.sample(front_pool, FRONT_PICK))
        back = sorted(random.sample(back_pool, BACK_PICK))
        key = _combo_key(front, back)
        if key not in appeared and key not in seen:
            seen.add(key)
            results.append({'front': front, 'back': back, 'key': ','.join(str(n) for n in key)})
        attempts += 1

    return {'data': results, 'found': len(results)}


def get_total_combo_count():
    """返回总组合数"""
    return {'total': math.comb(35, 5) * math.comb(12, 2),
            'front_combos': math.comb(35, 5),
            'back_combos': math.comb(12, 2)}


def get_recommendation_logic():
    """返回推荐逻辑说明"""
    return (
        '推荐逻辑：基于最近30期历史数据统计分析，'
        '从热号（出现频率最高）中随机选取2-3个作为前区主号，'
        '从冷号（出现频率最低）中随机选取1-2个进行回补，'
        '剩余1个从前区全量号码中随机补充；'
        '后区从热号中选1个，从冷号或全量中选1个。'
        '每组推荐均检查是否在历史开奖中出现过。'
        '该推荐仅供参考，彩票具有随机性，请理性投注。'
    )


# ── 历史数据查询 ──────────────────────────────────────

def get_history(limit=50, offset=0):
    """获取历史开奖数据"""
    history = load_history()
    total = len(history)
    if limit > 0:
        page = history[offset:offset + limit]
    else:
        page = history[offset:]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": page,
    }


def get_raw_history(limit=50, offset=0):
    """获取完整历史数据（含奖金信息）"""
    raw = load_raw()
    total = len(raw)
    if limit > 0:
        page = raw[offset:offset + limit]
    else:
        page = raw[offset:]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": page,
    }


def get_latest():
    """获取最新一期"""
    history = load_history()
    if not history:
        return {"error": "无历史数据"}
    return history[0]


# ── 导出 ──────────────────────────────────────────────

def export_csv_text():
    """
    导出历史数据为 CSV 和 TXT 格式的字符串。
    返回 dict: {csv: str, txt: str, count: int}
    """
    import csv
    import io

    raw = load_raw()
    if not raw:
        return {"error": "无完整原始数据，请先抓取数据"}

    raw_sorted = sorted(raw, key=lambda x: x["period"])

    rows = []
    for r in raw_sorted:
        front_str = " ".join(f"{n:02d}" for n in r["front"])
        back_str = " ".join(f"{n:02d}" for n in r["back"])
        draw_date = r.get("draw_time", "").split()[0] if r.get("draw_time") else ""
        rows.append({
            "期号": r["period"],
            "开奖日期": draw_date,
            "前区号码": front_str,
            "后区号码": back_str,
            "销售额": r.get("sales", ""),
            "奖池奖金": r.get("prize_pool", ""),
            "一等奖注数": r.get("first_win_count", ""),
            "一等奖地区": r.get("first_area", ""),
            "二等奖注数": r.get("second_win_count", ""),
            "三等奖注数": r.get("third_win_count", ""),
        })

    # CSV
    csv_buf = io.StringIO()
    writer = csv.DictWriter(csv_buf, fieldnames=EXPORT_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    csv_str = csv_buf.getvalue()

    # TXT
    txt_lines = [",".join(EXPORT_FIELDS)]
    for row in rows:
        txt_lines.append(",".join(str(row.get(k, "")) for k in EXPORT_FIELDS))
    txt_str = "\n".join(txt_lines)

    return {
        "csv": csv_str,
        "txt": txt_str,
        "count": len(rows),
    }
