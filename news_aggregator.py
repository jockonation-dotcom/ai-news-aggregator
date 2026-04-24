#!/usr/bin/env python3
import feedparser
import yaml
import json
import time
from anthropic import Anthropic
from datetime import datetime
from langdetect import detect
import os

# ========== 設定 ==========
YAML_FILE = "rss_sources.yaml"
OUTPUT_FILE = "docs/news_dashboard.html"

# ========== RSS フィード取得 ==========
def load_rss_config():
    """YAML から RSS フィード設定を読み込み"""
    with open(YAML_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config['sources']

def fetch_rss_feeds(rss_sources):
    """全 RSS フィードを取得"""
    articles = []
    
    for category, sources in rss_sources.items():
        for source_name, rss_url in sources.items():
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:3]:  # 最新 3 件
                    articles.append({
                        'category_hint': category,
                        'source': source_name,
                        'title': entry.title,
                        'url': entry.link,
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', '')[:300],
                    })
            except Exception as e:
                print(f"⚠️  {source_name}: {e}")
    
    return articles

# ========== 翻訳・分類 ==========
def detect_language(text):
    """言語判定"""
    try:
        return detect(text)
    except:
        return 'unknown'

def process_articles(articles):
    """翻訳 + カテゴリ分類を同時実行"""
    client = Anthropic()
    processed = []
    
    for i, article in enumerate(articles):
        lang = detect_language(article['title'] + " " + article['summary'])
        article['original_language'] = lang
        
        print(f"[{i+1}/{len(articles)}] {article['source']}: {lang}", end='')
        
        # 日本語の場合はスキップ
        if lang == 'ja':
            article['title_ja'] = article['title']
            article['summary_ja'] = article['summary']
            article['translated'] = False
            article['category'] = article['category_hint']
            article['relevance'] = 0.8
            processed.append(article)
            print(" ✓")
            continue
        
        # 英語など：翻訳 + 分類を同時実行
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""記事を処理してください：

【元タイトル】
{article['title']}

【元要約】
{article['summary']}

【タスク】
1. タイトルと要約を自然な日本語に翻訳
2. 以下5カテゴリのいずれかに分類（ヒント: {article['category_hint']}）

【カテゴリ】
- 01_建築AI
- 02_実務AI
- 03_海外AI本流
- 04_アートAI
- 05_偶発ネタ

