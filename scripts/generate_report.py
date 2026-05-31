#!/usr/bin/env python3
"""
阿根廷双周报自动化生成脚本 (Argentina Bi-weekly Newsletter Generator)

基于 setup-newsletter.md 方法论：
  [1/5] 获取 RSS 新闻 → [2/5] Claude 筛选 → [3/5] 分类汇总 → [4/5] 生成 HTML → [5/5] 发布

依赖安装：
  pip install feedparser requests anthropic openpyxl beautifulsoup4

用法：
  python generate_report.py                    # 交互模式
  python generate_report.py --auto             # 全自动模式
  python generate_report.py --date 2026-05-31  # 指定截止日期

环境变量：
  ANTHROPIC_API_KEY    必需
  ANTHROPIC_BASE_URL   可选（企业代理地址）
  GITHUB_TOKEN         可选（启用 GitHub Pages 自动发布时需要）
"""

import os
import sys
import json
import shutil
import subprocess
import hashlib
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# 配置区 — 根据实际环境修改
# ============================================================

# 项目目录
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

# 输出文件路径
OUTPUT_FILE = os.path.join(REPO_DIR, "generated_newsletter.html")
INDEX_FILE = os.path.join(REPO_DIR, "index.html")
EXCEL_FILE = os.path.join(REPO_DIR, "source_status.xlsx")

# 新闻信元数据
NEWSLETTER_TITLE = "🇦🇷 Argentina Biweekly Brief"
NEWSLETTER_SLUG = "argentina_biweekly"
ISSUE_NUMBER = 1  # 每次运行后自动 +1

# GitHub Pages 配置
GITHUB_ENABLED = True
GITHUB_OWNER = "yajiewang0930-prog"
GITHUB_REPO = "argentina-newsletter"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_BRANCH = "main"

# 编辑器密码（用于 HTML 在线编辑功能）
EDITOR_PASSWORD = "didiar"
EDITOR_PASSWORD_HASH = "58f7ec1878a1fef5a516886fa8d92494d936011fad765efec36215634b98aece"

# Cloudflare Worker URL（创建 Worker 后填入）
PUBLISH_URL = "https://argentina-newsletter-save.yajie-wang0930.workers.dev"

# Claude API 配置
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

# ============================================================
# RSS 源配置
# ============================================================

