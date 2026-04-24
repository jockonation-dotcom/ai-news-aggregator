#!/usr/bin/env python3
import feedparser
import yaml
import json
import os
import requests
from datetime import datetime
from langdetect import detect

YAML_FILE = "rss_sources.yaml"
OUTPUT_FILE = "docs/news_dashboard.html"

def load_rss_config():
    with open(YAML_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config['sources']

def fetch_rss_feeds(rss_sources):
    articles = []
    for category, sources in rss_sources.items():
        for source_name, rss_url in sources.items():
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:1]:
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

def detect_language(text):
    try:
        return detect(text)
    except:
        return 'unknown'

def translate_to_japanese(text):
    """Google Translate API REST を使用して日本語に翻訳"""
    try:
        api_key = os.environ.get('GOOGLE_TRANSLATE_API_KEY')
        url = "https://translation.googleapis.com/language/translate/v2"
        
        params = {
            'key': api_key,
            'q': text,
            'target': 'ja'
        }
        
        response = requests.post(url, data=params)
        result = response.json()
        
        if 'data' in result and 'translations' in result['data']:
            return result['data']['translations'][0]['translatedText']
        else:
            return text
    except Exception as e:
        print(f"翻訳エラー: {e}")
        return text

def classify_category(title, summary, hint):
    """簡易分類：ヒント + キーワードマッチング"""
    text = (title + " " + summary).lower()
    
    if '建築' in text or '建設' in text:
        return '01_建築AI'
    elif '実務' in text or 'ビジネス' in text or 'マーケティング' in text:
        return '02_実務AI'
    elif hint in ['03_海外AI本流', '海外AI本流']:
        return '03_海外AI本流'
    elif 'アート' in text or 'デザイン' in text or 'クリエイティブ' in text:
        return '04_アートAI'
    else:
        return '05_偶発ネタ'

def process_articles(articles):
    """翻訳と分類を実行"""
    print(f"🔄 翻訳・分類処理中（Google Translate API）...\n")
    
    processed = []
    
    for i, article in enumerate(articles):
        lang = detect_language(article['title'] + " " + article['summary'])
        article['original_language'] = lang
        
        print(f"[{i+1}/{len(articles)}] {article['source']}: {lang}", end='')
        
        if lang == 'ja':
            article['title_ja'] = article['title']
            article['summary_ja'] = article['summary']
            article['translated'] = False
            print(" ✓")
        else:
            # 翻訳実行
            article['title_ja'] = translate_to_japanese(article['title'])
            article['summary_ja'] = translate_to_japanese(article['summary'])
            article['translated'] = True
            print(" ✓")
        
        # カテゴリ分類
        article['category'] = classify_category(
            article['title_ja'], 
            article['summary_ja'], 
            article['category_hint']
        )
        article['relevance'] = 0.8 if article['translated'] else 0.7
        processed.append(article)
    
    return processed

