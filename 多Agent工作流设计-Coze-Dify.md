# 多 Agent 工作流设计：JD 词频分析器（Coze / Dify 搭建指南）

> **用途**：周末亲手搭建（预计 2 小时），搭完即可在简历中写"搭建多 Agent 工作流"。
> **参照系**：v1 脚本版（`03-开发/analyzer.py`）已产出同等报告（`04-交付/JD关键词匹配报告-v1.md`），工作流版以它为基准对齐输出。
> **平台选择**：Coze（字节系，中文免费，界面友好）或 Dify（企业采用广）。二选一，推荐先 Coze。

---

## 一、总体架构（三节点）

```
[输入] JD 文本（批量粘贴，一份一块）
   ↓
节点1【LLM 结构化提取】→ JSON（公司/岗位/方向/职责/要求/关键词）
   ↓
节点2【代码 聚合统计】→ 词频表（确定性的，非 LLM 统计）
   ↓
节点3【LLM 匹配报告】→ 报告（词频榜+缺口+简历优化建议）
```

**设计原则（面试可讲）**：
1. **能用代码的环节绝不用 LLM**——词频统计是确定性任务，LLM 数数会幻觉（这正是"清楚 AI 边界"的实证）
2. **LLM 只做它擅长的**——非结构化→结构化（提取）、结构化→叙事（报告）
3. **每个 LLM 节点都有输出 schema 约束**——JSON 格式限定 + 温度调低

---

## 二、节点详细设计

### 节点 1：结构化提取（LLM 节点）

**输入变量**：`jd_text`（用户粘贴，多份 JD 用 `===` 分隔）

**System Prompt**（直接粘贴）：

```
你是 JD 结构化助手。从输入的招聘 JD 文本中提取结构化信息。
规则：
1. 多份 JD 用 === 分隔，逐份提取
2. 只提取原文出现的内容，不推测、不补充
3. 关键词从职责和任职要求中提取，每条 2-8 字，动词开头或名词短语
4. 严格按以下 JSON 数组输出，不要输出任何其他文字：

[{"company":"公司名","position":"岗位名","direction":"GTM/销售/FAE/营销运营/其他",
"duties":["职责1","职责2"],"requirements":["要求1","要求2"],
"keywords":["关键词1","关键词2"]}]
```

**温度**：0.1-0.3。**输出**：`structured` (string)

### 节点 2：词频聚合（代码节点）

Coze 用"代码块"节点（Python），Dify 用"代码执行"节点。把 analyzer.py 的统计逻辑搬过来（精简版）：

```python
import json, re
from collections import Counter, defaultdict

def main(structured: str) -> dict:
    items = json.loads(structured)
    kw_counter = Counter()          # 关键词 -> 总频次
    kw_docs = defaultdict(set)     # 关键词 -> 出现的岗位
    dir_kw = defaultdict(Counter)  # 方向 -> 关键词计数
    for it in items:
        for kw in it.get("keywords", []):
            kw = kw.strip()
            if kw:
                kw_counter[kw] += 1
                kw_docs[kw].add(it["position"])
                dir_kw[it["direction"]][kw] += 1
    total_docs = len(items)
    top25 = [{"keyword": k, "count": v, "docs": len(kw_docs[k])}
             for k, v in kw_counter.most_common(25)]
    by_dir = {d: [k for k, _ in c.most_common(8)] for d, c in dir_kw.items()}
    stats = {"total_docs": total_docs, "top25": top25, "by_direction": by_dir}
    return {"stats": json.dumps(stats, ensure_ascii=False)}
```

**输出变量**：`stats` (string)

> 注意：关键词归一化（如"渠道管理"与"渠道"合并）v1 脚本用人工词典做了；工作流版可先用 LLM 提取时要求"合并同义词"，或把 analyzer.py 的 LEXICON 搬进来。这是两版结果的已知差异，如实讲即可。

### 节点 3：匹配报告生成（LLM 节点）

**输入**：节点2 的 `stats` + 预置的"我的画像"（写在 prompt 里）

**System Prompt**：

```
你是简历优化顾问。基于 JD 词频统计数据，输出匹配分析报告。

我的画像：西安交大自动化 2027 届；中航工业实习（Java/Spring Boot/MySQL/Kafka
端到端交付）；苏州 6 商圈 1000 份调研带队；ACCA 已过 4 门；TRAE AI Agent 重度
用户（搭建过 SOP 驱动运营系统）；CET-6；目标岗位 GTM/渠道销售/FAE。

输出格式（markdown）：
## 一、市场要什么（Top10 关键词 + 频次 + 出现岗位数）
## 二、我的覆盖（哪些高频词我已有证据，注明对应经历）
## 三、我的缺口（哪些高频词没有证据，按优先级排序）
## 四、行动建议（每条缺口给一句可落地的简历表述或面试准备建议）

规则：只基于提供的统计数据判断，不编造数据；我的覆盖判断必须指向真实存在的
经历，不确定就归入缺口。
```

**输出**：`report` (string)

---

## 三、测试与评测（对应"提示词评测"能力）

搭建完成后，用 3 份已知 JD 做验证集（预期输出已知，来自 v1 报告）：

| 测试用例 | 输入 | 预期（对照 v1 报告） |
|---|---|---|
| T1 单份 | 拓竹-GTM 画像 JD | 供应链/渠道类词频最高 |
| T2 批量 3 份 | 华为云BD+大疆销售+拓竹KOL | 合作伙伴/生态、KOL/社媒靠前 |
| T3 全量 8 份 | 完整语料 | Top5 ≈ 沟通协调/KOL社媒/合作伙伴/品牌/营销策划 |

**通过标准**：T1-T3 的 Top10 与 v1 报告重合度 ≥60%（关键词归一化差异属预期）。
**不达标时**：改节点 1 的提取 prompt（加同义词合并规则）而非改代码节点——留档每次修改原因，这就是你的"提示词迭代评测记录"。

## 四、边界与风险（面试讲这节最加分）

1. **LLM 数数幻觉** → 统计放代码节点（本工作流的核心设计决策）
2. **上下文限制** → JD 批量输入超长时分批跑节点 1，聚合在节点 2 天然支持增量合并
3. **提取漂移** → schema 约束 + 低温 + 验证集回归测试
4. **数据时效** → 语料是静态快照，简历结论需标注日期

## 五、搭完后的简历升级行（备用）

> 原 AI 行基础上追加：`；搭建多 Agent 工作流（结构化提取-代码聚合-报告生成三节点，Coze/Dify）完成 JD 批量分析与简历缺口诊断，LLM 与代码节点按"确定性任务不上模型"原则分工`

---

**搭建顺序建议**：注册 Coze → 建工作流 → 节点2 先粘代码 → 节点1、3 粘 prompt → 用 T1 用例联调 → 跑 T3 全量 → 截图存档 `04-交付/工作流截图/`。