RSS_SOURCES = [
    # === 宏观与政策 (Macro & Policy) ===
    {"name": "Página/12 - Economía",   "rss": "https://www.pagina12.com.ar/rss/secciones/economia/notas",  "type": "Macro & Policy"},
    {"name": "Página/12 - El País",     "rss": "https://www.pagina12.com.ar/rss/secciones/el-pais/notas",    "type": "Macro & Policy"},
    {"name": "Página/12 - Cash",        "rss": "https://www.pagina12.com.ar/rss/suplementos/cash/notas",     "type": "Macro & Policy"},
    {"name": "La Nación",               "rss": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/",         "type": "Macro & Policy"},
    {"name": "Infobae",                 "rss": "https://www.infobae.com/arc/outboundfeeds/rss/",            "type": "Macro & Policy"},

    # === 金融与信贷 (Financial & Credit) ===
    # 以下源需先验证 RSS 可用性，取消注释以启用：
    # {"name": "Ámbito Financiero",     "rss": "https://www.ambito.com/rss",                                 "type": "Financial & Credit"},
    # {"name": "El Cronista",           "rss": "https://www.cronista.com/rss",                               "type": "Financial & Credit"},
    # {"name": "Bloomberg Línea ARG",   "rss": "https://www.bloomberglinea.com/feed/",                       "type": "Financial & Credit"},

    # === 金融科技 (Fintech) ===
    {"name": "CoinTelegraph Español",   "rss": "https://es.cointelegraph.com/rss",                          "type": "Fintech"},
    # {"name": "iProUP",                "rss": "https://www.iproup.com/rss",                                 "type": "Fintech"},

    # === 国际影响 (International Impact) ===
    {"name": "MercoPress",              "rss": "https://en.mercopress.com/rss/",                            "type": "International Impact"},
]

# ============================================================
# 导入依赖（带友好错误提示）
# ============================================================

try:
    import feedparser
except ImportError:
    print("❌ 缺少依赖: pip install feedparser")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ 缺少依赖: pip install requests")
    sys.exit(1)

try:
    from anthropic import Anthropic
except ImportError:
    print("❌ 缺少依赖: pip install anthropic")
    sys.exit(1)

try:
    from openpyxl import Workbook
except ImportError:
    print("❌ 缺少依赖: pip install openpyxl")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ 缺少依赖: pip install beautifulsoup4")
    sys.exit(1)


# ============================================================
# Claude 客户端
# ============================================================

def get_claude_client():
    """初始化 Claude 客户端"""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("请设置环境变量 ANTHROPIC_API_KEY")
    kwargs = {"api_key": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        kwargs["base_url"] = ANTHROPIC_BASE_URL
    return Anthropic(**kwargs)


# ============================================================
# Step 1: 获取 RSS 新闻
# ============================================================

def fetch_rss_feeds(sources, days_back=14):
    """
    从 RSS 源抓取最近 N 天的文章。
    返回: list[dict], 每条包含 title, link, summary, published, source_name, source_type
    """
    cutoff = datetime.now() - timedelta(days=days_back)
    articles = []
    source_status = []  # 记录每个源的状态，用于 Excel

    print(f"\n{'='*60}")
    print(f"[1/5] 获取 RSS 新闻源 (最近 {days_back} 天)...")
    print(f"{'='*60}")

    for src in sources:
        name = src["name"]
        url = src["rss"]
        stype = src["type"]
        print(f"  📡 {name} ... ", end="", flush=True)

        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                print(f"⚠️ 解析失败 (可能 RSS 已失效)")
                source_status.append({"name": name, "status": "FAIL", "articles": 0, "error": "bozo"})
                continue

            count = 0
            for entry in feed.entries:
                # 解析发布日期
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])

                if pub_date and pub_date < cutoff:
                    continue  # 超过天数范围的旧闻

                articles.append({
                    "title": entry.get("title", "").strip(),
                    "link": entry.get("link", ""),
                    "summary": _clean_summary(entry.get("summary", "")),
                    "published": pub_date.isoformat() if pub_date else "",
                    "source_name": name,
                    "source_type": stype,
                })
                count += 1

            print(f"✅ {count} 篇")
            source_status.append({"name": name, "status": "OK", "articles": count, "error": ""})

        except Exception as e:
            print(f"❌ {e}")
            source_status.append({"name": name, "status": "FAIL", "articles": 0, "error": str(e)})

    total = len(articles)
    print(f"\n  📊 共获取 {total} 篇文章 (来自 {len(sources)} 个源)")
    return articles, source_status


def _clean_summary(html_text):
    """清洗 RSS summary 字段中的 HTML 标签"""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        return soup.get_text(separator=" ", strip=True)[:500]
    except Exception:
        return html_text[:500]


# ============================================================
# Step 2: Claude 筛选相关新闻
# ============================================================

FILTER_PROMPT = """Eres un analista de noticias especializado en Argentina. Revisa los siguientes artículos y filtra SOLO aquellos que sean relevantes para un informe bisemanal de economía, finanzas, fintech y políticas de Argentina.

Criterios de RELEVANCIA (INCLUIR):
- Datos macroeconómicos de Argentina (inflación, PBI, tasa de interés, tipo de cambio)
- Políticas del BCRA, Ministerio de Economía, CNV
- Noticias del sector financiero argentino (bancos, crédito, regulación)
- Industria Fintech argentina (billeteras digitales, BNPL, préstamos digitales, cripto)
- Relaciones con el FMI, comercio exterior, inversión extranjera en Argentina
- Informes de organismos internacionales sobre Argentina (FMI, Banco Mundial, CEPAL)
- Eventos políticos con impacto económico directo

Criterios de IRRELEVANCIA (EXCLUIR):
- Deportes, entretenimiento, cultura (sin impacto económico directo)
- Noticias policiales o de sucesos
- Noticias de otros países latinoamericanos sin relación directa con Argentina
- Artículos de opinión sin datos concretos

Devuelve un JSON con este formato exacto:
{
  "relevant": [
    {"title": "...", "reason": "breve razón en español (máx 15 palabras)"},
    ...
  ],
  "rejected_count": N
}

Artículos a revisar:
{articles_json}"""


