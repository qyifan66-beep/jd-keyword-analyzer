#!/usr/bin/env python3
"""JD 关键词词频与简历匹配分析器 v1
用法: python3 analyzer.py
输入: data/jd_corpus.md (### SOURCE: 分块)
输出: ../../04-交付/JD关键词匹配报告-v1.md
"""
import re
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).parent
CORPUS = HERE / "data" / "jd_corpus.md"
REPORT = HERE.parent / "04-交付" / "JD关键词匹配报告-v1.md"

# 关键词词典: (规范词, 类别, [别名正则])
LEXICON = [
    ("市场洞察/调研", "市场营销", [r"市场洞察", r"市场调研", r"行业趋势", r"消费者洞察", r"用户调研", r"人群特点研究"]),
    ("竞品分析", "市场营销", [r"竞品"]),
    ("品牌/传播", "市场营销", [r"品牌", r"传播"]),
    ("营销策划", "市场营销", [r"营销", r"campaign", r"市场活动"]),
    ("KOL/社媒", "市场营销", [r"KOL", r"社交媒体", r"社媒", r"social", r"TikTok", r"YouTube", r"Instagram"]),
    ("内容运营", "市场营销", [r"内容(运营|共创|营销|创意|资产|素材)"]),
    ("新品/GTM上市", "市场营销", [r"新品上市", r"产品上市", r"Go ?To ?Market", r"产品生命周期"]),
    ("渠道管理", "销售商务", [r"渠道"]),
    ("销售策略/目标", "销售商务", [r"销售(目标|策略|网络|考核|增长|预测)"]),
    ("经销商/零售/电商", "销售商务", [r"经销商", r"零售", r"电商"]),
    ("商务谈判", "销售商务", [r"谈判"]),
    ("客户关系管理", "销售商务", [r"客户关系", r"客户满意", r"大客户", r"客户需求", r"客户合作"]),
    ("合作伙伴/生态", "销售商务", [r"合作伙伴", r"生态", r"伙伴", r"agency", r"供应商"]),
    ("解决方案", "销售商务", [r"解决方案"]),
    ("市场拓展", "销售商务", [r"拓展", r"开拓"]),
    ("数据分析", "技术数据", [r"数据分析", r"数据(敏感|收集|驱动|识别|健康度)"]),
    ("AI工具应用", "技术数据", [r"\bAI\b", r"人工智能", r"自动化", r"智能化"]),
    ("技术背景", "技术数据", [r"软件(工程|开发)", r"芯片", r"计算机", r"技术问题"]),
    ("英语能力", "通用素质", [r"英语", r"英文", r"中英文"]),
    ("沟通协调", "通用素质", [r"沟通", r"协调"]),
    ("逻辑思维", "通用素质", [r"逻辑"]),
    ("学习能力", "通用素质", [r"学习能力", r"学习迁移", r"快速适应", r"持续关注"]),
    ("抗压/韧性", "通用素质", [r"抗压", r"韧性", r"挑战"]),
    ("跨部门协作", "通用素质", [r"跨部门", r"跨团队", r"协同", r"配合"]),
    ("项目管理", "通用素质", [r"项目(管理|运作|负责|brief|目标)", r"timeline", r"checklist", r"关键节点"]),
    ("自驱力", "通用素质", [r"自驱", r"自我驱动", r"独立推进"]),
    ("创新意识", "通用素质", [r"创新"]),
    ("实习经验", "通用素质", [r"实习经验", r"实习经历"]),
    ("学生干部/活动", "通用素质", [r"学生干部", r"社团", r"大型活动"]),
    ("供应链管理", "供应链", [r"供应链", r"进销存", r"要货", r"交付产品"]),
]

# 简历关键词(4 版并集) → 用于覆盖判定
MY_KEYWORDS = [
    r"市场调研", r"调研策略", r"客户画像", r"数据驱动", r"数据分析", r"渠道场景", r"话术",
    r"cold pitch", r"陌生客户", r"商务沟通", r"Java", r"Spring ?Boot", r"MySQL", r"Kafka",
    r"WebSocket", r"Git", r"数据库", r"消息队列", r"实时(通信|推送|传输)", r"ACCA",
    r"跨职能", r"跨团队", r"系统集成", r"端到端", r"需求分析", r"架构设计", r"英语", r"CET-?6",
    r"队长", r"团队协作", r"抗压", r"实时数据", r"低空飞行", r"自动化",
]

