# 阿根廷新闻 RSS 源配置

> 本文档提供预设的阿根廷新闻 RSS 源列表，供 Python 自动化脚本使用。
> 最后验证日期：2026-05-31

## 源列表

### 宏观经济与政策 (Macro & Policy)

| # | 名称 | RSS URL | 语言 | 备注 |
|---|------|---------|------|------|
| 1 | Página/12 - Economía | `https://www.pagina12.com.ar/rss/secciones/economia/notas` | ES | 经济新闻专区，偏左翼视角 |
| 2 | Página/12 - El País | `https://www.pagina12.com.ar/rss/secciones/el-pais/notas` | ES | 国内政治动态 |
| 3 | Página/12 - Cash (经济副刊) | `https://www.pagina12.com.ar/rss/suplementos/cash/notas` | ES | 深度经济分析 |
| 4 | La Nación | `https://www.lanacion.com.ar/arc/outboundfeeds/rss/` | ES | 阿根廷第一大报，综合新闻 |
| 5 | Infobae | `https://www.infobae.com/arc/outboundfeeds/rss/` | ES | 综合新闻，数字媒体 |
| 6 | BCRA (央行) 新闻页 | 无 RSS，需手动抓取 `https://www.bcra.gob.ar/Noticias/Noticias.asp` | ES | 央行官方公告 |
| 7 | INDEC (统计局) | 无 RSS，需手动抓取 `https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31` | ES | 官方经济数据发布 |

### 金融与信贷 (Financial & Credit)

| # | 名称 | RSS URL | 语言 | 备注 |
|---|------|---------|------|------|
| 8 | Ámbito Financiero | 待确认 — 尝试 URL: `https://www.ambito.com/rss` | ES | 阿根廷核心财经媒体 |
| 9 | El Cronista | 待确认 — 尝试 URL: `https://www.cronista.com/rss` | ES | 财经日报 |
| 10 | El Economista (Argentina) | 待确认 — 尝试 URL: `https://www.eleconomista.com.ar/rss` | ES | 经济金融新闻 |
| 11 | Bloomberg Línea Argentina | 待确认 — 尝试: `https://www.bloomberglinea.com/feed/` | ES | 彭博社拉美财经新闻 |
| 12 | Reuters Argentina | 待确认 — 搜索: `https://www.reuters.com/places/argentina` | EN | 路透社阿根廷报道 |

### 金融科技 (Fintech)

| # | 名称 | RSS URL | 语言 | 备注 |
|---|------|---------|------|------|
| 13 | iProUP | 待确认 — 尝试 URL: `https://www.iproup.com/rss` | ES | 阿根廷科技/Fintech 媒体 |
| 14 | Cámara Fintech Argentina | 无 RSS — 抓取: `https://camarafintech.com.ar/` | ES | Fintech 行业动态 |
| 15 | CoinTelegraph (Español) | `https://es.cointelegraph.com/rss` | ES | 加密/区块链，拉美视角 |

### 国际影响 (International Impact)

| # | 名称 | RSS URL | 语言 | 备注 |
|---|------|---------|------|------|
| 16 | IMF Argentina Page | 无 RSS — 抓取: `https://www.imf.org/en/Countries/ARG` | EN | IMF 对阿根廷的评估 |
| 17 | World Bank Argentina | 无 RSS — 抓取: `https://www.worldbank.org/en/country/argentina` | EN | 世行阿根廷项目 |
| 18 | MercoPress | `https://en.mercopress.com/rss/` | EN | 南南美独立新闻 |
| 19 | BNamericas | 待确认 — 需 API key | EN | 拉美矿业/能源/基建 |

## Google News 替代方案（RSS 已停用，使用以下方式）

由于 Google News 于 2012 年正式停用 RSS 订阅，推荐以下替代方案：

### 方案 A：使用 RSS.app 生成自定义 Feed

在 [rss.app](https://rss.app) 中可基于以下 Google News 搜索生成 RSS：
- 阿根廷经济：`https://news.google.com/search?q=Argentina+econom%C3%ADa&hl=es-419`
- 阿根廷 Fintech：`https://news.google.com/search?q=Argentina+fintech+cr%C3%A9dito&hl=es-419`
- 阿根廷央行：`https://news.google.com/search?q=BCRA+Banco+Central+Argentina&hl=es-419`

### 方案 B：使用 NewsAPI

注册免费 API Key，以编程方式拉取阿根廷相关新闻：
```
https://newsapi.org/v2/everything?q=Argentina+economy&language=es&sortBy=publishedAt
```

### 方案 C：使用 Feed43 网页转 RSS

对于无 RSS 的网站（如 BCRA、INDEC），可通过 [feed43.com](https://feed43.com) 将静态网页转为 RSS Feed。

## Python 脚本中的 RSS_SOURCES 配置

```python
RSS_SOURCES = [
    # === 宏观与政策 ===
    {"name": "Página/12 - Economía",    "rss": "https://www.pagina12.com.ar/rss/secciones/economia/notas",   "type": "Macro & Policy"},
    {"name": "Página/12 - El País",      "rss": "https://www.pagina12.com.ar/rss/secciones/el-pais/notas",     "type": "Macro & Policy"},
    {"name": "Página/12 - Cash",         "rss": "https://www.pagina12.com.ar/rss/suplementos/cash/notas",      "type": "Macro & Policy"},
    {"name": "La Nación",                "rss": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/",          "type": "Macro & Policy"},
    {"name": "Infobae",                  "rss": "https://www.infobae.com/arc/outboundfeeds/rss/",             "type": "Macro & Policy"},

    # === 金融与信贷 ===
    # （以下需先验证 RSS 可用性）
    # {"name": "Ámbito Financiero",     "rss": "https://www.ambito.com/rss",                                  "type": "Financial & Credit"},
    # {"name": "El Cronista",           "rss": "https://www.cronista.com/rss",                               "type": "Financial & Credit"},
    # {"name": "Bloomberg Línea ARG",   "rss": "https://www.bloomberglinea.com/feed/",                       "type": "Financial & Credit"},

    # === 金融科技 ===
    # {"name": "iProUP",                "rss": "https://www.iproup.com/rss",                                 "type": "Fintech"},
    {"name": "CoinTelegraph Español",    "rss": "https://es.cointelegraph.com/rss",                           "type": "Fintech"},

    # === 国际影响 ===
    {"name": "MercoPress",               "rss": "https://en.mercopress.com/rss/",                             "type": "International Impact"},
]
```

## 注意事项

1. **RSS 源稳定性**：阿根廷新闻网站的 RSS 可能随时变更或停用。建议每次运行前用 `feedparser` 的 `bozo` 标记检查 feed 是否有效。
2. **编码问题**：阿根廷西班牙语 RSS 可能使用 ISO-8859-1 编码（而非 UTF-8），Python 脚本需做好编码处理。
3. **频率控制**：建议每两周运行一次（双周报），避免过频触发反爬。
4. **数据补充**：INDEC、BCRA 等官方源无 RSS 时，应通过 WebSearch 或 WebFetch 手动补充核心数据。
5. **多视角平衡**：建议包含不同政治倾向的媒体来源，如 Página/12（中左）和 La Nación（中右）。
