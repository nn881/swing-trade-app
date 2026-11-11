import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime, timedelta
import urllib.parse
import concurrent.futures

st.set_page_config(page_title="スイング監視", layout="wide")

# ==========================================
# スマホ最適化 CSS ＆ JavaScript
# ==========================================
st.markdown("""
    <style>
    @media (max-width: 768px) {
        h1 { 
            font-size: min(1.2rem, 4.5vw) !important; 
            white-space: nowrap !important; 
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            padding-bottom: 0px !important; 
        }
    }
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .total-dash {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid #4a90e2;
    }
    </style>
""", unsafe_allow_html=True)

components.html(
    """
    <script>
    const parentDoc = window.parent.document;
    parentDoc.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
            if (sidebar && !sidebar.contains(e.target)) {
                const closeBtn = sidebar.querySelector('button');
                if (closeBtn && sidebar.getAttribute('aria-expanded') === 'true') {
                    closeBtn.click();
                }
            }
        }
    });
    </script>
    """,
    height=0, width=0
)

# ==========================================
# 銘柄リスト定義
# ==========================================
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
TARGET_STOCKS = list(dict.fromkeys(MY_STOCKS + list(MAJOR_NAMES.keys())))

# ==========================================
# ユーティリティ・アラート・データ取得関数
# ==========================================
@st.cache_data(ttl=3600)
def get_earnings_date(code):
    url = f"https://finance.yahoo.co.jp/quote/{code}.T"
    try:
        html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3).text
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        match = re.search(r'決算発表日.*?([0-9]{4}/[0-9]{1,2}/[0-9]{1,2})', text)
        if match:
            date_str = match.group(1)
            days_left = (datetime.strptime(date_str, "%Y/%m/%d") - datetime.now()).days
            if 0 <= days_left <= 7: return f"⚠️ 近日決算予定（{date_str}）"
        return None
    except: return None

def check_rights_date_warning():
    now = datetime.now()
    if 22 <= now.day <= 31:
        return "⚠️ 【権利落ち日 接近アラート】まもなく月末の配当・優待権利落ち日が到来します。権利落ちによる株価の急落リスクにご注意ください。"
    return None

def get_chart_data(code, tf_choice, period_choice):
    yf_period_map = {
        "1日": "1d", "2日": "2d", "4日": "4d", "5日": "5d",
        "1ヶ月": "1mo", "3ヶ月": "3mo", "6ヶ月": "6mo",
        "1年": "1y", "2年": "2y", "5年": "5y", "10年": "10y", "最大": "max"
    }
    yf_period = yf_period_map.get(period_choice, "1y")

    if tf_choice == "週足":
        df = yf.Ticker(code + ".T").history(period=yf_period, interval="1wk")
        return df, 13, 26, "13週線", "26週線"
    elif tf_choice == "月足":
        df = yf.Ticker(code + ".T").history(period=yf_period, interval="1mo")
        return df, 12, 24, "12ヶ月線", "24ヶ月線"
    elif tf_choice == "5分足":
        if yf_period in ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"]:
            yf_period = "60d"
        df = yf.Ticker(code + ".T").history(period=yf_period, interval="5m")
        if not df.empty and df.index.tz is not None:
            df.index = df.index.tz_convert('Asia/Tokyo').tz_localize(None)
        return df, 25, 75, "25本線", "75本線"
    else:
        df = yf.Ticker(code + ".T").history(period=yf_period, interval="1d")
        return df, 5, 25, "5日線", "25日線"

def apply_axis_formatting(fig, df, tf_choice, tp=None, sl=None):
    if df.empty: return
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    if tf_choice == "5分足":
        fig.update_xaxes(
            dtick=3600000, tickformat="%H:%M", tickangle=-45,
            rangebreaks=[dict(bounds=["sat", "mon"]), dict(bounds=[15, 9], pattern="hour"), dict(bounds=[11.5, 12.5], pattern="hour")]
        )
    elif tf_choice == "日足":
        fig.update_xaxes(dtick="M1", tickformat="%Y-%m", tickangle=-45, rangebreaks=[dict(bounds=["sat", "mon"])])
    elif tf_choice == "週足":
        fig.update_xaxes(dtick="M3", tickformat="%Y-%m", tickangle=-45)
    elif tf_choice == "月足":
        fig.update_xaxes(dtick="M12", tickformat="%Y", tickangle=0)
        
    try:
        cols_max = ['High']
        cols_min = ['Low']
        if 'BB_upper' in df.columns: cols_max.append('BB_upper')
        if 'BB_lower' in df.columns: cols_min.append('BB_lower')
        if 'Resistance' in df.columns: cols_max.append('Resistance')
        
        # 修正ポイント: 利確・損切(tp, sl)を範囲計算から完全に除外
        y_max = df[cols_max].max(skipna=True).max()
        y_min = df[cols_min].min(skipna=True).min()
            
        # 修正ポイント: 上下余白を10%に設定して綺麗に収める
        margin = (y_max - y_min) * 0.1 
        if margin == 0: margin = y_max * 0.05
        
        if pd.notna(y_max) and pd.notna(y_min):
            dtick_val = 20 if tf_choice == "5分足" else 200
            fig.update_yaxes(
                range=[y_min - margin, y_max + margin],
                dtick=dtick_val,
                row=1, col=1
            )
    except Exception as e:
        pass

