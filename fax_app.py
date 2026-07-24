import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io
import os
import base64
import textwrap

st.set_page_config(page_title="処方箋送付状作成BOT", layout="wide")

FONT_NAME = "HeiseiMin-W3" 

if 'note_input' not in st.session_state: 
    st.session_state['note_input'] = ""

def setup_font():
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))
    except Exception as e:
        st.error(f"フォントの読み込みに失敗しました: {e}")

@st.cache_data
def load_data():
    try:
        return pd.read_csv("pharmacy_list.csv")
    except Exception:
        return pd.DataFrame({
            "薬局名": ["サンプル薬局"], "ふりがな": ["さんぷる"],
            "TEL番号": ["000-000-0000"], "FAX番号": ["000-000-0000"]
        })

def get_logo_path():
    if os.path.exists("logo.png"):
        return "logo.png"
    elif os.path.exists("陽だまりロゴ.jpg"):
        return "陽だまりロゴ.jpg"
    return None

def get_logo_base64():
    logo_path = get_logo_path()
    if logo_path:
        try:
            with open(logo_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode()
                ext = logo_path.split('.')[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{encoded}"
        except Exception:
            pass
    return ""

def sanitize_for_pdf(text):
    if not text:
        return ""
    replacements = {
        '〜': '～', '①': '(1)', '②': '(2)', '③': '(3)', '④': '(4)', 
        '⑤': '(5)', '⑥': '(6)', '⑦': '(7)', '⑧': '(8)', '⑨': '(9)', '⑩': '(10)',
        '株': '(株)', '有': '(有)', '代': '(代)'
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return "".join([char for char in text if ord(char) < 0x10000])

def create_pdf(p_name, p_tel, p_fax, d_type, target_info, note_text, is_urgent):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    setup_font()
    
    # データをクリーニング
    p_name_clean = sanitize_for_pdf(p_name)
    p_tel_clean = sanitize_for_pdf(p_tel)
    p_fax_clean = sanitize_for_pdf(p_fax)
    target_info_clean = sanitize_for_pdf(target_info)
    note_text_clean = sanitize_for_pdf(note_text)
    
    # --- ヘッダー部分 ---
    if is_urgent:
        p.setFont(FONT_NAME, 16)
        p.setFillColorRGB(0.8, 0, 0) # 至急は赤系
        p.drawCentredString(width/2, height - 40, "【至急配達希望】")
        p.setFillColorRGB(0, 0, 0)
    
    p.setFont(FONT_NAME, 18)
    p.drawCentredString(width/2, height - 70, "処 方 箋 送 付 状")
    
    # --- 日付・宛先 ---
    y = height - 110
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y, f"送信日: {datetime.now().strftime('%Y.%m.%d')}")
    
    p.setFont(FONT_NAME, 14)
    p.drawString(40, y - 25, f"{p_name_clean}  御中")
    
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y - 42, f"TEL: {p_tel_clean}  /  FAX: {p_fax_clean}")
    
    p.setStrokeColorRGB(0.7, 0.7, 0.7)
    p.line(40, y - 52, width - 40, y - 52)
    
    # --- 本文・情報 ---
    y -= 80
    p.setFont(FONT_NAME, 11)
    p.drawString(40, y, f"■ 受け取り方法： {d_type}")
    
    y -= 25
    p.setFont(FONT_NAME, 10)
    p.drawString(40, y, "いつも大変お世話になっております。")
    p.drawString(40, y - 15, "以下の通り処方箋を送付いたしますので、ご対応のほど宜しくお願い申し上げます。")
    
    # 枠付きエリア（モダンデザイン）
    y -= 50
    p.setStrokeColorRGB(0.9, 0.9, 0.9)
    p.rect(40, y - 45, width - 80, 50, fill=0, stroke=1) # 施設・患者名枠
    
    p.setFont(FONT_NAME, 8)
    p.drawString(50, y + 2, "施設・患者名など")
    p.setFont(FONT_NAME, 11)
    p.drawString(50, y - 25, target_info_clean if target_info_clean else "---")
    
    y -= 85
    p.setFont(FONT_NAME, 8)
    p.drawString(40, y + 10, "備考")
    if note_text_clean:
        text_obj = p.beginText(40, y - 5)
        text_obj.setFont(FONT_NAME, 10)
        text_obj.setLeading(14)
        lines = []
        for raw_line in note_text_clean.split("\n"):
            lines.extend(textwrap.wrap(raw_line, width=40))
        for line in lines[:8]: # 8行制限
            text_obj.textLine(line)
        p.drawText(text_obj)
    
    # --- フッター ---
    p.setStrokeColorRGB(0.7, 0.7, 0.7)
    p.line(40, 80, width - 40, 80)
    p.setFont(FONT_NAME, 11)
    p.drawString(40, 60, "陽だまり診療所")
    p.setFont(FONT_NAME, 8)
    p.drawString(40, 45, "TEL: 0178-32-7358  /  FAX: 0178-32-7359")
    
    logo = get_logo_path()
    if logo:
        p.drawImage(logo, 295, 45, width=80, height=25, preserveAspectRatio=True, mask='auto')
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def add_template(text):
    st.session_state['note_input'] += text

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
        background-color: #ffffff !important; 
        color: #1d1d1f !important; 
    }
    .block-container { padding-top: 2rem !important; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        background-color: #fdfdfd !important;
        border: 1px solid #eaeaea !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
        padding: 0.5rem;
    }
    .stDownloadButton > button {
        background-color: #0071e3 !important; color: white !important;
        font-weight: bold !important; height: 2.8em !important; 
        border-radius: 12px !important; width: 100%;
    }
    .stDownloadButton > button:disabled {
        background-color: #e5e5ea !important; color: #8e8e93 !important;
    }
    </style>
    """, unsafe_allow_html=True)

col_header_logo, col_header_title = st.columns([2, 8], vertical_alignment="center")
if logo := get_logo_path():
    with col_header_logo: st.image(logo, use_container_width=True)
with col_header_title: st.title("📄 処方箋送付状作成BOT")

st.divider()
col_input, col_preview = st.columns([1, 1.1], gap="large")

with col_input:
    # --- 薬局情報カード ---
    with st.container(border=True):
        st.markdown("**🏥 宛先（薬局）情報**")
        input_mode = st.segmented_control("モード", ["リスト選択", "手動入力"], default="リスト選択", label_visibility="collapsed")
        
        pharmacy_name, tel_number, fax_number = "", "", ""
        if input_mode == "リスト選択":
            df = load_data()
            pharmacy_selection = st.selectbox("薬局", df["薬局名"].tolist(), index=None, placeholder="薬局名", label_visibility="collapsed")
            if pharmacy_selection:
                row = df[df["薬局名"] == pharmacy_selection].iloc[0]
                pharmacy_name, tel_number, fax_number = row['薬局名'], row['TEL番号'], row['FAX番号']
                st.caption(f"📞 {tel_number} ｜ 📠 {fax_number}")
        else:
            pharmacy_name = st.text_input("薬局名", placeholder="薬局名", label_visibility="collapsed")
            c1, c2 = st.columns(2)
            tel_number = c1.text_input("TEL", placeholder="TEL", label_visibility="collapsed")
            fax_number = c2.text_input("FAX", placeholder="FAX", label_visibility="collapsed")

    # --- 伝達内容カード ---
    with st.container(border=True):
        st.markdown("**📋 伝達内容**")
        target_info = st.text_input("施設名・患者名など", placeholder="例：山田太郎 様", key="target_info")
        c3, c4 = st.columns([1.5, 1], vertical_alignment="center")
        delivery_type = c3.radio("受取方法", ["配達", "薬局受取"], horizontal=True, key="delivery_radio")
        is_urgent = c4.toggle("🚨 至急", value=False, key="urgent_toggle")

    # --- 備考カード ---
    with st.container(border=True):
        st.markdown("**✍️ 備考**")
        note_text = st.text_area("備考", height=80, key="note_input", label_visibility="collapsed")
        c1, c2 = st.columns(2)
        c1.button("＋ 原本後日郵送", use_container_width=True, on_click=add_template, args=("処方箋原本は後日郵送いたします。\n",))
        c2.button("＋ 連絡依頼", use_container_width=True, on_click=add_template, args=("調剤後連絡をお願い致します。\n",))

    # --- アクション ---
    if pharmacy_name:
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("🔄 作成", type="primary", use_container_width=True):
            pdf_data = create_pdf(pharmacy_name, tel_number, fax_number, delivery_type, target_info, note_text, is_urgent)
            st.session_state['generated_pdf'] = pdf_data.getvalue()
            st.session_state['current_pharmacy'] = pharmacy_name
            
        is_ready = 'generated_pdf' in st.session_state and st.session_state.get('current_pharmacy') == pharmacy_name
        col_btn2.download_button(
            label="📄 ダウンロード" if is_ready else "🚫 先に作成",
            data=st.session_state.get('generated_pdf', b''),
            file_name=f"送付状_{pharmacy_name}.pdf" if is_ready else "dummy.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=not is_ready
        )
    else:
        st.info("👆 薬局を指定するとボタンが表示されます。")

with col_preview:
    st.subheader("🔭 リアルタイムプレビュー")
    # プレビュー表示用
    note_disp = (note_text or "---").replace("\n", "<br>")
    urgent_header = '<div style="color:red; font-weight:bold;">【至急配達希望】</div>' if is_urgent else ''
    
    st.markdown(f"""
    <div style="background:#f0f2f5; padding:20px; border-radius:12px; display:flex; justify-content:center;">
        <div style="background:white; width:350px; padding:30px; box-shadow:0 4px 15px rgba(0,0,0,0.1); font-size:12px; line-height:1.6;">
            {urgent_header}
            <div style="text-align:center; font-size:16px; font-weight:bold; border-bottom:1px solid #000; margin-bottom:10px;">処方箋送付状</div>
            <div>**{pharmacy_name or '...'} 御中**</div>
            <div style="margin:10px 0;">受取方法：{delivery_type}</div>
            <div style="border:1px solid #eee; padding:5px; margin-bottom:10px;">**施設/患者:** {target_info or '---'}</div>
            <div>**備考:** {note_disp}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
