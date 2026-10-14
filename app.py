import streamlit as st
import yfinance as yf
import pandas as pd

st.title("スイングトレード監視ダッシュボード")
st.write("25日移動平均線を上回っている銘柄を抽出します。")

# 監視対象の銘柄コード (日本の銘柄は末尾に .T をつける)
tickers = ["7203.T", "8306.T", "9984.T", "6758.T", "6861.T"]

# データを格納するリスト
data_list = []

with st.spinner("データを取得中..."):
    for ticker in tickers:
        # 過去3ヶ月のデータを取得
        df = yf.download(ticker, period="3mo", progress=False)
        if df.empty or len(df) < 25:
            continue
        
        # 25日移動平均を計算
        df['25MA'] = df['Close'].rolling(window=25).mean()
        
        latest_close = float(df['Close'].iloc[-1])
        latest_ma25 = float(df['25MA'].iloc[-1])
        
        # 判定ロジック
        signal = "★上昇ブレイク" if latest_close > latest_ma25 else "-"
        
        data_list.append({
            "銘柄": ticker.replace(".T", ""),
            "終値": round(latest_close, 1),
            "25日線": round(latest_ma25, 1),
            "判定": signal
        })

# 結果をテーブル表示
if data_list:
    st.dataframe(pd.DataFrame(data_list), use_container_width=True)