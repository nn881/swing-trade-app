import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import urllib.request

st.set_page_config(page_title="スイング監視", layout="wide")

# --- 修正箇所1：Wikipediaからの取得エラー（ブロック）対策 ---
@st.cache_data(ttl=86400)
def get_nikkei225():
    url = "https://ja.wikipedia.org/wiki/%E6%97%A5%E7%B5%8C%E5%B9%B3%E5%9D%87%E6%A0%AA%E4%BE%A1%E3%81%AE%E6%A7%8B%E6%88%90%E9%8A%98%E6%9F%84%E4%B8%80%E8%A6%A7"
    # 普通のブラウザ（Chrome等）からのアクセスに見せかける偽装ヘッダー
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read()
    
    # 取得したHTMLからテーブルを読み込む
    tables = pd.read_html(html)
    df = tables[1]
    return [str(code) + ".T" for code in df['コード']]

st.sidebar.header("⚙️ 動作モード")
mode = st.sidebar.radio("モードを選択", ["手動監視モード", "🤖 日経225 自動スクリーニング"])

tickers = []
if mode == "手動監視モード":
    # --- 修正箇所2：スマホで入力しやすい「改行区切り」のテキストエリアに変更 ---
    st.sidebar.write("監視したい銘柄コードを**改行**で入力してください")
    default_tickers = "7203\n8306\n9984\n6758\n6861"
    ticker_input = st.sidebar.text_area("銘柄コード (1行に1つ)", default_tickers, height=150)
    
    # 改行(\n)で分割してリスト化する
    tickers = [t.strip() + ".T" for t in ticker_input.split('\n') if t.strip()]
else:
    st.sidebar.success("日経225の全銘柄から、買いシグナルが出ている株だけを自動で探し出します。")
    if st.sidebar.button("▶️ スクリーニング開始"):
        tickers = get_nikkei225()
    else:
        st.info("上の「スクリーニング開始」ボタンを押してください。")

st.title("📈 スイングトレード監視ダッシュボード")

data_list = []

if tickers:
    st.subheader("① 買いシグナル抽出結果")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        progress_bar.progress((i + 1) / len(tickers))
        status_text.text(f"データ解析中... {i+1}/{len(tickers)} ({ticker.replace('.T', '')})")
        
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
            
            if mode == "🤖 日経225 自動スクリーニング":
                if signal not in ["🔥 激アツ！買いシグナル", "👍 上昇トレンド"]:
                    continue
            
            data_list.append({
                "銘柄": ticker.replace(".T", ""),
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
        
        event = st.dataframe(
            df_result, 
            use_container_width=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )
        
        st.subheader("② チャート確認")
        
        if event.selection.rows:
            selected_index = event.selection.rows[0]
            selected_name = df_result.iloc[selected_index]["銘柄"]
        else:
            selected_name = df_result.iloc[0]["銘柄"]
            
        selected_ticker = selected_name + ".T"

        df_chart = yf.Ticker(selected_ticker).history(period="6mo")
        if not df_chart.empty:
            df_chart['5MA'] = df_chart['Close'].rolling(window=5).mean()
            df_chart['25MA'] = df_chart['Close'].rolling(window=25).mean()

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='ローソク足'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['5MA'], mode='lines', name='5日線(短期)', line=dict(color='lime', width=1.5)))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['25MA'], mode='lines', name='25日線(中期)', line=dict(color='orange', width=2)))

            fig.update_layout(title=f"{selected_name} の日足チャート", xaxis_rangeslider_visible=False, height=500, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("現在、強力な買いシグナルが出ている銘柄は見つかりませんでした。")