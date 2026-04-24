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
        'uncategorized'
    ]
    
    lines = [
        '<!DOCTYPE html>',
        '<html lang="ja">',
        '<head>',
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '    <title>AI ニュース統合ダッシュボード</title>',
        '    <script src="https://cdn.tailwindcss.com"></script>',
        '    <style>',
        "        body { font-family: 'Yu Gothic', 'Hiragino Sans', sans-serif; }",
        '        .card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }',
        '        .badge-translated { display: inline-block; background: #22c55e; color: white; font-size: 0.75rem; padding: 2px 6px; border-radius: 3px; }',
        '    </style>',
        '</head>',
        '<body class="bg-gray-50">',
        '    <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-8 px-4 sticky top-0 z-10 shadow-lg">',
        '        <div class="max-w-6xl mx-auto">',
        '            <h1 class="text-3xl md:text-4xl font-bold">🤖 AI ニュース統合ダッシュボード</h1>',
        '            <p class="text-indigo-100 mt-2">建築AI × 実務AI × 海外AI本流 × アートAI</p>',
        f'            <p class="text-sm text-indigo-200 mt-1">最終更新: {datetime.now().strftime("%Y年%m月%d日 %H:%M")}</p>',
        '        </div>',
        '    </div>',
        '    <div class="max-w-6xl mx-auto px-4 py-8">',
    ]
    
    for category in category_order:
        if category not in by_category:
            continue
        
        items = by_category[category]
        lines.append(f'        <div class="mb-12">')
        lines.append(f'            <h2 class="text-2xl font-bold text-gray-800 border-l-4 border-indigo-600 pl-4 mb-6">')
        lines.append(f'                {category}')
        lines.append(f'                <span class="text-sm text-gray-500 font-normal">({len(items)}件)</span>')
        lines.append(f'            </h2>')
        lines.append(f'            <div class="grid gap-4">')
        
        for item in items:
            title = html_lib.escape(item['title_ja'])
            summary = html_lib.escape(item['summary_ja'])
            url = html_lib.escape(item['url'])
            source = html_lib.escape(item['source'])
            published = item['published'][:10] if item.get('published') else 'N/A'
            
            translated_badge = '<span class="badge-translated">翻訳</span>' if item.get('translated') else ''
            original_lang = f' <span class="text-xs text-gray-500">({item["original_language"]})</span>' if item.get('original_language') and item['original_language'] != 'ja' else ''
            relevance = int(item.get('relevance', 0) * 100)
            
            lines.append('                <div class="bg-white rounded-lg p-4 md:p-6 border border-gray-200 card-hover transition-all duration-200">')
            lines.append('                    <div class="flex flex-col md:flex-row md:justify-between md:items-start gap-2 mb-3">')
            lines.append('                        <div class="flex-1">')
            lines.append(f'                            <a href="{url}" target="_blank" class="text-lg font-semibold text-indigo-600 hover:text-indigo-800 hover:underline block">')
            lines.append(f'                                {title}')
            lines.append('                            </a>')
            lines.append('                        </div>')
            lines.append(f'                        {translated_badge}')
            lines.append('                    </div>')
            lines.append('                    <div class="text-xs text-gray-600 mb-3">')
            lines.append(f'                        <span class="font-semibold">{source}</span>')
            lines.append(f'                        {original_lang}')
            lines.append('                        <span class="mx-1">·</span>')
            lines.append(f'                        <span>{published}</span>')
            lines.append('                    </div>')
            lines.append(f'                    <p class="text-gray-700 leading-relaxed mb-2">{summary}</p>')
            lines.append(f'                    <div class="text-xs text-gray-500 mt-2">関連度: {relevance}%</div>')
            lines.append('                </div>')
        
        lines.append('            </div>')
        lines.append('        </div>')
    
    lines.extend([
        '    </div>',
        '    <div class="bg-gray-800 text-gray-400 text-center py-6 mt-12">',
        '        <p class="text-sm">自動生成ニュースダッシュボード | RSS + Claude 翻訳・分類</p>',
        '        <p class="text-xs mt-1">毎日 09:00 JST に更新</p>',
        '    </div>',
        '</body>',
        '</html>',
    ])
    
    return '\n'.join(lines)
