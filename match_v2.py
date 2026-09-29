#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单岗匹配分 v2.2（纯 Python 零 LLM）——定位：词面覆盖率诊断 + 差距清单生成器
⚠️ 本分不是投递建议。投递决策 = 多维评估 + 人工裁决。
v2.2 变更（依方法论备忘 20260927）：
  1. 撤"投/不投"定档 → 观测性相对分层（按本期分布百分位，非规范阈值）
  2. 新增公司级口径（每公司 JD 关键词并集后算覆盖）——与岗位级并列，两口径结论冲突即标注
  3. 头部偏差警告（构成偏差：字节占半/实习岗混入；词面匹配局限）
方法：加权覆盖率 = Σ(市场常见度权重×命中)/Σ(权重)；权重 = 该词在主统计语料出现的岗位数。
"""

import json
import os
from collections import Counter, defaultdict
from datetime import date

with open("data/keywords_frozen_v2.json", encoding="utf-8") as f:
    data = json.load(f)

SYN = {
    "沟通协调能力": ["沟通能力","沟通协作","沟通表达","跨部门沟通","乐于沟通"],
    "市场洞察": ["市场意识","商业洞察","市场洞察力"],
    "逻辑思维": ["逻辑清晰","逻辑性强","逻辑性","逻辑推理","结构化思考","逻辑思维能力","逻辑分析"],
    "学习能力": ["快速学习","学习迁移能力"],
    "自驱力": ["自我驱动","自驱推进","自驱能力","自驱动力"],
    "客户需求": ["用户需求","用户诉求","客户需求沟通"],
    "解决方案": ["解决方案设计","综合解决方案","标准化解决方案","数字化企业解决方案"],
    "AI工具": ["生成式AI工具","数字化工具"],
    "英语": ["英语工作语言","英语听说读写"],
    "抗压能力": ["抗压"],
    "服务意识": ["客户服务意识"],
    "用户洞察": ["用户洞察分析","消费者洞察"],
    "跨部门协同": ["跨部门","跨部门协作","跨团队协同","跨团队协作"],
    "产品演示": ["演示"],
    "培训": ["产品培训","方案培训"],
    "项目管理": ["项目统筹","项目进度管理"],
    "数据分析": ["数据收集","数据监控"],
    "执行力": ["强大的执行力"],
    "团队协作": ["团队合作","协作能力","团队协作能力"],
}
V2C = {}
for c, vs in SYN.items():
    V2C[c] = c
    for v in vs:
        V2C[v] = c
def norm(k):
    return V2C.get(k, k)

main = [j for j in data["jds"] if j["family"] != "X"]
for j in main:
    j["_kws"] = sorted({norm(k) for k in j["keywords"]})

freq = Counter()
for j in main:
    for k in j["_kws"]:
        freq[k] += 1
def W(k):
    return freq.get(k, 1)

def cover(kws, ps):
    Wt = sum(W(k) for k in kws)
    Mt = sum(W(k) for k in kws if k in ps)
    return round(Mt / Wt, 2) if Wt else 0.0

def band(scores, s):
    """观测性相对分层：P75/P25 分位。仅描述本期分布位置，非规范阈值、非投递建议。"""
    ss = sorted(scores)
    n = len(ss)
    p75, p25 = ss[int(n * 0.75)], ss[max(int(n * 0.25) - 1, 0)]
    if s >= p75: return "相对高位"
    if s >= p25: return "中位区间"
    return "相对低位"

lines = []
w = lines.append
w(f"# 单岗匹配分 v2.2（{date.today()}，词面覆盖率诊断口径）")
w("")
w("> ⚠️ **读前必知（三条）**")
w("> 1. **本分不是投递建议**——它只量化「简历证据词对 JD 要求词的词面覆盖」。投递决策 = 多维评估＋人工裁决。v2.1 的「谨慎/不投」定档已被经验证伪（多家被判『谨慎』的公司实际发出了面试）并在此撤除。")
w(f"> 2. **构成偏差警告**：语料为分层配额便利样本（共 {len(data['jds'])} 份，每公司 ≤3 份），词频权重受语料构成影响；本版双口径（岗位级/公司级）并列呈现，结论冲突即构成敏感。")
w("> 3. **词面匹配局限**：同义不同词（如『技术答疑』vs『技术汇报』）的语义缺口词面匹配看不见——缺失词 ≠ 没有相关证据，须结合个人素质清单人工解读。")
w("")
w("> 方法：加权覆盖率 = Σ(市场常见度权重×命中)/Σ(权重)；相对分层 = 本期分布百分位（P75/P25）。方法论与校准史详见 README。")

for ver, prof in data["resume_profiles"].items():
    ps = set(prof["keywords"])
    scored = []
    for j in main:
        s = cover(j["_kws"], ps)
        missing = [k for k in j["_kws"] if k not in ps]
        missing.sort(key=lambda k: -W(k))
        scored.append((s, j, missing))
        j.setdefault("match", {})[ver] = s
    ss = [s for s, _, _ in scored]
    scored.sort(key=lambda x: -x[0])
    w("")
    w(f"## {ver}（目标族 {prof['family_target']}）｜ 岗位级口径（{len(main)} 份主统计）")
    w("")
    w(f"分布：max {max(ss):.2f} ｜ 中位 {sorted(ss)[len(ss)//2]:.2f} ｜ min {min(ss):.2f}（相对分层据此观测）")
    w("")
    w("| JD | 族 | 词面覆盖率 | 相对位置 | 高权重缺失词（差距清单） |")
    w("|---|---|---|---|---|")
    for s, jd, missing in scored:
        hi = [k for k in missing if W(k) >= 3]
        w(f"| {jd['company']}-{jd['title']} | {jd['family']} | {s:.2f} | {band(ss, s)} | {('、'.join(hi[:8]) + ('…' if len(hi) > 8 else '')) or '—'} |")

    # 公司级口径（并集）
    comp = defaultdict(lambda: {"kws": set(), "jds": []})
    for j in main:
        c = j["company"]
        comp[c]["kws"].update(j["_kws"])
        comp[c]["jds"].append(j)
    cscored = []
    for c, d in comp.items():
        ks = sorted(d["kws"])
        cscored.append((cover(ks, ps), c, [k for k in ks if k not in ps], len(d["jds"])))
    cscored.sort(key=lambda x: -x[0])
    css = [s for s, *_ in cscored]
    w("")
    w(f"### 公司级口径（{len(comp)} 家，每家关键词并集）——与岗位级对照，冲突即构成敏感")
    w("")
    w("| 公司 | 岗位数 | 词面覆盖率 | 相对位置 | 高权重缺失词 |")
    w("|---|---|---|---|---|")
    for s, c, missing, n in cscored:
        hi = [k for k in missing if W(k) >= 3]
        w(f"| {c} | {n} | {s:.2f} | {band(css, s)} | {('、'.join(hi[:6]) + ('…' if len(hi) > 6 else '')) or '—'} |")

w("")
w("## 校准记录")
w("")
w("- v2.0 未加权：全员 <0.40（行业专名稀释失真）→ 弃")
w("- v2.1 加权＋绝对阈值定档：分布合理但「谨慎/不投」判决被经验证伪（多家被判『谨慎』的公司实际发出了面试）→ 撤判决")
w("- v2.2 加权＋相对观测分层＋公司级双口径＋三警告（本版）；语料扩至 54 份（分层配额，每公司 ≤3）后整体重算")

_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "单岗匹配分-v2.md")
with open(_out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

json.dump(data, open("data/keywords_frozen_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for ver in data["resume_profiles"]:
    scored = sorted([(j["match"][ver], j) for j in main if ver in j.get("match", {})], key=lambda x: -x[0])
    print(f"【{ver}】岗位级 Top5：")
    for s, jd in scored[:5]:
        print(f"  {s:.2f} {jd['company']}-{jd['title']}（族{jd['family']}）")
print(f"\n匹配分报告 v2.2 已写：{_out}")
