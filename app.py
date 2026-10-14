import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="スイング監視", layout="wide")

# ==========================================
# ⚙️ カスタマイズ設定エリア
# ==========================================
# ① ここに、ご自身が注目している特定の銘柄コードを追加してください（4桁の数字）
MY_STOCKS = [
    "7974", # 任天堂
    "4751", # サイバーエージェント
    "9101", # 日本郵船
    "3990", # UUUM (例)
]

# ② 日本を代表する主要銘柄リスト（約80社）
MAJOR_STOCKS = [
    "7203", "7267", "7269", "6902", "7201", "7270", "6758", "6861", "8035", "6501", 
    "6981", "6954", "6594", "6702", "6752", "7741", "7751", "6146", "6857", "6920",
    "9984", "9432", "9433", "4307", "8306", "8316", "8411", "8766", "8604", "8750",
    "8058", "8031", "8001", "8053", "8002", "9983", "3382", "4661", "6098", "9843",
    "4063", "4502", "4568", "4519", "4503", "4523", "4528", "4911", "4901", "4188", 
    "3407", "3402", "6367", "6273", "6301", "8801", "8802", "1925", "5401", "5108", 
    "9022", "9020", "9104"
]

# カスタム銘柄と主要銘柄を結合し、重複を削除
TARGET_STOCKS = list(dict.fromkeys(MY_STOCKS + MAJOR_STOCKS))

# ==========================================
# アプリケーション本体
# ==========================================
if "manual_tickers" not in st.session_state:
    st.session_state.manual_tickers = "7203\n8306\n9984\n6758\n6861"
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None

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
    else:
        if st.session_state.analysis_result is None:
            st.info("上の「スクリーニング開始」ボタンを押してください。")

st.title("📈 スイングトレード監視ダッシュボード")

# --- 解析処理 ---
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
            if df.empty or len(df) < 35: continue # MACD用に期間確保
            
            # 1. 移動平均線の計算
            df['5MA'] = df['Close'].rolling(window=5).mean()
            df['25MA'] = df['Close'].rolling(window=25).mean()
            
            # 2. RSI（相対力指数: 14日）の計算
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # 3. MACDの計算
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            latest_close = float(df['Close'].dropna().values[-1])
            latest_5ma = float(df['5MA'].dropna().values[-1])
            latest_25ma = float(df['25MA'].dropna().values[-1])
            prev_5ma = float(df['5MA'].dropna().values[-2])
            prev_25ma = float(df['25MA'].dropna().values[-2])
            
            latest_rsi = float(df['RSI'].dropna().values[-1])
            latest_macd = float(df['MACD'].dropna().values[-1])
            latest_signal = float(df['Signal'].dropna().values[-1])
            prev_macd = float(df['MACD'].dropna().values[-2])
            prev_signal = float(df['Signal'].dropna().values[-2])
            
            # --- 複合買いシグナル判定（多角的な視点） ---
            signal_text = "様子見"
            
            # 条件A: 5日線と25日線のゴールデンクロス
            is_gc_ma = (prev_5ma <= prev_25ma) and (latest_5ma > latest_25ma)
            # 条件B: MACDのゴールデンクロス（トレンド転換の先行指標）
            is_gc_macd = (prev_macd <= prev_signal) and (latest_macd > latest_signal)
            # 条件C: 上昇トレンド（5日線、25日線より上）
            is_uptrend = (latest_close > latest_25ma) and (latest_5ma > latest_25ma)
            
            if is_gc_ma and is_gc_macd:
                signal_text = "🌟 超激アツ！(Wゴールデンクロス)"
            elif is_gc_ma:
                signal_text = "🔥 買い(MAクロス)"
            elif is_gc_macd and is_uptrend:
                signal_text = "🔥 買い(MACD転換+上昇)"
            elif is_uptrend:
                if latest_rsi > 70:
                    signal_text = "⚠️ 買われすぎ(利確注意)"
                else:
                    signal_text = "👍 上昇トレンド"
            elif latest_close < latest_25ma:
                if latest_rsi < 30:
                    signal_text = "📉 売られすぎ(反発狙い)"
                else:
                    signal_text = "⚠️ 下落トレンド"
            
            if mode == "🤖 注目・主要銘柄 自動スクリーニング":
                if signal_text not in ["🌟 超激アツ！(Wゴールデンクロス)", "🔥 買い(MAクロス)", "🔥 買い(MACD転換+上昇)", "👍 上昇トレンド", "📉 売られすぎ(反発狙い)"]:
                    continue
            
            # --- 銘柄名取得の安定化 ---
            try:
                # yfinanceの仕様変更対策：ロングネームを取得し、なければショート、それでもなければコード
                name = stock.info.get('longName') or stock.info.get('shortName', code_str)
            except:
                name = code_str
                
            data_list.append({
                "コード": code_str,
                "銘柄名": name,
                "終値": round(latest_close, 1),
                "RSI": round(latest_rsi, 1), # RSIを追加表示
                "判定": signal_text
            })
        except Exception:
            continue
            
    status_text.text("✅ 解析完了！")
    
    st.session_state.analysis_result = data_list
    if data_list:
        st.session_state.selected_code = data_list[0]["コード"]
        st.session_state.selected_name = data_list[0]["銘柄名"]