def fetch_single_stock_summary(code):
    try:
        df = yf.Ticker(code + ".T").history(period="5d")
        if len(df) >= 2:
            c_c = df['Close'].iloc[-1]
            p_c = df['Close'].iloc[-2]
            v_c = df['Volume'].iloc[-1]
            v_mean = df['Volume'].iloc[:-1].mean()
            h_max = df['High'].max()
            
            up_rate = (c_c - p_c) / p_c if p_c > 0 else 0
            vol_ratio = v_c / v_mean if v_mean > 0 else 0
            is_high = c_c >= h_max
            return {"code": code, "up_rate": up_rate, "vol_ratio": vol_ratio, "is_high": is_high}
    except: pass
    return None

@st.cache_data(ttl=900)
def get_internal_trend_stocks(ranking_type, manual_tickers_str=""):
    manual_codes = [c.strip().upper() for c in manual_tickers_str.split('\n') if re.match(r'^[0-9A-Z]{4}$', c.strip().upper())]
    all_codes = list(dict.fromkeys(TARGET_STOCKS + manual_codes))
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_single_stock_summary, code): code for code in all_codes}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                res["name"] = MAJOR_NAMES.get(res["code"], f"銘柄({res['code']})")
                results.append(res)
                
    if ranking_type == "up_rate":
        results.sort(key=lambda x: x["up_rate"], reverse=True)
    elif ranking_type == "vol_surge":
        results.sort(key=lambda x: x["vol_ratio"], reverse=True)
    elif ranking_type == "high_update":
        results = [r for r in results if r["is_high"]]
        results.sort(key=lambda x: x["up_rate"], reverse=True)
        
    return results[:50]

@st.cache_data(ttl=86400)
def search_code_by_name(query):
    query = str(query).strip().upper()
    if re.match(r'^[0-9A-Z]{4}$', query):
        try:
            info = yf.Ticker(query + ".T").info
            name = info.get('shortName', query)
            if name: return query, name
        except:
            return query, f"銘柄({query})"
    
    url = f"https://finance.yahoo.co.jp/search/?query={urllib.parse.quote(query)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        first_result = soup.select_one('a[href^="https://finance.yahoo.co.jp/quote/"]')
        if first_result:
            code_match = re.search(r'/quote/([0-9A-Z]{4})\.T', first_result['href'], re.IGNORECASE)
            if code_match:
                name = first_result.get_text(strip=True)
                return code_match.group(1).upper(), name
    except: pass
    return None, None

