#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JD 词频分析器 v2 · 统计层（纯 Python 标准库，零 LLM）
输入：data/keywords_frozen_v2.json（提取层已冻结的关键词数据，份数/状态从数据动态统计）
输出：词频分析-v2-报告.md（脚本同目录；交付时复制到 04-交付）
纪律：本脚本只做同义词合并与频次统计，不做任何语义推测；改词频先改冻结 JSON。
"""

import json
import os
from collections import Counter, defaultdict

FAMILY_NAME = {
    "A": "A-方案/技术支持",
    "B": "B-AI产品/运营",
    "C": "C-销售/BD",
    "D": "D-GTM/营销",
    "X": "X-研发对照（不进主统计）",
}

# ============================================================
# 同义词合并映射 v2（v1 基础上扩展；只合并语义明确相同的词）
# ============================================================
SYNONYM_MAP = {
    # —— v1 原有 ——
    "沟通协调能力": ["沟通能力", "沟通协调"],
    "产品上市": ["新品上市"],
    "社交媒体": ["海外社交平台"],
    "项目管理": ["项目统筹", "项目进度管理"],
    "客户关系": ["合作关系"],
    "KOL运营": ["KOL合作", "KOL BD", "KOL资源开发"],
    "数据分析": ["数据收集", "数据监控"],
    "营销活动": ["大促campaign"],
    "海外经历": ["海外留学"],
    "消费电子": ["电子消费品", "科技硬件", "硬件产品"],
    "逻辑思维": ["逻辑思维能力", "结构化思考"],
    "学习能力": ["学习迁移能力"],
    "销售渠道": ["渠道建设"],
    "品牌营销": ["品牌传播", "品牌Campaign", "品牌内容运营"],
    "内容创作": ["内容共创"],
    "自驱力": ["自我驱动"],
    # —— v2 新增（22 份新语料中出现的合并对）——
    "沟通协调能力": ["沟通能力", "沟通协作", "沟通表达", "跨部门沟通", "乐于沟通"],
    "市场洞察": ["市场意识", "商业洞察", "市场洞察力"],
    "逻辑思维": ["逻辑思维能力", "结构化思考", "逻辑清晰", "逻辑性强", "逻辑性", "逻辑推理"],
    "学习能力": ["学习迁移能力", "快速学习"],
    "自驱力": ["自我驱动", "自驱推进", "自驱能力", "自驱动力"],
    "客户需求": ["用户需求", "用户诉求", "客户需求沟通"],
    "竞品分析": ["竞品监测"],
    "抗压能力": ["抗压"],
    "商业思维": ["商业意识"],
    "服务意识": ["客户服务意识"],
    "用户洞察": ["用户洞察分析", "消费者洞察"],
    "跨部门协同": ["跨部门", "跨部门协作", "跨团队协同", "跨团队协作"],
    "产品演示": ["演示"],
    "培训": ["产品培训", "方案培训"],
    "AI工具": ["生成式AI工具", "数字化工具"],
    "英语": ["英语工作语言", "英语听说读写"],
    "执行力": ["强大的执行力"],
    "团队协作": ["团队合作", "协作能力", "团队协作能力"],
    "解决方案": ["解决方案设计", "综合解决方案", "标准化解决方案", "数字化企业解决方案"],
}

VARIANT_TO_CANONICAL = {}
for canonical, variants in SYNONYM_MAP.items():
    VARIANT_TO_CANONICAL[canonical] = canonical
    for v in variants:
        VARIANT_TO_CANONICAL[v] = canonical

def normalize(kw):
    return VARIANT_TO_CANONICAL.get(kw, kw)

# ============================================================
# 载入冻结数据
# ============================================================
with open("data/keywords_frozen_v2.json", encoding="utf-8") as f:
    data = json.load(f)

jds = []
for jd in data["jds"]:
    seen, kws = set(), []
    for kw in jd["keywords"]:
        c = normalize(kw)
        if c not in seen:
            seen.add(c)
            kws.append(c)
    jds.append({**jd, "keywords": kws, "family": jd["family"]})

main = [j for j in jds if j["family"] != "X"]  # 主统计（不含研发对照族）

# ============================================================
# 统计
# ============================================================
total = Counter()
kw_jds = defaultdict(set)
kw_fams = defaultdict(set)
fam_counter = defaultdict(Counter)

for jd in main:
    for kw in jd["keywords"]:
        total[kw] += 1
        kw_jds[kw].add(jd["id"])
        kw_fams[kw].add(jd["family"])
        fam_counter[jd["family"]][kw] += 1

top30 = total.most_common(30)
common = [(kw, sorted(fams)) for kw, fams in kw_fams.items() if len(fams) >= 3]
common.sort(key=lambda x: (-total[x[0]], x[0]))
high = [(kw, f, len(kw_jds[kw])) for kw, f in total.items() if f >= 4 and len(kw_jds[kw]) >= 3]
high.sort(key=lambda x: (-x[1], -x[2]))

# ============================================================
# 产出报告
# ============================================================
lines = []
w = lines.append
n_total, n_main = len(jds), len(main)
n_x = n_total - n_main
fam_n = {f: len([j for j in main if j["family"] == f]) for f in "ABCD"}
n_byted = sum(1 for j in jds if "字节" in j.get("company", ""))
prov_stat = "｜".join(f"{k} {v} 份" for k, v in sorted(Counter(j.get("provenance", "未标注") for j in jds).items()))
w(f"# JD 词频分析 v2 · 报告（语料快照 {n_total} 份，2026-09 重算）")
w("")
w(f"> 语料：{n_total} 份逐字 JD（主统计 {n_main} 份：族A {fam_n['A']}／族B {fam_n['B']}／族C {fam_n['C']}／族D {fam_n['D']}；X-研发对照 {n_x} 份不进主统计）｜ 提取层 provenance：{prov_stat}｜ 统计层：本脚本纯 Python 零 LLM")
w(f"> ⚠️ **构成偏差警告**：语料为分层配额便利样本（每公司 ≤3 份；字节 {n_byted}/{n_total}），词频排序受语料构成影响；解读以『某素质在某族 JD 中**是否被要求**（存在性）』为主，『频次排序』为辅。方法论详见 README。")
w("> 同义词合并映射见 `analyze_v2.py`（全映射显式可查）")
w("")
w(f"## 一、总榜 Top 30（主统计 {n_main} 份，同义词已合并）")
w("")
w("| # | 关键词 | 频次 | 岗位数 | 覆盖族 |")
w("|---|---|---|---|---|")
for i, (kw, freq) in enumerate(top30, 1):
    w(f"| {i} | {kw} | {freq} | {len(kw_jds[kw])} | {'、'.join(sorted(kw_fams[kw]))} |")
w("")
w("## 二、跨族共性词（出现在 ≥3 个岗位族 = 通用素质）")
w("")
w("| 关键词 | 频次 | 覆盖族 |")
w("|---|---|---|")
for kw, fams in common:
    w(f"| {kw} | {total[kw]} | {'、'.join(fams)} |")
w("")
w("## 三、分族 Top 12")
w("")
for fam in ["A", "B", "C", "D"]:
    w(f"### 族{fam}｜{FAMILY_NAME[fam]}（{len([j for j in main if j['family']==fam])} 份）")
    w("")
    w("| # | 关键词 | 频次 |")
    w("|---|---|---|")
    for i, (kw, freq) in enumerate(fam_counter[fam].most_common(12), 1):
        w(f"| {i} | {kw} | {freq} |")
    w("")
w("## 四、高频核心词（频次 ≥4 且岗位数 ≥3）")
w("")
for kw, freq, n in high:
    w(f"- {kw}：频次 {freq}，{n} 份岗位")
w("")
w("## 五、方法与边界")
w("")
w("- 提取层关键词冻结于 `data/keywords_frozen_v2.json`，改统计先改数据，不改代码口径")
w(f"- 提取层状态（动态）：{prov_stat}；提取规则：2-8 字、只提取原文、不推测")
w("- X-研发对照族仅存档对照用，不进任何主榜")
w("- 已知边界：关键词为人工/LLM 判读的『原文能力词』，非全文 n-gram；v1 双实现交叉验证经验（Coze n-gram 抓漏『消费电子』）提示统计层可再叠一层 n-gram 兜底，v2.1 待办")

report = "\n".join(lines)
_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "词频分析-v2-报告.md")
with open(_out, "w", encoding="utf-8") as f:
    f.write(report)

# 控制台摘要
print("=" * 60)
print(f"主统计 {n_main} 份 ｜ Top 15：")
for i, (kw, freq) in enumerate(top30[:15], 1):
    print(f"{i:>2}. {kw:<12} 频次{freq:<3} 岗位数{len(kw_jds[kw]):<3} 族{'、'.join(sorted(kw_fams[kw]))}")
print("-" * 60)
print(f"跨族共性词（≥3 族）：{len(common)} 个")
for kw, fams in common[:12]:
    print(f"  {kw:<12} {total[kw]}次  {'、'.join(fams)}")
print("-" * 60)
for fam in ["A", "B", "C", "D"]:
    tops = "、".join(f"{kw}({f})" for kw, f in fam_counter[fam].most_common(6))
    print(f"族{fam} Top6：{tops}")
print(f"\n报告已写：{_out}")