# --- 画面表示処理 ---
if st.session_state.analysis_result is not None:
    data_list = st.session_state.analysis_result
    
    if len(data_list) > 0:
        df_result = pd.DataFrame(data_list)
        st.subheader("① 買いシグナル抽出結果")
        
        # RSIが低い(割安)順に並べ替えて見やすくする機能
        df_result = df_result.sort_values('RSI', ascending=True).reset_index(drop=True)
        
        st.write("👇 **表の行をクリック（タップ）すると、下のチャートが切り替わります**")
        
        event = st.dataframe(
            df_result, 
            use_container_width=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )
        
        if event.selection.rows:
            selected_index = event.selection.rows[0]
            st.session_state.selected_code = df_result.iloc[selected_index]["コード"]
            st.session_state.selected_name = df_result.iloc[selected_index]["銘柄名"]
            
        st.subheader("② 詳細チャート確認 (MACD・RSI付き)")
        
        display_name = f"{st.session_state.selected_code} {st.session_state.selected_name}"
        selected_ticker = st.session_state.selected_code + ".T"

        df_chart = yf.Ticker(selected_ticker).history(period="6mo")
        if not df_chart.empty:
            df_chart['5MA'] = df_chart['Close'].rolling(window=5).mean()
            df_chart['25MA'] = df_chart['Close'].rolling(window=25).mean()
            
            # MACD
            exp1 = df_chart['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df_chart['Close'].ewm(span=26, adjust=False).mean()
            df_chart['MACD'] = exp1 - exp2
            df_chart['Signal'] = df_chart['MACD'].ewm(span=9, adjust=False).mean()
            df_chart['MACD_Hist'] = df_chart['MACD'] - df_chart['Signal']
            
            # RSI
            delta = df_chart['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df_chart['RSI'] = 100 - (100 / (1 + rs))

            # サブプロットの作成 (上: ローソク足, 中: MACD, 下: RSI)
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, 
                                row_heights=[0.6, 0.2, 0.2])

            # 1段目: ローソク足と移動平均線
            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='ローソク足'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['5MA'], mode='lines', name='5日線', line=dict(color='lime', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['25MA'], mode='lines', name='25日線', line=dict(color='orange', width=1.5)), row=1, col=1)

            # 2段目: MACD
            fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['MACD_Hist'], name='MACDヒストグラム', marker_color='gray'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACD'], mode='lines', name='MACD', line=dict(color='cyan', width=1)), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Signal'], mode='lines', name='シグナル', line=dict(color='magenta', width=1)), row=2, col=1)

            # 3段目: RSI
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI'], mode='lines', name='RSI', line=dict(color='yellow', width=1)), row=3, col=1)
            # RSIの目安ライン(30と70)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

            fig.update_layout(title=f"{display_name} の日足チャート分析", xaxis_rangeslider_visible=False, height=800, template="plotly_dark")
            
            # y軸のラベル設定
            fig.update_yaxes(title_text="株価", row=1, col=1)
            fig.update_yaxes(title_text="MACD", row=2, col=1)
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.subheader("① 買いシグナル抽出結果")
        st.warning("現在、強力な買いシグナルが出ている銘柄は見つかりませんでした。")