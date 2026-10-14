import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="スイング監視", layout="wide")

MY_STOCKS = ["7974", "4751", "9101", "3990"]
MAJOR_NAMES = {
    "7203": "トヨタ自動車", "7267": "ホンダ", "7269": "スズキ", "6902": "デンソー", "7201": "日産自動車", "7270": "SUBARU",
    "6758": "ソニーG", "6861": "キーエンス", "8035": "東京エレクトロン", "6501": "日立製作所", "6981": "村田製作所", "6954": "ファナック",
    "6594": "ニデック", "6702": "富士通", "6752": "パナソニック", "7741": "HOYA", "7751": "キヤノン", "6146": "ディスコ", "6857": "アドバンテスト", "6920": "レーザーテック",
    "9984": "ソフトバンクG", "9432": "NTT", "9433": "KDDI", "4307": "野村総研",
    "8306": "三菱UFJ", "8316": "三井住友", "8411": "みずほ", "8766": "東京海上", "8604": "野村HD", "8750": "第一生命",
    "8058": "三菱商事", "8031": "三井物産", "8001": "伊藤忠商事", "8053": "住友商事", "8002": "丸紅",
    "9983": "ファーストリテイリング", "7974": "任天堂", "3382": "セブン＆アイ", "4661": "オリエンタルランド", "6098": "リクルート", "9843": "ニトリ",
    "4063": "信越化学工業", "4502": "武田薬品工業", "4568": "第一三共", "4519": "中外製薬", "4503": "アステラス製薬", "4523": "エーザイ", "4528": "小野薬品工業", "4911": "資生堂", "4901": "富士フイルム", "4188": "三菱ケミカルG", "3407": "旭化成", "3402": "東レ",
    "6367": "ダイキン工業", "6273": "SMC", "6301": "コマツ", "8801": "三井不動産", "8802": "三菱地所", "1925": "大和ハウス", "5401": "日本製鉄", "5108": "ブリヂストン", "9022": "JR東海", "9020": "JR東日本", "9104": "商船三井", "9101": "日本郵船"
}
MAJOR_STOCKS = list(MAJOR_NAMES.keys())
TARGET_STOCKS = list(dict.fromkeys(MY_STOCKS + MAJOR_STOCKS))

# ==========================================
# ① 需給データの取得ロジックをさらに強固に修正
# ==========================================
@st.cache_data(ttl=3600)
def get_margin_data(code):
    url = f"https://finance.yahoo.co.jp/quote/{code}.T/margin"
    # Yahooファイナンスのブロックを避けるための強力なヘッダー
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
    try:
        html = requests.get(url, headers=headers, timeout=5).text
        soup = BeautifulSoup(html, 'html.parser')
        
        # 邪魔なスクリプトタグなどを削除してからテキスト化
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        
        # 【修正】日付などを誤検知しないよう、後ろに「株」や「倍」がつく数字だけを厳格に狙う
        buy_match = re.search(r'信用買残.*?([0-9,]+)\s*株', text)
        sell_match = re.search(r'信用売残.*?([0-9,]+)\s*株', text)
        ratio_match = re.search(r'(?:貸借|信用)倍率.*?([0-9.,]+)\s*倍', text)
        
        buy_val = float(buy_match.group(1).replace(',', '')) if buy_match else 0
        sell_val = float(sell_match.group(1).replace(',', '')) if sell_match else 0
        
        # サイトに倍率が載っていればそれを、なければ自前で計算
        if ratio_match:
            ratio_str = ratio_match.group(1) + "倍"
        elif sell_val > 0:
            ratio_str = f"{round(buy_val / sell_val, 2)}倍"
        elif buy_val > 0:
            ratio_str = "売残0"
        else:
            ratio_str = "-"
            
        return {
            "買残": f"{int(buy_val):,}株" if buy_val > 0 else "-",
            "売残": f"{int(sell_val):,}株" if sell_val > 0 else "-",
            "倍率": ratio_str
        }
    except Exception:
        return {"買残": "-", "売残": "-", "倍率": "-"}

if "manual_tickers" not in st.session_state: st.session_state.manual_tickers = "7203\n8306\n9984\n6758\n6861"
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "current_mode" not in st.session_state: st.session_state.current_mode = None

