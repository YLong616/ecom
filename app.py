#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透分析服务 - Flask API
提供 RESTful 接口: 历史数据、统计分析、推荐生成、开奖复盘、数据导出
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, render_template, Response

import dlt_core
from dlt_core import FRONT_PICK, BACK_PICK

app = Flask(__name__)


@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ── 页面路由 ──────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── API: 历史数据 ─────────────────────────────────────

@app.route("/api/history")
def api_history():
    """获取历史开奖数据（精简版）"""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    result = dlt_core.get_history(limit=limit, offset=offset)
    return jsonify(result)


@app.route("/api/history/raw")
def api_history_raw():
    """获取完整历史数据（含奖金信息）"""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    result = dlt_core.get_raw_history(limit=limit, offset=offset)
    return jsonify(result)


@app.route("/api/latest")
def api_latest():
    """获取最新一期开奖（从本地文件加载）"""
    return jsonify(dlt_core.get_latest_from_local())


@app.route("/api/local-history")
def api_local_history():
    """从本地 txt 文件加载历史数据（新到旧）"""
    data = dlt_core.get_local_history_data()
    return jsonify({"total": len(data), "data": data})


# ── API: 统计分析 ─────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    """获取统计分析结果（支持按期数或日期范围筛选）"""
    refresh = request.args.get("refresh", "0") == "1"
    window = request.args.get("window", dlt_core.ANALYZE_WINDOW, type=int)
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    # 有日期参数或刷新时，强制重新计算
    if refresh or start_date or end_date:
        result = dlt_core.do_analyze(window=window, start_date=start_date or None, end_date=end_date or None)
    else:
        cached = dlt_core.load_stats()
        if cached:
            result = cached
        else:
            result = dlt_core.do_analyze(window=window)

    return jsonify(result)


# ── API: 数据抓取 ─────────────────────────────────────

@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    """触发数据抓取"""
    max_pages = request.args.get("max_pages", type=int)
    try:
        result = dlt_core.do_fetch(max_pages=max_pages)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── API: 推荐生成 ─────────────────────────────────────

@app.route("/api/recommend")
def api_recommend():
    """生成推荐号码"""
    n = request.args.get("n", dlt_core.RECOMMEND_N, type=int)
    regenerate = request.args.get("regenerate", "0") == "1"

    if regenerate:
        result = dlt_core.do_recommend(n=n)
    else:
        # 返回最近一组推荐
        arch = dlt_core.load_archive()
        if arch and arch[-1].get("predictions"):
            latest = arch[-1]
            result = {
                "recommendations": latest["predictions"],
                "generated_at": latest.get("generated_at"),
                "logic": dlt_core.get_recommendation_logic(),
            }
        else:
            result = dlt_core.do_recommend(n=n)

    return jsonify(result)


# ── API: 所有组合 ─────────────────────────────────────

@app.route("/api/all-combos")
def api_all_combos():
    """分页获取所有大乐透组合"""
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    filter_type = request.args.get("filter", "all")
    result = dlt_core.get_all_combos(page=page, page_size=page_size, filter_type=filter_type)
    return jsonify(result)


@app.route("/api/appeared-combos")
def api_appeared_combos():
    """获取已开奖组合列表"""
    return jsonify(dlt_core.get_appeared_combos_list())


@app.route("/api/random-unopened")
def api_random_unopened():
    """从未开奖组合中随机选取"""
    n = request.args.get("n", 5, type=int)
    front_min = request.args.get("front_min", 1, type=int)
    front_max = request.args.get("front_max", 35, type=int)
    back_min = request.args.get("back_min", 1, type=int)
    back_max = request.args.get("back_max", 12, type=int)
    result = dlt_core.get_random_unopened(n=n, front_min=front_min, front_max=front_max,
                                          back_min=back_min, back_max=back_max)
    return jsonify(result)


@app.route("/api/combo-count")
def api_combo_count():
    """获取总组合数"""
    return jsonify(dlt_core.get_total_combo_count())


# ── API: 开奖复盘 ─────────────────────────────────────

@app.route("/api/review", methods=["POST"])
def api_review():
    """复盘: 根据期号查找实际开奖号码，对比推荐"""
    data = request.get_json(force=True)
    period = data.get("period", "")

    if not period:
        return jsonify({"error": "需要提供 period"}), 400

    result = dlt_core.do_review(period)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/archive")
def api_archive():
    """获取所有推荐及复盘记录"""
    return jsonify(dlt_core.get_archive())


# ── API: 开奖兑奖 ─────────────────────────────────────

@app.route("/api/prize-check", methods=["POST"])
def api_prize_check():
    """开奖兑奖: 根据期号和用户选号，对比实际开奖号码（支持多组）"""
    data = request.get_json(force=True)
    period = data.get("period", "")
    bet_sets = data.get("bet_sets", [])

    # 兼容旧格式
    if not bet_sets:
        front = data.get("front", [])
        back = data.get("back", [])
        if front and back:
            bet_sets = [{"front": front, "back": back}]

    if not period or not bet_sets:
        return jsonify({"error": "需要提供 period 和 bet_sets"}), 400

    try:
        parsed_sets = []
        for bs in bet_sets:
            front = [int(n) for n in bs.get("front", [])]
            back = [int(n) for n in bs.get("back", [])]
            if len(front) < FRONT_PICK or len(back) < BACK_PICK:
                return jsonify({"error": "前区至少选5个，后区至少选2个"}), 400
            if any(n < 1 or n > 35 for n in front):
                return jsonify({"error": "前区号码需为1-35"}), 400
            if any(n < 1 or n > 12 for n in back):
                return jsonify({"error": "后区号码需为1-12"}), 400
            parsed_sets.append({"front": front, "back": back})
    except (ValueError, TypeError):
        return jsonify({"error": "号码必须为整数"}), 400

    results = []
    total_prize = 0
    total_cost = 0

    for i, bs in enumerate(parsed_sets):
        result = dlt_core.do_prize_check(period, bs["front"], bs["back"])
        if "error" in result:
            return jsonify(result), 400
        result["set_idx"] = i + 1
        results.append(result)
        total_prize += result.get("total_prize", 0)
        total_cost += result.get("total_cost", 0)

    return jsonify({
        "period": period,
        "actual_front": results[0]["actual_front"],
        "actual_back": results[0]["actual_back"],
        "sets": results,
        "total_prize": total_prize,
        "total_cost": total_cost,
        "net_profit": total_prize - total_cost,
    })


@app.route("/api/prize-rules")
def api_prize_rules():
    """获取大乐透玩法规则"""
    return jsonify(dlt_core.get_prize_rules())


# ── API: 数据导出 ─────────────────────────────────────

@app.route("/api/export/csv")
def api_export_csv():
    """导出 CSV"""
    result = dlt_core.export_csv_text()
    if "error" in result:
        return jsonify(result), 400

    return Response(
        result["csv"],
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=dlt_history.csv"}
    )


@app.route("/api/export/txt")
def api_export_txt():
    """导出 TXT"""
    result = dlt_core.export_csv_text()
    if "error" in result:
        return jsonify(result), 400

    return Response(
        result["txt"],
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=dlt_history.txt"}
    )


# ── 启动 ──────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
