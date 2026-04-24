#!/usr/bin/env python3
import feedparser
import yaml
import json
import time
from anthropic import Anthropic
from datetime import datetime
from langdetect import detect
import os

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
                for entry in feed.entries[:3]:
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

def process_articles(articles):
    client = Anthropic()
    processed = []
    
    for i, article in enumerate(articles):
        lang = detect_language(article['title'] + " " + article['summary'])
        article['original_language'] = lang
        
        print(f"[{i+1}/{len(articles)}] {article['source']}: {lang}", end='')
        
        if lang == 'ja':
            article['title_ja'] = article['title']
            article['summary_ja'] = article['summary']
            article['translated'] = False
            article['category'] = article['category_hint']
            article['relevance'] = 0.8
            processed.append(article)
            print(" ✓")
            continue
        
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
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
            time.sleep(2)
        except Exception as e:
            print(f" ✗ ({e})")
            article['title_ja'] = article['title']
            article['summary_ja'] = article['summary']
            article['category'] = article['category_hint']
            article['relevance'] = 0.5
            article['translated'] = False
            processed.append(article)
    
    return processed

def generate_html_dashboard(articles):
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
    
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI ニュース統合ダッシュボード</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Yu Gothic', 'Hiragino Sans', sans-serif; }}
        .card-hover:hover {{ transform: translateY(-2px); box-s