st.sidebar.header("⚙️ 動作モード")
mode = st.sidebar.radio("モードを選択", ["手動監視モード", "🤖 注目・主要銘柄 自動スクリーニング"])

if st.session_state.current_mode != mode:
    st.session_state.analysis_result = None
    st.session_state.current_mode = mode

tickers_to_analyze = []
run_analysis = False

if mode == "手動監視モード":
    st.sidebar.write("監視したい銘柄コードを**改行**で入力してください")
    ticker_input = st.sidebar.text_area("銘柄コード (1行に1つ)", value=st.session_state.manual_tickers, height=150)
    if ticker_input != st.session_state.manual_tickers or st.session_state.analysis_result is None:
        st.session_state.manual_tickers = ticker_input
        tickers_to_analyze = [t.strip() + ".T" for t in ticker_input.split('\n') if t.strip()]
        run_analysis = True
else:
    st.sidebar.success(f"ご自身の注目銘柄と主要銘柄（計{len(TARGET_STOCKS)}社）から自動抽出します。")
    if st.sidebar.button("▶️ スクリーニング開始"):
        tickers_to_analyze = [t + ".T" for t in TARGET_STOCKS]
        run_analysis = True

st.title("📈 スイングトレード監視ダッシュボード")

if run_analysis and tickers_to_analyze:
    st.subheader("① 買いシグナル抽出結果")
    progress_bar = st.progress(0)
    status_text = st.empty()
    data_list = []
    
    for i, ticker in enumerate(tickers_to_analyze):
        code_str = ticker.replace('.T', '')
        progress_bar.progress((i + 1) / len(tickers_to_analyze))
        status_text.text(f"データ解析中... {i+1}/{len(tickers_to_analyze)} ({code_str})")
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="6mo")
            if df.empty or len(df) < 60: continue
            
            df['5MA'] = df['Close'].rolling(window=5).mean()
            df['25MA'] = df['Close'].rolling(window=25).mean()
            df['Volume_5MA'] = df['Volume'].rolling(window=5).mean()
            df['High_60'] = df['High'].rolling(window=60).max()
            
            latest_close = float(df['Close'].dropna().values[-1])
            latest_5ma = float(df['5MA'].dropna().values[-1])
            latest_25ma = float(df['25MA'].dropna().values[-1])
            prev_5ma = float(df['5MA'].dropna().values[-2])
            prev_25ma = float(df['25MA'].dropna().values[-2])
            
            latest_vol = float(df['Volume'].dropna().values[-1])
            avg_vol_5 = float(df['Volume_5MA'].dropna().values[-2])
            latest_high_60 = float(df['High_60'].dropna().values[-1])
            
            distance_to_res = ((latest_high_60 - latest_close) / latest_close) * 100
            is_vol_surge = latest_vol > (avg_vol_5 * 1.5)
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            latest_rsi = float(df['RSI'].dropna().values[-1])
            
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9, adjust=False).mean()
            latest_macd, prev_macd = float(macd.dropna().values[-1]), float(macd.dropna().values[-2])
            latest_sig, prev_sig = float(signal_line.dropna().values[-1]), float(signal_line.dropna().values[-2])
            
            is_gc_ma = (prev_5ma <= prev_25ma) and (latest_5ma > latest_25ma)
            is_gc_macd = (prev_macd <= prev_sig) and (latest_macd > latest_sig)
            is_uptrend = (latest_close > latest_25ma) and (latest_5ma > latest_25ma)
            
            signal_text = "様子見"
            if is_gc_ma and is_gc_macd: signal_text = "🌟 超激アツ！(Wクロス)"
            elif is_gc_ma: signal_text = "🔥 買い(MAクロス)"
            elif is_gc_macd and is_uptrend: signal_text = "🔥 買い(MACD転換)"
            elif is_uptrend: signal_text = "👍 上昇トレンド"
            elif latest_close < latest_25ma and latest_rsi < 30: signal_text = "📉 売られすぎ(反発狙い)"
            
            if "買い" in signal_text or "激アツ" in signal_text:
                if distance_to_res < 3.0: signal_text = "⚠️ 買い(上値抵抗線接近)"
                elif is_vol_surge: signal_text = signal_text.replace("買い", "買い(大商い)").replace("超激アツ！", "超激アツ！(大商い)")

            if mode == "🤖 注目・主要銘柄 自動スクリーニング":
                if signal_text == "様子見" or "⚠️" in signal_text: continue
            
            name = MAJOR_NAMES.get(code_str, code_str)
            if name == code_str:
                try: name = stock.info.get('longName') or stock.info.get('shortName', code_str)
                except: pass
                
            data_list.append({
                "コード": code_str, "銘柄名": name, "終値": round(latest_close, 1),
                "上値余地": f"{round(distance_to_res, 1)}%", "RSI": round(latest_rsi, 1), "判定": signal_text
            })
        except Exception:
            continue
            
    status_text.text("✅ 解析完了！")
    st.session_state.analysis_result = data_list
    if data_list:
        st.session_state.selected_code = data_list[0]["コード"]
        st.session_state.selected_name = data_list[0]["銘柄名"]

