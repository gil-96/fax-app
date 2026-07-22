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

# --- 1. フォント・環境設定 ---
FONT_NAME = "HeiseiMin-W3" 

def setup_font():
    """ReportLabに日本語フォントを登録"""
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))

@st.cache_data
def load_data():
    """薬局リストの読み込み（ファイルがない場合はサンプルデータ）"""
    try:
        return pd.read_csv("pharmacy_list.csv")
    except:
        return pd.DataFrame({
            "薬局名": ["サンプル薬局"], "ふりがな": ["さんぷる"],
            "TEL番号": ["000-000-0000"], "FAX番号": ["000-000-0000"]
        })

# --- 2. PDF作成ロジック（高密度レイアウト） ---
def create_pdf(p_name, p_tel, p_fax, d_type, target_info, note_text, is_urgent):
    """入力情報に基づいてA5サイズの処方箋送付状PDFを生成"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    setup_font()
    
    # 至急フラグの描画
    if is_urgent:
        p.setFont(FONT_NAME, 16)
        p.drawString(40, height - 40, "【至急配達希望】")
    
    # タイトル
    p.setFont(FONT_NAME, 18)
    p.drawCentredString(width/2, height - 70, "処 方 箋 送 付 状")
    
    # 区切り線と宛先情報
    p.setStrokeColorRGB(0.85, 0.85, 0.85)
    p.setLineWidth(0.5)
    
    y = height - 105
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y, f"送信日: {datetime.now().strftime('%Y.%m.%d')}")
    p.setFont(FONT_NAME, 14)
    p.drawString(40, y - 25, f"{p_name} 御中" if p_name else "御中")
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y - 42, f"TEL: {p_tel if p_tel else ''} / FAX: {p_fax if p_fax else ''}")
    
    p.line(40, y - 55, width - 40, y - 55) 
    
    # 送付目的・受け取り方法
    y -= 85 
    p.setFont(FONT_NAME, 11)
    p.drawString(40, y, f"受け取り方法： {d_type}")
    
    y -= 30
    p.setFont(FONT_NAME, 9)
    p.drawString(40, y, "いつも大変お世話になっております。")
    p.drawString(40, y - 13, "以下の通り処方箋を送付いたしますので、ご対応のほど宜しくお願い申し上げます。")
    
    # 施設・患者名情報
    y -= 55 
    p.setFont(FONT_NAME, 8)
    p.drawString(40, y + 8, "施設・患者名など")
    p.setFont(FONT_NAME, 12)
    p.drawString(50, y - 8, target_info if target_info else "---")
    
    # 備考欄
    y -= 55 
    p.setFont(FONT_NAME, 8)
    p.drawString(40, y + 8, "備考")
    text_obj = p.beginText(50, y - 8)
    text_obj.setFont(FONT_NAME, 10)
    text_obj.setLeading(14)
    if note_text:
        for line in note_text.split("\n"):
            text_obj.textLine(line)
    p.drawText(text_obj)
    
    # 送信元情報（フッター）
    p.line(40, 90, width - 40, 90)
    p.setFont(FONT_NAME, 11)
    p.drawString(40, 65, "陽だまり診療所")
    p.setFont(FONT_NAME, 8)
    p.drawString(40, 50, "TEL: 0178-32-7358 / FAX: 0178-32-7359")
    
    # ロゴ画像の挿入（存在する場合）
    logo_path = "logo.png"
    if not os.path.exists(logo_path): 
        logo_path = "陽だまりロゴ.jpg"
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 300, height - 715, width=70, preserveAspectRatio=True, mask='auto')
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. コールバック関数（安全にテキストを追加） ---
def add_template_text(text_to_add):
    """定型文ボタンが押された際に安全にテキストエリアへ追加するコールバック"""
    if 'note_input' in st.session_state:
        st.session_state['note_input'] = (st.session_state['note_input'] or "") + text_to_add

# --- 4. アプリ画面設定 ---
st.set_page_config(page_title="処方箋送付状作成BOT", layout="centered")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #ffffff !important; color: #1d1d1f !important; }
    header[data-testid="stHeader"] { background-color: #ffffff !important; }
    input, select, textarea, label, div, p { color: #1d1d1f !important; }
    .stDownloadButton > button {
        background-color: #0071e3 !important; color: white !important;
        font-size: 1.2rem !important; font-weight: bold !important;
        height: 2.8em !important; border-radius: 12px !important; border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%;
    }
    .stTextInput input, .stTextArea textarea, [data-baseweb="select"] {
        background-color: #f5f5f7 !important; border-radius: 10px !important;
    }
    /* A5用紙プレビュー用スタイル */
    .a5-paper {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-radius: 8px;
        padding: 30px;
        margin-top: 15px;
        font-family: "Hiragino Sans", "Meiryo", sans-serif;
        color: #222222;
    }
    .urgent-tag {
        color: #d93025;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 10px;
    }
    .paper-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        letter-spacing: 4px;
        margin-bottom: 20px;
    }
    .paper-line {
        border-bottom: 1px solid #cccccc;
        margin: 15px 0;
    }
    .paper-section {
        margin-bottom: 15px;
    }
    .paper-label {
        font-size: 0.8rem;
        color: #666666;
        margin-bottom: 3px;
    }
    .paper-content {
        font-size: 1.05rem;
        font-weight: 500;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

# セッション状態の初期化
if 'note_input' not in st.session_state: 
    st.session_state['note_input'] = ""

# ロゴの表示
logo_top = "logo.png"
if not os.path.exists(logo_top): 
    logo_top = "陽だまりロゴ.jpg"
if os.path.exists(logo_top): 
    st.image(logo_top, width=120)

st.title("📄 処方箋送付状作成BOT")
st.caption("入力した情報はリアルタイムで下部のプレビューに反映されます。")
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
        format_func=lambda x: x.split(" (")[0], 
        key="pharmacy_selector"
    )
    
    if pharmacy_selection:
        pharmacy_name = pharmacy_selection.split(" (")[0]
        row = df_display[df_display["薬局名"] == pharmacy_name].iloc[0]
        tel_number = str(row['TEL番号'])
        fax_number = str(row['FAX番号'])
        st.markdown(f"**📞 TEL:** `{tel_number}` / **📠 FAX:** `{fax_number}`")
else:
    st.info("薬局情報を手入力してください")
    pharmacy_name = st.text_input("🏥 薬局名", key="manual_p_name")
    col_tel, col_fax = st.columns(2)
    tel_number = col_tel.text_input("📞 TEL番号", key="manual_tel")
    fax_number = col_fax.text_input("📠 FAX番号", key="manual_fax")

# --- 共通入力セクション ---
st.write("")
col_a, col_b = st.columns([2, 1])
with col_a:
    delivery_type = st.radio("🚚 受け取り方法", ["配達", "薬局で受け取り"], horizontal=True, key="delivery_radio")
with col_b:
    is_urgent = st.toggle("🚨 至急モード", value=False, key="urgent_toggle")

target_info = st.text_input("🏢 施設名・患者名など", key="target_info")

# 備考欄（session_stateと直接連携）
note_text = st.text_area("✍️ 備考", height=100, key="note_input")

# 定型文ボタン（on_clickで安全に追加）
with st.expander("📋 定型文を利用する", expanded=False):
    t1, t2 = st.columns(2)
    t1.button("原本後日郵送 ＋", use_container_width=True, 
              on_click=add_template_text, args=("処方箋原本は後日郵送いたします。\n",))
    t2.button("連絡依頼 ＋", use_container_width=True, 
              on_click=add_template_text, args=("調剤できましたら、ご連絡をお願い致します。\n",))

st.divider()

# --- PDFの生成 & リアルタイム紙面プレビュー表示 ---
if pharmacy_name or input_mode == "手動入力":
    pdf_buffer = create_pdf(
        pharmacy_name, 
        tel_number, 
        fax_number, 
        delivery_type, 
        target_info, 
        note_text, 
        is_urgent
    )
    
    pdf_bytes = pdf_buffer.getvalue()
    
    # 1. ダウンロードボタン
    st.download_button(
        label="📥 送付状PDFをダウンロード",
        data=pdf_bytes,
        file_name=f"送付状_{pharmacy_name if pharmacy_name else '未定'}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    # 2. Chromeのブロックを絶対回避するHTML/CSS紙面プレビュー
    st.markdown("### 👁️ リアルタイムプレビュー")
    
    urgent_html = '<div class="urgent-tag">【至急配達希望】</div>' if is_urgent else ''
    target_disp = target_info if target_info else "---"
    note_disp = note_text if note_text else "---"
    today_str = datetime.now().strftime('%Y.%m.%d')
    p_name_disp = f"{pharmacy_name} 御中" if pharmacy_name else "御中"
    
    preview_html = f"""
    <div class="a5-paper">
        {urgent_html}
        <div class="paper-title">処 方 箋 送 付 状</div>
        <div style="font-size: 0.85rem; color: #555;">送信日: {today_str}</div>
        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 5px;">{p_name_disp}</div>
        <div style="font-size: 0.85rem; color: #555;">TEL: {tel_number} / FAX: {fax_number}</div>
        <div class="paper-line"></div>
        <div style="font-size: 1rem; margin-bottom: 12px;"><strong>受け取り方法：</strong> {delivery_type}</div>
        <div style="font-size: 0.85rem; line-height: 1.5; color: #333;">
            いつも大変お世話になっております。<br>
            以下の通り処方箋を送付いたしますので、ご対応のほど宜しくお願い申し上げます。
        </div>
        <div class="paper-line"></div>
        <div class="paper-section">
            <div class="paper-label">施設・患者名など</div>
            <div class="paper-content">{target_disp}</div>
        </div>
        <div class="paper-section">
            <div class="paper-label">備考</div>
            <div class="paper-content">{note_disp}</div>
        </div>
        <div class="paper-line"></div>
        <div style="font-size: 0.95rem; font-weight: bold;">陽だまり診療所</div>
        <div style="font-size: 0.8rem; color: #555;">TEL: 0178-32-7358 / FAX: 0178-32-7359</div>
    </div>
    """
    st.markdown(preview_html, unsafe_allow_html=True)
else:
    st.warning("👈 薬局名を選択するか手入力すると、PDFの発行とプレビューが表示されます。")
