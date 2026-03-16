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

# --- 2. PDF作成ロジック ---
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
    
    # TEL/FAXの表示判定
    p.setFont(FONT_NAME, 9)
    contact_info = []
    if p_tel: contact_info.append(f"TEL: {p_tel}")
    if p_fax: contact_info.append(f"FAX: {p_fax}")
    p.drawString(40, y - 42, "  /  ".join(contact_info))
    
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

# --- 3. アプリ画面 ---
st.set_page_config(page_title="Hidamari Clinic FAX", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stDownloadButton > button {
        background-color: #0071e3 !important;
        color: white !important;
        font-size: 1.15rem !important;
        font-weight: bold !important;
        height: 3.8em !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

logo_top = "logo.png"
if not os.path.exists(logo_top): logo_top = "陽だまりロゴ.jpg"
if os.path.exists(logo_top): st.image(logo_top, width=120)

st.title("処方箋送付状の作成")
st.divider()

# 入力モードの選択
input_mode = st.segmented_control("入力方法", ["リストから選択", "新規（手入力）"], default="リストから選択")

if input_mode == "リストから選択":
    df_pharmacy = load_data()
    sort_order = st.segmented_control("並び順", ["リスト順", "あいうえお順"], default="リスト順")
    df_display = df_pharmacy.sort_values("ふりがな") if sort_order == "あいうえお順" else df_pharmacy
    
    pharmacy_name = st.selectbox("🏥 薬局を選択", df_display["薬局名"].tolist())
    row = df_display[df_display["薬局名"] == pharmacy_name].iloc[0]
    p_tel = row['TEL番号']
    p_fax = row['FAX番号']
else:
    # --- 手入力モード ---
    pharmacy_name = st.text_input("🏥 薬局名", placeholder="例：ひだまり薬局")
    
    col1, col2 = st.columns(2)
    with col1:
        use_tel = st.checkbox("TELを入力する")
        p_tel = st.text_input("📞 TEL番号", disabled=not use_tel) if use_tel else ""
    with col2:
        use_fax = st.checkbox("FAXを入力する")
        p_fax = st.text_input("📠 FAX番号", disabled=not use_fax) if use_fax else ""

st.divider()

col_a, col_b = st.columns([2, 1])
with col_a:
    delivery_type = st.radio("🚚 受け取り方法", ["配達", "薬局で受け取り"], horizontal=True)
with col_b:
    is_urgent = st.toggle("🚨 至急モード", value=False)

# 患者名（プレースホルダー削除）
target_info = st.text_input("🏢 施設名・患者名など")

if 'note_input' not in st.session_state: st.session_state.note_input = ""
notes = st.text_area("✍️ 備考", value=st.session_state.note_input, height=120)
st.session_state.note_input = notes

with st.expander("📋 定型文を利用する"):
    t1, t2 = st.columns(2)
    if t1.button("原本後日郵送 ＋", use_container_width=True):
        st.session_state.note_input += "処方箋原本は後日郵送いたします。\n"
        st.rerun()
    if t2.button("連絡依頼 ＋", use_container_width=True):
        st.session_state.note_input += "調剤できましたら、○○に連絡をお願い致します。\n"
        st.rerun()

st.divider()

if pharmacy_name:
    pdf_data = create_pdf(pharmacy_name, p_tel, p_fax, delivery_type, target_info, st.session_state.note_input, is_urgent)

    st.download_button(
        label=f"🖨️ {pharmacy_name} 宛のPDFを発行",
        data=pdf_data,
        file_name=f"送付状_{pharmacy_name}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.info("薬局名を入力または選択してください。")
