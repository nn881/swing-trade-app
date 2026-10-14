import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="スイング監視", layout="wide")

# --- ⚙️ 新機能：サイドバー (設定画面) ---
st.sidebar.header("⚙️ 設定")
st.sidebar.write("監視したい銘柄コードをカンマ(,)区切りで入力してください。")
# ユーザーが画面から銘柄を変更できるようにする
ticker_input = st.sidebar.text_input("銘柄コード", "7203, 8306, 9984, 6758, 6861, 9101, 7974")
# 入力された文字をリストに変換
tickers = [t.strip() + ".T" for t in ticker_input.split(",") if t.strip()]

st.title("📈 スイングトレード監視ダッシュボード")
st.write("初心者向けに「買うべきタイミング」を自動判定して表示します。")

data_list = []

st.subheader("① 本日のシグナル判定")
with st.spinner("データを取得中..."):
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        
        if df.empty or len(df) < 26: 
            continue
        
        # 5日移動平均線（短期）と25日移動平均線（中期）を計算
        df['5MA'] = df['Close'].rolling(window=5).mean()
        df['25MA'] = df['Close'].rolling(window=25).mean()
        
        try:
            # 最新の値
            latest_close = float(df['Close'].dropna().values[-1])
            latest_5ma = float(df['5MA'].dropna().values[-1])
            latest_25ma = float(df['25MA'].dropna().values[-1])
            
            # 1日前の値（クロス判定用）
            prev_5ma = float(df['5MA'].dropna().values[-2])
            prev_25ma = float(df['25MA'].dropna().values[-2])
        except Exception:
            continue
        
        # --- 🔥 新機能：初心者向けの売買判定ロジック ---
        # ゴールデンクロス（短期線が中期線を下から上に突き抜けた瞬間）＝ 強い買いシグナル
        if prev_5ma <= prev_25ma and latest_5ma > latest_25ma:
            signal = "🔥 激アツ！買いシグナル (ゴールデンクロス)"
        # 上昇トレンド継続中（終値も短期線も中期線より上）
        elif latest_close > latest_25ma and latest_5ma > latest_25ma:
            signal = "👍 上昇トレンド (買い候補)"
        # 下落トレンド（中期線を下回っている）
        elif latest_close < latest_25ma:
            signal = "⚠️ 下落トレンド (様子見)"
        else:
            signal = "様子見"
        
        data_list.append({
            "銘柄": ticker.replace(".T", ""),
            "終値": round(latest_close, 1),
            "5日線(短期)": round(latest_5ma, 1),
            "25日線(中期)": round(latest_25ma, 1),
            "総合判定": signal
        })

if data_list:
    df_result = pd.DataFrame(data_list)
    st.dataframe(df_result, use_container_width=True)
else:
    st.warning("有効な銘柄データが取得できませんでした。コードを確認してください。")

st.subheader("② チャート確認")
if tickers:
    selected_name = st.selectbox("詳細チャートを表示する銘柄を選択してください", [t.replace(".T", "") for t in tickers])
    selected_ticker = selected_name + ".T"

    df_chart = yf.Ticker(selected_ticker).history(period="6mo")
    if not df_chart.empty:
        df_chart['5MA'] = df_chart['Close'].rolling(window=5).mean()
        df_chart['25MA'] = df_chart['Close'].rolling(window=25).mean()

        fig = go.Figure()
        # ローソク足
        fig.add_trace(go.Candlestick(
            x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
            low=df_chart['Low'], close=df_chart['Close'], name='ローソク足'
        ))
        # 5日線 (短期・緑色)
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart['5MA'], mode='lines', 
            name='5日線(短期)', line=dict(color='lime', width=1.5)
        ))
        # 25日線 (中期・オレンジ色)
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart['25MA'], mode='lines', 
            name='25日線(中期)', line=dict(color='orange', width=2)
        ))

        fig.update_layout(
            title=f"{selected_name} の日足チャート (緑:短期線 / オレンジ:中期線)", 
            xaxis_rangeslider_visible=False, 
            height=500,
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)