def filter_with_claude(client, articles):
    """使用 Claude 筛选相关文章"""
    print(f"\n{'='*60}")
    print(f"[2/5] Claude 筛选相关新闻...")
    print(f"{'='*60}")

    if not articles:
        print("  ⚠️ 没有文章可筛选")
        return []

    # 分批处理，每批最多 50 篇
    batch_size = 50
    relevant_indices = set()

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        articles_for_prompt = [{"id": j, "title": a["title"], "source": a["source_name"]}
                               for j, a in enumerate(batch, start=i)]

        print(f"  发送 {len(batch)} 篇到 Claude 筛选...")

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": FILTER_PROMPT.format(articles_json=json.dumps(articles_for_prompt, ensure_ascii=False, indent=2))
                }]
            )

            # 解析 JSON 响应
            text = response.content[0].text
            # 提取 JSON 块
            json_start = text.find("{")
            json_end = text.rfind("}")
            if json_start >= 0 and json_end >= 0:
                result = json.loads(text[json_start:json_end + 1])
                for item in result.get("relevant", []):
                    relevant_indices.add(item.get("id", item.get("index", -1)))
                rejected = result.get("rejected_count", len(batch) - len(relevant_indices))
                print(f"  ✅ {len(result.get('relevant', []))} 篇相关, {rejected} 篇过滤")

        except Exception as e:
            print(f"  ❌ Claude 筛选出错: {e}")
            # 出错时保守保留所有文章
            for j in range(i, min(i + batch_size, len(articles))):
                relevant_indices.add(j)

    filtered = [articles[i] for i in sorted(relevant_indices) if i < len(articles)]
    print(f"\n  📊 筛选结果: {len(filtered)}/{len(articles)} 篇相关")
    return filtered


# ============================================================
# Step 3: Claude 分类汇总
# ============================================================

SUMMARIZE_PROMPT = """Eres un analista senior especializado en economía argentina. Genera un resumen bisemanal de noticias clasificadas en 4 categorías.

Para cada categoría, proporciona:
1. "summary": Un párrafo de 1-2 oraciones que capture la tendencia principal del período (en español)
2. "items": 3-5 noticias clave, cada una con:
   - "title": Título descriptivo en español (máx 80 caracteres)
   - "detail": Descripción de 1 oración con datos concretos (máx 120 caracteres)
   - "source": Nombre de la fuente
   - "link": URL del artículo original
   - "importance": "high" | "medium"

Además, proporciona:
- "key_metrics": 4 indicadores clave con sus valores actuales, tendencia (up/down/stable) y fuente
- "top_story": La noticia más importante de la quincena (título + descripción de 2 oraciones)

Categorías:
1. macro: Macro y Política (GDP, inflación, tasa de interés, política fiscal/monetaria, reformas)
2. financial: Finanzas y Crédito (bancos, préstamos, regulación financiera, BCRA)
3. fintech: Fintech (billeteras digitales, BNPL, cripto, pagos digitales, startups)
4. international: Impacto Internacional (FMI, comercio exterior, inversión extranjera, geopolítica)

Devuelve SOLO un JSON válido con esta estructura exacta:
{
  "top_story": {"title": "...", "description": "..."},
  "key_metrics": [
    {"label": "Inflación mensual", "value": "X.X%", "trend": "down", "source": "INDEC"},
    {"label": "Tasa de referencia BCRA", "value": "XX%", "trend": "down", "source": "BCRA"},
    {"label": "Brecha cambiaria", "value": "XX%", "trend": "up", "source": "Ámbito"},
    {"label": "Confianza del consumidor", "value": "XX.X", "trend": "stable", "source": "UTDT"}
  ],
  "macro": {"summary": "...", "items": [{"title": "...", "detail": "...", "source": "...", "link": "...", "importance": "high"}]},
  "financial": {"summary": "...", "items": [...]},
  "fintech": {"summary": "...", "items": [...]},
  "international": {"summary": "...", "items": [...]}
}

Artículos a resumir (ya filtrados por relevancia):
{articles_json}"""


