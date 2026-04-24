# AI News Aggregator

建築AI、実務AI、海外AI本流、アートAI、偶発ネタから、毎日 RSS フィードを自動取得 → 翻訳 → 分類 → HTML ダッシュボード化するシステム。

PC・スマホ両対応。

## セットアップ（5分）

### 1. リポジトリをクローン

```bash
git clone https://github.com/YOUR_NAME/ai-news-aggregator.git
cd ai-news-aggregator
```

### 2. Python 環境をセットアップ

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. Anthropic API キーを設定

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 4. ローカルで実行（テスト）

```bash
python news_aggregator.py
```

実行完了後、`docs/news_dashboard.html` をブラウザで開く。

## GitHub Actions での自動実行

### 1. GitHub にシークレットを設定

1. リポジトリ → Settings → Secrets and variables → Actions
2. 「New repository secret」をクリック
3. Name: `ANTHROPIC_API_KEY`
4. Value: あなたの API キー（`sk-ant-...`）
5. Add secret

### 2. GitHub Pages を有効化

1. Settings → Pages
2. Source: `Deploy from a branch`
3. Branch: `main`, Folder: `/docs`
4. Save

### 3. 毎日 09:00 JST に自動実行開始

`.github/workflows/daily_news.yml` が毎日 09:00 JST に自動実行。

手動実行：Actions → Daily AI News Aggregation → Run workflow

## カスタマイズ

### RSS フィードを追加・削除

`rss_sources.yaml` を編集：

```yaml
sources:
  01_建築AI:
    YourNewSource: https://example.com/feed.xml
    # ↑ 新規フィード追加
```

保存後、次回実行時に自動的に反映。

### 実行時間を変更

`.github/workflows/daily_news.yml` の `cron` を編集：

```yaml
cron: '0 0 * * *'  # UTC 時刻（00:00 = JST 09:00）
```

別の時間例：
- `0 2 * * *` = JST 11:00
- `0 6 * * *` = JST 15:00

### 翻訳言語を変更

`news_aggregator.py` の Claude メッセージプロンプトを編集：

```python
"タイトルと要約を自然な日本語に翻訳"
↓
"タイトルと要約を自然な英語に翻訳"
```

## トラブルシューティング

### API エラー

- API キーが正しく設定されているか確認
- Anthropic コンソール → Usage で使用状況を確認

### RSS が更新されない

- RSS フィード URL が有効か確認（`feedparser.parse(url)` でテスト）
- サイトが RSS を提供しているか確認

### HTML が表示されない

- `docs/news_dashboard.html` が存在するか確認
- ブラウザのキャッシュをクリア（Ctrl+Shift+Delete）

## コスト（月単位）

- **Anthropic API**: 約 $2/月（記事 30 件/日 × 30 日）
- **GitHub Actions**: 無料（public リポジトリの場合）
- **GitHub Pages**: 無料

## 構造
