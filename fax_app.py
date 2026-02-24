import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io

# --- 1. 日本語フォントの設定 ---
def setup_font():
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

# --- 2. CSVデータの読み込み ---
@st.cache_data # データを毎回読み込まないようにキャッシュする
def load_data():
    try:
        # CSVを読み込む（ファイル名は pharmacy_list.csv に変更して配置）
        df = pd.read_csv("pharmacy_list.csv")
        return df
    except:
        # ファイルがない場合の予備データ
        return pd.DataFrame({"薬局名": ["データが見つかりません"], "FAX番号": ["000-000-0000"]})

# --- 3. PDF作成ロジック ---
def create_pdf(p_name, f_num, d_type, note_text):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    setup_font()
    
    p.setFont("HeiseiKakuGo-W5", 18)
    p.drawCentredString(300, 800, "F A X  送  付  状")
    
    p.setFont("HeiseiKakuGo-W5", 12)
    p.drawString(50, 750, f"送信日: {datetime.now().strftime('%Y年 %m月 %d日')}")
    p.drawString(50, 730, f"送信先: {p_name} 御中")
    p.drawString(50, 710, f"FAX番号: {f_num}")
    
    p.line(50, 700, 550, 700)
    
    p.setFont("HeiseiKakuGo-W5", 14)
    p.drawString(50, 670, f"件名: 処方箋送付の件（{d_type}）")
    
    p.setFont("HeiseiKakuGo-W5", 11)
    p.drawString(50, 640, "いつも大変お世話になっております。")
    p.drawString(50, 625, "以下の通り処方箋を送付いたしますので、ご対応のほど宜しくお願い申し上げます。")
    
    p.drawString(50, 590, "【詳細・備考】")
    text_obj = p.beginText(60, 570)
    text_obj.setFont("HeiseiKakuGo-W5", 11)
    for line in note_text.split("\n"):
        text_obj.textLine(line)
    p.drawText(text_obj)
    
    p.line(50, 150, 550, 150)
    p.setFont("HeiseiKakuGo-W5", 12)
    p.drawString(50, 130, "送信元： 陽だまり診療所")
    p.drawString(50, 110, "TEL： 0178-32-7358 / FAX： 0178-32-7359")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 4. アプリ画面 ---
st.set_page_config(page_title="FAX作成 | 陽だまり診療所", layout="centered")
st.title("📄 FAX送付状作成")

df_pharmacy = load_data()

col1, col2 = st.columns(2)
with col1:
    # CSVから薬局名のリストを取得してプルダウンを作成
    pharmacy_name = st.selectbox("🏥 薬局を選択", df_pharmacy["薬局名"].tolist())
    # 選択された薬局のFAX番号を抽出
    fax_number = df_pharmacy[df_pharmacy["薬局名"] == pharmacy_name]["FAX番号"].values[0]

with col2:
    delivery_type = st.radio("🚚 方法", ("自宅へ配達", "薬局で受け取り"), horizontal=True)

st.write(f"**送信先FAX:** {fax_number}")
notes = st.text_area("✍️ 備考欄（患者名など）", height=100)

pdf_data = create_pdf(pharmacy_name, fax_number, delivery_type, notes)
st.download_button(
    label="🖨️ 送付状をPDFで発行する",
    data=pdf_data,
    file_name=f"FAX_{pharmacy_name}.pdf",
    mime="application/pdf",
    use_container_width=True
)