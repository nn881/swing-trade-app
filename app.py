import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="スイング監視", layout="wide")

st.markdown("""
    <style>
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; padding-bottom: 0px !important; }
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
MAJOR_STOCKS = list(MAJOR_NAMES.keys())
TARGET_STOCKS = list(dict.fromkeys(MY_STOCKS + MAJOR_STOCKS))

# ==========================================
# 新機能③ 決算日取得関数
# ==========================================
@st.cache_data(ttl=3600)
def get_earnings_date(code):
    url = f"https://finance.yahoo.co.jp/quote/{code}.T"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        html = requests.get(url, headers=headers, timeout=5).text
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # 決算発表日を抽出（例: "決算発表日 2026/11/05"）
        match = re.search(r'決算発表日.*?([0-9]{4}/[0-9]{1,2}/[0-9]{1,2})', text)
        if match:
            date_str = match.group(1)
            earnings_date = datetime.strptime(date_str, "%Y/%m/%d")
            # 現在から7日以内か判定
            days_left = (earnings_date - datetime.now()).days
            if 0 <= days_left <= 7:
                return f"⚠️ 注意：近日中に決算発表が予定されています（{date_str}）"
        return None
    except:
        return None

if "manual_tickers" not in st.session_state: st.session_state.manual_tickers = "7203\n8306\n9984\n6758\n6861"
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "current_mode" not in st.session_state: st.session_state.current_mode = None

st.sidebar.header("⚙️ 動作モード")
mode = st.sidebar.radio("モードを選択", ["手動監視モード", "🤖 注目・主要銘柄 自動スクリーニング"], index=1)

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
        st.write("👇 **表の行をタップすると、下のチャートが切り替わります**")
        event = st.dataframe(df_result, use_container_width=True, on_select="rerun", selection_mode="single-row")
        
        if event.selection.rows:
            selected_index = event.selection.rows[0]
            st.session_state.selected_code = df_result.iloc[selected_index]["コード"]
            st.session_state.selected_name = df_result.iloc[selected_index]["銘柄名"]
            
        st.subheader(f"② {st.session_state.selected_code} {st.session_state.selected_name} の詳細分析")
        
        # 新機能③：決算日警告の表示
        warning_msg = get_earnings_date(st.session_state.selected_code)
        if warning_msg:
            st.error(warning_msg)
        
        st.info("💡 信用倍率や買残などの需給データは、以下のボタンからYahoo!ファイナンスで正確な最新情報をご確認ください。")
        yahoo_url = f"https://finance.yahoo.co.jp/quote/{st.session_state.selected_code}.T/margin"
        st.link_button(f"🔗 {st.session_state.selected_name} の「信用残高・信用倍率」を確認する", yahoo_url, type="primary")
        
        selected_ticker = st.session_state.selected_code + ".T"
        df_chart = yf.Ticker(selected_ticker).history(period="6mo")
        
        if not df_chart.empty:
            df_chart['5MA'] = df_chart['Close'].rolling(window=5).mean()
            df_chart['25MA'] = df_chart['Close'].rolling(window=25).mean()
            
            # 新機能①：ボリンジャーバンド計算
            df_chart['BB_std'] = df_chart['Close'].rolling(window=25).std()
            df_chart['BB_upper'] = df_chart['25MA'] + (df_chart['BB_std'] * 2)
            df_chart['BB_lower'] = df_chart['25MA'] - (df_chart['BB_std'] * 2)
            
            # 新機能②：リスク管理（ATRを利用した利確・損切りライン）計算
            df_chart['High-Low'] = df_chart['High'] - df_chart['Low']
            df_chart['High-PrevClose'] = abs(df_chart['High'] - df_chart['Close'].shift(1))
            df_chart['Low-PrevClose'] = abs(df_chart['Low'] - df_chart['Close'].shift(1))
            df_chart['TR'] = df_chart[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
            atr = df_chart['TR'].rolling(window=14).mean().iloc[-1]
            
            latest_c = df_chart['Close'].iloc[-1]
            take_profit = latest_c + (atr * 2) # 利確目標（現在値 + ATR×2）
            stop_loss = latest_c - (atr * 1.5) # 損切りライン（現在値 - ATR×1.5）
            
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

            # ローソク足と移動平均線
            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='ローソク足'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['5MA'], mode='lines', name='5日線', line=dict(color='lime', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['25MA'], mode='lines', name='25日線', line=dict(color='orange', width=1.5)), row=1, col=1)
            
            # ボリンジャーバンド描画（半透明の帯）
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['BB_upper'], mode='lines', line=dict(width=0), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['BB_lower'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(173, 216, 230, 0.1)', name='ボリンジャー±2σ'), row=1, col=1)
            
            # リスク管理ライン（最新日から未来方向へ線を引く）
            last_date = df_chart.index[-1]
            future_date = last_date + timedelta(days=5) # 5日先まで線を伸ばす
            fig.add_trace(go.Scatter(x=[last_date, future_date], y=[take_profit, take_profit], mode='lines+text', text=["", "🎯 利確目安"], textposition="top right", name='利確目安', line=dict(color='lightgreen', width=2, dash='dot')), row=1, col=1)
            fig.add_trace(go.Scatter(x=[last_date, future_date], y=[stop_loss, stop_loss], mode='lines+text', text=["", "✂️ 損切ライン"], textposition="bottom right", name='損切ライン', line=dict(color='red', width=2, dash='dot')), row=1, col=1)

            # MACDとRSI
            fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['MACD_Hist'], name='MACDヒストグラム', marker_color='gray'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACD'], mode='lines', name='MACD', line=dict(color='cyan', width=1)), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Signal'], mode='lines', name='シグナル', line=dict(color='magenta', width=1)), row=2, col=1)

            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI'], mode='lines', name='RSI', line=dict(color='yellow', width=1)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

            fig.update_layout(
                xaxis_rangeslider_visible=False, 
                height=650, 
                template="plotly_dark",
                margin=dict(l=10, r=10, t=10, b=10), 
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("現在、強力な買いシグナルが出ている銘柄は見つかりませんでした。")