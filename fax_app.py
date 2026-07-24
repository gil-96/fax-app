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

# --- 1. 定数・環境設定 ---
FONT_NAME = "HeiseiMin-W3" 

# セッションステートの初期化
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
    """ロゴ画像のパスを取得する共通関数（DRY原則）"""
    if os.path.exists("logo.png"):
        return "logo.png"
    elif os.path.exists("陽だまりロゴ.jpg"):
        return "陽だまりロゴ.jpg"
    return None

def get_logo_base64():
    """ロゴ画像をBase64形式で取得する"""
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
    """絵文字や特殊Unicode文字を安全な文字に変換・除去する関数"""
    if not text:
        return ""
    
    replacements = {
        '〜': '～',
        '①': '(1)', '②': '(2)', '③': '(3)', '④': '(4)', '⑤': '(5)',
        '⑥': '(6)', '⑦': '(7)', '⑧': '(8)', '⑨': '(9)', '⑩': '(10)',
        '株': '(株)', '有': '(有)', '代': '(代)'
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
        
    clean_chars = [char for char in text if ord(char) < 0x10000]
    return "".join(clean_chars)

def create_pdf(p_name, p_tel, p_fax, d_type, target_info, note_text, is_urgent):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    setup_font()
    
    p_name_clean = sanitize_for_pdf(p_name)
    p_tel_clean = sanitize_for_pdf(p_tel)
    p_fax_clean = sanitize_for_pdf(p_fax)
    target_info_clean = sanitize_for_pdf(target_info)
    note_text_clean = sanitize_for_pdf(note_text)
    
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
    p.drawString(40, y - 25, f"{p_name_clean}  御中")
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y - 42, f"TEL: {p_tel_clean if p_tel_clean else ''}  /  FAX: {p_fax_clean if p_fax_clean else ''}")
    
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
    p.drawString(50, y - 8, target_info_clean if target_info_clean else "---")
    
    y -= 55 
    p.setFont(FONT_NAME, 8)
    p.drawString(40, y + 8, "備考")
    
    if note_text_clean:
        text_obj = p.beginText(50, y - 8)
        text_obj.setFont(FONT_NAME, 10)
        text_obj.setLeading(14)
        
        wrap_width = 35 
        lines = []
        for raw_line in note_text_clean.split("\n"):
            wrapped = textwrap.wrap(raw_line, width=wrap_width)
            if not wrapped: 
                lines.append("")
            else:
                lines.extend(wrapped)

        max_lines = 10
        for i, line in enumerate(lines):
            if i < max_lines:
                text_obj.textLine(line)
            elif i == max_lines:
                text_obj.textLine("…（以下省略）")
                break
        p.drawText(text_obj)
    else:
        p.setFont(FONT_NAME, 10)
        p.drawString(50, y - 8, "---")
    
    # フッター部
    p.line(40, 90, width - 40, 90)
    p.setFont(FONT_NAME, 11)
    p.drawString(40, 65, "陽だまり診療所")
    p.setFont(FONT_NAME, 8)
    p.drawString(40, 50, "TEL: 0178-32-7358  /  FAX: 0178-32-7359")
    
    logo_path = get_logo_path()
    if logo_path:
        try:
            p.drawImage(logo_path, 295, 50, width=85, height=30, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def add_template(text):
    """定型文を追加する安全なコールバック関数"""
    st.session_state['note_input'] += text

st.markdown("""
    <style>
    /* 強制ライトモード化と真っ白な背景設定 */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
        background-color: #ffffff !important; 
        color: #0f172a !important; 
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1400px;
    }

    input, select, textarea, label, div, p, span { color: #0f172a !important; }

    /* テキスト入力・エリア・セレクトボックスのモダン化 */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        color: #0f172a !important;
        font-size: 0.92rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus, div[data-baseweb="select"]:focus-within > div {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18), 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    /* ボタンの共通スタイリング */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        color: #334155 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    .stButton > button:hover {
        border-color: #94a3b8 !important;
        background: #f8fafc !important;
        color: #0f172a !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px -2px rgba(0, 0, 0, 0.08) !important;
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* Primaryボタン (1. PDFを作成) のモダンデザイン */
    button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28) !important;
    }
    button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.38) !important;
    }

    /* ダウンロードボタンのモダンデザイン */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        height: 2.6em !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
    }
    .stDownloadButton > button:hover:not(:disabled) {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 6px 16px rgba(16, 185, 129, 0.35) !important;
        transform: translateY(-1px);
    }
    .stDownloadButton > button:disabled {
        background: #e2e8f0 !important;
        color: #94a3b8 !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
        transform: none !important;
    }

    /* エクスパンダー（定型文アコーディオン）のカスタマイズ */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }

    /* 中央配置のメインタイトル */
    .page-main-title {
        text-align: center;
        font-size: 1.75rem;
        font-weight: 800;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
        color: #0f172a;
        letter-spacing: -0.02em;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="page-main-title">処方箋送付状作成</div>', unsafe_allow_html=True)

col_input, col_preview = st.columns([1, 1.1], gap="large")

with col_input:
    st.subheader("📝 入力フォーム")
    
    # 作成モードと並び順を横並び（2カラム）に配置
    col_mode, col_sort = st.columns([1, 1], gap="small")
    
    with col_mode:
        input_mode = st.segmented_control("作成モード", ["リストから選択", "手動入力"], default="リストから選択", key="mode_ctrl")

    pharmacy_name = ""
    tel_number = ""
    fax_number = ""

    with col_sort:
        if input_mode == "リストから選択":
            sort_order = st.segmented_control("並び順", ["リスト順", "あいうえお順"], default="リスト順", key="sort_ctrl")
        else:
            sort_order = "リスト順"

    if input_mode == "リストから選択":
        df_pharmacy = load_data()
        df_display = df_pharmacy.sort_values("ふりがな") if sort_order == "あいうえお順" else df_pharmacy

        search_list = [f"{row['薬局名']} ({row['ふりがな']})" for _, row in df_display.iterrows()]
        
        pharmacy_selection = st.selectbox(
            "🏥 薬局名を選択もしくは入力", 
            search_list,
            index=None,
            placeholder="薬局名",
            format_func=lambda x: x.split(" (")[0], 
            key="pharmacy_selector"
        )
        
        if pharmacy_selection:
            pharmacy_name = pharmacy_selection.split(" (")[0]
            row = df_display[df_display["薬局名"] == pharmacy_name].iloc[0]
            tel_number = row['TEL番号']
            fax_number = row['FAX番号']
            st.markdown(f"**📞 TEL:** `{tel_number}` / **📠 FAX:** `{fax_number}`")
    else:
        st.info("薬局情報を手入力してください")
        pharmacy_name = st.text_input("🏥 薬局名", placeholder="薬局名", key="manual_p_name")
        col_tel, col_fax = st.columns(2)
        tel_number = col_tel.text_input("📞 TEL番号", key="manual_tel")
        fax_number = col_fax.text_input("📠 FAX番号", key="manual_fax")

    col_a, col_b = st.columns([1.8, 1.2])
    with col_a:
        delivery_type = st.radio("🚚 受け取り方法", ["配達", "薬局で受け取り"], horizontal=True, key="delivery_radio")
    with col_b:
        is_urgent = st.toggle("🚨 至急モード", value=False, key="urgent_toggle")

    target_info = st.text_input("🏢 施設名・患者名など", key="target_info")
    note_text = st.text_area("✍️ 備考", height=100, key="note_input")

    with st.expander("📋 定型文を利用する"):
        t1, t2 = st.columns(2)
        t1.button("原本後日郵送 ＋", use_container_width=True, 
                  on_click=add_template, args=("処方箋原本は後日郵送いたします。\n",))
        t2.button("連絡依頼 ＋", use_container_width=True, 
                  on_click=add_template, args=("調剤できましたら、○○に連絡をお願い致します。\n",))

    st.divider()

    if pharmacy_name:
        st.caption("⚠️ 入力内容を変更した場合は、必ず左の「1. PDFを作成」を押してください")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔄 1. PDFを作成 (内容確定)", type="primary", use_container_width=True):
                with st.spinner("作成中..."):
                    pdf_data = create_pdf(pharmacy_name, tel_number, fax_number, delivery_type, target_info, note_text, is_urgent)
                    st.session_state['generated_pdf'] = pdf_data.getvalue()
                    st.session_state['current_pharmacy'] = pharmacy_name

        with col_btn2:
            is_ready = 'generated_pdf' in st.session_state and st.session_state.get('current_pharmacy') == pharmacy_name
            
            st.download_button(
                label="📄 2. ダウンロード" if is_ready else "🚫 先に作成してください",
                data=st.session_state.get('generated_pdf', b''),
                file_name=f"送付状_{pharmacy_name}.pdf" if is_ready else "dummy.pdf",
                mime="application/pdf",
                use_container_width=True,
                disabled=not is_ready
            )
    else:
        st.info("👆 薬局名を選択または手入力すると、作成・ダウンロードボタンが有効化されます。")

with col_preview:
    st.subheader("🔭 プレビュー")
    
    today_str = datetime.now().strftime('%Y年%m月%d日')
    p_name_disp = f"{pharmacy_name} 御中" if pharmacy_name else "御中"
    target_disp = target_info if target_info else "---"
    
    note_disp = note_text.replace("\n", "<br>") if note_text else "---"
    
    urgent_header = '<div style="color: #000; font-weight: bold; font-size: 15px; margin-bottom: 8px;">【至急配達希望】</div>' if is_urgent else ''
    
    logo_b64 = get_logo_base64()
    logo_html = f'<img src="{logo_b64}" style="height: 38px; width: auto; object-fit: contain;">' if logo_b64 else ''

    preview_html = f"""
    <div style="
        background-color: #f0f2f5; 
        padding: 16px; 
        border-radius: 12px; 
        display: flex; 
        justify-content: center;
        box-shadow: inset 0 0 8px rgba(0,0,0,0.05);
    ">
        <div id="fax-preview-container" style="
            background-color: white;
            width: 148mm;
            min-height: 200mm;
            padding: 12mm 15mm 10mm 15mm;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
            color: #000;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <!-- ヘッダーエリア -->
                {urgent_header}
                <div style="text-align: center; margin-bottom: 12px;">
                    <span style="font-size: 20px; font-weight: bold; letter-spacing: 2px; border-bottom: 2px solid #000; padding-bottom: 2px; display: inline-block;">
                        処 方 箋 送 付 状
                    </span>
                </div>
                
                <div style="text-align: right; font-size: 11px; color: #333; margin-bottom: 8px;">
                    送信日: {today_str}
                </div>

                <!-- 宛先 -->
                <div style="border-bottom: 1px solid #ccc; padding-bottom: 8px; margin-bottom: 12px;">
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 2px;">{p_name_disp}</div>
                    <div style="font-size: 11px; color: #444;">TEL: {tel_number} &nbsp;/&nbsp; FAX: {fax_number}</div>
                </div>

                <!-- 受け取り方法・挨拶 -->
                <div style="font-size: 13px; font-weight: bold; margin-bottom: 10px;">
                    受け取り方法： {delivery_type}
                </div>
                <div style="font-size: 11px; color: #333; line-height: 1.5; margin-bottom: 15px;">
                    いつも大変お世話になっております。<br>
                    以下の通り処方箋を送付いたしますので、ご対応のほど宜しくお願い申し上げます。
                </div>

                <!-- 施設・患者名など -->
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 10px; color: #666; margin-bottom: 2px;">■ 施設・患者名など</div>
                    <div id="preview-target-info" style="font-size: 13px; font-weight: bold; padding-left: 8px;">{target_disp}</div>
                </div>

                <!-- 備考 -->
                <div style="margin-bottom: 15px;">
                    <div style="font-size: 10px; color: #666; margin-bottom: 2px;">■ 備考</div>
                    <div id="preview-note-text" style="font-size: 12px; padding-left: 8px; line-height: 1.5; word-break: break-all;">{note_disp}</div>
                </div>
            </div>

            <!-- フッター（送信元＆ロゴ） -->
            <div style="border-top: 1px solid #000; padding-top: 8px; margin-top: 10px; display: flex; justify-content: space-between; align-items: flex-end;">
                <div>
                    <div style="font-size: 13px; font-weight: bold;">陽だまり診療所</div>
                    <div style="font-size: 10px; color: #444;">TEL: 0178-32-7358 &nbsp;/&nbsp; FAX: 0178-32-7359</div>
                </div>
                <div>
                    {logo_html}
                </div>
            </div>
        </div>
    </div>
    """
    st.components.v1.html(preview_html, height=730, scrolling=True)
