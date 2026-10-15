import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="スイング監視", layout="wide")

st.markdown("""
    <style>
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; padding-bottom: 0px !important; }
    }
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .total-dash {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid #4a90e2;
    }
    </style>
""", unsafe_allow_html=True)

MY_STOCKS = ["7974", "4751", "9101", "3990"]
MAJOR_NAMES = {
    "2002": "日清製粉G", "2267": "ヤクルト", "2269": "明治HD", "2282": "日本ハム", "2502": "アサヒG", "2503": "キリンHD", "2801": "キッコーマン", "2802": "味の素", "2914": "JT",
    "3402": "東レ", "3407": "旭化成", "4005": "住友化学", "4021": "日産化学", "4061": "デンカ", "4063": "信越化学工業", "4183": "三井化学", "4188": "三菱ケミカルG", "4452": "花王", "4901": "富士フイルム", "4911": "資生堂", "8113": "ユニ・チャーム",
    "4502": "武田薬品工業", "4503": "アステラス製薬", "4507": "塩野義製薬", "4519": "中外製薬", "4523": "エーザイ", "4528": "小野薬品工業", "4568": "第一三共", "4578": "大塚HD",
    "5019": "出光興産", "5020": "ENEOS", "5201": "AGC", "5332": "TOTO", "5333": "日本ガイシ", "5401": "日本製鉄", "5411": "JFE", "5713": "住友金属鉱山", "5714": "DOWA", "5802": "住友電工",
    "6273": "SMC", "6301": "コマツ", "6326": "クボタ", "6367": "ダイキン工業", "6432": "竹内製作所", "6481": "THK", "7011": "三菱重工", "7012": "川崎重工", "7013": "IHI",
    "6146": "ディスコ", "6501": "日立製作所", "6503": "三菱電機", "6504": "富士電機", "6506": "安川電機", "6594": "ニデック", "6645": "オムロン", "6702": "富士通", "6723": "ルネサス", "6752": "パナソニック", "6758": "ソニーG", "6762": "TDK", "6857": "アドバンテスト", "6861": "キーエンス", "6902": "デンソー", "6920": "レーザーテック", "6954": "ファナック", "6971": "京セラ", "6981": "村田製作所", "7733": "オリンパス", "7741": "HOYA", "7751": "キヤノン", "8035": "東京エレクトロン",
    "7201": "日産自動車", "7202": "いすゞ", "7203": "トヨタ自動車", "7259": "アイシン", "7267": "ホンダ", "7269": "スズキ", "7270": "SUBARU", "7272": "ヤマハ発動機",
    "2768": "双日", "8001": "伊藤忠商事", "8002": "丸紅", "8015": "豊田通商", "8031": "三井物産", "8053": "住友商事", "8058": "三菱商事",
    "3086": "Jフロント", "3092": "ZOZO", "3382": "セブン＆アイ", "3659": "ネクソン", "4307": "野村総研", "4324": "電通G", "4661": "オリエンタルランド", "4704": "トレンドマイクロ", "4751": "サイバーエージェント", "6098": "リクルート", "7532": "パンパシフィック", "7974": "任天堂", "8252": "丸井G", "8267": "イオン", "9432": "NTT", "9433": "KDDI", "9434": "ソフトバンク", "9613": "NTTデータ", "9735": "セコム", "9843": "ニトリ", "9983": "ファーストリテイリング", "9984": "ソフトバンクG",
    "8306": "三菱UFJ", "8308": "りそな", "8309": "三井住友トラスト", "8316": "三井住友", "8411": "みずほ", "8591": "オリックス", "8604": "野村HD", "8630": "SOMPO", "8725": "MS&AD", "8750": "第一生命", "8766": "東京海上",
    "1801": "大成建設", "1802": "大林組", "1803": "清水建設", "1812": "鹿島", "1925": "大和ハウス", "1928": "積水ハウス", "3289": "東急不動産", "8801": "三井不動産", "8802": "三菱地所", "8804": "東京建物", "8830": "住友不動産",
    "9501": "東京電力HD", "9502": "中部電力", "9503": "関西電力", "9531": "東京ガス", "9532": "大阪ガス",
    "9020": "JR東日本", "9021": "JR西日本", "9022": "JR東海", "9101": "日本郵船", "9104": "商船三井", "9107": "川崎汽船", "9143": "SGHD", "9147": "NIPPON EXPRESS", "9201": "JAL", "9202": "ANA",
    "7911": "TOPPAN", "7912": "大日本印刷", "7936": "アシックス", "7951": "ヤマハ"
}
TARGET_STOCKS = list(dict.fromkeys(MY_STOCKS + list(MAJOR_NAMES.keys())))

