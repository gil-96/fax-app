import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io
import os

# --- 1. 初期設定 ---
FONT_NAME = "HeiseiMin-W3" 

def setup_font():
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))

@st.cache_data
def load_data():
    try:
        # CSVを読み込む
        return pd.read_csv("pharmacy_list.csv")
    except:
        return pd.DataFrame({
            "薬局名": ["サンプル薬局"], 
            "ふりがな": ["さんぷる"],
            "TEL番号": ["000-000-0000"], 
            "FAX番号": ["000-000-0000"]
        })

# --- 2. PDF作成ロジック (A5サイズ) ---
def create_pdf(p_name, p_tel, p_fax, d_type, target_info, note_text, is_urgent):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    setup_font()
    
    if is_urgent:
        p.setFont(FONT_NAME, 24)
        p.drawString(40, height - 60, "【至急】")
    
    p.setFont(FONT_NAME, 18)
    p.drawCentredString(width/2, height - 55, "処 方 箋 送 付 状")
    
    p.setFont(FONT_NAME, 10)
    p.drawString(40, height - 90, f"送信日: {datetime.now().strftime('%Y年 %m月 %d日')}")
    
    p.setFont(FONT_NAME, 14)
    p.drawString(40, height - 110, f"送信先: {p_name} 御中")
    
    p.setFont(FONT_NAME, 10)
    p.drawString(40, height - 130, f"TEL番号: {p_tel}")
    p.drawString(40, height - 145, f"FAX番号: {p_fax}")
    
    p.line(40, height - 155, width - 40, height - 155)
    
    p.setFont(FONT_NAME, 12)
    p.drawString(40, height - 180, f"受け取り方法：{d_type}")
    
    p.setFont(FONT_NAME, 9)
    p.drawString(40, height - 210, "いつも大変お世話になっております。")
    p.drawString(40, height - 222, "以下の通り処方箋を送付いたしますので、ご対応のほど宜しくお願い申し上げます。")
    
    p.setFont(FONT_NAME, 10)
    p.drawString(40, height - 250, "■ 施設名・患者名など")
    p.setFont(FONT_NAME, 12)
    p.drawString(50, height - 270, target_info if target_info else "（未入力）")
    
    p.setFont(FONT_NAME, 10)
    p.drawString(40, height - 300, "■ 備考")
    text_obj = p.beginText(50, height - 320)
    text_obj.setFont(FONT_NAME, 10)
    text_obj.setLeading(14)
    for line in note_text.split("\n"):
        text_obj.textLine(line)
    p.drawText(text_obj)
    
    p.line(40, 90, width - 40, 90)
    p.setFont(FONT_NAME, 11)
    p.drawString(40, 65, "送信元： 陽だまり診療所")
    
    if os.path.exists("logo.png"):
        p.drawImage("logo.png", 300, height - 715, width=70, preserveAspectRatio=True, mask='auto')
    
    p.setFont(FONT_NAME, 9)
    p.drawString(40, 50, "TEL： 0178-32-7358 / FAX： 0178-32-7359")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. アプリ画面の構成 ---
st.set_page_config(page_title="陽だまりFAX", layout="centered")
st.title("📄 処方箋送付状作成")

df_pharmacy = load_data()

# --- 並び替え機能の追加 ---
sort_order = st.radio("表示順", ("リスト順", "あいうえお順"), horizontal=True)

if sort_order == "あいうえお順":
    # 「ふりがな」列を使って並び替え
    df_display = df_pharmacy.sort_values("ふりがな")
else:
    # そのまま（CSVの並び）
    df_display = df_pharmacy

# 薬局選択（並び替えたデータを使用）
pharmacy_name = st.selectbox("🏥 薬局を選択", df_display["薬局名"].tolist())
row = df_display[df_display["薬局名"] == pharmacy_name].iloc[0]
tel_number = row["TEL番号"]
fax_number = row["FAX番号"]

# 後の入力項目は変更なし
delivery_type = st.radio("🚚 受け取り方法", ("配達", "薬局で受け取り"), horizontal=True)
is_urgent = st.checkbox("🚩 至急 (PDFに大きく表示します)", value=False)

st.write(f"**送信先 TEL:** {tel_number} / **FAX:** {fax_number}")
st.divider()

target_info = st.text_input("🏢 施設名・患者名など", placeholder="例：シニアハウス松原 松原潔様")

if 'note_input' not in st.session_state:
    st.session_state.note_input = ""
notes = st.text_area("✍️ 備考", value=st.session_state.note_input, height=120)

st.write("📋 定型文を追加：")
t_col1, t_col2 = st.columns(2)
if t_col1.button("原本後日郵送"):
    st.session_state.note_input = notes + "処方箋原本は後日郵送いたします。\n"
    st.rerun()
if t_col2.button("連絡依頼"):
    st.session_state.note_input = notes + "調剤できましたら、○○に連絡をお願い致します。\n"
    st.rerun()

st.divider()

pdf_data = create_pdf(pharmacy_name, tel_number, fax_number, delivery_type, target_info, notes, is_urgent)

st.download_button(
    label="🖨️ A5サイズPDFを発行する",
    data=pdf_data,
    file_name=f"送付状_{pharmacy_name}.pdf",
    mime="application/pdf",
    use_container_width=True
)