JSON形式で返答してください（マークダウンなし、JSONのみ）：
{{
  "title_ja": "日本語タイトル",
  "summary_ja": "日本語要約（200字程度）",
  "category": "該当カテゴリ",
  "relevance": 0.0-1.0
}}"""
                }]
            )
            
            result_text = response.content[0].text.strip()
            result = json.loads(result_text)
            
            article['title_ja'] = result['title_ja']
            article['summary_ja'] = result['summary_ja']
            article['category'] = result['category']
            article['relevance'] = result['relevance']
            article['translated'] = True
            processed.append(article)
            print(" ✓")
            time.sleep(5)  # ← リクエスト間隔
            
        except Exception as e:
            print(f" ✗ ({e})")
            article['title_ja'] = article['title']
            article['summary_ja'] = article['summary']
            article['category'] = article['category_hint']
            article['relevance'] = 0.5
            article['translated'] = False
            processed.append(article)
    
    return processed

# ========== HTML 生成 ==========
def generate_html_dashboard(articles):
    """レスポンシブ HTML ダッシュボード生成"""
    
    # カテゴリ別にグループ化
    by_category = {}
    for article in articles:
        cat = article.get('category', 'uncategorized')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(article)
    
    # 関連度でソート
    for cat in by_category:
        by_category[cat].sort(key=lambda x: x.get('relevance', 0), reverse=True)
    
    # カテゴリ順序
    category_order = [
        '01_建築AI',
        '02_実務AI',
        '03_海外AI本流',
        '04_アートAI',
        '05_偶発ネタ',
        'uncategorized'
    ]
    
    # HTML 生成
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI ニュース統合ダッシュボード</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Yu Gothic', 'Hiragino Sans', sans-serif; }}
        .card-hover:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
        .badge-translated {{ @apply inline-block bg-green-500 text-white text-xs px-2 py-1 rounded; }}
    </style>
</head>
<body class="bg-gray-50">
    <!-- ヘッダー -->
    <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-8 px-4 sticky top-0 z-10 shadow-lg">
        <div class="max-w-6xl mx-auto">
            <h1 class="text-3xl md:text-4xl font-bold">🤖 AI ニュース統合ダッシュボード</h1>
            <p class="text-indigo-100 mt-2">建築AI × 実務AI × 海外AI本流 × アートAI</p>
            <p class="text-sm text-indigo-200 mt-1">最終更新: {datetime.now().strftime("%Y年%m月%d日 %H:%M")}</p>
        </div>
    </div>

    <!-- メインコンテンツ -->
    <div class="max-w-6xl mx-auto px-4 py-8">
"""
    
    # カテゴリごとに出力
    for category in category_order:
        if category not in by_category:
            continue
        
        items = by_category[category]
        html += f"""
        <!-- {category} セクション -->
        <div class="mb-12">
            <h2 class="text-2xl font-bold text-gray-800 border-l-4 border-indigo-600 pl-4 mb-6">
                {category}
                <span class="text-sm text-gray-500 font-normal">({len(items)}件)</span>
            </h2>
            
            <div class="grid gap-4">
"""
        
        # 記事カード
        for item in items:
            translated_badge = '<span class="badge-translated">翻訳</span>' if item.get('translated') else ''
            original_lang = f' <span class="text-xs text-gray-500">({item["original_language"]})</span>' if item.get('original_language') and item['original_language'] != 'ja' else ''
            relevance_bar = f'<div class="text-xs text-gray-500 mt-2">関連度: {int(item.get("relevance", 0) * 100)}%</div>'
            
            html += f"""
                <div class="bg-white rounded-lg p-4 md:p-6 border border-gray-200 card-hover transition-all duration-200">
                    <div class="flex flex-col md:flex-row md:justify-between md:items-start gap-2 mb-3">
                        <div class="flex-1">
                            <a href="{item['url']}" target="_blank" class="text-lg font-semibold text-indigo-600 hover:text-indigo-800 hover:underline block">
                                {item['title_ja']}
                            </a>
                        </div>
                        {translated_badge}
                    </div>
                    
                    <div class="text-xs text-gray-600 mb-3">
                        <span class="font-semibold">{item['source']}</span>
                        {original_lang}
                        <span class="mx-1">·</span>
                        <span>{item['published'][:10] if item.get('published') else 'N/A'}</span>
                    </div>
                    
                    <p class="text-gray-700 leading-relaxed mb-2">{item['summary_ja']}</p>
                    {relevance_bar}
                </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += """
    </div>

    <!-- フッター -->
    <div class="bg-gray-800 text-gray-400 text-center py-6 mt-12">
        <p class="text-sm">自動生成ニュースダッシュボード | RSS + Claude 翻訳・分類</p>
        <p class="text-xs mt-1">毎日 09:00 JST に更新</p>
    </div>
</body>
</html>
"""
    
    return html

# ========== メイン処理 ==========
if __name__ == "__main__":
    print("🚀 AI ニュース集約開始\n")
    
    # RSS フィード取得
    print("📥 RSS フィード読み込み中...")
    rss_sources = load_rss_config()
    articles = fetch_rss_feeds(rss_sources)
    print(f"✓ {len(articles)} 件の記事を取得\n")
    
    # 翻訳・分類
    print("🔄 翻訳・分類処理中...")
    processed = process_articles(articles)
    print(f"\n✓ {len(processed)} 件を処理\n")
    
    # HTML 生成
    print("📄 HTML ダッシュボード生成中...")
    os.makedirs("docs", exist_ok=True)
    html = generate_html_dashboard(processed)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✓ {OUTPUT_FILE}\n")
    
    print("✨ 完成！")