DIRECTION = {
    "华为-云BD实习生": ("B端销售/BD", "华为云"),
    "华为-消费者管理培训生": ("销售管培", "华为终端"),
    "华为-芯片器件FAE经理": ("FAE/技术售前", "华为芯片"),
    "大疆海外-销售培训生": ("渠道销售", "大疆"),
    "拓竹-IMC整合营销": ("整合营销", "拓竹"),
    "拓竹-海外KOL": ("KOL/生态运营", "拓竹"),
    "拓竹-海外市场营销": ("海外市场营销", "拓竹"),
    "拓竹-GTM": ("GTM", "拓竹"),
}

# 我的可验证证据文本（4 版简历关键表述并集）
MY_CLAIMS = ("跨职能资源整合 商务沟通 客户画像分层 市场调研 调研策略 渠道场景优化 数据驱动 "
             "数据分析 话术 cold pitch 陌生客户转化 高考提分59分 长期主义 端到端交付 需求分析 "
             "架构设计 MySQL Kafka WebSocket Git Spring Boot 数据库 实时数据传输 低空飞行数据 "
             "系统集成 协同开发 团队协作 篮球书院联赛队长 抗压 围棋 爵士鼓 AI Agent SOP "
             "运营管理系统 理工逻辑底座 嵌入式 Java 自动化 英语 CET-6 CET-4")

# JD 关键词 → 我的证据正则（语义覆盖映射；无映射则检查字面）
COVERAGE_MAP = {
    "沟通协调": r"沟通",
    "学习能力": r"提分|长期主义|爵士鼓",
    "项目管理": r"端到端|需求分析|架构设计",
    "跨部门协作": r"跨职能|跨团队|协同|系统集成",
    "逻辑思维": r"理工|逻辑",
    "市场洞察/调研": r"市场调研|调研",
    "AI工具应用": r"AI|Agent|TRAE",
    "技术背景": r"Java|Spring|嵌入式|理工",
    "客户关系管理": r"客户画像|客户转化|客户",
    "市场拓展": r"陌生|拓展",
    "学生干部/活动": r"队长|联赛",
    "英语能力": r"英语|CET",
    "数据分析": r"数据分析|数据驱动",
    "抗压/韧性": r"抗压|长期主义",
}


