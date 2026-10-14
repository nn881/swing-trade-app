import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="スイング監視", layout="wide")
st.title("スイングトレード監視ダッシュボード")

# 監視対象の銘柄コード
tickers = ["7203.T", "8306.T", "9984.T", "6758.T", "6861.T"]
data_list = []

st.subheader("① 本日のシグナル判定")
with st.spinner("データを取得中..."):
    for ticker in tickers:
        df = yf.Ticker(ticker).history(period="3mo")
        if df.empty or len(df) < 25:
            continue
        
        df['25MA'] = df['Close'].rolling(window=25).mean()
        latest_close = float(df['Close'].iloc[-1])
        latest_ma25 = float(df['25MA'].iloc[-1])
        
        signal = "★上昇ブレイク" if latest_close > latest_ma25 else "-"
        
        data_list.append({
            "銘柄": ticker.replace(".T", ""),
            "終値": round(latest_close, 1),
            "25日線": round(latest_ma25, 1),
            "判定": signal
        })

if data_list:
    st.dataframe(pd.DataFrame(data_list), use_container_width=True)

# ーーー ここから下が新しく追加したチャート機能 ーーー
st.subheader("② チャート確認")
# セレクトボックスで銘柄を選択
selected_name = st.selectbox("チャートを表示する銘柄を選択してください", [t.replace(".T", "") for t in tickers])
selected_ticker = selected_name + ".T"

# チャート用の少し長め（半年分）のデータを取得
df_chart = yf.Ticker(selected_ticker).history(period="6mo")
df_chart['25MA'] = df_chart['Close'].rolling(window=25).mean()

# Plotlyでローソク足と移動平均線を描画
fig = go.Figure()
# ローソク足
fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='ローソク足'))
# 25日移動平均線
fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['25MA'], mode='lines', name='25日線', line=dict(color='orange', width=2)))

# チャートのレイアウト調整（スマホで見やすくする）
fig.update_layout(title=f"{selected_name} の日足チャート", xaxis_rangeslider_visible=False, height=500)
st.plotly_chart(fig, use_container_width=True)