# app.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import io
import csv
import json

import dlt_core as core

app = FastAPI(title="大乐透分析API", description="提供抓取、分析、推荐、复盘等功能", version="3.0")

# 允许跨域（前端可直接调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 请求模型 ----------
class ReviewRequest(BaseModel):
    period: str
    front: List[int]  # 5个号码
    back: List[int]   # 2个号码

class AnalyzeRequest(BaseModel):
    window: int = 30

class RecommendRequest(BaseModel):
    count: int = 4
    window: int = 30

# ---------- API 端点 ----------

@app.post("/fetch", summary="抓取全部历史数据")
def fetch_data():
    """从体彩官网抓取全部历史数据并存储"""
    try:
        records = core.fetch_all()
        if not records:
            raise HTTPException(status_code=500, detail="未获取到任何数据")
        # 更新精简历史
        existing = core.load_history()
        exist_set = {r["period"] for r in existing}
        new_count = 0
        for r in records:
            simple = {"period": r["period"], "front": r["front"], "back": r["back"]}
            if r["period"] not in exist_set:
                existing.append(simple)
                new_count += 1
        existing.sort(key=lambda x: x["period"], reverse=True)
        core.save_history(existing)

        # 更新完整原始数据
        raw_existing = core.load_raw()
        raw_set = {r["period"] for r in raw_existing}
        new_raw = 0
        for r in records:
            if r["period"] not in raw_set:
                raw_existing.append(r)
                new_raw += 1
        raw_existing.sort(key=lambda x: x["period"], reverse=True)
        core.save_raw(raw_existing)

        return {
            "message": f"抓取成功，共 {len(records)} 期，新增 {new_raw} 期",
            "total": len(records),
            "new": new_raw
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", summary="获取历史数据列表（精简）")
def get_history(limit: Optional[int] = Query(None, description="返回最近N期")):
    data = core.load_history()
    if limit:
        data = data[:limit]
    return data

@app.get("/history/raw", summary="获取完整原始数据（含奖金信息）")
def get_raw_history(limit: Optional[int] = Query(None)):
    data = core.load_raw()
    if limit:
        data = data[:limit]
    return data

@app.post("/analyze", summary="分析最近N期，返回频率统计")
def analyze(req: AnalyzeRequest):
    records = core.load_history()
    if not records:
        raise HTTPException(status_code=404, detail="暂无数据，请先抓取")
    stats = core.compute_stats(records, req.window)
    if not stats:
        raise HTTPException(status_code=500, detail="分析失败")
    return stats

@app.post("/recommend", summary="生成推荐号码")
def recommend(req: RecommendRequest):
    records = core.load_history()
    if not records:
        raise HTTPException(status_code=404, detail="暂无数据，请先抓取")
    recs = core.generate_recommendations(records, req.count, req.window)
    return {"recommendations": recs}

@app.post("/review", summary="复盘：输入期号和号码，返回命中情况")
def review(req: ReviewRequest):
    if len(req.front) != 5 or len(req.back) != 2:
        raise HTTPException(status_code=400, detail="前区需5个号码，后区需2个号码")
    result = core.review(req.period, req.front, req.back)
    if not result["found"]:
        raise HTTPException(status_code=404, detail=result["msg"])
    return result

@app.get("/export/csv", summary="导出CSV文件")
def export_csv():
    rows = core.get_export_data()
    if not rows:
        raise HTTPException(status_code=404, detail="无数据可导出")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    response = StreamingResponse(io.BytesIO(output.getvalue().encode('utf-8-sig')),
                                 media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=dlt_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return response

@app.get("/export/txt", summary="导出TXT文件（逗号分隔）")
def export_txt():
    rows = core.get_export_data()
    if not rows:
        raise HTTPException(status_code=404, detail="无数据可导出")
    lines = []
    header = ",".join(rows[0].keys())
    lines.append(header)
    for row in rows:
        lines.append(",".join(str(v) for v in row.values()))
    content = "\n".join(lines)
    response = StreamingResponse(io.BytesIO(('\uFEFF' + content).encode('utf-8')),
                                 media_type="text/plain")
    response.headers["Content-Disposition"] = f"attachment; filename=dlt_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return response

@app.delete("/clear", summary="清空所有数据")
def clear_data():
    core.save_history([])
    core.save_raw([])
    core.save_archive([])
    return {"message": "所有数据已清空"}

@app.get("/archive", summary="获取复盘历史记录")
def get_archive():
    return core.load_archive()

# 添加一个健康检查
@app.get("/health")
def health():
    return {"status": "ok"}

# 如果需要，启动命令：uvicorn app:app --host 0.0.0.0 --port 8000 --reload