def calculate_score_and_technical(ticker):
    try:
        df = yf.Ticker(ticker).history(period="1y")
        if df.empty or len(df) < 30: return None
        
        df['5MA'] = df['Close'].rolling(window=5).mean()
        df['25MA'] = df['Close'].rolling(window=25).mean()
        df['75MA'] = df['Close'].rolling(window=75).mean()
        df['Volume_5MA'] = df['Volume'].rolling(window=5).mean()
        df['High_60'] = df['High'].rolling(window=60).max()
        df['High_20'] = df['High'].rolling(window=20).max()
        
        df['BB_std'] = df['Close'].rolling(window=25).std()
        df['BB_upper'] = df['25MA'] + (df['BB_std'] * 2)
        df['BB_lower'] = df['25MA'] - (df['BB_std'] * 2)
        df['BB_width'] = df['BB_upper'] - df['BB_lower']
        
        high_9, low_9 = df['High'].rolling(9).max(), df['Low'].rolling(9).min()
        df['Tenkan'] = (high_9 + low_9) / 2
        high_26, low_26 = df['High'].rolling(26).max(), df['Low'].rolling(26).min()
        df['Kijun'] = (high_26 + low_26) / 2
        df['Senkou_A'] = ((df['Tenkan'] + df['Kijun']) / 2).shift(25)
        high_52, low_52 = df['High'].rolling(52).max(), df['Low'].rolling(52).min()
        df['Senkou_B'] = ((high_52 + low_52) / 2).shift(25)
        
        c_c = df['Close'].iloc[-1]
        c_5 = df['5MA'].iloc[-1] if not pd.isna(df['5MA'].iloc[-1]) else c_c
        c_25 = df['25MA'].iloc[-1] if not pd.isna(df['25MA'].iloc[-1]) else c_c
        c_75 = df['75MA'].iloc[-1] if not pd.isna(df['75MA'].iloc[-1]) else c_c
        
        p_5 = df['5MA'].iloc[-2] if len(df) > 1 and not pd.isna(df['5MA'].iloc[-2]) else c_5
        p_25 = df['25MA'].iloc[-2] if len(df) > 1 and not pd.isna(df['25MA'].iloc[-2]) else c_25
        p_75 = df['75MA'].iloc[-2] if len(df) > 1 and not pd.isna(df['75MA'].iloc[-2]) else c_75
        
        vol_surge = False
        if len(df) > 1 and not pd.isna(df['Volume_5MA'].iloc[-2]):
             vol_surge = df['Volume'].iloc[-1] > (df['Volume_5MA'].iloc[-2] * 1.5)
             
        dist_res = 0
        if not pd.isna(df['High_60'].iloc[-1]) and c_c > 0:
            dist_res = ((df['High_60'].iloc[-1] - c_c) / c_c) * 100
        
        delta = df['Close'].diff()
        rs = (delta.where(delta > 0, 0)).rolling(14).mean() / (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + rs)).iloc[-1] if not pd.isna(rs.iloc[-1]) else 50
        
        macd = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
        sig = macd.ewm(span=9).mean()
        
        is_25ma_up = (c_25 >= p_25)
        is_gc_ma = (p_5 <= p_25) and (c_5 > c_25) and is_25ma_up
        is_gc_macd = (macd.iloc[-2] <= sig.iloc[-2]) and (macd.iloc[-1] > sig.iloc[-1]) and is_25ma_up
        
        is_po = (c_5 > c_25 > c_75) and (c_5 >= p_5) and (c_25 >= p_25) and (c_75 >= p_75)
        
        is_bandwalk = False
        if len(df) > 5 and not pd.isna(df['BB_width'].iloc[-5]):
            is_bb_exp = df['BB_width'].iloc[-1] > (df['BB_width'].iloc[-5] * 1.1)
            is_bandwalk = is_bb_exp and (c_c >= (c_25 + df['BB_std'].iloc[-1]))
        
        stock_5d_ret = 0
        if len(df) > 6: stock_5d_ret = (c_c - df['Close'].iloc[-6]) / df['Close'].iloc[-6]
        
        senkou_max = max(df['Senkou_A'].iloc[-1], df['Senkou_B'].iloc[-1]) if not pd.isna(df['Senkou_A'].iloc[-1]) else c_c
        p_senkou_max = max(df['Senkou_A'].iloc[-2], df['Senkou_B'].iloc[-2]) if len(df) > 1 and not pd.isna(df['Senkou_A'].iloc[-2]) else c_c
        is_above_cloud = c_c > senkou_max
        is_cloud_breakout = is_above_cloud and (df['Close'].iloc[-2] <= p_senkou_max)
        is_tenkan_above_kijun = df['Tenkan'].iloc[-1] > df['Kijun'].iloc[-1] if not pd.isna(df['Tenkan'].iloc[-1]) else False
        is_chikou_above = c_c > df['Close'].iloc[-26] if len(df) >= 26 else False
        is_sanyaku = is_above_cloud and is_tenkan_above_kijun and is_chikou_above
        
        score = 0
        reasons = []
        
        if is_po: score += 20; reasons.append("✨PO形成")
        elif c_c > c_25 and c_5 > c_25 and is_25ma_up: score += 10
        if c_25 > c_75 and c_c > c_75: score += 5
            
        if is_gc_ma: score += 15; reasons.append("MAクロス")
        if is_gc_macd: score += 15; reasons.append("MACD転換")
            
        if is_bandwalk: score += 15; reasons.append("🚀バンドウォーク")
        if stock_5d_ret > 0.05: score += 10; reasons.append("💪強いモメンタム")
            
        if is_sanyaku: score += 15; reasons.append("☀️三役好転")
        elif is_cloud_breakout: score += 10; reasons.append("☁️雲抜け")
            
        if 50 <= rsi <= 75: score += 10
        elif rsi < 30: score += 15; reasons.append("売られすぎ")
            
        if vol_surge: score += 10; reasons.append("出来高急増")
        if len(df) > 1 and not pd.isna(df['High_20'].iloc[-2]) and c_c >= df['High_20'].iloc[-2]: 
            score += 10; reasons.append("高値更新")

        if dist_res < 3.0: score -= 20; reasons.append("⚠️抵抗線接近")
        if rsi > 80: score -= 20; reasons.append("⚠️買われすぎ")

        score = max(0, min(100, score))
        reason_str = "、".join(reasons) if reasons else "特になし"
        
        return {
            "終値": round(c_c, 1), 
            "スコア": score,
            "主な要因・警告": reason_str,
            "上値余地": f"{round(dist_res, 1)}%", 
            "RSI": round(rsi, 1)
        }
    except Exception as e: 
        return None

# ==========================================
# データの保存・読み込み
# ==========================================
PORTFOLIO_FILE = "portfolio_data.csv"
TICKERS_FILE = "manual_tickers_data.txt"

def load_tickers():
    if os.path.exists(TICKERS_FILE):
        with open(TICKERS_FILE, "r", encoding="utf-8") as f: return f.read()
    return ""
def save_tickers(text):
    with open(TICKERS_FILE, "w", encoding="utf-8") as f: f.write(text)

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        df = pd.read_csv(PORTFOLIO_FILE, dtype={"コード": str, "取得日": str, "メモ (戦略など)": str})
        df = df.fillna({'コード': '', '取得日': '', '取得単価': 0.0, '保有株数': 0.0, 'メモ (戦略など)': ''})
        if '口座区分' in df.columns: df = df.drop(columns=['口座区分'])
        return df
    return pd.DataFrame({
        "コード": pd.Series(dtype='str'), "取得日": pd.Series(dtype='str'),
        "取得単価": pd.Series(dtype='float'), "保有株数": pd.Series(dtype='float'), "メモ (戦略など)": pd.Series(dtype='str')
    })
def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)

