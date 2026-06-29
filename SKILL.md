---
name: argentina-biweekly-newsletter
description: 用于生成阿根廷双周报（Argentina Biweekly Brief）。当用户说"生成阿根廷最新双周报"、"阿根廷双周报"、"Argentina newsletter"、"更新阿根廷周报"时触发。自动搜索近两周阿根廷新闻 → 筛选 → 按4大分类汇总 → 生成全英文 HTML 报告 → 推送到 GitHub Pages。报告标题简练清晰，每条新闻正文 100-150 词。
---

# 阿根廷双周报 Skill

## 1. 触发场景

用户说出以下任一表述时，直接按本 skill 流程执行，无需额外确认：

- "生成阿根廷最新双周报"
- "生成阿根廷双周报"
- "Argentina biweekly brief"
- "更新阿根廷周报"

## 2. 核心工作流（5 步，一步到底）

```
[1/5] WebSearch 搜索 → [2/5] 筛选 → [3/5] 汇总 → [4/5] 生成 HTML → [5/5] 推送 GitHub Pages
```

**重要：5 步连续执行，中间不打断、不确认，直到推送完成。**

### Step 1：搜索新闻源（6 维度并行搜索）

使用 WebSearch 工具同时搜索以下 6 个维度（英文关键词），每个维度 1 次搜索：

| # | 维度 | 搜索关键词 | 优先级 |
|---|------|-----------|--------|
| 1 | 宏观经济 | `Argentina economía inflación [当前月份] 2026` | ⭐⭐⭐ |
| 2 | 货币政策 | `Argentina BCRA tasa de interés política monetaria [当前月份] 2026` | ⭐⭐⭐ |
| 3 | 金融科技 | `Argentina fintech crédito digital noticias [当前月份] 2026` | ⭐⭐⭐ |
| 4 | 国际/IMF | `Argentina IMF FMI acuerdo negociaciones 2026` | ⭐⭐⭐ |
| 5 | 汇率/市场 | `Argentina dólar blue brecha cambiaria riesgo país [当前月份] 2026` | ⭐⭐⭐ |
| 6 | 信贷行业 | `Argentina crédito bancario préstamos personales crecimiento 2026` | ⭐⭐ |

如果首轮搜索结果不足，补充搜索：
- `Argentina Mercado Pago Ualá Naranja X billetera digital noticias 2026`
- `Argentina comercio exterior inversión extranjera RIGI 2026`
- `Argentina índice confianza consumidor UTDT [当前月份] 2026`

### Step 2：筛选（在脑内完成）

从搜索结果中筛掉：
- 纯体育/娱乐/文化
- 与阿根廷无关的拉美新闻
- 重复报道（保留最权威来源）
- 超过 3 周的旧闻

保留 16-20 条高相关新闻。

### Step 3：分类汇总

将新闻归入 4 大分类，**每个分类输出**：

```
分类标题（英文，简练）
1 句话 section summary
4 条新闻，每条包含：
  - 标题：英文，简练清晰，12 词以内
  - 正文：英文，100-150 词，包含具体数据、归因分析、来源引用
  - 来源链接：每条的 source span 末尾必须包含至少一个可点击的 `<a href="..." target="_blank">Read source →</a>` 链接，指向搜索时找到的实际原文 URL
  - 重要性标签：high / medium
```

4 大分类固定为：

| 分类 | 覆盖内容 |
|------|---------|
| **Macro & Policy** | GDP、通胀、利率、财政、货币政策、政治动态、RIGI |
| **Financial & Credit** | 信贷数据、银行动态、不良率、利率变化、监管新规 |
| **Fintech** | 数字钱包、支付、BNPL、虚拟银行、加密、监管 |
| **International Impact** | 外资、贸易、IMF、Mercosur、国际评级 |

**额外输出**：
- 1 条 **Top Story**（最重大新闻，150 词以内正文）
- 4 个 **Key Indicators**（月度通胀、基准利率、汇率差距、消费者信心）
- **Executive Summary**：Tailwinds 5 条 + Headwinds 5 条
- **Key Data Table**：14 行指标一览表（Indicator / Value / Trend / Source）

### Step 4：生成全英文 HTML 报告

直接使用 `Write` 工具写出 `generated_newsletter.html`。

