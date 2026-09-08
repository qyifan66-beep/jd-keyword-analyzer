#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JD关键词匹配分析
从8份JD中提取原文关键词（2-8字），同义词合并，代码统计词频。
"""

from collections import Counter, defaultdict

# ============================================================
# 同义词合并映射（canonical -> variants）
# 只合并语义明确相同的词
# ============================================================
SYNONYM_MAP = {
    "沟通协调能力": ["沟通能力", "沟通协调"],
    "产品上市": ["新品上市"],
    "社交媒体": ["海外社交平台"],
    "项目管理": ["项目统筹"],
    "客户关系": ["合作关系"],
    "KOL运营": ["KOL合作", "KOL BD", "KOL资源开发"],
    "数据分析": ["数据收集"],
    "营销活动": ["大促campaign"],
    "海外经历": ["海外留学"],
    "消费电子": ["电子消费品", "科技硬件", "硬件产品"],
    "逻辑思维": ["逻辑思维能力", "结构化思考"],
    "学习能力": ["学习迁移能力"],
    "销售渠道": ["渠道建设"],
    "品牌营销": ["品牌传播", "品牌Campaign", "品牌内容运营"],
    "内容创作": ["内容共创"],
    "自驱力": ["自我驱动"],
}

# 反向映射：variant -> canonical
VARIANT_TO_CANONICAL = {}
for canonical, variants in SYNONYM_MAP.items():
    VARIANT_TO_CANONICAL[canonical] = canonical
    for v in variants:
        VARIANT_TO_CANONICAL[v] = canonical

def normalize(kw):
    return VARIANT_TO_CANONICAL.get(kw, kw)

# ============================================================
# 第一步：结构化提取 —— 每份JD的元数据 + 原文关键词
# 关键词规则：2-8字，只提取原文出现的内容，不推测
# ============================================================

raw_jds = [
    {
        "id": "JD1",
        "company": "华为",
        "title": "云BD实习生",
        "direction": "销售/BD",
        "keywords": [
            "行业趋势", "客户需求", "拓展策略", "项目管理", "客户关系",
            "解决方案", "端到端", "合作伙伴", "渠道政策", "品牌营销",
            "产品上市", "学习能力", "市场意识", "逻辑思维", "沟通协调能力",
            "创新", "理工科", "实习经验", "学生干部", "市场洞察",
            "生态建设", "客户满意度", "竞争力",
        ],
    },
    {
        "id": "JD2",
        "company": "华为",
        "title": "消费者管理培训生",
        "direction": "GTM/销售/营销",
        "keywords": [
            "产品上市", "全生命周期", "渠道销售", "销售策略", "销售网络",
            "营销", "零售", "门店运营", "市场活动", "电商",
            "用户体验", "学习能力", "自驱力", "沟通协调能力", "创新",
            "社会实践", "消费电子", "品牌高端化", "智驾", "出海",
            "消费者洞察",
        ],
    },
    {
        "id": "JD3",
        "company": "华为",
        "title": "芯片器件FAE经理",
        "direction": "FAE",
        "keywords": [
            "市场机会", "推广宣讲", "方案设计", "项目管理", "客户关系",
            "技术问题", "问题分析", "学习能力", "行业趋势", "市场意识",
            "逻辑思维", "沟通协调能力", "创新", "抗压能力", "出差",
            "理工科", "学生干部", "软件开发", "芯片设计", "实习经验",
            "竞争力",
        ],
    },
    {
        "id": "JD4",
        "company": "大疆",
        "title": "海外销售培训生",
        "direction": "销售",
        "keywords": [
            "销售渠道", "客户开拓", "客户管理", "进销存", "市场秩序",
            "零售覆盖", "销售考核", "经营指标", "营销活动", "线索生成",
            "销售策略", "细分市场", "全渠道", "商业思维", "逻辑思维",
            "沟通协调能力", "抗压能力", "谈判能力", "国际化",
            "数据敏感", "流程思维", "端到端",
        ],
    },
    {
        "id": "JD5",
        "company": "拓竹",
        "title": "IMC整合营销",
        "direction": "营销运营",
        "keywords": [
            "产品传播", "传播素材", "内容更新", "竞品分析", "行业信息",
            "AI工具", "营销活动", "项目管理", "跨部门", "品牌营销",
            "social内容", "文案", "内容资产", "agency沟通", "自驱力",
            "多任务", "信息整理", "沟通协调能力", "英语", "项目统筹",
            "内容营销", "社交媒体", "产品上市", "KOL合作", "社媒运营",
        ],
    },
    {
        "id": "JD6",
        "company": "拓竹",
        "title": "海外KOL",
        "direction": "营销运营",
        "keywords": [
            "KOL物色", "KOL沟通", "内容共创", "全流程", "短视频",
            "创作者矩阵", "内容创意", "产品推广", "素材整理", "人群研究",
            "用户调研", "目标人群", "英语", "社交媒体", "内容创作",
            "KOL行业", "YouTube", "TikTok", "Instagram", "认真细致",
            "责任心", "沟通协调能力", "自驱力", "学习能力", "KOL运营",
            "自媒体运营", "消费电子",
        ],
    },
    {
        "id": "JD7",
        "company": "拓竹",
        "title": "海外市场营销",
        "direction": "营销运营/GTM",
        "keywords": [
            "品牌营销", "内容素材", "日常运营", "内容质量",
            "传播效果", "KOL BD", "商务谈判", "供应商管理",
            "KOL资源", "KOL运营", "资源筛选", "内容审稿", "数据分析",
            "优质内容", "竞品监测", "英语", "沟通协调能力",
            "社交媒体", "执行力", "学习能力",
            "海外经历", "消费电子", "DIY",
        ],
    },
    {
        "id": "JD8",
        "company": "拓竹",
        "title": "GTM",
        "direction": "GTM",
        "keywords": [
            "市场洞察", "消费者洞察", "宏观市场", "行业竞争", "目标消费者",
            "产品操盘", "经营目标", "产品上市", "生命周期", "销售目标",
            "渠道销售", "电商", "营销策略", "营销物料", "供应链管理",
            "销售预测", "数据分析", "商科", "工科", "英语",
            "海外经历", "逻辑思维", "消费电子", "竞争力",
        ],
    },
]

# 应用同义词合并
jds = []
for jd in raw_jds:
    normalized_kws = []
    seen = set()
    for kw in jd["keywords"]:
        canon = normalize(kw)
        if canon not in seen:
            normalized_kws.append(canon)
            seen.add(canon)
    jds.append({**jd, "keywords": normalized_kws})

# ============================================================
# 第二步：词频统计
# ============================================================

total_counter = Counter()
keyword_jds = defaultdict(set)
keyword_dirs = defaultdict(set)
dir_counter = defaultdict(Counter)

for jd in jds:
    for kw in jd["keywords"]:
        total_counter[kw] += 1
        keyword_jds[kw].add(jd["id"])
        keyword_dirs[kw].add(jd["direction"])
        dir_counter[jd["direction"]][kw] += 1

# Top25
top25 = total_counter.most_common(25)

print("=" * 72)
print("Top 25 关键词总频次表（同义词已合并）")
print("=" * 72)
print(f"{'排名':<4} {'关键词':<16} {'总频次':<6} {'出现岗位数':<10} {'覆盖方向'}")
print("-" * 72)
for i, (kw, freq) in enumerate(top25, 1):
    jd_count = len(keyword_jds[kw])
    dirs = "、".join(sorted(keyword_dirs[kw]))
    print(f"{i:<4} {kw:<16} {freq:<6} {jd_count:<10} {dirs}")

print("\n")
print("=" * 72)
print("分方向 Top8 侧重词")
print("=" * 72)

direction_groups = {
    "GTM方向": ["GTM", "GTM/销售/营销", "营销运营/GTM"],
    "销售/BD方向": ["销售/BD", "销售", "GTM/销售/营销"],
    "FAE方向": ["FAE"],
    "营销运营方向": ["营销运营", "营销运营/GTM"],
}

for group_name, dirs in direction_groups.items():
    group_counter = Counter()
    for d in dirs:
        group_counter.update(dir_counter[d])
    top8 = group_counter.most_common(8)
    print(f"\n【{group_name}】")
    print(f"  {'关键词':<16} {'频次'}")
    print(f"  {'-'*30}")
    for kw, freq in top8:
        print(f"  {kw:<16} {freq}")

# ============================================================
# 高频词筛选（频次≥3 且 岗位数≥2）
# ============================================================
print("\n")
print("=" * 72)
print("高频关键词（总频次≥3 且 出现岗位数≥2）")
print("=" * 72)
high_freq = [(kw, freq, len(keyword_jds[kw])) for kw, freq in total_counter.items()
             if freq >= 3 and len(keyword_jds[kw]) >= 2]
high_freq.sort(key=lambda x: (-x[1], -x[2]))
for kw, freq, jd_count in high_freq:
    print(f"  {kw:<16} 频次={freq}  岗位数={jd_count}")

# Top10
print("\n")
print("=" * 72)
print("Top 10 关键词（用于报告第一节）")
print("=" * 72)
for i, (kw, freq) in enumerate(top25[:10], 1):
    jd_count = len(keyword_jds[kw])
    print(f"  {i}. {kw}  频次={freq}  岗位数={jd_count}")