if "manual_tickers" not in st.session_state: st.session_state.manual_tickers = load_tickers()
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "portfolio_df" not in st.session_state: st.session_state.portfolio_df = load_portfolio()
if "show_portfolio_charts" not in st.session_state: st.session_state.show_portfolio_charts = False

# ==========================================
# サイドバー
# ==========================================
st.sidebar.header("📁 メニュー")
app_page = st.sidebar.radio("機能を選択してください", ["🔍 銘柄スクリーニング", "💼 保有銘柄ポートフォリオ"])

st.sidebar.markdown("---")
with st.sidebar.expander("💾 データのバックアップと復元"):
    st.caption("サーバーのスリープ等でデータが初期化された場合、ここから復元できます。")
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            st.download_button("💼 ポートフォリオを保存 (.csv)", f.read(), file_name=PORTFOLIO_FILE, use_container_width=True)
    if os.path.exists(TICKERS_FILE):
        with open(TICKERS_FILE, "r", encoding="utf-8") as f:
            st.download_button("🔍 監視リストを保存 (.txt)", f.read(), file_name=TICKERS_FILE, use_container_width=True)

    upload_port = st.file_uploader("ポートフォリオの復元", type=['csv'])
    if upload_port:
        with open(PORTFOLIO_FILE, "wb") as f: f.write(upload_port.getbuffer())
        st.session_state.portfolio_df = load_portfolio()
        st.success("✅ 復元成功！画面をリロードしてください")

st.title("📈 スイングトレード監視ダッシュボード")
rights_warning = check_rights_date_warning()
if rights_warning: st.warning(rights_warning)

