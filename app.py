import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="スイング監視", layout="wide")

# ① 主要銘柄の大幅増量（約80社）
MAJOR_STOCKS = [
    # 自動車・輸送機
    "7203", "7267", "7269", "6902", "7201", "7270",
    # 電機・精密・半導体
    "6758", "6861", "8035", "6501", "6981", "6954", "6594", "6702", "6752", "7741", "7751", "6146", "6857", "6920",
    # 通信・情報
    "9984", "9432", "9433", "4307",
    # 銀行・証券・保険
    "8306", "8316", "8411", "8766", "8604", "8750",
    # 商社
    "8058", "8031", "8001", "8053", "8002",
    # 小売・サービス・ゲーム
    "9983", "7974", "3382", "4661", "6098", "4751", "9843",
    # 医薬品・化学
    "4063", "4502", "4568", "4519", "4503", "4523", "4528", "4911", "4901", "4188", "3407", "3402",
    # 機械・インフラ・不動産・その他
    "6367", "6273", "6301", "8801", "8802", "1925", "5401", "5108", "9022", "9020", "9101", "9104"
]
# 重複を削除しておく
MAJOR_STOCKS = list(dict.fromkeys(MAJOR_STOCKS))

# --- ② 状態（記憶）の管理 ---
# 表をクリックした際の「再読み込みループ」を防ぐため、結果を記憶する箱を用意します
if "manual_tickers" not in st.session_state:
    st.session_state.manual_tickers = "7203\n8306\n9984\n6758\n6861"
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None  # 抽出結果を記憶
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None

st.sidebar.header("⚙️ 動作モード")
mode = st.sidebar.radio("モードを選択", ["手動監視モード", "🤖 主要銘柄 自動スクリーニング"])

# モードが切り替わったら記憶をリセット
if st.session_state.current_mode != mode:
    st.session_state.analysis_result = None
    st.session_state.current_mode = mode

tickers_to_analyze = []
run_analysis = False # 解析を実際に実行するかどうかのスイッチ

if mode == "手動監視モード":
    st.sidebar.write("監視したい銘柄コードを**改行**で入力してください")
    ticker_input = st.sidebar.text_area("銘柄コード (1行に1つ)", value=st.session_state.manual_tickers, height=150)
    
    # 入力内容が変わった、またはまだ一度も解析していない場合のみ解析スイッチON
    if ticker_input != st.session_state.manual_tickers or st.session_state.analysis_result is None:
        st.session_state.manual_tickers = ticker_input
        tickers_to_analyze = [t.strip() + ".T" for t in ticker_input.split('\n') if t.strip()]
        run_analysis = True

else:
    st.sidebar.success(f"日本を代表する主要銘柄（{len(MAJOR_STOCKS)}社）から自動抽出します。")
    if st.sidebar.button("▶️ スクリーニング開始"):
        tickers_to_analyze = [t + ".T" for t in MAJOR_STOCKS]
        run_analysis = True # ボタンが押された時だけ解析スイッチON
    else:
        if st.session_state.analysis_result is None:
            st.info("上の「スクリーニング開始」ボタンを押してください。")

st.title("📈 スイングトレード監視ダッシュボード")

# --- 解析処理（スイッチがONの時だけ実行） ---
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
            
            try:
                name = stock.info.get('shortName', code_str)
            except:
                name = code_str
                
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
    
    # 抽出結果をセッション（記憶）に保存する
    st.session_state.analysis_result = data_list
    if data_list:
        st.session_state.selected_code = data_list[0]["コード"]
        st.session_state.selected_name = data_list[0]["銘柄名"]


# --- 画面表示処理（記憶されたデータを使って表示するため、ループしない） ---
if st.session_state.analysis_result is not None:
    data_list = st.session_state.analysis_result
    
    if len(data_list) > 0:
        df_result = pd.DataFrame(data_list)
        st.subheader("① 買いシグナル抽出結果")
        st.write("👇 **表の行をクリック（タップ）すると、下のチャートが切り替わります**")
        
        event = st.dataframe(
            df_result, 
            use_container_width=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )
        
        # 行がクリックされたら、選択された銘柄を更新する
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
        st.subheader("① 買いシグナル抽出結果")
        st.warning("現在、強力な買いシグナルが出ている銘柄は見つかりませんでした。")