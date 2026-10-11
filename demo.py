import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlt_core as dc

# 1. 统计分析
print("=" * 60)
print("  1. 统计 - 频率分析（最近30期）")
print("=" * 60)
stats = dc.do_analyze(window=30)
print("分析窗口: {}期, 总历史: {}期".format(stats["window"], stats["total_history"]))
print("前区和值均值: {}, 后区和值均值: {}".format(stats["front_sum_avg"], stats["back_sum_avg"]))
print("前区跨度均值: {}, 连号出现率: {}".format(stats["front_span_avg"], stats["consecutive_ratio"]))
print()
print("前区热号(Top5):")
for h in stats["front_hot"][:5]:
    print("  {:02d} -> {}次".format(h["number"], h["count"]))
print("前区冷号(Top5):")
for c in stats["front_cold"][:5]:
    print("  {:02d} -> {}次".format(c["number"], c["count"]))
print("后区热号(Top3):")
for h in stats["back_hot"][:3]:
    print("  {:02d} -> {}次".format(h["number"], h["count"]))
print()

# 2. 智能推荐
print("=" * 60)
print("  2. 推荐 - 智能推荐（4组）")
print("=" * 60)
rec = dc.do_recommend(n=4)
if "error" in rec:
    print("错误:", rec["error"])
else:
    print("生成时间:", rec["generated_at"])
    print()
    for r in rec["recommendations"]:
        front_str = " ".join("{:02d}".format(n) for n in r["front"])
        back_str = " ".join("{:02d}".format(n) for n in r["back"])
        print("第{}组: 前区[{}] 后区[{}]".format(r["idx"], front_str, back_str))
        print("  奇{}/偶{} 大{}/小{} 和值{} 跨度{}".format(
            r["odd_count"], r["even_count"], r["big_count"], r["small_count"], r["sum"], r["span"]))
        print()

# 3. 开奖复盘
print("=" * 60)
print("  3. 复盘 - 对比推荐与实际开奖")
print("=" * 60)
# 模拟最新一期开奖: 前区 02 09 17 24 29, 后区 01 11 (25009期)
result = dc.do_review("25009", [2, 9, 17, 24, 29], [1, 11])
if "error" in result:
    print("错误:", result["error"])
else:
    print("开奖期号: {}, 前区{}, 后区{}".format(
        result["period"],
        " ".join("{:02d}".format(n) for n in result["actual_front"]),
        " ".join("{:02d}".format(n) for n in result["actual_back"])))
    print()
    for r in result["results"]:
        front_str = " ".join("{:02d}".format(n) for n in r["front"])
        back_str = " ".join("{:02d}".format(n) for n in r["back"])
        print("第{}组推荐: 前区[{}] 后区[{}]".format(r["idx"], front_str, back_str))
        print("  命中: 前{}/5 后{}/2 -> {}".format(r["hit_front"], r["hit_back"], r["prize"]))
        print()