# ==============================================================================
# ページ1: 銘柄スクリーニング
# ==============================================================================
if app_page == "🔍 銘柄スクリーニング":
    st.markdown("### どのような方法で銘柄を探しますか？")
    
    search_mode = st.radio("スクリーニング手法", 
                           ["🔥 今日のトレンド株を発掘 (自社エンジン)", 
                            "🔍 特定の銘柄を深く分析 (フリーワード/コード検索)",
                            "📝 いつもの監視リストをチェック"], 
                           horizontal=True, label_visibility="collapsed")
    
    tickers_to_analyze = []
    run_analysis = False
    is_strict_mode = True 
    
    st.markdown("---")
    
    if search_mode == "🔥 今日のトレンド株を発掘 (自社エンジン)":
        st.write("アプリ内部の自立型エンジンが「主要150銘柄＋監視リスト」のデータをリアルタイムで一斉取得し、ランキングを自動生成します。（※外部サイトに依存しないためブロックされません）")
        col1, col2, col3 = st.columns(3)
        ranking_choice = "up_rate"
        
        with col1:
            if st.button("📈 値上がり率 トップ50", use_container_width=True):
                ranking_choice, run_analysis = "up_rate", True
        with col2:
            if st.button("📊 出来高急増 トップ50", use_container_width=True):
                ranking_choice, run_analysis = "vol_surge", True
        with col3:
            if st.button("🚀 新高値更新 トップ50", use_container_width=True):
                ranking_choice, run_analysis = "high_update", True
                
        if run_analysis:
            with st.spinner("市場データを並列収集中...（数秒かかります）"):
                trend_list = get_internal_trend_stocks(ranking_choice, st.session_state.manual_tickers)
                if not trend_list:
                    st.error("データの取得に失敗しました。")
                    run_analysis = False
                else:
                    st.success(f"{len(trend_list)}銘柄を抽出しました。スコアリングを開始します...")
                    tickers_to_analyze = [{"code": t["code"]+".T", "name": t["name"]} for t in trend_list]

    elif search_mode == "🔍 特定の銘柄を深く分析 (フリーワード/コード検索)":
        st.write("企業名または証券コードを入力してください。IPO・新コードにも対応しています。")
        search_query = st.text_input("企業名 または 証券コード (4桁)", placeholder="例: 627A, 7974, 任天堂")
        
        if st.button("🔍 分析開始", type="primary") and search_query:
            with st.spinner("銘柄データを取得・分析中..."):
                code, name = search_code_by_name(search_query)
                if code:
                    st.success(f"「{name} ({code})」のデータを取得しました。")
                    tickers_to_analyze = [{"code": code+".T", "name": name}]
                    run_analysis = True
                    is_strict_mode = False 
                else:
                    st.error("銘柄が見つかりませんでした。正式な企業名かコードを確認してください。")

    elif search_mode == "📝 いつもの監視リストをチェック":
        st.write("手動で登録した銘柄コード（改行区切り、新コード対応）を一括で分析します。")
        ticker_input = st.text_area("監視リスト (4桁の英数字コード)", value=st.session_state.manual_tickers, height=100)
        if ticker_input != st.session_state.manual_tickers:
            st.session_state.manual_tickers = ticker_input
            save_tickers(ticker_input)
            
        if st.button("▶️ リストを一括分析", type="primary"):
            codes = [t.strip().upper() for t in st.session_state.manual_tickers.split('\n') if t.strip()]
            tickers_to_analyze = [{"code": c+".T", "name": c} for c in codes]
            if tickers_to_analyze: run_analysis = True

    if run_analysis and tickers_to_analyze:
        st.markdown("### ① 買いシグナル抽出結果")
        progress_bar = st.progress(0)
        data_list = []
        
        for i, item in enumerate(tickers_to_analyze):
            ticker = item["code"]
            code_str = ticker.replace('.T', '')
            name = item["name"]
            progress_bar.progress((i + 1) / len(tickers_to_analyze))
            
            res = calculate_score_and_technical(ticker)
            
            if not res:
                if not is_strict_mode:
                    st.warning(f"⚠️ 「{name} ({code_str})」は上場直後のIPOであるか、データ制限によりチャートを描画できません。")
                    col_btn_a, col_btn_b = st.columns(2)
                    rak_url = f"https://www.rakuten-sec.co.jp/web/market/search/quote.html?ric={code_str}.t"
                    yah_url = f"https://finance.yahoo.co.jp/quote/{code_str}.T"
                    col_btn_a.link_button(f"🛒 {code_str}を楽天証券で確認・発注", rak_url, type="primary", use_container_width=True)
                    col_btn_b.link_button(f"🔗 Yahoo!でチャートを確認", yah_url, use_container_width=True)
                continue
            
            if is_strict_mode and (res["スコア"] < 60 or "⚠️" in res["主な要因・警告"]):
                continue
            
            ex_div_txt = "-"
            try:
                info = yf.Ticker(ticker).info
                ex_ts = info.get('exDividendDate')
                if pd.notna(ex_ts) and ex_ts is not None:
                    ex_div_txt = datetime.fromtimestamp(ex_ts).strftime("%Y/%m/%d")
            except: pass
            
            data_list.append({
                "コード": code_str, 
                "銘柄名": name, 
                "終値": res["終値"], 
                "スコア": res["スコア"],
                "主な要因・警告": res["主な要因・警告"],
                "権利落ち日": ex_div_txt,
                "上値余地": res["上値余地"], 
                "RSI": res["RSI"]
            })
                
        st.session_state.analysis_result = data_list
        if data_list:
            st.session_state.selected_code = data_list[0]["コード"]
            st.session_state.selected_name = data_list[0]["銘柄名"]
        elif is_strict_mode:
            st.info("現在、条件を満たす強い銘柄はありませんでした。（相場全体の地合いが悪い可能性があります）")

    if st.session_state.analysis_result:
        df_res = pd.DataFrame(st.session_state.analysis_result).sort_values(by="スコア", ascending=False).reset_index(drop=True)
        
        event = st.dataframe(
            df_res, 
            use_container_width=True, 
            on_select="rerun", 
            selection_mode="single-row",
            column_config={
                "スコア": st.column_config.ProgressColumn(
                    "おすすめ度 (100点満点)",
                    help="複合的なテクニカル指標から算出した総合スコア",
                    format="%d点",
                    min_value=0,
                    max_value=100,
                ),
                "権利落ち日": st.column_config.TextColumn("直近の権利落ち日")
            }
        )
        
        if event.selection.rows:
            st.session_state.selected_code = df_res.iloc[event.selection.rows[0]]["コード"]
            st.session_state.selected_name = df_res.iloc[event.selection.rows[0]]["銘柄名"]
            
        st.markdown(f"### ② {st.session_state.selected_code} {st.session_state.selected_name} の詳細分析")
        warn = get_earnings_date(st.session_state.selected_code)
        if warn: st.error(warn)
        
        col_btn1, col_btn2 = st.columns(2)
        rakuten_url = f"https://www.rakuten-sec.co.jp/web/market/search/quote.html?ric={st.session_state.selected_code}.t"
        yahoo_url = f"https://finance.yahoo.co.jp/quote/{st.session_state.selected_code}.T/margin"
        col_btn1.link_button(f"🛒 楽天証券で確認・発注する", rakuten_url, type="primary", use_container_width=True)
        col_btn2.link_button(f"🔗 Yahoo!で信用倍率を見る", yahoo_url, use_container_width=True)
        
        c_tf, c_pd = st.columns(2)
        with c_tf:
            tf_choice = st.radio("📊 チャート足種", ["5分足", "日足", "週足", "月足"], index=1, horizontal=True, key="screen_chart_tf")
        
        if tf_choice == "5分足":
            s_pd_opts, s_pd_idx = ["1日", "2日", "4日", "5日"], 0
        elif tf_choice == "日足":
            s_pd_opts, s_pd_idx = ["1ヶ月", "3ヶ月", "6ヶ月", "1年", "2年"], 1
        elif tf_choice == "週足":
            s_pd_opts, s_pd_idx = ["3ヶ月", "6ヶ月", "1年", "2年", "5年"], 2
        elif tf_choice == "月足":
            s_pd_opts, s_pd_idx = ["1年", "2年", "5年", "10年", "最大"], 2

        with c_pd:
            period_choice = st.radio("⏱️ 表示期間", s_pd_opts, index=s_pd_idx, horizontal=True, key="screen_chart_pd")
        
        df_daily = yf.Ticker(st.session_state.selected_code + ".T").history(period="1y")
        if not df_daily.empty:
            tr = pd.concat([df_daily['High'] - df_daily['Low'], abs(df_daily['High'] - df_daily['Close'].shift()), abs(df_daily['Low'] - df_daily['Close'].shift())], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1] if len(tr) >= 14 else (df_daily['High'].iloc[-1] - df_daily['Low'].iloc[-1])
            latest_price = df_daily['Close'].iloc[-1]
            take_profit = latest_price + (atr * 2)
            stop_loss = latest_price - (atr * 1.5)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("現在値 (Entry)", f"¥{latest_price:,.1f}")
            col2.metric("🎯 利確目標 (日足基準)", f"¥{take_profit:,.1f}")
            col3.metric("✂️ 損切ライン (日足基準)", f"¥{stop_loss:,.1f}")
            
            df_c, ma_s, ma_l, name_s, name_l = get_chart_data(st.session_state.selected_code, tf_choice, period_choice)
            
            if not df_c.empty:
                df_c['MA_S'] = df_c['Close'].rolling(min(ma_s, len(df_c))).mean()
                df_c['MA_L'] = df_c['Close'].rolling(min(ma_l, len(df_c))).mean()
                
                res_period = 60 if tf_choice in ["日足", "5分足"] else (26 if tf_choice == "週足" else 12)
                df_c['Resistance'] = df_c['High'].rolling(min(res_period, len(df_c))).max()
                
                fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.15, 0.15, 0.2])
                
                fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name='ローソク足'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['MA_S'], mode='lines', name=name_s, line=dict(color='lime', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['MA_L'], mode='lines', name=name_l, line=dict(color='orange', width=1.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['Resistance'], mode='lines', name='上値抵抗線', line=dict(color='pink', width=1.5, dash='dash')), row=1, col=1)
                
                if tf_choice in ["日足", "5分足"]:
                    ma_75_name = "75日線" if tf_choice == "日足" else "75本線"
                    df_c['MA_75'] = df_c['Close'].rolling(min(75, len(df_c))).mean()
                    fig.add_trace(go.Scatter(x=df_c.index, y=df_c['MA_75'], mode='lines', name=ma_75_name, line=dict(color='#ab63fa', width=1, dash='dot')), row=1, col=1)

                df_c['BB_std'] = df_c['Close'].rolling(min(ma_l, len(df_c))).std()
                df_c['BB_upper'] = df_c['MA_L'] + (df_c['BB_std']*2)
                df_c['BB_lower'] = df_c['MA_L'] - (df_c['BB_std']*2)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['BB_upper'], mode='lines', line=dict(width=0), showlegend=False), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['BB_lower'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(173, 216, 230, 0.1)', name='BB±2σ'), row=1, col=1)
                
                if tf_choice == "5分足": f_date = df_c.index[-1] + timedelta(hours=5)
                elif tf_choice == "日足": f_date = df_c.index[-1] + timedelta(days=5)
                else: f_date = df_c.index[-1] + timedelta(days=20)
                fig.add_trace(go.Scatter(x=[df_c.index[-1], f_date], y=[take_profit, take_profit], mode='lines', name='利確目安', line=dict(color='lightgreen', dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=[df_c.index[-1], f_date], y=[stop_loss, stop_loss], mode='lines', name='損切ライン', line=dict(color='red', dash='dot')), row=1, col=1)

                vol_colors = ['#ef5350' if row['Open'] > row['Close'] else '#26a69a' for index, row in df_c.iterrows()]
                fig.add_trace(go.Bar(x=df_c.index, y=df_c['Volume'], marker_color=vol_colors, name='出来高'), row=2, col=1)

                macd = df_c['Close'].ewm(span=12, adjust=False).mean() - df_c['Close'].ewm(span=26, adjust=False).mean()
                sig = macd.ewm(span=9, adjust=False).mean()
                fig.add_trace(go.Bar(x=df_c.index, y=macd-sig, name='MACD Hist', marker_color='gray'), row=3, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=macd, mode='lines', name='MACD', line=dict(color='cyan', width=1)), row=3, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=sig, mode='lines', name='Signal', line=dict(color='magenta', width=1)), row=3, col=1)

                delta = df_c['Close'].diff()
                rs = (delta.where(delta > 0, 0)).rolling(14).mean() / (-delta.where(delta < 0, 0)).rolling(14).mean()
                if len(rsi_series := 100 - (100 / (1 + rs))) > 0:
                    fig.add_trace(go.Scatter(x=df_c.index, y=rsi_series, mode='lines', name='RSI', line=dict(color='yellow', width=1)), row=4, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1)

                fig.update_layout(
                    height=800, 
                    template="plotly_dark", 
                    dragmode="pan", 
                    margin=dict(l=10, r=10, t=10, b=10), 
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    hovermode="x unified"
                )
                
                apply_axis_formatting(fig, df_c, tf_choice, tp=take_profit, sl=stop_loss)
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