def generate_html_dashboard(articles):
    import html as html_lib
    
    by_category = {}
    for article in articles:
        cat = article.get('category', 'uncategorized')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(article)
    
    for cat in by_category:
        by_category[cat].sort(key=lambda x: x.get('relevance', 0), reverse=True)
    
    category_order = [
        '01_建築AI',
        '02_実務AI',
        '03_海外AI本流',
        '04_アートAI',
        '05_偶発ネタ',
    ]
    
    # タブ HTML 生成
    tabs_html = '''
    <div class="sticky top-20 bg-white border-b border-gray-200 z-9">
        <div class="max-w-6xl mx-auto px-4">
            <div class="flex gap-2 overflow-x-auto">
                <button onclick="showTab('all')" class="tab-button active px-4 py-3 font-semibold text-indigo-600 border-b-2 border-indigo-600 whitespace-nowrap">
                    ALL
                </button>
'''
    
    for cat in category_order:
        display_name = cat.replace('01_', '').replace('02_', '').replace('03_', '').replace('04_', '').replace('05_', '')
        tabs_html += f'''                <button onclick="showTab('{cat}')" class="tab-button px-4 py-3 font-semibold text-gray-600 border-b-2 border-transparent hover:text-indigo-600 whitespace-nowrap">
                    {display_name}
                </button>
'''
    
    tabs_html += '''            </div>
        </div>
    </div>
'''
    
    # ALL タブ：全記事を時系列で表示
    all_articles_sorted = sorted(articles, key=lambda x: x.get('published', ''), reverse=True)
    
    all_tab_html = '        <div id="all" class="tab-content">'
    all_tab_html += f'            <h2 class="text-2xl font-bold text-gray-800 pl-4 mb-6 mt-8">最新記事（全{len(all_articles_sorted)}件）</h2>'
    all_tab_html += '            <div class="grid gap-4">'
    
    for item in all_articles_sorted[:20]:  # 最新 20 件
        title = html_lib.escape(item['title_ja'])
        summary = html_lib.escape(item['summary_ja'])
        url = html_lib.escape(item['url'])
        source = html_lib.escape(item['source'])
        published = item['published'][:10] if item.get('published') else 'N/A'
        
        translated_badge = '<span class="badge-translated">翻訳</span>' if item.get('translated') else ''
        original_lang = f' <span class="text-xs text-gray-500">({item["original_language"]})</span>' if item.get('original_language') and item['original_language'] != 'ja' else ''
        category_label = item.get('category', 'uncategorized')
        
        all_tab_html += f'''                <div class="bg-white rounded-lg p-4 md:p-6 border border-gray-200 card-hover transition-all duration-200">
                    <div class="flex flex-col md:flex-row md:justify-between md:items-start gap-2 mb-3">
                        <div class="flex-1">
                            <a href="{url}" target="_blank" class="text-lg font-semibold text-indigo-600 hover:text-indigo-800 hover:underline block">
                                {title}
                            </a>
                        </div>
                        {translated_badge}
                    </div>
                    <div class="text-xs text-gray-600 mb-3">
                        <span class="inline-block bg-gray-100 px-2 py-1 rounded mr-2">{category_label}</span>
                        <span class="font-semibold">{source}</span>
                        {original_lang}
                        <span class="mx-1">·</span>
                        <span>{published}</span>
                    </div>
                    <p class="text-gray-700 leading-relaxed mb-2">{summary}</p>
                </div>
'''
    
    all_tab_html += '            </div>\n        </div>\n'
    
    # カテゴリ別タブ
    category_tabs_html = ''
    
    for category in category_order:
        if category not in by_category:
            continue
        
        items = by_category[category]
        category_tabs_html += f'        <div id="{category}" class="tab-content hidden">'
        category_tabs_html += f'            <h2 class="text-2xl font-bold text-gray-800 border-l-4 border-indigo-600 pl-4 mb-6 mt-8">'
        category_tabs_html += f'                {category}'
        category_tabs_html += f'                <span class="text-sm text-gray-500 font-normal">({len(items)}件)</span>'
        category_tabs_html += f'            </h2>'
        category_tabs_html += f'            <div class="grid gap-4">'
        
        for item in items:
            title = html_lib.escape(item['title_ja'])
            summary = html_lib.escape(item['summary_ja'])
            url = html_lib.escape(item['url'])
            source = html_lib.escape(item['source'])
            published = item['published'][:10] if item.get('published') else 'N/A'
            
            translated_badge = '<span class="badge-translated">翻訳</span>' if item.get('translated') else ''
            original_lang = f' <span class="text-xs text-gray-500">({item["original_language"]})</span>' if item.get('original_language') and item['original_language'] != 'ja' else ''
            relevance = int(item.get('relevance', 0) * 100)
            
            category_tabs_html += f'''                <div class="bg-white rounded-lg p-4 md:p-6 border border-gray-200 card-hover transition-all duration-200">
                    <div class="flex flex-col md:flex-row md:justify-between md:items-start gap-2 mb-3">
                        <div class="flex-1">
                            <a href="{url}" target="_blank" class="text-lg font-semibold text-indigo-600 hover:text-indigo-800 hover:underline block">
                                {title}
                            </a>
                        </div>
                        {translated_badge}
                    </div>
                    <div class="text-xs text-gray-600 mb-3">
                        <span class="font-semibold">{source}</span>
                        {original_lang}
                        <span class="mx-1">·</span>
                        <span>{published}</span>
                    </div>
                    <p class="text-gray-700 leading-relaxed mb-2">{summary}</p>
                    <div class="text-xs text-gray-500 mt-2">関連度: {relevance}%</div>
                </div>
'''
        
        category_tabs_html += '            </div>\n        </div>\n'
    
    # 完全な HTML を構築
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI ニュース統合ダッシュボード</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Yu Gothic', 'Hiragino Sans', sans-serif; }}
        .card-hover:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
        .badge-translated {{ display: inline-block; background: #22c55e; color: white; font-size: 0.75rem; padding: 2px 6px; border-radius: 3px; }}
        .tab-button {{ transition: all 0.3s ease; }}
        .tab-button.active {{ color: #4f46e5; border-bottom-color: #4f46e5; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
</head>
<body class="bg-gray-50">
    <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-8 px-4 sticky top-0 z-20 shadow-lg">
        <div class="max-w-6xl mx-auto">
            <h1 class="text-3xl md:text-4xl font-bold">🤖 AI ニュース統合ダッシュボード</h1>
            <p class="text-indigo-100 mt-2">建築AI × 実務AI × 海外AI本流 × アートAI × 偶発ネタ</p>
            <p class="text-sm text-indigo-200 mt-1">最終更新: {datetime.now().strftime("%Y年%m月%d日 %H:%M")}</p>
        </div>
    </div>

{tabs_html}

    <div class="max-w-6xl mx-auto px-4 py-8">
{all_tab_html}
{category_tabs_html}
    </div>

    <div class="bg-gray-800 text-gray-400 text-center py-6 mt-12">
        <p class="text-sm">自動生成ニュースダッシュボード | RSS + Google Translate</p>
        <p class="text-xs mt-1">毎日 09:00 JST に更新</p>
    </div>

    <script>
        function showTab(tabName) {{
            // すべてのタブを非表示
            document.querySelectorAll('.tab-content').forEach(el => {{
                el.classList.remove('active');
            }});
            
            // すべてのボタンを非アクティブに
            document.querySelectorAll('.tab-button').forEach(el => {{
                el.classList.remove('active');
            }});
            
            // 選択されたタブを表示
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {{
                selectedTab.classList.add('active');
            }}
            
            // 選択されたボタンをアクティブに
            event.target.classList.add('active');
        }}
        
        // ページロード時に ALL タブを表示
        document.addEventListener('DOMContentLoaded', function() {{
            document.getElementById('all').classList.add('active');
        }});
    </script>
</body>
</html>
'''
    
    return html

if __name__ == "__main__":
    print("🚀 AI ニュース集約開始\n")
    
    print("📥 RSS フィード読み込み中...")
    rss_sources = load_rss_config()
    articles = fetch_rss_feeds(rss_sources)
    print(f"✓ {len(articles)} 件の記事を取得\n")
    
    print("🔄 翻訳・分類処理中...")
    processed = process_articles(articles)
    print(f"\n✓ {len(processed)} 件を処理\n")
    
    print("📄 HTML ダッシュボード生成中...")
    os.makedirs("docs", exist_ok=True)
    html = generate_html_dashboard(processed)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✓ {OUTPUT_FILE}\n")
    
    print("✨ 完成！")
