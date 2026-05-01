import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io
import os

# --- 1. フォント・環境設定 ---
FONT_NAME = "HeiseiMin-W3" 

def setup_font():
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))

@st.cache_data
def load_data():
    try:
        return pd.read_csv("pharmacy_list.csv")
    except:
        return pd.DataFrame({
            "薬局名": ["サンプル薬局"], "ふりがな": ["さんぷる"],
            "TEL番号": ["000-000-0000"], "FAX番号": ["000-000-0000"]
        })

# --- 2. PDF作成ロジック（高密度レイアウト） ---
def create_pdf(p_name, p_tel, p_fax, d_type, target_info, note_text, is_urgent):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    setup_font()
    
    if is_urgent:
        p.setFont(FONT_NAME, 16)
        p.drawString(40, height - 40, "【至急配達希望】")
    
    p.setFont(FONT_NAME, 18)
    p.drawCentredString(width/2, height - 70, "処 方 箋 送 付 状")
    
    p.setStrokeColorRGB(0.85, 0.85, 0.85)
    p.setLineWidth(0.5)
    
    y = height - 105
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y, f"送信日: {datetime.now().strftime('%Y.%m.%d')}")
    p.setFont(FONT_NAME, 14)
    p.drawString(40, y - 25, f"{p_name}  御中")
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y - 42, f"TEL: {p_tel if p_tel else ''}  /  FAX: {p_fax if p_fax else ''}")
    
    p.line(40, y - 55, width - 40, y - 55) 
    
    y -= 85 
    p.setFont(FONT_NAME, 11)
    p.drawString(40, y, f"受け取り方法： {d_type}")
    
    y -= 30
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y, "いつも大変お世話になっております。")
    p.drawString(40, y - 13, "以下の通り処方箋を送付いたしますので、ご対応のほど宜しくお願い申し上げます。")
    
    y -= 55 
    p.setFont(FONT_NAME, 8)
    p.drawString(40, y + 8, "施設・患者名など")
    p.setFont(FONT_NAME, 12)
    p.drawString(50, y - 8, target_info if target_info else "---")
    
    y -= 55 
    p.setFont(FONT_NAME, 8)
    p.drawString(40, y + 8, "備考")
    text_obj = p.beginText(50, y - 8)
    text_obj.setFont(FONT_NAME, 10)
    text_obj.setLeading(14)
    for line in note_text.split("\n"):
        text_obj.textLine(line)
    p.drawText(text_obj)
    
    p.line(40, 90, width - 40, 90)
    p.setFont(FONT_NAME, 11)
    p.drawString(40, 65, "陽だまり診療所")
    p.setFont(FONT_NAME, 8)
    p.drawString(40, 50, "TEL: 0178-32-7358  /  FAX: 0178-32-7359")
    
    logo_path = "logo.png"
    if not os.path.exists(logo_path): logo_path = "陽だまりロゴ.jpg"
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 300, height - 715, width=70, preserveAspectRatio=True, mask='auto')
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. コールバック関数（エラー対策） ---
def add_template(text):
    """ボタンが押された時に備考欄に文字を追加する関数"""
    if 'note_input' in st.session_state:
        st.session_state.note_input += text

# --- 4. アプリ画面設定 ---
st.set_page_config(page_title="処方箋送付状作成BOT", layout="centered")

# ライトモード固定 & 最新デザイン
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: white !important; color: #1d1d1f !important; }
    header[data-testid="stHeader"] { background-color: white !important; }
    input, select, textarea, label, div, p { color: #1d1d1f !important; }
    .stDownloadButton > button {
        background-color: #0071e3 !important; color: white !important;
        font-size: 1.4rem !important; font-weight: bold !important;
        height: 2.8em !important; border-radius: 12px !important; border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%;
    }
    .stTextInput input, .stTextArea textarea, [data-baseweb="select"] {
        background-color: #f5f5f7 !important; border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# セッション状態の初期化
if 'note_input' not in st.session_state: st.session_state.note_input = ""

logo_top = "logo.png"
if not os.path.exists(logo_top): logo_top = "陽だまりロゴ.jpg"
if os.path.exists(logo_top): st.image(logo_top, width=120)

st.title("処方箋送付状作成BOT")
st.divider()

# モード選択
input_mode = st.segmented_control("作成モード", ["リストから選択", "手動入力"], default="リストから選択")

pharmacy_name = ""
tel_number = ""
fax_number = ""

# --- 薬局選択 ---
if input_mode == "リストから選択":
    df_pharmacy = load_data()
    sort_order = st.segmented_control("並び順", ["リスト順", "あいうえお順"], default="リスト順")
    df_display = df_pharmacy.sort_values("ふりがな") if sort_order == "あいうえお順" else df_pharmacy

    search_list = [f"{row['薬局名']} ({row['ふりがな']})" for _, row in df_display.iterrows()]
    
    pharmacy_selection = st.selectbox(
        "🏥 薬局名を選択", 
        search_list,
        index=None,
        placeholder="薬局名を入力...",
        format_func=lambda x: x.split(" (")[0], 
        key="pharmacy_selector"
    )
    
    if pharmacy_selection:
        pharmacy_name = pharmacy_selection.split(" (")[0]
        row = df_display[df_display["薬局名"] == pharmacy_name].iloc[0]
        tel_number = row['TEL番号']
        fax_number = row['FAX番号']
        st.markdown(f"**📞 TEL:** `{tel_number}`　/　**📠 FAX:** `{fax_number}`")
else:
    st.info("薬局情報を手入力してください")
    pharmacy_name = st.text_input("🏥 薬局名", key="manual_p_name")
    col_tel, col_fax = st.columns(2)
    tel_number = col_tel.text_input("📞 TEL番号", key="manual_tel")
    fax_number = col_fax.text_input("📠 FAX番号", key="manual_fax")

# --- 共通入力セクション（常時表示） ---
st.write("")
col_a, col_b = st.columns([2, 1])
with col_a:
    delivery_type = st.radio("🚚 受け取り方法", ["配達", "薬局で受け取り"], horizontal=True, key="delivery_radio")
with col_b:
    is_urgent = st.toggle("🚨 至急モード", value=False, key="urgent_toggle")

target_info = st.text_input("🏢 施設名・患者名など", key="target_info", placeholder="")

# 備考欄（Keyを指定）
notes = st.text_area("✍️ 備考", height=120, key="note_input")

# 定型文ボタン（コールバック方式に変更）
with st.expander("📋 定型文を利用する"):
    t1, t2 = st.columns(2)
    # on_click を使うことで、安全にデータを追加できます
    t1.button("原本後日郵送 ＋", use_container_width=True, 
              on_click=add_template, args=("処方箋原本は後日郵送いたします。\n",))
    t2.button("連絡依頼 ＋", use_container_width=True, 
              on_click=add_template, args=("調剤できましたら、○○に連絡をお願い致します。\n",))

st.divider()

# --- PDF発行ボタン（薬局名があればOK） ---
if pharmacy_name:
    pdf_data = create_pdf(pharmacy_name, tel_number, fax_number, delivery_type, target_info, st.session_state.note_input, is_urgent)
    st.download_button(
        label="PDFを発行",
        data=pdf_data,
        file_name=f"送付状_{pharmacy_name}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.warning("薬局名を入力または選択すると、PDFを発行できるようになります。")