# ==============================================================================
# ページ2: 保有銘柄ポートフォリオ
# ==============================================================================
elif app_page == "💼 保有銘柄ポートフォリオ":
    st.subheader("💼 保有銘柄の管理")
    st.write("保有しているスイング銘柄を管理します。")
    
    edited_df = st.data_editor(
        st.session_state.portfolio_df, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "コード": st.column_config.TextColumn("コード (4桁の英数字)"),
            "取得日": st.column_config.TextColumn("取得日 (YYYY/MM/DD)"),
            "取得単価": st.column_config.NumberColumn("取得単価", format="%g"),
            "保有株数": st.column_config.NumberColumn("保有株数", step=0.01, format="%g"),
            "メモ (戦略など)": st.column_config.TextColumn("メモ (戦略など)", max_chars=100)
        }
    )
    
    need_auto_fetch_rerun = False
    for index, row in edited_df.iterrows():
        code = str(row.get('コード', '')).strip().upper()
        if code.endswith('.0'): code = code[:-2]
        if code.lower() in ['nan', 'none']: code = ''
            
        date_str = str(row.get('取得日', '')).strip()
        if date_str.lower() in ['nan', 'none']: date_str = ''
            
        try: price = float(row.get('取得単価', 0.0))
        except: price = 0.0
            
        if code and len(code) >= 4 and date_str and price == 0.0:
            try:
                date_str_fmt = date_str.replace('-', '/')
                dt = datetime.strptime(date_str_fmt, "%Y/%m/%d")
                end_dt = dt + timedelta(days=7) 
                
                df_hist = yf.Ticker(code + ".T").history(start=dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d"))
                if not df_hist.empty:
                    auto_price = df_hist['Close'].iloc[0]
                    edited_df.at[index, '取得単価'] = round(auto_price, 1)
                    need_auto_fetch_rerun = True
            except: pass

    save_portfolio(edited_df)

    if need_auto_fetch_rerun:
        st.session_state.portfolio_df = edited_df
        st.rerun()

    st.markdown("---")
    dash_placeholder = st.empty()
    
    c_tf_p, c_pd_p = st.columns(2)
    with c_tf_p:
        port_tf_choice = st.radio("📊 全チャート足種", ["5分足", "日足", "週足", "月足"], index=1, horizontal=True, key="port_chart_tf")
        
    if port_tf_choice == "5分足":
        p_pd_opts, p_pd_idx = ["1日", "2日", "4日", "5日"], 0
    elif port_tf_choice == "日足":
        p_pd_opts, p_pd_idx = ["1ヶ月", "3ヶ月", "6ヶ月", "1年", "2年"], 1
    elif port_tf_choice == "週足":
        p_pd_opts, p_pd_idx = ["3ヶ月", "6ヶ月", "1年", "2年", "5年"], 2
    elif port_tf_choice == "月足":
        p_pd_opts, p_pd_idx = ["1年", "2年", "5年", "10年", "最大"], 2

    with c_pd_p:
        port_period_choice = st.radio("⏱️ 全チャート表示期間", p_pd_opts, index=p_pd_idx, horizontal=True, key="port_chart_pd")
    
    if st.button("🔄 最新の状況をチェックする", type="primary"):
        st.session_state.show_portfolio_charts = True
        
    if st.session_state.show_portfolio_charts:
        total_invested = 0.0
        total_current_value = 0.0
        
        for index, row in edited_df.iterrows():
            code = str(row.get('コード', '')).strip().upper()
            if code.endswith('.0'): code = code[:-2]
            if not code or code.lower() in ['nan', 'none']: continue
            
            try: entry_price = float(row['取得単価'])
            except: entry_price = 0.0
            try: shares = float(row['保有株数'])
            except: shares = 0.0
                
            name = code
            st.markdown(f"### {code} {name}")
            
            try:
                df_daily_p = yf.Ticker(code + ".T").history(period="1y")
                if df_daily_p.empty:
                    st.error(f"⚠️ {code}のデータが取得できませんでした（IPOなど）。")
                    rak_url = f"https://www.rakuten-sec.co.jp/web/market/search/quote.html?ric={code}.t"
                    st.link_button(f"🛒 楽天証券で直接確認する", rak_url, use_container_width=True)
                    continue
                
                latest_price = df_daily_p['Close'].iloc[-1]
                total_invested += (entry_price * shares)
                total_current_value += (latest_price * shares)
                
                tr = pd.concat([df_daily_p['High'] - df_daily_p['Low'], abs(df_daily_p['High'] - df_daily_p['Close'].shift()), abs(df_daily_p['Low'] - df_daily_p['Close'].shift())], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1] if len(tr) >= 14 else (df_daily_p['High'].iloc[-1] - df_daily_p['Low'].iloc[-1])
                
                take_profit = entry_price + (atr * 2) if entry_price > 0 else 0
                stop_loss = entry_price - (atr * 1.5) if entry_price > 0 else 0
                
                profit_loss_per_share = latest_price - entry_price
                profit_loss_total = profit_loss_per_share * shares
                pl_color = "normal" if profit_loss_total >= 0 else "inverse"
                
                col_btn, _ = st.columns([1, 2])
                rakuten_port_url = f"https://www.rakuten-sec.co.jp/web/market/search/quote.html?ric={code}.t"
                col_btn.link_button(f"🛒 {name} を楽天証券で確認・発注", rakuten_port_url, use_container_width=True)
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("取得単価", f"¥{entry_price:,.1f}")
                c2.metric("現在値", f"¥{latest_price:,.1f}", f"{profit_loss_per_share:,.1f}円", delta_color=pl_color)
                c3.metric("🎯 利確目標", f"¥{take_profit:,.1f}")
                c4.metric("✂️ 損切ライン", f"¥{stop_loss:,.1f}")
                
                st.info(f"💰 **評価損益:** ¥{profit_loss_total:,.0f} （保有: {shares:g}株）")
                
                memo_txt = str(row.get('メモ (戦略など)', '')).strip()
                if memo_txt and memo_txt.lower() not in ['nan', 'none']:
                    st.caption(f"📝 メモ: {memo_txt}")
                
                df_p, ma_s, ma_l, name_s, name_l = get_chart_data(code, port_tf_choice, port_period_choice)
                
                if not df_p.empty:
                    df_p['MA_S'] = df_p['Close'].rolling(min(ma_s, len(df_p))).mean()
                    df_p['MA_L'] = df_p['Close'].rolling(min(ma_l, len(df_p))).mean()
                    
                    res_period = 60 if port_tf_choice in ["日足", "5分足"] else (26 if port_tf_choice == "週足" else 12)
                    df_p['Resistance'] = df_p['High'].rolling(min(res_period, len(df_p))).max()
                    
                    fig_p = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.15, 0.15, 0.2])
                    
                    fig_p.add_trace(go.Candlestick(x=df_p.index, open=df_p['Open'], high=df_p['High'], low=df_p['Low'], close=df_p['Close'], name='ローソク足'), row=1, col=1)
                    fig_p.add_trace(go.Scatter(x=df_p.index, y=df_p['MA_S'], mode='lines', name=name_s, line=dict(color='lime', width=1)), row=1, col=1)
                    fig_p.add_trace(go.Scatter(x=df_p.index, y=df_p['MA_L'], mode='lines', name=name_l, line=dict(color='orange', width=1.5)), row=1, col=1)
                    fig_p.add_trace(go.Scatter(x=df_p.index, y=df_p['Resistance'], mode='lines', name='上値抵抗線', line=dict(color='pink', width=1.5, dash='dash')), row=1, col=1)
                    
                    if port_tf_choice in ["日足", "5分足"]:
                        ma_75_name = "75日線" if port_tf_choice == "日足" else "75本線"
                        df_p['MA_75'] = df_p['Close'].rolling(min(75, len(df_p))).mean()
                        fig_p.add_trace(go.Scatter(x=df_p.index, y=df_p['MA_75'], mode='lines', name=ma_75_name, line=dict(color='#ab63fa', width=1, dash='dot')), row=1, col=1)
                    
                    if entry_price > 0:
                        fig_p.add_hline(y=entry_price, line_dash="solid", line_color="white", annotation_text="取得単価", annotation_position="top left", row=1, col=1)
                        fig_p.add_hline(y=take_profit, line_dash="dot", line_color="lightgreen", annotation_text="利確目標", annotation_position="top right", row=1, col=1)
                        fig_p.add_hline(y=stop_loss, line_dash="dot", line_color="red", annotation_text="損切ライン", annotation_position="bottom right", row=1, col=1)

                    vol_colors_p = ['#ef5350' if row['Open'] > row['Close'] else '#26a69a' for index, row in df_p.iterrows()]
                    fig_p.add_trace(go.Bar(x=df_p.index, y=df_p['Volume'], marker_color=vol_colors_p, name='出来高'), row=2, col=1)

                    macd_p = df_p['Close'].ewm(span=12, adjust=False).mean() - df_p['Close'].ewm(span=26, adjust=False).mean()
                    sig_p = macd_p.ewm(span=9, adjust=False).mean()
                    fig_p.add_trace(go.Bar(x=df_p.index, y=macd_p-sig_p, name='MACD Hist', marker_color='gray'), row=3, col=1)
                    fig_p.add_trace(go.Scatter(x=df_p.index, y=macd_p, mode='lines', name='MACD', line=dict(color='cyan', width=1)), row=3, col=1)
                    fig_p.add_trace(go.Scatter(x=df_p.index, y=sig_p, mode='lines', name='Signal', line=dict(color='magenta', width=1)), row=3, col=1)

                    delta_p = df_p['Close'].diff()
                    rs_p = (delta_p.where(delta_p > 0, 0)).rolling(14).mean() / (-delta_p.where(delta_p < 0, 0)).rolling(14).mean()
                    if len(rsi_series_p := 100 - (100 / (1 + rs_p))) > 0:
                        fig_p.add_trace(go.Scatter(x=df_p.index, y=rsi_series_p, mode='lines', name='RSI', line=dict(color='yellow', width=1)), row=4, col=1)
                        fig_p.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1)
                        fig_p.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1)

                    fig_p.update_layout(
                        height=800, 
                        template="plotly_dark", 
                        dragmode="pan", 
                        margin=dict(l=10, r=10, t=10, b=10), 
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                        hovermode="x unified"
                    )
                    
                    apply_axis_formatting(fig_p, df_p, port_tf_choice, tp=take_profit, sl=stop_loss)
                    st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})
                
                st.markdown("---")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
        
        total_pnl = total_current_value - total_invested
        pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        total_color = "normal" if total_pnl >= 0 else "inverse"
        
        with dash_placeholder.container():
            st.markdown('<div class="total-dash"><h3>📊 ポートフォリオ総合ダッシュボード</h3></div>', unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            d1.metric("総投資額 (元本)", f"¥{total_invested:,.0f}")
            d2.metric("現在の総資産額", f"¥{total_current_value:,.0f}", f"{total_pnl:,.0f}円 ({pnl_percent:,.1f}%)", delta_color=total_color)
            st.markdown("---")