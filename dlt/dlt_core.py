# dlt_core.py
import json
import math
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

FRONT_MIN, FRONT_MAX = 1, 35
FRONT_PICK = 5
BACK_MIN, BACK_MAX = 1, 12
BACK_PICK = 2

DATA_DIR = Path("data")
HIST_FILE = DATA_DIR / "history.json"
RAW_HIST_FILE = DATA_DIR / "raw_history.json"
ARCHIVE_FILE = DATA_DIR / "archive.json"

DATA_DIR.mkdir(exist_ok=True)

# ---------- 数据存储 ----------
def _load_json(path: Path) -> list:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []

def _save_json(path: Path, data: list):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_history() -> list:
    return _load_json(HIST_FILE)

def save_history(data: list):
    _save_json(HIST_FILE, data)

def load_raw() -> list:
    return _load_json(RAW_HIST_FILE)

def save_raw(data: list):
    _save_json(RAW_HIST_FILE, data)

def load_archive() -> list:
    return _load_json(ARCHIVE_FILE)

def save_archive(data: list):
    _save_json(ARCHIVE_FILE, data)

# ---------- 工具函数 ----------
def sort_nums(nums):
    return sorted(nums)

def fmt_num(n):
    return str(n).zfill(2)

def prize_level(hit_front, hit_back):
    if hit_front == 5 and hit_back == 2: return "一等奖"
    if hit_front == 5 and hit_back == 1: return "二等奖"
    if hit_front == 5 and hit_back == 0: return "三等奖"
    if hit_front == 4 and hit_back == 2: return "四等奖"
    if hit_front == 4 and hit_back == 1: return "五等奖"
    if hit_front == 3 and hit_back == 2: return "六等奖"
    if hit_front == 4 and hit_back == 0: return "七等奖"
    if (hit_front == 3 and hit_back == 1) or (hit_front == 2 and hit_back == 2): return "八等奖"
    if (hit_front == 3 and hit_back == 0) or (hit_front == 1 and hit_back == 2) or (hit_front == 0 and hit_back == 2): return "九等奖"
    return "未中奖"

# ---------- 数据抓取（全量，带简单重试） ----------
def fetch_all(timeout=20) -> List[Dict]:
    url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
    all_records = []
    page_no = 1
    page_size = 100
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://static.sporttery.cn/",
    }
    while True:
        params = {
            "gameNo": "85",
            "provinceId": "0",
            "pageSize": str(page_size),
            "isVerify": "1",
            "pageNo": str(page_no),
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}")
            data = resp.json()
            if data.get("errorCode") != "0":
                raise Exception(data.get("errorMsg", "API error"))

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
                    "front": sort_nums(nums[:5]),
                    "back": sort_nums(nums[5:]),
                    "sales": item.get("sales", ""),
                    "prize_pool": item.get("prizePool", ""),
                    "first_win_count": str(first_count),
                    "first_area": first_area,
                    "second_win_count": str(second_count),
                    "third_win_count": str(third_count),
                })

            if len(items) < page_size:
                break
            page_no += 1
            # 适当延时
            import time
            time.sleep(0.5)
        except Exception as e:
            raise Exception(f"抓取第{page_no}页失败: {e}")

    return all_records

# ---------- 统计 ----------
def compute_stats(records: List[Dict], window: int):
    if not records:
        return None
    recent = records[:window] if window > 0 else records
    front_freq = {i: 0 for i in range(FRONT_MIN, FRONT_MAX+1)}
    back_freq = {i: 0 for i in range(BACK_MIN, BACK_MAX+1)}
    for r in recent:
        for n in r["front"]:
            front_freq[n] += 1
        for n in r["back"]:
            back_freq[n] += 1
    front_sorted = sorted(front_freq.items(), key=lambda x: x[1], reverse=True)
    back_sorted = sorted(back_freq.items(), key=lambda x: x[1], reverse=True)
    front_hot = [x[0] for x in front_sorted[:5]]
    front_cold = [x[0] for x in front_sorted[-5:]]
    back_hot = [x[0] for x in back_sorted[:3]]
    back_cold = [x[0] for x in back_sorted[-3:]]
    return {
        "front_freq": front_freq,
        "back_freq": back_freq,
        "front_sorted": front_sorted,
        "back_sorted": back_sorted,
        "front_hot": front_hot,
        "front_cold": front_cold,
        "back_hot": back_hot,
        "back_cold": back_cold,
        "total": len(recent)
    }

# ---------- 推荐 ----------
def generate_recommendations(records: List[Dict], count: int, window: int):
    stats = compute_stats(records, window)
    if not stats:
        return []
    front_pool = []
    back_pool = []
    for num, freq in stats["front_sorted"]:
        weight = freq + 1
        front_pool.extend([num] * weight)
    for num, freq in stats["back_sorted"]:
        weight = freq + 1
        back_pool.extend([num] * weight)

    results = []
    used = set()
    for _ in range(count * 2):
        if len(results) >= count:
            break
        front = set()
        attempts = 0
        while len(front) < FRONT_PICK and attempts < 50:
            picks = random.sample(front_pool, min(FRONT_PICK*2, len(front_pool)))
            for n in picks:
                front.add(n)
                if len(front) == FRONT_PICK:
                    break
            attempts += 1
        if len(front) < FRONT_PICK:
            fallback = [x for x in range(FRONT_MIN, FRONT_MAX+1) if x not in front]
            front.update(fallback[:FRONT_PICK - len(front)])
        front = list(front)

        back = set()
        attempts = 0
        while len(back) < BACK_PICK and attempts < 50:
            picks = random.sample(back_pool, min(BACK_PICK*2, len(back_pool)))
            for n in picks:
                back.add(n)
                if len(back) == BACK_PICK:
                    break
            attempts += 1
        if len(back) < BACK_PICK:
            fallback = [x for x in range(BACK_MIN, BACK_MAX+1) if x not in back]
            back.update(fallback[:BACK_PICK - len(back)])
        back = list(back)

        key = tuple(sorted(front)) + tuple(sorted(back))
        if key not in used:
            used.add(key)
            results.append({
                "front": sorted(front),
                "back": sorted(back)
            })
    return results[:count]

# ---------- 复盘 ----------
def review(period: str, front: List[int], back: List[int]):
    raw = load_raw()
    target = next((r for r in raw if r["period"] == period), None)
    if not target:
        return {"found": False, "msg": f"未找到期号 {period}"}
    hit_f = len(set(target["front"]) & set(front))
    hit_b = len(set(target["back"]) & set(back))
    prize = prize_level(hit_f, hit_b)
    return {
        "found": True,
        "period": period,
        "actual_front": target["front"],
        "actual_back": target["back"],
        "hit_front": hit_f,
        "hit_back": hit_b,
        "prize": prize
    }

# ---------- 导出数据（返回字典列表，用于生成CSV/TXT） ----------
def get_export_data():
    raw = load_raw()
    sorted_raw = sorted(raw, key=lambda x: x["period"])
    rows = []
    for r in sorted_raw:
        rows.append({
            "期号": r["period"],
            "开奖日期": (r.get("draw_time") or "").split()[0] if r.get("draw_time") else "",
            "前区号码": " ".join(fmt_num(n) for n in r["front"]),
            "后区号码": " ".join(fmt_num(n) for n in r["back"]),
            "销售额": r.get("sales", ""),
            "奖池奖金": r.get("prize_pool", ""),
            "一等奖注数": r.get("first_win_count", ""),
            "一等奖地区": r.get("first_area", ""),
            "二等奖注数": r.get("second_win_count", ""),
            "三等奖注数": r.get("third_win_count", ""),
        })
    return rows