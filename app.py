import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="スイング監視", layout="wide")

# --- 修正1：エラー対策 ---
# Wikipediaのブロックを回避するため、日本を代表する主要銘柄をシステムに直接組み込みます。
MAJOR_STOCKS = [
    "7203", "8306", "9984", "6758", "6861", "9983", "8035", "4063", "6501", "8316",
    "7267", "9433", "9432", "8001", "8031", "8058", "6367", "7974", "6098", "4502",
    "4568", "7741", "4661", "6273", "6902", "8411", "3382", "4503", "6752", "6981",
    "7269", "6954", "8766", "8053", "8801", "1925", "4519", "7751", "6594", "4901"
]

# --- 修正2：手動銘柄の保存 ---
# Session State（セッション状態）を使って、ユーザーの入力を画面更新後も保持します。
if "manual_tickers" not in st.session_state:
    st.session_state.manual_tickers = "7203\n8306\n9984\n6758\n6861"

st.sidebar.header("⚙️ 動作モード")
mode = st.sidebar.radio("モードを選択", ["手動監視モード", "🤖 主要銘柄 自動スクリーニング"])

tickers = []
if mode == "手動監視モード":
    st.sidebar.write("監視したい銘柄コードを**改行**で入力してください")
    # valueに保存された状態をセットし、入力されたら保存し直す
    ticker_input = st.sidebar.text_area("銘柄コード (1行に1つ)", value=st.session_state.manual_tickers, height=150)
    st.session_state.manual_tickers = ticker_input
    tickers = [t.strip() + ".T" for t in ticker_input.split('\n') if t.strip()]
else:
    st.sidebar.success("日本を代表する主要銘柄（約40社）から、買いシグナルが出ている株を自動抽出します。エラーなく高速に処理されます。")
    if st.sidebar.button("▶️ スクリーニング開始"):
        tickers = [t + ".T" for t in MAJOR_STOCKS]
    else:
        st.info("上の「スクリーニング開始」ボタンを押してください。")

st.title("📈 スイングトレード監視ダッシュボード")

data_list = []

if tickers:
    st.subheader("① 買いシグナル抽出結果")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        code_str = ticker.replace('.T', '')
        progress_bar.progress((i + 1) / len(tickers))
        status_text.text(f"データ解析中... {i+1}/{len(tickers)} ({code_str})")
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="6mo")
            if df.empty or len(df) < 26: continue
            
            df['5MA'] = df['Close'].rolling(window=5).mean()
            df['25MA'] = df['Close'].rolling(window=25).mean()
            
            latest_close = float(df['Close'].dropna().values[-1])
            latest_5ma = float(df['5MA'].dropna().values[-1])
            latest_25ma = float(df['25MA'].dropna().values[-1])
            prev_5ma = float(df['5MA'].dropna().values[-2])
            prev_25ma = float(df['25MA'].dropna().values[-2])
            
            if prev_5ma <= prev_25ma and latest_5ma > latest_25ma:
                signal = "🔥 激アツ！買いシグナル"
            elif latest_close > latest_25ma and latest_5ma > latest_25ma:
                signal = "👍 上昇トレンド"
            elif latest_close < latest_25ma:
                signal = "⚠️ 下落トレンド"
            else:
                signal = "様子見"
            
            if mode == "🤖 主要銘柄 自動スクリーニング":
                if signal not in ["🔥 激アツ！買いシグナル", "👍 上昇トレンド"]:
                    continue
            
            # --- 修正3：銘柄名の取得 ---
            # 抽出対象になった銘柄のみ「銘柄名」を取得（全銘柄やると重くなるため）
            try:
                name = stock.info.get('shortName', code_str)
            except:
                name = code_str # 取得失敗時はコードを表示
                
            data_list.append({
                "コード": code_str,
                "銘柄名": name,
                "終値": round(latest_close, 1),
                "5日線": round(latest_5ma, 1),
                "25日線": round(latest_25ma, 1),
                "判定": signal
            })
        except Exception:
            continue
            
    status_text.text("✅ 解析完了！")
    
    if data_list:
        df_result = pd.DataFrame(data_list)
        st.write("👇 **表の行をクリック（タップ）すると、下のチャートが切り替わります**")
        
        # --- 修正4：チャート切り替えの安定化 ---
        # 選択された銘柄をSession Stateに保存し、確実にチャートに反映させる
        if "selected_code" not in st.session_state:
            st.session_state.selected_code = df_result.iloc[0]["コード"]
            st.session_state.selected_name = df_result.iloc[0]["銘柄名"]

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
            
        st.subheader("② チャート確認")
        
        display_name = f"{st.session_state.selected_code} {st.session_state.selected_name}"
        selected_ticker = st.session_state.selected_code + ".T"

        df_chart = yf.Ticker(selected_ticker).history(period="6mo")
        if not df_chart.empty:
            df_chart['5MA'] = df_chart['Close'].rolling(window=5).mean()
            df_chart['25MA'] = df_chart['Close'].rolling(window=25).mean()

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='ローソク足'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['5MA'], mode='lines', name='5日線(短期)', line=dict(color='lime', width=1.5)))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['25MA'], mode='lines', name='25日線(中期)', line=dict(color='orange', width=2)))

            fig.update_layout(title=f"{display_name} の日足チャート", xaxis_rangeslider_visible=False, height=500, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("現在、強力な買いシグナルが出ている銘柄は見つかりませんでした。")