@st.cache_data(ttl=3600)
def get_earnings_date(code):
    url = f"https://finance.yahoo.co.jp/quote/{code}.T"
    try:
        html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3).text
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        match = re.search(r'決算発表日.*?([0-9]{4}/[0-9]{1,2}/[0-9]{1,2})', text)
        if match:
            date_str = match.group(1)
            days_left = (datetime.strptime(date_str, "%Y/%m/%d") - datetime.now()).days
            if 0 <= days_left <= 7: return f"⚠️ 近日決算予定（{date_str}）"
        return None
    except: return None

def check_rights_date_warning():
    now = datetime.now()
    if 22 <= now.day <= 31:
        return "⚠️ 【権利落ち日 接近アラート】まもなく月末の配当・優待権利落ち日が到来します。権利落ちによる株価の急落リスクにご注意ください。"
    return None

def get_chart_data(code, tf_choice):
    if tf_choice == "週足":
        df = yf.Ticker(code + ".T").history(period="2y", interval="1wk")
        return df, 13, 26, "13週線", "26週線"
    elif tf_choice == "月足":
        df = yf.Ticker(code + ".T").history(period="5y", interval="1mo")
        return df, 12, 24, "12ヶ月線", "24ヶ月線"
    else:
        df = yf.Ticker(code + ".T").history(period="6mo", interval="1d")
        return df, 5, 25, "5日線", "25日線"

PORTFOLIO_FILE = "portfolio_data.csv"
TICKERS_FILE = "manual_tickers_data.txt"

def load_tickers():
    if os.path.exists(TICKERS_FILE):
        with open(TICKERS_FILE, "r", encoding="utf-8") as f: return f.read()
    return ""

def save_tickers(text):
    with open(TICKERS_FILE, "w", encoding="utf-8") as f: f.write(text)

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        df = pd.read_csv(PORTFOLIO_FILE, dtype={"コード": str})
        if '口座区分' in df.columns: df = df.drop(columns=['口座区分'])
        return df
    return pd.DataFrame({
        "コード": pd.Series(dtype='str'),
        "取得日": pd.Series(dtype='str'),
        "取得単価": pd.Series(dtype='float'),
        "保有株数": pd.Series(dtype='float'),
        "メモ (戦略など)": pd.Series(dtype='str')
    })

def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)

if "manual_tickers" not in st.session_state: st.session_state.manual_tickers = load_tickers()
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "portfolio_df" not in st.session_state: st.session_state.portfolio_df = load_portfolio()
if "show_portfolio_charts" not in st.session_state: st.session_state.show_portfolio_charts = False

st.sidebar.header("📁 メニュー")
app_page = st.sidebar.radio("機能を選択してください", ["🔍 銘柄スクリーニング", "💼 保有銘柄ポートフォリオ"])

st.title("📈 スイングトレード監視ダッシュボード")

rights_warning = check_rights_date_warning()
if rights_warning: st.warning(rights_warning)

