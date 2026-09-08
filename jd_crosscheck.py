#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交叉校验：纯Python n-gram频次统计（不依赖jieba）
从JD原文提取2-6字中文片段，统计文档频率，
验证手工提取的Top词是否有遗漏。
"""
import re
from collections import Counter, defaultdict

with open("/app/data/所有对话/主对话/jd_corpus_1787927771603_0_3nsm.md", "r", encoding="utf-8") as f:
    raw = f.read()

# 按SOURCE切分成8份文档
docs = re.split(r'### SOURCE:', raw)[1:]  # 第一个是空
print(f"文档数: {len(docs)}")

# 停用片段（无意义的高频组合）
stop_substrings = set("""
的 了 和 与 及 在 是 有 对 等 中 为 以 到 从 被 把 让 向 这 那 你 我 他 她 它 们 个 之 于 上 下 不 也 都 就 还 而 但 并 或 且 如 所 其 该 各 每 某 另 此 因 由 应 将 能 可 要 会 来 去 做 说 看 想 知道 觉得 比如 包括 通过 进行 负责 相关 工作 能力 要求 经验 优先 岗位 职责 任职 公司 团队 业务 项目 产品 客户 市场 渠道 销售 营销 品牌
具备 能够 以及 等相关 相关专业 专业优先 有经验 有较强 较强 良好 优秀 杰出 敏锐 持续 不断 深入 一定 较大 较强 相关 等岗位 岗位 岗位职责 岗位要求 任职要求 原文 标题 业务方向 业务定位 加分项 薪资 福利 学历 地域 专业 截图 未显示 显示 范围 常规 估 元 天 含 系统 导师 跨部门 轮岗 培训 培训生 管培 管培生 实习 实习生 经理 负责人 参与 协助 支持 主导 开展 制定 推动 实现 提升 构建 打造 协同 协调 管理 运营 建设 拓展 开拓 维护 负责 包括 以及 等的 工作
""".split())

# 对每个文档提取2-6字的连续中文片段
doc_ngrams = []
for doc in docs:
    # 去掉markdown/英文/数字/标点，只保留中文
    chinese = re.sub(r'[^\u4e00-\u9fff]+', ' ', doc)
    ngrams = set()
    for n in range(2, 7):
        for i in range(len(chinese) - n + 1):
            gram = chinese[i:i+n]
            if ' ' in gram:
                continue
            # 过滤包含停用词的
            if any(sw in gram for sw in stop_substrings):
                continue
            ngrams.add(gram)
    doc_ngrams.append(ngrams)

# 文档频率：出现在多少份JD中
df_counter = Counter()
for ngrams in doc_ngrams:
    for g in ngrams:
        df_counter[g] += 1

# 词频（总出现次数）
tf_counter = Counter()
for doc in docs:
    chinese = re.sub(r'[^\u4e00-\u9fff]+', ' ', doc)
    for n in range(2, 7):
        for i in range(len(chinese) - n + 1):
            gram = chinese[i:i+n]
            if ' ' not in gram and not any(sw in gram for sw in stop_substrings):
                tf_counter[gram] += 1

# 输出文档频率>=2且词频>=3的高频片段（这些是跨JD的共性词）
print("\n" + "=" * 70)
print("n-gram 交叉校验：跨文档高频片段（文档频率≥2，词频≥3）")
print("=" * 70)
candidates = [(g, tf_counter[g], df_counter[g]) for g in df_counter if df_counter[g] >= 2 and tf_counter[g] >= 3]
candidates.sort(key=lambda x: (-x[2], -x[1]))
for g, tf, df in candidates:
    # 过滤掉太短或明显是词组碎片的
    print(f"  {g:<12} 词频={tf:<4} 文档数={df}")