if st.session_state.analysis_result is not None:
    data_list = st.session_state.analysis_result
    
    if len(data_list) > 0:
        df_result = pd.DataFrame(data_list)
        df_result = df_result.sort_values('RSI', ascending=True).reset_index(drop=True)
        
        st.subheader("① 買いシグナル抽出結果")
        st.write("👇 **表の行をタップすると、下のチャートと需給データが切り替わります**")
        event = st.dataframe(df_result, use_container_width=True, on_select="rerun", selection_mode="single-row")
        
        if event.selection.rows:
            selected_index = event.selection.rows[0]
            st.session_state.selected_code = df_result.iloc[selected_index]["コード"]
            st.session_state.selected_name = df_result.iloc[selected_index]["銘柄名"]
            
        st.subheader(f"② {st.session_state.selected_code} {st.session_state.selected_name} の詳細分析")
        
        margin_data = get_margin_data(st.session_state.selected_code)
        cols = st.columns(3)
        cols[0].metric(label="信用倍率 (需給バランス)", value=margin_data["倍率"])
        cols[1].metric(label="信用買残 (将来の売り圧力)", value=margin_data["買残"])
        cols[2].metric(label="信用売残 (将来の買い圧力)", value=margin_data["売残"])
        
        selected_ticker = st.session_state.selected_code + ".T"
        df_chart = yf.Ticker(selected_ticker).history(period="6mo")
        
        if not df_chart.empty:
            df_chart['5MA'] = df_chart['Close'].rolling(window=5).mean()
            df_chart['25MA'] = df_chart['Close'].rolling(window=25).mean()
            
            exp1 = df_chart['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df_chart['Close'].ewm(span=26, adjust=False).mean()
            df_chart['MACD'] = exp1 - exp2
            df_chart['Signal'] = df_chart['MACD'].ewm(span=9, adjust=False).mean()
            df_chart['MACD_Hist'] = df_chart['MACD'] - df_chart['Signal']
            
            delta = df_chart['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df_chart['RSI'] = 100 - (100 / (1 + (gain / loss)))

            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])

            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='ローソク足'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['5MA'], mode='lines', name='5日線', line=dict(color='lime', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['25MA'], mode='lines', name='25日線', line=dict(color='orange', width=1.5)), row=1, col=1)

            fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['MACD_Hist'], name='MACDヒストグラム', marker_color='gray'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACD'], mode='lines', name='MACD', line=dict(color='cyan', width=1)), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Signal'], mode='lines', name='シグナル', line=dict(color='magenta', width=1)), row=2, col=1)

            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI'], mode='lines', name='RSI', line=dict(color='yellow', width=1)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

            # ==========================================
            # ② スマホでの操作性（ドラッグ＆ピンチ）の改善設定
            # ==========================================
            fig.update_layout(
                xaxis_rangeslider_visible=False, 
                height=650, 
                template="plotly_dark",
                dragmode="pan", # 【追加】デフォルトを「範囲選択(Zoom)」から「移動(Pan)」に変更
                margin=dict(l=10, r=10, t=10, b=10), 
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.02, 
                    xanchor="center", 
                    x=0.5
                )
            )
            
            # 【追加】config でスクロール（ピンチ）による拡大縮小を有効化
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    else:
        st.warning("現在、強力な買いシグナルが出ている銘柄は見つかりませんでした。")