# ==============================================================================
# ページ1: 銘柄スクリーニング
# ==============================================================================
if app_page == "🔍 銘柄スクリーニング":
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ 動作モード")
    mode = st.sidebar.radio("モードを選択", ["手動監視モード", "🤖 注目・主要銘柄 自動スクリーニング"], index=1)
    
    tickers_to_analyze = []
    run_analysis = False
    
    if mode == "手動監視モード":
        st.sidebar.write("監視したい銘柄コードを**改行**で入力してください")
        ticker_input = st.sidebar.text_area("銘柄コード", value=st.session_state.manual_tickers, height=150)
        
        if ticker_input != st.session_state.manual_tickers:
            st.session_state.manual_tickers = ticker_input
            save_tickers(ticker_input)
            
        tickers_to_analyze = [t.strip() + ".T" for t in st.session_state.manual_tickers.split('\n') if t.strip()]
        if tickers_to_analyze: run_analysis = True
    else:
        st.sidebar.success(f"主要銘柄（計{len(TARGET_STOCKS)}社）から自動抽出します。")
        if st.sidebar.button("▶️ スクリーニング開始"):
            tickers_to_analyze = [t + ".T" for t in TARGET_STOCKS]
            run_analysis = True

    if run_analysis and tickers_to_analyze:
        st.subheader("① 買いシグナル抽出結果")
        progress_bar = st.progress(0)
        data_list = []
        
        for i, ticker in enumerate(tickers_to_analyze):
            code_str = ticker.replace('.T', '')
            progress_bar.progress((i + 1) / len(tickers_to_analyze))
            
            try:
                df = yf.Ticker(ticker).history(period="6mo")
                if df.empty or len(df) < 60: continue
                
                df['5MA'] = df['Close'].rolling(window=5).mean()
                df['25MA'] = df['Close'].rolling(window=25).mean()
                df['Volume_5MA'] = df['Volume'].rolling(window=5).mean()
                df['High_60'] = df['High'].rolling(window=60).max()
                
                c_c, c_5, c_25 = df['Close'].iloc[-1], df['5MA'].iloc[-1], df['25MA'].iloc[-1]
                p_5, p_25 = df['5MA'].iloc[-2], df['25MA'].iloc[-2]
                
                is_vol_surge = df['Volume'].iloc[-1] > (df['Volume_5MA'].iloc[-2] * 1.5)
                dist_res = ((df['High_60'].iloc[-1] - c_c) / c_c) * 100
                
                delta = df['Close'].diff()
                rs = (delta.where(delta > 0, 0)).rolling(14).mean() / (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                
                macd = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
                sig = macd.ewm(span=9).mean()
                
                # ==================================================
                # 🛡️ 【新機能】ダマシ回避フィルター：25日線が上向きか横ばい
                # ==================================================
                is_25ma_up = (c_25 >= p_25)
                
                is_gc_ma = (p_5 <= p_25) and (c_5 > c_25) and is_25ma_up
                is_gc_macd = (macd.iloc[-2] <= sig.iloc[-2]) and (macd.iloc[-1] > sig.iloc[-1]) and is_25ma_up
                is_uptrend = (c_c > c_25) and (c_5 > c_25) and is_25ma_up
                
                sig_txt = "様子見"
                if is_gc_ma and is_gc_macd: sig_txt = "🌟 超激アツ！(Wクロス)"
                elif is_gc_ma: sig_txt = "🔥 買い(MAクロス)"
                elif is_gc_macd and is_uptrend: sig_txt = "🔥 買い(MACD転換)"
                elif is_uptrend: sig_txt = "👍 上昇トレンド"
                elif c_c < c_25 and rsi < 30: sig_txt = "📉 売られすぎ(反発狙い)"
                
                if "買い" in sig_txt or "激アツ" in sig_txt:
                    if dist_res < 3.0: sig_txt = "⚠️ 買い(上値抵抗線接近)"
                    elif is_vol_surge: sig_txt = sig_txt.replace("買い", "買い(大商い)").replace("超激アツ！", "超激アツ！(大商い)")

                if mode == "🤖 注目・主要銘柄 自動スクリーニング" and (sig_txt == "様子見" or "⚠️" in sig_txt): continue
                
                name = MAJOR_NAMES.get(code_str, code_str)
                data_list.append({"コード": code_str, "銘柄名": name, "終値": round(c_c, 1), "上値余地": f"{round(dist_res, 1)}%", "RSI": round(rsi, 1), "判定": sig_txt})
            except: continue
                
        st.session_state.analysis_result = data_list
        if data_list:
            st.session_state.selected_code = data_list[0]["コード"]
            st.session_state.selected_name = data_list[0]["銘柄名"]

    if st.session_state.analysis_result:
        df_res = pd.DataFrame(st.session_state.analysis_result).sort_values('RSI').reset_index(drop=True)
        st.subheader("① 買いシグナル抽出結果")
        event = st.dataframe(df_res, use_container_width=True, on_select="rerun", selection_mode="single-row")
        if event.selection.rows:
            st.session_state.selected_code = df_res.iloc[event.selection.rows[0]]["コード"]
            st.session_state.selected_name = df_res.iloc[event.selection.rows[0]]["銘柄名"]
            
        st.subheader(f"② {st.session_state.selected_code} {st.session_state.selected_name} の詳細分析")
        warn = get_earnings_date(st.session_state.selected_code)
        if warn: st.error(warn)
        
        col_btn1, col_btn2 = st.columns(2)
        rakuten_url = f"https://www.rakuten-sec.co.jp/web/market/search/quote.html?ric={st.session_state.selected_code}.t"
        yahoo_url = f"https://finance.yahoo.co.jp/quote/{st.session_state.selected_code}.T/margin"
        col_btn1.link_button(f"🛒 楽天証券で確認・発注する", rakuten_url, type="primary", use_container_width=True)
        col_btn2.link_button(f"🔗 Yahoo!で信用倍率を見る", yahoo_url, use_container_width=True)
        
        tf_choice = st.radio("チャート表示（足種切り替え）", ["日足", "週足", "月足"], horizontal=True)
        
        df_daily = yf.Ticker(st.session_state.selected_code + ".T").history(period="6mo")
        if not df_daily.empty:
            tr = pd.concat([df_daily['High'] - df_daily['Low'], abs(df_daily['High'] - df_daily['Close'].shift()), abs(df_daily['Low'] - df_daily['Close'].shift())], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            latest_price = df_daily['Close'].iloc[-1]
            take_profit = latest_price + (atr * 2)
            stop_loss = latest_price - (atr * 1.5)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("現在値 (Entry)", f"¥{latest_price:,.1f}")
            col2.metric("🎯 利確目標 (日足基準)", f"¥{take_profit:,.1f}")
            col3.metric("✂️ 損切ライン (日足基準)", f"¥{stop_loss:,.1f}")
            
            df_c, ma_s, ma_l, name_s, name_l = get_chart_data(st.session_state.selected_code, tf_choice)
            
            if not df_c.empty:
                df_c['MA_S'] = df_c['Close'].rolling(ma_s).mean()
                df_c['MA_L'] = df_c['Close'].rolling(ma_l).mean()
                df_c['BB_std'] = df_c['Close'].rolling(ma_l).std()
                df_c['BB_upper'], df_c['BB_lower'] = df_c['MA_L'] + (df_c['BB_std']*2), df_c['MA_L'] - (df_c['BB_std']*2)
                
                macd = df_c['Close'].ewm(span=12).mean() - df_c['Close'].ewm(span=26).mean()
                sig = macd.ewm(span=9).mean()
                delta = df_c['Close'].diff()
                rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean())))

                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
                fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name='ローソク足'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['MA_S'], mode='lines', name=name_s, line=dict(color='lime', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['MA_L'], mode='lines', name=name_l, line=dict(color='orange', width=1.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['BB_upper'], mode='lines', line=dict(width=0), showlegend=False), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['BB_lower'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(173, 216, 230, 0.1)', name='BB±2σ'), row=1, col=1)
                
                f_days = 20 if tf_choice != "日足" else 5
                f_date = df_c.index[-1] + timedelta(days=f_days)
                fig.add_trace(go.Scatter(x=[df_c.index[-1], f_date], y=[take_profit, take_profit], mode='lines', name='利確目安', line=dict(color='lightgreen', dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=[df_c.index[-1], f_date], y=[stop_loss, stop_loss], mode='lines', name='損切ライン', line=dict(color='red', dash='dot')), row=1, col=1)

                fig.add_trace(go.Bar(x=df_c.index, y=macd-sig, name='MACD Hist', marker_color='gray'), row=2, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=macd, mode='lines', name='MACD', line=dict(color='cyan', width=1)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=sig, mode='lines', name='Signal', line=dict(color='magenta', width=1)), row=2, col=1)

                fig.add_trace(go.Scatter(x=df_c.index, y=rsi, mode='lines', name='RSI', line=dict(color='yellow', width=1)), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

                fig.update_layout(xaxis_rangeslider_visible=False, height=650, template="plotly_dark", dragmode="pan", margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

# ==============================================================================
# ページ2: 保有銘柄ポートフォリオ
# ==============================================================================
elif app_page == "💼 保有銘柄ポートフォリオ":
    st.subheader("💼 保有銘柄の管理")
    st.write("保有しているスイング銘柄を管理します。")
    
    edited_df = st.data_editor(
        st.session_state.portfolio_df, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "コード": st.column_config.TextColumn("コード (4桁)"),
            "保有株数": st.column_config.NumberColumn("保有株数", step=0.01, format="%g"),
            "メモ (戦略など)": st.column_config.TextColumn("メモ (戦略など)", max_chars=100)
        }
    )
    
    need_rerun = False
    for index, row in edited_df.iterrows():
        code = str(row.get('コード', '')).strip()
        if code.endswith('.0'): code = code[:-2]
            
        date_str = str(row.get('取得日', '')).strip()
        try: price = float(row.get('取得単価', 0.0))
        except: price = 0.0
            
        if code and len(code) >= 4 and code.lower() != 'nan' and date_str and price == 0.0:
            try:
                date_str = date_str.replace('-', '/')
                dt = datetime.strptime(date_str, "%Y/%m/%d")
                end_dt = dt + timedelta(days=7) 
                
                df_hist = yf.Ticker(code + ".T").history(start=dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d"))
                if not df_hist.empty:
                    auto_price = df_hist['Close'].iloc[0]
                    edited_df.at[index, '取得単価'] = round(auto_price, 1)
                    need_rerun = True
            except: pass

    if not edited_df.equals(st.session_state.portfolio_df) or need_rerun:
        st.session_state.portfolio_df = edited_df
        save_portfolio(edited_df)
        if need_rerun: st.rerun()

    st.markdown("---")
    dash_placeholder = st.empty()
    
    port_tf_choice = st.radio("全チャートの表示期間を一括切り替え", ["日足", "週足", "月足"], horizontal=True)
    
    if st.button("🔄 最新の状況をチェックする", type="primary"):
        st.session_state.show_portfolio_charts = True
        
    if st.session_state.show_portfolio_charts:
        total_invested = 0.0
        total_current_value = 0.0
        
        for index, row in edited_df.iterrows():
            code = str(row.get('コード', '')).strip()
            if code.endswith('.0'): code = code[:-2]
            if not code or code.lower() == 'nan': continue
            
            try: entry_price = float(row['取得単価'])
            except: entry_price = 0.0
            try: shares = float(row['保有株数'])
            except: shares = 0.0
                
            name = MAJOR_NAMES.get(code, code)
            st.markdown(f"### {code} {name}")
            
            try:
                df_daily_p = yf.Ticker(code + ".T").history(period="6mo")
                if df_daily_p.empty:
                    st.error("データが取得できませんでした。")
                    continue
                
                latest_price = df_daily_p['Close'].iloc[-1]
                total_invested += (entry_price * shares)
                total_current_value += (latest_price * shares)
                
                tr = pd.concat([df_daily_p['High'] - df_daily_p['Low'], abs(df_daily_p['High'] - df_daily_p['Close'].shift()), abs(df_daily_p['Low'] - df_daily_p['Close'].shift())], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1]
                
                take_profit = entry_price + (atr * 2) if entry_price > 0 else 0
                stop_loss = entry_price - (atr * 1.5) if entry_price > 0 else 0
                
                profit_loss_per_share = latest_price - entry_price
                profit_loss_total = profit_loss_per_share * shares
                pl_color = "normal" if profit_loss_total >= 0 else "inverse"
                
                col_btn, _ = st.columns([1, 2])
                rakuten_port_url = f"https://www.rakuten-sec.co.jp/web/market/search/quote.html?ric={code}.t"
                col_btn.link_button(f"🛒 {name} を楽天証券で確認・発注", rakuten_port_url, use_container_width=True)
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("取得単価", f"¥{entry_price:,.1f}")
                c2.metric("現在値", f"¥{latest_price:,.1f}", f"{profit_loss_per_share:,.1f}円", delta_color=pl_color)
                c3.metric("🎯 利確目標", f"¥{take_profit:,.1f}")
                c4.metric("✂️ 損切ライン", f"¥{stop_loss:,.1f}")
                
                st.info(f"💰 **評価損益:** ¥{profit_loss_total:,.0f} （保有: {shares:g}株）")
                
                if pd.notna(row.get('メモ (戦略など)')) and row.get('メモ (戦略など)'):
                    st.caption(f"📝 メモ: {row.get('メモ (戦略など)')}")
                
                df_p, ma_s, ma_l, name_s, name_l = get_chart_data(code, port_tf_choice)
                
                if not df_p.empty:
                    df_p['MA_L'] = df_p['Close'].rolling(ma_l).mean()
                    fig_p = go.Figure()
                    fig_p.add_trace(go.Candlestick(x=df_p.index, open=df_p['Open'], high=df_p['High'], low=df_p['Low'], close=df_p['Close'], name='ローソク足'))
                    fig_p.add_trace(go.Scatter(x=df_p.index, y=df_p['MA_L'], mode='lines', name=name_l, line=dict(color='orange', width=1.5)))
                    
                    if entry_price > 0:
                        fig_p.add_hline(y=entry_price, line_dash="solid", line_color="white", annotation_text="取得単価", annotation_position="top left")
                        fig_p.add_hline(y=take_profit, line_dash="dot", line_color="lightgreen", annotation_text="利確目標", annotation_position="top right")
                        fig_p.add_hline(y=stop_loss, line_dash="dot", line_color="red", annotation_text="損切ライン", annotation_position="bottom right")

                    fig_p.update_layout(xaxis_rangeslider_visible=False, height=400, template="plotly_dark", dragmode="pan", margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})
                
                st.markdown("---")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
        
        total_pnl = total_current_value - total_invested
        pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        total_color = "normal" if total_pnl >= 0 else "inverse"
        
        with dash_placeholder.container():
            st.markdown('<div class="total-dash"><h3>📊 ポートフォリオ総合ダッシュボード</h3></div>', unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            d1.metric("総投資額 (元本)", f"¥{total_invested:,.0f}")
            d2.metric("現在の総資産額", f"¥{total_current_value:,.0f}", f"{total_pnl:,.0f}円 ({pnl_percent:,.1f}%)", delta_color=total_color)
            st.markdown("---")