def summarize_with_claude(client, articles):
    """使用 Claude 分类汇总"""
    print(f"\n{'='*60}")
    print(f"[3/5] Claude 分类汇总...")
    print(f"{'='*60}")

    if not articles:
        print("  ⚠️ 没有文章可汇总")
        return _empty_summary()

    articles_for_prompt = []
    for i, a in enumerate(articles):
        articles_for_prompt.append({
            "id": i,
            "title": a["title"],
            "source": a["source_name"],
            "category": a["source_type"],
            "link": a["link"],
        })

    print(f"  发送 {len(articles_for_prompt)} 篇到 Claude 汇总...")

    try:
        client_obj = client
        response = client_obj.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": SUMMARIZE_PROMPT.format(
                    articles_json=json.dumps(articles_for_prompt, ensure_ascii=False, indent=2)
                )
            }]
        )

        text = response.content[0].text
        json_start = text.find("{")
        json_end = text.rfind("}")
        if json_start >= 0 and json_end >= 0:
            result = json.loads(text[json_start:json_end + 1])
            print(f"  ✅ 汇总完成")
            print(f"    头条: {result.get('top_story', {}).get('title', 'N/A')}")
            for cat in ["macro", "financial", "fintech", "international"]:
                items = result.get(cat, {}).get("items", [])
                print(f"    {cat}: {len(items)} 条")
            return result
        else:
            raise ValueError("无法从 Claude 响应中提取 JSON")

    except Exception as e:
        print(f"  ❌ Claude 汇总出错: {e}")
        return _empty_summary()


def _empty_summary():
    """返回空的汇总结构"""
    return {
        "top_story": {"title": "Datos insuficientes", "description": "No se encontraron noticias relevantes en este período."},
        "key_metrics": [
            {"label": "Inflación mensual", "value": "N/D", "trend": "stable", "source": "INDEC"},
            {"label": "Tasa de referencia BCRA", "value": "N/D", "trend": "stable", "source": "BCRA"},
            {"label": "Brecha cambiaria", "value": "N/D", "trend": "stable", "source": "Ámbito"},
            {"label": "Confianza del consumidor", "value": "N/D", "trend": "stable", "source": "UTDT"},
        ],
        "macro": {"summary": "No se encontraron noticias en esta categoría.", "items": []},
        "financial": {"summary": "No se encontraron noticias en esta categoría.", "items": []},
        "fintech": {"summary": "No se encontraron noticias en esta categoría.", "items": []},
        "international": {"summary": "No se encontraron noticias en esta categoría.", "items": []},
    }


# ============================================================
# Step 4: 生成 HTML 报告
# ============================================================

HTML_TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "references", "newsletter-template.html"
)

METRIC_CARD_TEMPLATE = """
<div class="metric-card bg-white rounded-xl shadow-sm p-4 text-center">
    <p class="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
    <p class="text-2xl font-bold text-gray-800 mb-1">{value}</p>
    <p class="text-xs {trend_class}">{trend_icon} {trend_text}</p>
    <p class="text-xs text-gray-300 mt-1">Fuente: {source}</p>
</div>"""