**报告规范**：

| 项目 | 规范 |
|------|------|
| 语言 | **全英文** |
| 标题 | `Argentina Biweekly Brief`（不加副标题） |
| 日期格式 | `May 18 – 31, 2026 · Issue #N` |
| 新闻标题 | 简练清晰，12 词以内 |
| 新闻正文 | **100-150 词**，包含数据+分析+来源 |
| 新闻源链接 | 每条底部包含 `<a href="URL" target="_blank" class="text-blue-500 hover:underline">Read source →</a>`，指向搜索时找到的实际原文 URL |
| 指标卡片 | 4 个：Monthly Inflation / Reference Rate / FX Spread / Consumer Confidence |
| 执行摘要 | Tailwinds（5 条）+ Headwinds（5 条） |
| 数据表 | 14 行，表头：Indicator / Value / Trend / Source |

**样式**：
- Tailwind CDN：`<script src="https://cdn.tailwindcss.com"></script>`
- Font Awesome：`https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css`
- 阿根廷蓝金渐变色 header
- 4 色分类标签（蓝/绿/紫/橙）
- 响应式布局（grid-cols-2 md:grid-cols-4）

### Step 5：推送到 GitHub Pages

生成报告后，自动执行：

```bash
cp generated_newsletter.html index.html
git add index.html
git commit -m "Argentina Biweekly Brief #N — [日期范围]"
git push origin main
```

使用的仓库配置：
- Owner: `yajiewang0930-prog`
- Repo: `argentina-newsletter`
- Branch: `main`
- 网站地址: `https://yajiewang0930-prog.github.io/argentina-newsletter/`

推送完成后告知用户网站地址，提示约 1 分钟后生效。

## 3. 报告质量标准

### 必须包含的数据点

每期报告至少覆盖以下指标（标注 as of 日期）：

| 指标 | 来源 |
|------|------|
| Monthly Inflation (latest estimate) | INDEC / Consultoras |
| Reference Rate (TAMAR) | BCRA REM |
| FX Spread (Blue vs Official) | Ámbito / DolarHoy |
| Consumer Confidence (ICC) | UTDT |
| Sovereign Risk (EMBI+) | JP Morgan |
| Gross Intl. Reserves | BCRA |
| Household NPL Ratio | BCRA |
| Personal Loan NPL Ratio | BCRA |
| Fintech Credit NPL Ratio | IMF / BCRA |
| Credit-to-GDP | BCRA |
| RIGI Investment Commitments | Min. Economía |

### 新闻正文写作规范

每条新闻 100-150 词，结构：
1. **Lead sentence**：发生了什么 + 具体数据
2. **Context**：为什么重要，与之前趋势的对比
3. **Analysis**：影响、归因、后续风险
4. **Source attribution**：数据/观点来源

### 数据时效性

- 所有数据标明 "as of YYYY-MM-DD"
- 宏观数据标注发布日期
- 汇率标注取值日期
- 预估数据标注 "est."

## 4. 当前配置

| 配置项 | 值 |
|--------|-----|
| 报告标题 | Argentina Biweekly Brief |
| 报告语言 | English |
| GitHub Owner | yajiewang0930-prog |
| GitHub Repo | argentina-newsletter |
| GitHub Pages URL | https://yajiewang0930-prog.github.io/argentina-newsletter/ |
| 默认时间范围 | 过去 14 天 |
| 新闻条数 | 16 条（4 分类 × 4 条） |
| 正文词数 | 100-150 words |

## 5. 生成完成后输出

报告生成完成后，向用户展示：
1. 📄 本地文件路径
2. 🌐 GitHub Pages URL
3. 📊 本期摘要（一个简洁的表格，4 行 × 核心发现）
4. 🟢🔴 Tailwinds / Headwinds 各 5 条

## 6. 参考资料

- [RSS 源配置](references/rss-sources.md) — 预设 RSS 源（用于 Python 自动化脚本）
- [HTML 模板](references/newsletter-template.html) — 带编辑功能的完整模板
- [Python 自动化脚本](scripts/generate_report.py) — RSS 抓取 + Claude API 筛选汇总 + 发布
- [setup-newsletter.md](../setup-newsletter.md) — 原始系统搭建指南
