import csv
import json
import requests

# 1. まず tickers.csv から全銘柄データを読み込んでベースのデータベースを作る
stock_database = {}
print("tickers.csv から全銘柄データを読み込み中...")

try:
    with open("tickers.csv", mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_ticker = row.get("ticker", "").strip()
            code = full_ticker.replace(".T", "")
            name = row.get("name", "").strip()

            if code and name:
                stock_database[code] = {
                    "name": name,
                    "market": "東証", # デフォルト
                    "industry": "その他"
                }
    print(f"✨ CSV読み込み成功: {len(stock_database)} 銘柄")
except Exception as e:
    print(f"注意: tickers.csv が見つからないか読み込めません ({e})。基本データで代用します。")

# 2. IRBANK APIを使って、主要な監視銘柄の公式データを自動で上書き・リッチ化する
# ※IRBANKで発行された実際のAPIキーに書き換えてください（キーが不要な場合は空欄でも動きます）
API_KEY = "irbk_key_LheN3cbVmVpJ3UfACnXtBUGPEGzxUHN5ya3zRprN1VY"
rich_target_codes = ["7203", "9432", "6758", "8306", "9984"]

if API_KEY and "ここに" not in API_KEY:
    print("IRBANK APIから公式詳細データを取得中...")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    for code in rich_target_codes:
        if code in stock_database:
            url = f"https://api.irbank.net/v1/securities/{code}"
            try:
                response = requests.get(url, headers=headers, timeout=3)
                if response.status_code == 200:
                    item = response.json()
                    # IRBANKの公式データで上書きしてリッチ化
                    stock_database[code]["market"] = item.get("market", "東証")
                    stock_database[code]["industry"] = item.get("industry_33", "その他")
            except Exception as e:
                pass

db_json = json.dumps(stock_database, ensure_ascii=False, indent=4)

# 3. 投資日記アプリ（HTML）の生成
html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>My 投資日記 & 取引ノート</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0; color: #333; }
        header { background-color: #1e293b; color: white; text-align: center; padding: 12px; font-size: 18px; font-weight: bold; }
        
        .tab-bar { display: flex; background-color: #0f172a; }
        .tab-btn { flex: 1; padding: 12px 5px; background: none; border: none; color: #94a3b8; font-size: 12px; font-weight: bold; cursor: pointer; border-bottom: 3px solid transparent; }
        .tab-btn.active { color: #38bdf8; border-bottom-color: #38bdf8; background-color: #1e293b; }
        
        .tab-content { display: none; padding: 12px; }
        .tab-content.active { display: block; }
        
        .card { background: white; padding: 12px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 12px; }
        .card h3 { margin-top: 0; font-size: 15px; color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }
        
        label { font-size: 11px; color: #64748b; font-weight: bold; display: block; margin-top: 8px; }
        input, select, textarea { width: 100%; padding: 8px; margin-top: 3px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; }
        textarea { height: 60px; resize: vertical; }
        
        .btn-submit { width: 100%; background-color: #2563eb; color: white; border: none; padding: 12px; margin-top: 14px; border-radius: 6px; font-weight: bold; font-size: 14px; cursor: pointer; }
        .btn-submit:active { background-color: #1d4ed8; }
        
        .btn-cancel { background-color: #64748b; margin-top: 6px; display: none; }

        .table-container { overflow-x: auto; max-width: 100%; border-radius: 8px; background: white; }
        table.history-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; white-space: nowrap; }
        table.history-table th { background-color: #1e293b; color: white; padding: 8px 6px; }
        table.history-table td { padding: 8px 6px; border-bottom: 1px solid #e2e8f0; cursor: pointer; }
        table.history-table tr:hover { background-color: #f1f5f9; }
        
        .badge-buy { background-color: #ef4444; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
        .badge-sell { background-color: #3b82f6; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
        .profit-plus { color: #dc2626; font-weight: bold; }
        .profit-minus { color: #2563eb; font-weight: bold; }

        .link-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
        .link-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; text-decoration: none; color: #1e293b; font-weight: bold; font-size: 13px; text-align: center; }
        
        .auto-info { background-color: #f1f5f9; padding: 8px; border-radius: 6px; margin-top: 6px; font-size: 12px; color: #334155; }
        .hint-text { font-size: 10px; color: #0284c7; margin-top: 4px; }
    </style>
</head>
<body>

    <header>📈 My 投資ダイアリー</header>

    <div class="tab-bar">
        <button class="tab-btn active" onclick="switchTab('tab1')">📋 銘柄リスト</button>
        <button class="tab-btn" onclick="switchTab('tab2')" id="btn-tab2">✏️ 取引入力</button>
        <button class="tab-btn" onclick="switchTab('tab3')">🔍 銘柄検索</button>
    </div>

    <!-- タブ1: 銘柄リスト -->
    <div id="tab1" class="tab-content active">
        <div class="card">
            <h3>登録済み取引一覧 <span style="font-size:11px; color:#64748b; font-weight:normal;">(行を押すと修正できます)</span></h3>
            <div class="table-container">
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>No</th>
                            <th>購入日</th>
                            <th>コード</th>
                            <th>銘柄名</th>
                            <th>売買</th>
                            <th>損益</th>
                        </tr>
                    </thead>
                    <tbody id="history-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- タブ2: 銘柄登録・入力・修正 -->
    <div id="tab2" class="tab-content">
        <div class="card">
            <h3 id="form-title">新規取引記録の入力</h3>
            
            <label>銘柄コード (4桁)</label>
            <input type="text" id="code" placeholder="例: 7203" oninput="autoFillStockInfo()">
            <div class="hint-text">※CSV & IRBANK連携で自動判定されます</div>
            
            <div id="auto-stock-details" class="auto-info">
                <div>銘柄名: <strong id="info-name">-</strong></div>
                <div>市場: <span id="info-market">-</span> | 業種: <span id="info-industry">-</span></div>
            </div>

            <label>購入日、時間</label>
            <input type="datetime-local" id="buy-datetime">

            <label>売り・買い</label>
            <select id="trade-type">
                <option value="買い">買い</option>
                <option value="売り">売り</option>
            </select>

            <label>購入株価</label>
            <input type="number" id="buy-price" placeholder="例: 1200">

            <label>購入した理由</label>
            <input type="text" id="buy-reason" placeholder="例: 2日連続の出来高増加">

            <label>保有期間</label>
            <input type="text" id="hold-period" placeholder="例: 当日決済、1週間保有">

            <label>売却した日付、時間</label>
            <input type="datetime-local" id="sell-datetime">

            <label>決済した際の収支 (損益額)</label>
            <input type="number" id="profit-loss" placeholder="例: +15000 または -5000">

            <label>売却した理由</label>
            <input type="text" id="sell-reason" placeholder="例: 月次レポートの結果">

            <label>メモ (気づいた点・反省点)</label>
            <textarea id="memo" placeholder="売買での気付いた点、反省点を記載する"></textarea>

            <button class="btn-submit" id="submit-btn" onclick="saveTradeRecord()">取引を保存して追加する</button>
            <button class="btn-submit btn-cancel" id="cancel-btn" onclick="resetForm()">編集をキャンセルして新規に戻る</button>
        </div>
    </div>

    <!-- タブ3: 銘柄検索・クイックリンク -->
    <div id="tab3" class="tab-content">
        <div class="card">
            <h3>世界の株価 & 市場データ</h3>
            <div class="link-grid">
                <a href="https://sekai-kabuka.com/" target="_blank" class="link-card">🌏 世界の株価・先物</a>
                <a href="https://kabutan.jp/" target="_blank" class="link-card">📈 株探 (Kabutan)</a>
                <a href="https://finance.yahoo.co.jp/" target="_blank" class="link-card">🟣 Yahoo!ファイナンス</a>
                <a href="https://irbank.net/" target="_blank" class="link-card">📙 IR BANK</a>
            </div>
        </div>

        <div class="card">
            <h3>個別に銘柄を検索</h3>
            <label>4桁コードを入力</label>
            <input type="text" id="search-code" placeholder="例: 9432">
            <div class="link-grid" style="margin-top:10px;">
                <button class="link-card" onclick="openExternal('kabutan')">株探で開く</button>
                <button class="link-card" onclick="openExternal('irbank')">IR BANKで開く</button>
            </div>
        </div>
    </div>

    <script>
        const masterDB = __MASTER_DB__;
        let tradeHistory = JSON.parse(localStorage.getItem('my_trade_history')) || [];
        let editingId = null;

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            if (tabId === 'tab1') document.querySelector('.tab-bar button:nth-child(1)').classList.add('active');
            if (tabId === 'tab2') document.querySelector('.tab-bar button:nth-child(2)').classList.add('active');
            if (tabId === 'tab3') document.querySelector('.tab-bar button:nth-child(3)').classList.add('active');

            if (tabId === 'tab1') renderHistoryTable();
        }

        function autoFillStockInfo() {
            const code = document.getElementById('code').value.trim();
            const nameEl = document.getElementById('info-name');
            const marketEl = document.getElementById('info-market');
            const industryEl = document.getElementById('info-industry');

            if (masterDB[code]) {
                nameEl.innerText = masterDB[code].name;
                marketEl.innerText = masterDB[code].market;
                industryEl.innerText = masterDB[code].industry;
            } else if (code.length === 4) {
                nameEl.innerText = `銘柄 ${code} (未登録コード)`;
                marketEl.innerText = "-";
                industryEl.innerText = "-";
            } else {
                nameEl.innerText = "-";
                marketEl.innerText = "-";
                industryEl.innerText = "-";
            }
        }

        function saveTradeRecord() {
            const code = document.getElementById('code').value.trim();
            const name = document.getElementById('info-name').innerText;
            const buyDateTime = document.getElementById('buy-datetime').value;
            const tradeType = document.getElementById('trade-type').value;
            const buyPrice = document.getElementById('buy-price').value;
            const buyReason = document.getElementById('buy-reason').value;
            const holdPeriod = document.getElementById('hold-period').value;
            const sellDateTime = document.getElementById('sell-datetime').value;
            const profitLoss = parseFloat(document.getElementById('profit-loss').value) || 0;
            const sellReason = document.getElementById('sell-reason').value;
            const memo = document.getElementById('memo').value;

            if (!code) {
                alert('銘柄コードを入力してください');
                return;
            }

            if (editingId !== null) {
                const index = tradeHistory.findIndex(item => item.id === editingId);
                if (index !== -1) {
                    tradeHistory[index] = {
                        ...tradeHistory[index],
                        code,
                        name: name !== '-' ? name : `銘柄 ${code}`,
                        date: buyDateTime ? buyDateTime.replace('T', ' ') : tradeHistory[index].date,
                        type: tradeType,
                        buyPrice,
                        buyReason,
                        holdPeriod,
                        sellDateTime,
                        profitLoss,
                        sellReason,
                        memo
                    };
                }
                alert('取引記録を更新しました！');
            } else {
                const record = {
                    id: Date.now(),
                    date: buyDateTime ? buyDateTime.replace('T', ' ') : '未入力',
                    code,
                    name: name !== '-' ? name : `銘柄 ${code}`,
                    type: tradeType,
                    buyPrice,
                    buyReason,
                    holdPeriod,
                    sellDateTime,
                    profitLoss,
                    sellReason,
                    memo
                };
                tradeHistory.unshift(record);
                alert('取引記録を保存しました！');
            }

            localStorage.setItem('my_trade_history', JSON.stringify(tradeHistory));
            resetForm();
            switchTab('tab1');
        }

        function renderHistoryTable() {
            const tbody = document.getElementById('history-body');
            tbody.innerHTML = '';

            if (tradeHistory.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="padding:15px; color:#64748b;">登録された取引記録はありません</td></tr>`;
                return;
            }

            tradeHistory.forEach((item, index) => {
                const tr = document.createElement('tr');
                const badgeClass = item.type === '買い' ? 'badge-buy' : 'badge-sell';
                const profitClass = item.profitLoss > 0 ? 'profit-plus' : (item.profitLoss < 0 ? 'profit-minus' : '');
                const profitText = item.profitLoss > 0 ? `+${item.profitLoss.toLocaleString()}円` : `${item.profitLoss.toLocaleString()}円`;

                tr.onclick = () => loadRecordForEdit(item.id);

                tr.innerHTML = `
                    <td>${tradeHistory.length - index}</td>
                    <td>${item.date.split(' ')[0] || '-'}</td>
                    <td>${item.code}</td>
                    <td style="text-align:left; font-weight:bold;">${item.name}</td>
                    <td><span class="${badgeClass}">${item.type}</span></td>
                    <td class="${profitClass}">${profitText}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function loadRecordForEdit(id) {
            const item = tradeHistory.find(r => r.id === id);
            if (!item) return;

            editingId = id;
            document.getElementById('code').value = item.code;
            autoFillStockInfo();
            document.getElementById('buy-datetime').value = item.date !== '未入力' ? item.date.replace(' ', 'T') : '';
            document.getElementById('trade-type').value = item.type;
            document.getElementById('buy-price').value = item.buyPrice || '';
            document.getElementById('buy-reason').value = item.buyReason || '';
            document.getElementById('hold-period').value = item.holdPeriod || '';
            document.getElementById('sell-datetime').value = item.sellDateTime || '';
            document.getElementById('profit-loss').value = item.profitLoss !== 0 ? item.profitLoss : '';
            document.getElementById('sell-reason').value = item.sellReason || '';
            document.getElementById('memo').value = item.memo || '';

            document.getElementById('form-title').innerText = '✏️ 取引記録の修正';
            document.getElementById('submit-btn').innerText = '変更を保存（更新）する';
            document.getElementById('cancel-btn').style.display = 'block';
            document.getElementById('btn-tab2').innerText = '✏️ 編集中';

            switchTab('tab2');
        }

        function resetForm() {
            editingId = null;
            document.getElementById('code').value = '';
            autoFillStockInfo();
            document.getElementById('buy-datetime').value = '';
            document.getElementById('trade-type').value = '買い';
            document.getElementById('buy-price').value = '';
            document.getElementById('buy-reason').value = '';
            document.getElementById('hold-period').value = '';
            document.getElementById('sell-datetime').value = '';
            document.getElementById('profit-loss').value = '';
            document.getElementById('sell-reason').value = '';
            document.getElementById('memo').value = '';

            document.getElementById('form-title').innerText = '新規取引記録の入力';
            document.getElementById('submit-btn').innerText = '取引を保存して追加する';
            document.getElementById('cancel-btn').style.display = 'none';
            document.getElementById('btn-tab2').innerText = '✏️ 取引入力';
        }

        function openExternal(site) {
            const code = document.getElementById('search-code').value.trim();
            if (!code) {
                alert('銘柄コードを入力してください');
                return;
            }
            if (site === 'kabutan') window.open(`https://kabutan.jp/stock/?code=${code}`, '_blank');
            if (site === 'irbank') window.open(`https://irbank.net/${code}`, '_blank');
        }

        renderHistoryTable();
    </script>
</body>
</html>
"""

html_content = html_template.replace("__MASTER_DB__", db_json)

with open("screening.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✨ 成功！CSV＋IRBANK公式データのハイブリッド版 'screening.html' が生成されました！")