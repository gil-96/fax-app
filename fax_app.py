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

FONT_NAME = "HeiseiMin-W3" 

def get_logo_base64():
    """ロゴ画像をbase64エンコードして取得（プレビュー用）"""
    logo_path = "logo.png"
    if not os.path.exists(logo_path):
        logo_path = "陽だまりロゴ.jpg"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(logo_path)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            return f"data:{mime};base64,{encoded}"
    return None

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
    
    # ロゴ画像の挿入（右下フッターの位置・サイズを最適化）
    logo_path = "logo.png"
    if not os.path.exists(logo_path): 
        logo_path = "陽だまりロゴ.jpg"
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 295, 50, width=85, height=30, preserveAspectRatio=True, mask='auto')
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def add_template_text(text_to_add):
    """定型文ボタンが押された際に安全にテキストエリアへ追加するコールバック"""
    if 'note_input' in st.session_state:
        st.session_state['note_input'] = (st.session_state['note_input'] or "") + text_to_add

st.set_page_config(page_title="処方箋送付状作成BOT", layout="wide")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #ffffff !important; color: #1d1d1f !important; }
    header[data-testid="stHeader"] { background-color: #ffffff !important; }
    input, select, textarea, label, div, p { color: #1d1d1f !important; }
    .stDownloadButton > button {
        background-color: #0071e3 !important; color: white !important;
        font-size: 1.1rem !important; font-weight: bold !important;
        height: 2.8em !important; border-radius: 10px !important; border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%;
    }
    .stTextInput input, .stTextArea textarea, [data-baseweb="select"] {
        background-color: #f5f5f7 !important; border-radius: 8px !important;
    }
    .block-container { padding-top: 4rem !important; padding-bottom: 2rem !important; }
    [data-testid="stImage"] img { padding-top: 8px !important; padding-bottom: 4px !important; }
    </style>
    """, unsafe_allow_html=True)

# セッション状態の初期化
if 'note_input' not in st.session_state: 
    st.session_state['note_input'] = ""

# 上部ヘッダー（カラム幅を広げ垂直中央揃えでロゴの上部見切れを修正）
header_col1, header_col2 = st.columns([2.5, 9.5], vertical_alignment="center")
with header_col1:
    logo_top = "logo.png"
    if not os.path.exists(logo_top): 
        logo_top = "陽だまりロゴ.jpg"
    if os.path.exists(logo_top): 
        st.image(logo_top, use_container_width=True)

with header_col2:
    st.title("📄 処方箋送付状作成BOT")

st.divider()

col_input, col_preview = st.columns([1, 1], gap="large")

# --- 左カラム：入力フォーム ---
with col_input:
    st.subheader("📝 入力フォーム")
    
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
            tel_number = str(row['TEL番号'])
            fax_number = str(row['FAX番号'])
            st.markdown(f"**📞 TEL:** `{tel_number}` / **📠 FAX:** `{fax_number}`")
    else:
        pharmacy_name = st.text_input("🏥 薬局名を選択もしくは入力", placeholder="薬局名", key="manual_p_name")
        col_tel, col_fax = st.columns(2)
        tel_number = col_tel.text_input("📞 TEL番号", key="manual_tel")
        fax_number = col_fax.text_input("📠 FAX番号", key="manual_fax")

    st.write("")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        delivery_type = st.radio("🚚 受け取り方法", ["配達", "薬局で受け取り"], horizontal=True, key="delivery_radio")
    with col_b:
        is_urgent = st.toggle("🚨 至急モード", value=False, key="urgent_toggle")

    target_info = st.text_input("🏢 施設名・患者名など", key="target_info")

    # 備考欄
    note_text = st.text_area("✍️ 備考", height=100, key="note_input")

    # 定型文ボタン
    with st.expander("📋 定型文を利用する", expanded=False):
        t1, t2 = st.columns(2)
        t1.button("原本後日郵送 ＋", use_container_width=True, 
                  on_click=add_template_text, args=("処方箋原本は後日郵送いたします。\n",))
        t2.button("連絡依頼 ＋", use_container_width=True, 
                  on_click=add_template_text, args=("調剤できましたら、ご連絡をお願い致します。\n",))

    st.write("")
    
    # PDFダウンロードボタン
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
        
        st.download_button(
            label="📥 送付状PDFをダウンロード",
            data=pdf_bytes,
            file_name=f"送付状_{pharmacy_name if pharmacy_name else '未定'}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.info("👈 薬局名を選択または手入力すると、ダウンロードボタンが有効化されます。")

# --- 右カラム：リアルタイムプレビュー ---
with col_preview:
    st.subheader("🔭 リアルタイム プレビュー")
    
    today_str = datetime.now().strftime('%Y年%m月%d日')
    p_name_disp = f"{pharmacy_name} 御中" if pharmacy_name else "御中"
    target_disp = target_info if target_info else "---"
    note_disp = note_text if note_text else "---"
    urgent_header = '<div style="color: #000; font-weight: bold; font-size: 15px; margin-bottom: 8px;">【至急配達希望】</div>' if is_urgent else ''
    
    logo_b64 = get_logo_base64()
    logo_html = f'<img src="{logo_b64}" style="height: 38px; width: auto; object-fit: contain;">' if logo_b64 else ''

    preview_html = f"""
    <div style="background-color: #f4f5f7; padding: 15px; display: flex; justify-content: center; align-items: flex-start; min-height: 720px; border-radius: 8px;">
        <div id="fax-content" style="
            background-color: white;
            padding: 12mm 14mm 12mm 14mm;
            width: 100%;
            max-width: 140mm;
            min-height: 185mm;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border-radius: 4px;
            font-family: 'Helvetica Neue', Arial, 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
            color: #333;
            line-height: 1.4;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
        ">
            {urgent_header}
            
            <!-- タイトル -->
            <div style="text-align: center; margin-bottom: 16px;">
                <div style="font-size: 20px; font-weight: bold; letter-spacing: 3px; border-bottom: 2px solid #333; display: inline-block; padding: 0 25px 3px 25px; color: #000;">
                    処 方 箋 送 付 状
                </div>
            </div>

            <!-- 送信日 & 宛先 -->
            <div style="border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 12px;">
                <div style="text-align: right; font-size: 11px; color: #666; margin-bottom: 6px;">
                    送信日：{today_str}
                </div>
                <div style="font-size: 16px; font-weight: bold; color: #111;">
                    {p_name_disp}
                </div>
                <div style="font-size: 12px; color: #555; margin-top: 3px;">
                    TEL: {tel_number if tel_number else ''} &nbsp;/&nbsp; FAX: {fax_number if fax_number else ''}
                </div>
            </div>

            <!-- 内容ステートメント -->
            <div style="margin-bottom: 12px; font-size: 13px;">
                <div style="font-weight: bold; margin-bottom: 4px;">受け取り方法： {delivery_type}</div>
                <div style="color: #444; font-size: 12px; line-height: 1.4;">
                    いつも大変お世話になっております。<br>
                    以下の通り処方箋を送付いたしますので、ご対応のほど宜しくお願い申し上げます。
                </div>
            </div>

            <div style="border-top: 1px solid #ddd; margin: 8px 0;"></div>

            <!-- 施設・患者名 -->
            <div style="margin-bottom: 12px;">
                <div style="font-size: 10px; color: #777; margin-bottom: 2px;">施設・患者名など</div>
                <div style="font-size: 14px; font-weight: 500; white-space: pre-wrap; color: #111;">{target_disp}</div>
            </div>

            <!-- 備考 -->
            <div style="margin-bottom: 16px; flex-grow: 1;">
                <div style="font-size: 10px; color: #777; margin-bottom: 2px;">備考</div>
                <div style="font-size: 13px; white-space: pre-wrap; color: #222; line-height: 1.4;">{note_disp}</div>
            </div>

            <div style="border-top: 1px solid #ddd; margin-bottom: 10px;"></div>

            <!-- 送信元 & ロゴ -->
            <div style="display: flex; justify-content: space-between; align-items: flex-end; font-size: 12px; color: #333;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #000;">陽だまり診療所</div>
                    <div style="font-size: 11px; color: #555;">TEL: 0178-32-7358 &nbsp;/&nbsp; FAX: 0178-32-7359</div>
                </div>
                {logo_html}
            </div>
        </div>
    </div>
    """
    
    st.components.v1.html(preview_html, height=760, scrolling=True)