NEWS_ITEM_TEMPLATE = """
<li class="news-card bg-gray-50 rounded-lg p-3" contenteditable="false">
    <div class="flex items-start justify-between gap-2">
        <div class="flex-1">
            <h3 class="font-semibold text-gray-800 text-sm mb-1">{title}</h3>
            <p class="text-gray-500 text-xs mb-1">{detail}</p>
            <span class="text-xs text-gray-400">{source}</span>
        </div>
        <a href="{link}" target="_blank" rel="noopener" class="text-gray-300 hover:text-blue-500 flex-shrink-0">
            <i class="fa fa-external-link"></i>
        </a>
    </div>
</li>"""


def _get_trend_html(trend):
    """将 trend 值映射为 HTML 展示"""
    mapping = {
        "down": ("text-green-500", "↓", "Bajando"),
        "up": ("text-red-500", "↑", "Subiendo"),
        "stable": ("text-gray-400", "→", "Estable"),
    }
    return mapping.get(trend, ("text-gray-400", "→", "Estable"))


def generate_html(summary, date_start, date_end, issue_number):
    """基于模板和汇总数据生成 HTML 报告"""
    print(f"\n{'='*60}")
    print(f"[4/5] 生成 HTML 报告...")
    print(f"{'='*60}")

    # 读取模板
    if os.path.exists(HTML_TEMPLATE_PATH):
        with open(HTML_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        print("  ⚠️ 模板文件未找到，使用内置模板")
        html = _get_builtin_template()

    # 日期格式化
    date_range = f"{date_start.strftime('%d/%m/%Y')} – {date_end.strftime('%d/%m/%Y')}"
    gen_date = datetime.now().strftime("%d/%m/%Y %H:%M")

    # 替换元数据
    html = html.replace("{{NEWSLETTER_TITLE}}", NEWSLETTER_TITLE)
    html = html.replace("{{DATE_RANGE}}", date_range)
    html = html.replace("{{ISSUE_NUMBER}}", str(issue_number))
    html = html.replace("{{GENERATION_DATE}}", gen_date)
    html = html.replace("{{DATA_AS_OF}}", date_end.strftime("%d/%m/%Y"))
    html = html.replace("{{NEWSLETTER_SLUG}}", NEWSLETTER_SLUG)

    # 生成关键指标卡片
    metric_cards = ""
    for m in summary.get("key_metrics", []):
        trend_class, trend_icon, trend_text = _get_trend_html(m.get("trend", "stable"))
        metric_cards += METRIC_CARD_TEMPLATE.format(
            label=m.get("label", ""),
            value=m.get("value", "N/D"),
            trend_class=trend_class,
            trend_icon=trend_icon,
            trend_text=trend_text,
            source=m.get("source", ""),
        )
    html = html.replace("{{METRIC_CARDS}}", metric_cards)

    # 生成各分类新闻
    for cat_key, placeholder, summary_key in [
        ("macro", "{{MACRO_SUMMARY}}", "{{MACRO_NEWS_ITEMS}}"),
        ("financial", "{{FINANCIAL_SUMMARY}}", "{{FINANCIAL_NEWS_ITEMS}}"),
        ("fintech", "{{FINTECH_SUMMARY}}", "{{FINTECH_NEWS_ITEMS}}"),
        ("international", "{{INTERNATIONAL_SUMMARY}}", "{{INTERNATIONAL_NEWS_ITEMS}}"),
    ]:
        cat_data = summary.get(cat_key, {})
        html = html.replace(placeholder, cat_data.get("summary", ""))

        items_html = ""
        for item in cat_data.get("items", []):
            items_html += NEWS_ITEM_TEMPLATE.format(
                title=item.get("title", ""),
                detail=item.get("detail", ""),
                source=item.get("source", ""),
                link=item.get("link", "#"),
            )
        if not items_html:
            items_html = '<li class="text-gray-400 text-sm p-3">No hay noticias en esta categoría para este período.</li>'
        html = html.replace(summary_key, items_html)

    # 编辑器密码哈希（如果配置了）
    editor_hash = ""
    if EDITOR_PASSWORD:
        editor_hash = hashlib.sha256(EDITOR_PASSWORD.encode()).hexdigest()
    html = html.replace("{{EDITOR_HASH}}", editor_hash)
    html = html.replace("{{PUBLISH_URL}}", PUBLISH_URL)

    # 写入文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  ✅ HTML 已生成: {OUTPUT_FILE}")
    return html


def _get_builtin_template():
    """内置 HTML 模板（当外部模板文件不可用时）"""
    return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{NEWSLETTER_TITLE}} | {{DATE_RANGE}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css">
</head>
<body class="bg-gray-50 font-sans">
    <div class="max-w-4xl mx-auto px-4 py-6">
        <header class="text-center mb-8">
            <div style="background:linear-gradient(135deg,#75AADB,#4A8BC2,#F4B43A)" class="rounded-2xl p-8 text-white">
                <div style="font-size:2rem">🇦🇷</div>
                <h1 class="text-3xl font-bold mb-2">{{NEWSLETTER_TITLE}}</h1>
                <p class="text-white/80 text-lg">{{DATE_RANGE}} · Edición #{{ISSUE_NUMBER}}</p>
                <p class="text-white/60 text-sm mt-2">Generado el {{GENERATION_DATE}}</p>
            </div>
        </header>
        <section class="mb-10">
            <h2 class="text-lg font-semibold text-gray-500 uppercase tracking-wide mb-4">📊 Indicadores Clave</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">{{METRIC_CARDS}}</div>
        </section>
        <section class="mb-10"><h2 class="text-xl font-bold mb-4">📈 Macro y Política</h2>
            <div class="bg-white rounded-xl shadow-sm p-5"><p class="text-gray-600 text-sm mb-3">{{MACRO_SUMMARY}}</p><ul class="space-y-3">{{MACRO_NEWS_ITEMS}}</ul></div>
        </section>
        <section class="mb-10"><h2 class="text-xl font-bold mb-4">🏦 Finanzas y Crédito</h2>
            <div class="bg-white rounded-xl shadow-sm p-5"><p class="text-gray-600 text-sm mb-3">{{FINANCIAL_SUMMARY}}</p><ul class="space-y-3">{{FINANCIAL_NEWS_ITEMS}}</ul></div>
        </section>
        <section class="mb-10"><h2 class="text-xl font-bold mb-4">💳 Fintech</h2>
            <div class="bg-white rounded-xl shadow-sm p-5"><p class="text-gray-600 text-sm mb-3">{{FINTECH_SUMMARY}}</p><ul class="space-y-3">{{FINTECH_NEWS_ITEMS}}</ul></div>
        </section>
        <section class="mb-10"><h2 class="text-xl font-bold mb-4">🌐 Impacto Internacional</h2>
            <div class="bg-white rounded-xl shadow-sm p-5"><p class="text-gray-600 text-sm mb-3">{{INTERNATIONAL_SUMMARY}}</p><ul class="space-y-3">{{INTERNATIONAL_NEWS_ITEMS}}</ul></div>
        </section>
        <footer class="border-t pt-6 mt-12 text-center text-sm text-gray-400">
            <p>{{NEWSLETTER_TITLE}} · {{DATE_RANGE}}</p>
            <p>Este informe es una recopilación automatizada con fines informativos.</p>
        </footer>
    </div>
</body>
</html>"""


# ============================================================
# Step 5: 生成 Excel 源状态报告 + 发布到 GitHub Pages
# ============================================================

def generate_excel(source_status):
    """生成源状态 Excel 报告"""
    print(f"\n  📊 生成源状态报告...")

    wb = Workbook()
    ws = wb.active
    ws.title = "Source Status"

    # 表头
    ws.append(["Source Name", "Status", "Articles Fetched", "Error"])
    for status in source_status:
        ws.append([status["name"], status["status"], status["articles"], status["error"]])

    # 自动调整列宽
    for col in ["A", "B", "C", "D"]:
        ws.column_dimensions[col].width = 25

    wb.save(EXCEL_FILE)
    print(f"  ✅ Excel 已生成: {EXCEL_FILE}")


def publish_to_github():
    """将生成的 HTML 和 Excel 推送到 GitHub Pages"""
    if not GITHUB_ENABLED:
        print(f"\n  ⏭️ GitHub Pages 未启用，跳过发布。")
        return

    print(f"\n{'='*60}")
    print(f"[5/5] 发布到 GitHub Pages...")
    print(f"{'='*60}")

    if not GITHUB_TOKEN:
        print("  ❌ 缺少 GITHUB_TOKEN 环境变量")
        return

    try:
        # 复制 output → index.html
        shutil.copy2(OUTPUT_FILE, INDEX_FILE)

        # Git 操作
        subprocess.run(["git", "-C", REPO_DIR, "add", "index.html", "source_status.xlsx"], check=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", f"Newsletter {date_str}"], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "push", "origin", GITHUB_BRANCH], check=True)

        print(f"  ✅ 已推送到 GitHub")
        print(f"  🌐 网站将在约 1 分钟后更新: https://{GITHUB_OWNER}.github.io/{GITHUB_REPO}/")

    except subprocess.CalledProcessError as e:
        print(f"  ❌ Git 操作失败: {e}")
        print(f"  提示: 确认已配置 git remote 和 GitHub Token")


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="阿根廷双周报自动生成器")
    parser.add_argument("--auto", action="store_true", help="全自动模式（不交互）")
    parser.add_argument("--date", type=str, help="截止日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--days", type=int, default=14, help="覆盖天数（默认 14）")
    parser.add_argument("--issue", type=int, help="期号（默认自动读取+1）")
    args = parser.parse_args()

    # 确定日期范围
    end_date = datetime.now()
    if args.date:
        try:
            end_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ 日期格式错误: {args.date}，请使用 YYYY-MM-DD")
            sys.exit(1)
    start_date = end_date - timedelta(days=args.days)

    # 确定期号
    global ISSUE_NUMBER
    if args.issue:
        ISSUE_NUMBER = args.issue
    else:
        # 尝试从已有文件读取
        issue_file = os.path.join(REPO_DIR, ".issue_number")
        if os.path.exists(issue_file):
            with open(issue_file, "r") as f:
                ISSUE_NUMBER = int(f.read().strip()) + 1

    print(f"\n{'='*60}")
    print(f"  {NEWSLETTER_TITLE}")
    print(f"  日期范围: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
    print(f"  期号: #{ISSUE_NUMBER}")
    print(f"{'='*60}")

    # 验证 API Key
    if not ANTHROPIC_API_KEY:
        print("\n❌ 请设置环境变量 ANTHROPIC_API_KEY")
        print("   export ANTHROPIC_API_KEY=sk-ant-YOUR_KEY")
        sys.exit(1)

    # 初始化 Claude 客户端
    client = get_claude_client()

    # Step 1: 获取 RSS 新闻
    articles, source_status = fetch_rss_feeds(RSS_SOURCES, days_back=args.days)

    # Step 2: Claude 筛选
    filtered = filter_with_claude(client, articles)

    # Step 3: Claude 汇总
    summary = summarize_with_claude(client, filtered)

    # Step 4: 生成 HTML
    html = generate_html(summary, start_date, end_date, ISSUE_NUMBER)

    # Step 5: 生成 Excel + 发布
    generate_excel(source_status)
    publish_to_github()

    # 保存期号
    issue_file = os.path.join(REPO_DIR, ".issue_number")
    with open(issue_file, "w") as f:
        f.write(str(ISSUE_NUMBER))

    # 完成报告
    print(f"\n{'='*60}")
    print(f"  ✅ 阿根廷双周报 #{ISSUE_NUMBER} 生成完成!")
    print(f"  📄 HTML: {OUTPUT_FILE}")
    print(f"  📊 Excel: {EXCEL_FILE}")
    print(f"  📅 日期范围: {start_date.strftime('%d/%m/%Y')} – {end_date.strftime('%d/%m/%Y')}")
    print(f"  📰 新闻来源: {len(RSS_SOURCES)} 个源 → {len(articles)} 篇 → {len(filtered)} 篇相关")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
