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
        # yfinanceの最新仕様に完全対応させた取得方法
        stock = yf.Ticker(ticker)
        df = stock.history(period="3mo")
        
        if df.empty or len(df) < 25:
            continue
        
        # 移動平均の計算
        df['25MA'] = df['Close'].rolling(window=25).mean()
        
        # 【修正箇所】どんなデータ構造で返ってきても、確実に純粋な「数値」だけを抽出する処理
        try:
            # .values[-1] でNumPyの純粋な値を取り出し、float型に変換
            latest_close = float(df['Close'].dropna().values[-1])
            latest_ma25 = float(df['25MA'].dropna().values[-1])
        except Exception:
            # 万が一エラーになった銘柄はスキップする
            continue
        
        signal = "★上昇ブレイク" if latest_close > latest_ma25 else "-"
        
        data_list.append({
            "銘柄": ticker.replace(".T", ""),
            "終値": round(latest_close, 1),
            "25日線": round(latest_ma25, 1),
            "判定": signal
        })

if data_list:
    st.dataframe(pd.DataFrame(data_list), use_container_width=True)

st.subheader("② チャート確認")
selected_name = st.selectbox("チャートを表示する銘柄を選択してください", [t.replace(".T", "") for t in tickers])
selected_ticker = selected_name + ".T"

# チャート側の取得も修正
df_chart = yf.Ticker(selected_ticker).history(period="6mo")
if not df_chart.empty:
    df_chart['25MA'] = df_chart['Close'].rolling(window=25).mean()

    fig = go.Figure()
    # plotlyでローソク足を描画
    fig.add_trace(go.Candlestick(
        x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
        low=df_chart['Low'], close=df_chart['Close'], name='ローソク足'
    ))
    # 25日線を描画
    fig.add_trace(go.Scatter(
        x=df_chart.index, y=df_chart['25MA'], mode='lines', 
        name='25日線', line=dict(color='orange', width=2)
    ))

    # スマホで見やすいようにレイアウト調整
    fig.update_layout(title=f"{selected_name} の日足チャート", xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)