def main():
    text = CORPUS.read_text(encoding="utf-8")
    blocks = re.split(r"^### SOURCE: ", text, flags=re.M)[1:]
    jds = []
    for b in blocks:
        first_line, _, body = b.partition("\n")
        name = re.sub(r"-\d+$", "", first_line.replace(".md", "").strip())
        clean = re.sub(r"[*#>`|-]", " ", body)
        jds.append((name, clean))

    kw_total = defaultdict(int)
    kw_docs = defaultdict(set)
    kw_dir = defaultdict(lambda: defaultdict(int))
    cat_total = defaultdict(int)
    dir_cat = defaultdict(lambda: defaultdict(int))
    doc_counts = defaultdict(lambda: defaultdict(int))

    for name, body in jds:
        direction, company = DIRECTION.get(name, ("未知", name))
        for canon, cat, aliases in LEXICON:
            n = 0
            for a in aliases:
                n += len(re.findall(a, body, flags=re.I))
            if n:
                kw_total[canon] += n
                kw_docs[canon].add(name)
                kw_dir[canon][direction] += n
                cat_total[cat] += n
                dir_cat[direction][cat] += n
                doc_counts[name][canon] += n

    def is_covered(kw):
        if kw in COVERAGE_MAP:
            return bool(re.search(COVERAGE_MAP[kw], MY_CLAIMS))
        return any(re.search(p, kw.replace("/", ""), re.I) for p in MY_KEYWORDS)

    lines = []
    lines.append("# JD 关键词匹配报告 v1")
    lines.append("")
    lines.append(f"> 生成: analyzer.py v1 | 语料: {len(jds)} 份 JD | 数据源: Project_07 画像文件 | 日期: 2026-08-28")
    lines.append("")

    lines.append("## 一、语料概览")
    lines.append("")
    lines.append("| 方向 | 公司-岗位 |")
    lines.append("|---|---|")
    for name, _ in jds:
        d, c = DIRECTION.get(name, ("未知", name))
        lines.append(f"| {d} | {name} |")
    lines.append("")

    lines.append("## 二、关键词总频次榜（Top 25）")
    lines.append("")
    lines.append("| 排名 | 关键词 | 类别 | 总频次 | 覆盖 JD 数 | 简历覆盖 |")
    lines.append("|---|---|---|---|---|---|")
    cat_of = {c: cat for c, cat, _ in LEXICON}
    ranked = sorted(kw_total.items(), key=lambda x: -x[1])[:25]
    for i, (kw, n) in enumerate(ranked, 1):
        lines.append(f"| {i} | {kw} | {cat_of[kw]} | {n} | {len(kw_docs[kw])}/{len(jds)} | {'✓' if is_covered(kw) else '✗'} |")
    lines.append("")

    lines.append("## 三、分类词频统计")
    lines.append("")
    lines.append("| 类别 | 频次 | 占比 |")
    lines.append("|---|---|---|")
    total = sum(cat_total.values())
    for cat, n in sorted(cat_total.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | {n} | {n/total*100:.0f}% |")
    lines.append("")

    lines.append("## 四、分方向关键词侧重（各方向 Top 8）")
    lines.append("")
    for d in ["B端销售/BD", "销售管培", "渠道销售", "FAE/技术售前", "整合营销", "KOL/生态运营", "海外市场营销", "GTM"]:
        top = sorted(((kw, kw_dir[kw].get(d, 0)) for kw in kw_total if kw_dir[kw].get(d)),
                     key=lambda x: -x[1])[:8]
        if top:
            lines.append(f"**{d}**: " + "、".join(f"{k}({n})" for k, n in top))
            lines.append("")

    lines.append("## 五、简历覆盖缺口（Top 关键词中未覆盖项）")
    lines.append("")
    gaps = [(kw, n) for kw, n in ranked if not is_covered(kw)]
    lines.append("| 缺口关键词 | 频次 | 可行动建议 |")
    lines.append("|---|---|---|")
    advice = {
        "渠道管理": "中航实习交付流程可表述为渠道协同；面试储备渠道管理框架（选型-政策-秩序-进销存）",
        "KOL/社媒": "海外 KOL 岗相关，若投递需补自媒体运营证据",
        "合作伙伴/生态": "AI Agent 生态运营叙事可迁移（SOP 系统即多方协同）",
        "经销商/零售/电商": "渠道销售版简历加零售/电商认知表述（消费电子发烧友可关联）",
        "解决方案": "技术产品版已有端到端交付，补'解决方案思维'表述",
        "新品/GTM上市": "面试准备产品上市框架（目标市场-定价-渠道-节奏）",
        "供应链管理": "拓竹 GTM 特有，面试前补基本概念（预测-库存-交付）",
        "销售策略/目标": "苏州调研闭环可迁移为'数据驱动的策略制定'表述",
        "品牌/传播": "面试前准备品牌传播基本框架（定位-内容-渠道-度量）",
        "营销策划": "面试前准备 campaign 执行要素（brief-timeline-checklist-复盘）",
        "内容运营": "暂列低优先级",
    }
    for kw, n in gaps:
        lines.append(f"| {kw} | {n} | {advice.get(kw, '面试前定向准备')} |")
    lines.append("")

    lines.append("## 六、核心结论")
    lines.append("")
    mkt = cat_total.get("市场营销", 0)
    biz = cat_total.get("销售商务", 0)
    lines.append(f"1. 8 份冲刺档 JD 中，销售商务类词频 {biz}、市场营销类 {mkt}，"
                 f"合计占总词频 {(mkt+biz)/total*100:.0f}% —— 印证'商业-技术接口岗'定位")
    lines.append(f"2. 覆盖 JD 数最广的关键词: " + "、".join(
        f"{k}({len(v)}/8)" for k, v in sorted(kw_docs.items(), key=lambda x: -len(x[1]))[:5]))
    lines.append(f"3. 简历缺口共 {len(gaps)} 项（见第五节），其中高优先级: "
                 + "、".join(k for k, _ in gaps[:4] if k in advice))
    lines.append("")
    lines.append("---")
    lines.append("> 边界说明: 语料仅 8 份画像（冲刺档核心公司），非全部 79 条投递；"
                  "关键词词典 30 项为人工定义，LLM 未参与统计（防幻觉），全部由代码可重复计算。")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK 报告已生成: {REPORT}")
    print(f"语料: {len(jds)} 份 JD | 关键词命中: {len(kw_total)} 项 | 总频次: {total}")


if __name__ == "__main__":
    main()
