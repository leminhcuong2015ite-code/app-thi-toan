import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client
import pandas as pd
import random
import datetime
import re
import hashlib
import io
import uuid
import base64
import importlib
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage
import kntt_mapping
import latex_parser

# Tự động nạp lại module phụ mỗi khi cập nhật code trên GitHub mà không cần Reboot app
importlib.reload(kntt_mapping)
importlib.reload(latex_parser)

from latex_parser import parse_exam_tex, clean_latex_to_markdown, ensure_displaystyle_int, PARSER_VERSION
from kntt_mapping import KNTT_DATA, LEVEL_MAP, decode_kntt_tag

st.set_page_config(page_title="Hệ thống Kiểm tra Đánh giá Môn Toán - Thầy Lê Minh Cường", layout="wide", page_icon="📐")

# ================= CSS CHỐNG LỖI DARK MODE TRÊN LAPTOP & IPHONE + CỠ CHỮ ĐỀ BÀI TO RÕ =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

:root, html, body, [data-theme="dark"], [data-theme="light"] {
    color-scheme: light !important;
}

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0f172a !important;
}

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
    color: #0f172a !important;
}

section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
    border-right: 1px solid #cbd5e1 !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {
    color: #0f172a !important;
}

/* Ép tất cả khung viền, expander, ô nhập liệu luôn có nền sáng và chữ đậm rõ nét ngay cả khi máy bật Dark Mode */
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stExpander"],
div[data-testid="stForm"] {
    background-color: #ffffff !important;
    border-color: #cbd5e1 !important;
    color: #0f172a !important;
    border-radius: 12px !important;
}

div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* Ép chữ câu hỏi, công thức toán KaTeX/MathJax, tiêu đề phụ, nhãn widget luôn màu tối tương phản cao */
div[data-testid="stMarkdownContainer"],
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li,
div[data-testid="stMarkdownContainer"] span,
div[data-testid="stWidgetLabel"] p,
div[data-testid="stCaptionContainer"] p,
label[data-testid="stWidgetLabel"],
.katex, .katex *,
mjx-container, mjx-container * {
    color: #0f172a !important;
}

/* Ô nhập liệu, selectbox, textarea trên iPhone (Safari Dark Mode) và Laptop */
input, textarea, select,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    border-color: #94a3b8 !important;
}

/* Nút bấm mặc định (Secondary button) luôn có nền trắng viền rõ trên Dark Mode */
button[kind="secondary"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1.5px solid #cbd5e1 !important;
    font-weight: 600 !important;
}
button[kind="secondary"]:hover {
    background-color: #eff6ff !important;
    border-color: #3b82f6 !important;
    color: #1d4ed8 !important;
}
button[kind="primary"] p, button[kind="primary"] span {
    color: #ffffff !important;
}

/* Thanh Tab rõ nét trên cả nền tối */
button[data-baseweb="tab"] p, button[data-baseweb="tab"] span {
    color: #334155 !important;
    font-weight: 600 !important;
    font-size: 15.5px !important;
}
button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] span {
    color: #1d4ed8 !important;
    font-weight: 700 !important;
}

/* CỠ CHỮ CÂU HỎI (ĐỀ BÀI) TO RÕ HƠN (20.5px), CỠ CHỮ PHƯƠNG ÁN GIỮ NGUYÊN (18px) */
.q-stem-text,
.q-stem-text p,
.q-stem-text li {
    font-size: 20.5px !important;
    line-height: 1.72 !important;
    color: #0f172a !important;
    font-weight: 500 !important;
}

.opt-box-true, .opt-box-true p, .opt-box-true span,
.opt-box-false, .opt-box-false p, .opt-box-false span,
.solution-box, .solution-box p, .solution-box li,
div[role="radiogroup"] label,
div[role="radiogroup"] label p,
div[role="radiogroup"] label span,
div[role="radiogroup"] div[data-testid="stMarkdownContainer"] p {
    font-size: 18px !important;
    line-height: 1.65 !important;
}

.katex {
    font-size: 1.02em !important;
}
mjx-container {
    font-size: 102% !important;
}

.app-header-banner {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    padding: 18px 24px;
    border-radius: 16px;
    margin-bottom: 18px;
    box-shadow: 0 6px 20px rgba(30, 58, 138, 0.18);
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.15);
}
.app-header-banner h1 {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    margin: 0 !important;
    padding: 0 !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px;
}
.app-header-banner p {
    color: #fde047 !important;
    -webkit-text-fill-color: #fde047 !important;
    margin: 6px 0 0 0 !important;
    font-size: 17.5px !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px;
}

.question-card {
    background: #ffffff !important;
    color: #0f172a !important;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    border: 1px solid #cbd5e1;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
}

.section-banner-p1, .section-banner-p1 * {
    background: linear-gradient(90deg, #1d4ed8 0%, #3b82f6 100%) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 18px;
    margin: 20px 0 14px 0;
}
.section-banner-p2, .section-banner-p2 * {
    background: linear-gradient(90deg, #6d28d9 0%, #8b5cf6 100%) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 18px;
    margin: 20px 0 14px 0;
}
.section-banner-p3, .section-banner-p3 * {
    background: linear-gradient(90deg, #d97706 0%, #f59e0b 100%) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 18px;
    margin: 20px 0 14px 0;
}
.section-banner-p4, .section-banner-p4 * {
    background: linear-gradient(90deg, #047857 0%, #10b981 100%) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 18px;
    margin: 20px 0 14px 0;
}

.q-badge {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    padding: 5px 14px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 14px;
    display: inline-block;
}

.tag-pill {
    background-color: #f1f5f9 !important;
    color: #1e293b !important;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 8px;
    border: 1px solid #cbd5e1;
}

div[role="radiogroup"] > label {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    margin-bottom: 10px !important;
    width: 100%;
    transition: all 0.18s ease !important;
    cursor: pointer;
}
div[role="radiogroup"] > label:hover {
    background-color: #eff6ff !important;
    border-color: #3b82f6 !important;
}

.solution-box {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%) !important;
    border-left: 5px solid #16a34a !important;
    padding: 14px 18px;
    border-radius: 10px;
    margin-top: 12px;
    color: #0f172a !important;
}

.opt-box-true {
    background-color: #ecfdf5 !important;
    border: 1.5px solid #10b981 !important;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    color: #065f46 !important;
    font-weight: 600;
}
.opt-box-false {
    background-color: #f8fafc !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    color: #0f172a !important;
}
.opt-box-true p, .opt-box-false p {
    margin: 0 !important;
}

/* ÉP 4 Ô VUÔNG TRẢ LỜI NGẮN LUÔN NẰM NGANG TRÊN IPHONE & LAPTOP */
div[data-testid="stHorizontalBlock"]:has(input[aria-label^="sa_box_"]),
div[data-testid="stHorizontalBlock"]:has([class*="st-key-sa_b"]),
div[data-testid="stElementContainer"]:has(.sa-row-marker) + div[data-testid="stHorizontalBlock"],
div.element-container:has(.sa-row-marker) + div[data-testid="stHorizontalBlock"],
div[data-testid="stElementContainer"]:has(.sa-row-marker) + div[data-testid="stLayoutWrapper"] div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 8px !important;
    width: auto !important;
    max-width: 100% !important;
}

div[data-testid="stHorizontalBlock"]:has(input[aria-label^="sa_box_"]) > div,
div[data-testid="stHorizontalBlock"]:has([class*="st-key-sa_b"]) > div,
div[data-testid="stHorizontalBlock"]:has(input[aria-label^="sa_box_"]) div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has([class*="st-key-sa_b"]) div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(input[aria-label^="sa_box_"]) div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has([class*="st-key-sa_b"]) div[data-testid="column"],
div[data-testid="stElementContainer"]:has(.sa-row-marker) + div[data-testid="stHorizontalBlock"] > div,
div.element-container:has(.sa-row-marker) + div[data-testid="stHorizontalBlock"] > div {
    width: 60px !important;
    min-width: 60px !important;
    max-width: 60px !important;
    flex: 0 0 60px !important;
    padding: 0 !important;
}

@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"]:has(input[aria-label^="sa_box_"]),
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-sa_b"]),
    div[data-testid="stElementContainer"]:has(.sa-row-marker) + div[data-testid="stHorizontalBlock"],
    div.element-container:has(.sa-row-marker) + div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(input[aria-label^="sa_box_"]) > div,
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-sa_b"]) > div,
    div[data-testid="stHorizontalBlock"]:has(input[aria-label^="sa_box_"]) div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-sa_b"]) div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(input[aria-label^="sa_box_"]) div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-sa_b"]) div[data-testid="column"],
    div[data-testid="stElementContainer"]:has(.sa-row-marker) + div[data-testid="stHorizontalBlock"] > div,
    div.element-container:has(.sa-row-marker) + div[data-testid="stHorizontalBlock"] > div {
        width: 60px !important;
        min-width: 60px !important;
        max-width: 60px !important;
        flex: 0 0 60px !important;
    }
}

div[data-testid="stTextInput"]:has(input[aria-label^="sa_box_"]) div[data-baseweb="input"],
[class*="st-key-sa_b"] div[data-baseweb="input"] {
    width: 58px !important;
    min-width: 58px !important;
    max-width: 58px !important;
    height: 56px !important;
    background-color: #ffffff !important;
    border: 2.5px solid #2563eb !important;
    border-radius: 10px !important;
    padding: 0 !important;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.14) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stTextInput"]:has(input[aria-label^="sa_box_"]) div[data-baseweb="input"]:focus-within,
[class*="st-key-sa_b"] div[data-baseweb="input"]:focus-within {
    border-color: #d97706 !important;
    background-color: #fffbeb !important;
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.28) !important;
}

div[data-testid="stTextInput"]:has(input[aria-label^="sa_box_"]) div[data-baseweb="base-input"],
[class*="st-key-sa_b"] div[data-baseweb="base-input"] {
    background-color: transparent !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stTextInput"] input[aria-label^="sa_box_"],
[class*="st-key-sa_b"] input {
    text-align: center !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #1e3a8a !important;
    -webkit-text-fill-color: #1e3a8a !important;
    background-color: transparent !important;
    border: none !important;
    width: 100% !important;
    height: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    caret-color: #d97706 !important;
}

div[data-testid="stTextInput"]:has(input[aria-label^="sa_box_"]) div[data-testid="InputInstructions"],
[class*="st-key-sa_b"] div[data-testid="InputInstructions"] {
    display: none !important;
}

.essay-notice-box {
    background: linear-gradient(90deg, #ecfdf5 0%, #d1fae5 100%) !important;
    border: 1.5px dashed #059669 !important;
    color: #065f46 !important;
    padding: 12px 18px;
    border-radius: 10px;
    font-size: 17.5px;
    font-weight: 600;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# ================= HIỂN THỊ TIÊU ĐỀ CỐ ĐỊNH Ở ĐẦU MỌI TRANG =================
def render_app_header():
    st.markdown("""
    <div class="app-header-banner">
        <h1>🎓 Hệ Thống Kiểm Tra Đánh Giá Môn Toán</h1>
        <p>👨‍🏫 Thầy Lê Minh Cường - THPT Lương Thế Vinh</p>
    </div>
    """, unsafe_allow_html=True)

render_app_header()

# ================= KẾT NỐI SUPABASE =================
@st.cache_resource
def init_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_db()
except Exception:
    st.error("⚠️ Chưa cấu hình SUPABASE_URL và SUPABASE_KEY trong mục Secrets!")
    st.stop()

PART_LABELS = {
    1: "Phần I (Trắc nghiệm ABCD)",
    2: "Phần II (Đúng / Sai)",
    3: "Phần III (Trả lời ngắn)",
    4: "Phần IV (Tự luận)"
}

LEVEL_COLORS = {
    "N": ("#dbeafe", "#1e40af"),
    "H": ("#dcfce7", "#166534"),
    "V": ("#fef3c7", "#92400e"),
    "C": ("#fce7f3", "#9d174d")
}

SPECIAL_EXAM_TOPICS = [
    "Ôn thi giữa học kì 1",
    "Kiểm tra giữa học kì 1",
    "Ôn thi cuối học kì 1",
    "Kiểm tra cuối học kì 1",
    "Ôn thi giữa học kì 2",
    "Kiểm tra giữa học kì 2",
    "Ôn thi cuối học kì 2",
    "Kiểm tra cuối học kì 2",
    "Ôn thi Tốt nghiệp THPT / Tuyển sinh 10",
    "Đề thi thử / Khảo sát chất lượng",
    "Chuyên đề ôn tập tổng hợp"
]

def get_topic_options_for_grade(grade_str):
    """Trả về danh sách các Chương SGK của khối kết hợp với các mục Ôn thi giữa/cuối kì"""
    chap_dict = KNTT_DATA.get(str(grade_str), {}).get("chapters", {})
    return list(chap_dict.values()) + SPECIAL_EXAM_TOPICS + ["✍️ Tự nhập tên Chuyên đề / Kỳ thi khác..."]

def make_teacher_auth_token():
    secret_str = st.secrets.get("ADMIN_PASSWORD", "123456") + "_LMC_TEACHER"
    return hashlib.sha256(secret_str.encode("utf-8")).hexdigest()[:16]

# ================= HÀM XÓA CACHE WIDGET SỬA CÂU HỎI KHI XÓA/CẬP NHẬT =================
def clear_edit_widget_state(prefixes=("st_tag_", "st_stem_", "st_sa_", "st_sol_", "st_opt_", "st_true_", "st_tf_", "db_tag_", "db_stem_", "db_sa_", "db_sol_", "db_opt_", "db_true_", "db_tf_")):
    """Xóa triệt để state của các ô nhập liệu trong st.session_state để khi xóa câu không bị lưu nhầm sang câu kế tiếp"""
    keys_to_remove = [k for k in list(st.session_state.keys()) if any(k.startswith(p) for p in prefixes)]
    for k in keys_to_remove:
        del st.session_state[k]

# ================= HÀM TẢI TOÀN BỘ METADATA NGÂN HÀNG ĐỂ THỐNG KÊ =================
def fetch_all_bank_metadata():
    """Tải danh sách siêu dữ liệu (không kèm ảnh SVG nặng) của toàn bộ câu hỏi trong Ngân hàng để thống kê tức thì"""
    all_rows = []
    batch_size = 1000
    offset = 0
    while True:
        res = (
            supabase.table("question_bank")
            .select("id, tag_id, grade, chapter_code, chapter_name, lesson_code, lesson_name, level_code, level_name, part")
            .order("id")
            .range(offset, offset + batch_size - 1)
            .execute()
            .data
        )
        if not res:
            break
        all_rows.extend(res)
        if len(res) < batch_size:
            break
        offset += batch_size
    return all_rows

def fetch_all_bank_full_questions(grade_filter=None):
    """Tải toàn bộ dữ liệu câu hỏi kèm raw_tex từ Ngân hàng để xuất file LaTeX (.tex)"""
    all_rows = []
    batch_size = 500
    offset = 0
    while True:
        q_builder = supabase.table("question_bank").select("*").order("grade", desc=True).order("chapter_code").order("lesson_code").order("id")
        if grade_filter and grade_filter != "Tất cả các Khối":
            q_builder = q_builder.eq("grade", str(grade_filter))
        res = q_builder.range(offset, offset + batch_size - 1).execute().data
        if not res:
            break
        all_rows.extend(res)
        if len(res) < batch_size:
            break
        offset += batch_size
    return all_rows

# ================= HÀM KẾT XUẤT MÃ NGUỒN LATEX (.TEX) CHO NGÂN HÀNG & ĐỀ THI =================
def question_to_latex_block(q):
    """Chuyển 1 đối tượng câu hỏi sang khối lệnh LaTeX chuẩn gói ex_test (\begin{ex}...\end{ex} hoặc \begin{bt}...\end{bt})"""
    tag_id = q.get("tag_id", "12-C1-B1-N")
    raw_tex = (q.get("raw_tex") or "").strip()

    if raw_tex and not q.get("_manually_edited"):
        if re.match(r'^\\begin\{(ex|bt)\}\s*%\[[^\]]*\]', raw_tex):
            raw_tex = re.sub(r'^(\\begin\{(?:ex|bt)\})\s*%\[[^\]]*\]', rf'\1%[{tag_id}]', raw_tex, count=1)
        else:
            raw_tex = re.sub(r'^(\\begin\{(?:ex|bt)\})', rf'\1%[{tag_id}]', raw_tex, count=1)
        return raw_tex

    part = q.get("part", 1)
    env_name = "bt" if part == 4 else "ex"

    def _md_to_tex(md_str):
        if not md_str:
            return ""
        s = re.sub(r'<div[^>]*>.*?</div>', '% [Hình vẽ TikZ]', md_str, flags=re.DOTALL)
        s = re.sub(r'<br\s*/?>', r' \\\\ ', s)
        s = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', s)
        s = re.sub(r'<u>(.*?)</u>', r'\\underline{\1}', s)
        return s.strip()

    stem_tex = _md_to_tex(q.get("stem", ""))
    sol_tex = _md_to_tex(q.get("solution", ""))

    lines = [f"\\begin{{{env_name}}}%[{tag_id}]", stem_tex]
    if part == 1:
        lines.append("\\choice")
        for opt in q.get("options", []):
            prefix = "\\True " if opt.get("is_true") else ""
            lines.append(f"{{{prefix}{_md_to_tex(opt.get('text', ''))}}}")
    elif part == 2:
        lines.append("\\choiceTF")
        for st_i in q.get("statements", []):
            prefix = "\\True " if st_i.get("is_true") else ""
            lines.append(f"{{{prefix}{_md_to_tex(st_i.get('text', ''))}}}")
    elif part == 3:
        sa_val = str(q.get("short_ans", "")).replace(",", "{,}")
        lines.append(f"\\shortans{{{sa_val}}}")

    if sol_tex:
        lines.append(f"\\loigiai{{\n{sol_tex}\n}}")
    lines.append(f"\\end{{{env_name}}}")
    return "\n".join(lines)

def build_latex_export_content(questions_list, title="ĐỀ KIỂM TRA MÔN TOÁN", full_document=True):
    """Tạo nội dung file .tex (chỉ danh sách câu hỏi hoặc file LaTeX hoàn chỉnh biên dịch được ngay)"""
    blocks = []
    p1 = [q for q in questions_list if q.get("part") == 1]
    p2 = [q for q in questions_list if q.get("part") == 2]
    p3 = [q for q in questions_list if q.get("part") == 3]
    p4 = [q for q in questions_list if q.get("part") == 4]

    if p1:
        blocks.append("% ==============================================================")
        blocks.append("% PHẦN I. CÂU TRẮC NGHIỆM NHIỀU PHƯƠNG ÁN LỰA CHỌN")
        blocks.append("% ==============================================================")
        for q in p1:
            blocks.append(question_to_latex_block(q))
            blocks.append("")
    if p2:
        blocks.append("% ==============================================================")
        blocks.append("% PHẦN II. CÂU TRẮC NGHIỆM ĐÚNG SAI")
        blocks.append("% ==============================================================")
        for q in p2:
            blocks.append(question_to_latex_block(q))
            blocks.append("")
    if p3:
        blocks.append("% ==============================================================")
        blocks.append("% PHẦN III. CÂU TRẮC NGHIỆM TRẢ LỜI NGẮN")
        blocks.append("% ==============================================================")
        for q in p3:
            blocks.append(question_to_latex_block(q))
            blocks.append("")
    if p4:
        blocks.append("% ==============================================================")
        blocks.append("% PHẦN IV. TỰ LUẬN")
        blocks.append("% ==============================================================")
        for q in p4:
            blocks.append(question_to_latex_block(q))
            blocks.append("")

    body_tex = "\n".join(blocks).strip()
    if not full_document:
        return body_tex

    header_tex = (
        r"\documentclass[12pt,a4paper]{article}" + "\n"
        r"\usepackage[utf8]{vietnam}" + "\n"
        r"\usepackage{amsmath,amssymb,amsfonts,mathpazo}" + "\n"
        r"\usepackage[top=1.5cm,bottom=1.5cm,left=2cm,right=1.5cm]{geometry}" + "\n"
        r"\usepackage{tikz,tkz-tab}" + "\n"
        r"\usetikzlibrary{shapes.geometric,arrows,calc,intersections,angles,patterns,snakes}" + "\n"
        r"\usepackage[loigiai]{ex_test}" + "\n"
        r"\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}" + "\n"
        r"\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}" + "\n"
        r"\begin{document}" + "\n"
        r"\begin{center}" + "\n"
        r"\textbf{TRƯỜNG THPT LƯƠNG THẾ VINH — THẦY LÊ MINH CƯỜNG}\\" + "\n"
        rf"\textbf{{\Large {title}}}" + "\n"
        r"\end{center}" + "\n"
        r"\Opensolutionfile{ans}[ans/ans]" + "\n\n"
    )
    footer_tex = (
        "\n\n" + r"\Closesolutionfile{ans}" + "\n"
        r"\end{document}" + "\n"
    )
    return header_tex + body_tex + footer_tex

# ================= HÀM ĐỌC FILE EXCEL / CSV AN TOÀN =================
def read_student_file_safe(uploaded_file):
    """Đọc file danh sách học sinh (.xlsx hoặc .csv) tự động nhận diện bảng mã tiếng Việt"""
    raw_bytes = uploaded_file.getvalue()
    fname = uploaded_file.name.lower()

    if fname.endswith(".xlsx") or fname.endswith(".xls") or raw_bytes[:2] == b"PK":
        return pd.read_excel(io.BytesIO(raw_bytes))

    encodings_to_try = ["utf-8-sig", "utf-8", "utf-16", "cp1258", "windows-1252", "latin1"]
    for enc in encodings_to_try:
        try:
            text_content = raw_bytes.decode(enc)
            first_line = text_content.splitlines()[0] if text_content.splitlines() else ""
            sep = ";" if first_line.count(";") > first_line.count(",") else (", " if "\t" not in first_line else "\t")
            if sep == ", ":
                sep = ","
            df = pd.read_csv(io.StringIO(text_content), sep=sep)
            if len(df.columns) >= 4:
                return df
        except Exception:
            continue

    return pd.read_csv(io.BytesIO(raw_bytes), encoding="utf-8", errors="replace")

# ================= HÀM LÀM SẠCH LỆNH LATEX, XUỐNG DÒNG & KIỂM TRA TRẠNG THÁI =================
def clean_leftover_spaces(txt):
    """Làm sạch các lệnh \allowdisplaybreaks, listEX/lisEX, xuống dòng \\, \displaystyle\int và khoảng trắng LaTeX"""
    if not txt:
        return ""
    txt = re.sub(r'\\allowdisplaybreaks(\s*\[\d*\])?', '', txt)
    txt = re.sub(r'\\everymath\s*\{\s*\\displaystyle\s*\}', '', txt)
    txt = re.sub(
        r'\\begin\{(enumerate|itemize|listEX|lisEX|enumEX|tasks|inparaenum|compactenum|compactitem|description)\}\s*(\[[^\]]*\]|\([^)]*\))?',
        '\n',
        txt,
        flags=re.IGNORECASE
    )
    txt = re.sub(
        r'\\end\{(enumerate|itemize|listEX|lisEX|enumEX|tasks|inparaenum|compactenum|compactitem|description)\}',
        '\n',
        txt,
        flags=re.IGNORECASE
    )
    txt = re.sub(r'\\(?:item|task)\b(\s*\[[^\]]*\])?\s*', '<br>• ', txt)
    txt = re.sub(r'(?<!\$)\\(boldmath|unboldmath|noindent|indent|centering|leavevmode|vfill|hfill|smallskip|medskip|bigskip)\b', '', txt)
    txt = re.sub(r'\\lq\s*\\lq(?:\\\s+|\s*)', '"', txt)
    txt = re.sub(r'\s*\\rq\s*\\rq\\\s+', '" ', txt)
    txt = re.sub(r'\s*\\rq\s*\\rq', '"', txt)
    txt = re.sub(r'\\lq(?![a-zA-Z])(?:\\\s+|\s*)', "'", txt)
    txt = re.sub(r'\s*\\rq(?![a-zA-Z])\\\s+', "' ", txt)
    txt = re.sub(r'\s*\\rq(?![a-zA-Z])', "'", txt)

    saved_math = {}
    def _keep_math(m):
        k = f"@@M_{len(saved_math)}@@"
        saved_math[k] = ensure_displaystyle_int(m.group(0))
        return k

    txt = re.sub(r'\$\$.*?\$\$|\$(?!\$).*?\$', _keep_math, txt, flags=re.DOTALL)
    txt = re.sub(r'\\\\\*?(?:\s*\[[^\]]*\])?', '<br>\n', txt)
    txt = re.sub(r'\\(newline|par)\b', '<br>\n', txt)
    txt = re.sub(r'(?<!\\)\\(\s+|,|;|!|:|quad\b|qquad\b|enspace\b|thinspace\b)', ' ', txt)

    for k, v in saved_math.items():
        txt = txt.replace(k, v)

    return txt.strip()

def sanitize_question_obj(q):
    """Đồng bộ làm sạch nội dung đề bài, phương án và lời giải của câu hỏi (tự động biên dịch lại nếu câu cũ bị sót lệnh)"""
    if not q:
        return q
    if "_uid" not in q:
        q["_uid"] = str(uuid.uuid4())[:8]

    raw_tex = q.get("raw_tex", "")
    full_curr = q.get("stem", "") + " " + q.get("solution", "")
    needs_reparse = (
        r"\immini" in full_curr
        or "listEX" in full_curr
        or "lisEX" in full_curr
        or (raw_tex and q.get("_parser_ver") != PARSER_VERSION and not q.get("_manually_edited") and "tikzpicture" not in raw_tex and "tabvar" not in raw_tex)
    )
    if needs_reparse and raw_tex:
        try:
            reparsed_list = parse_exam_tex(raw_tex)
            if reparsed_list:
                rp = reparsed_list[0]
                q["stem"] = rp.get("stem", q["stem"])
                q["solution"] = rp.get("solution", q.get("solution", ""))
                if "options" in rp and not q.get("_manually_edited"):
                    q["options"] = rp["options"]
                if "statements" in rp and not q.get("_manually_edited"):
                    q["statements"] = rp["statements"]
                q["_parser_ver"] = PARSER_VERSION
        except Exception:
            pass

    q["stem"] = clean_leftover_spaces(q.get("stem", ""))
    q["solution"] = clean_leftover_spaces(q.get("solution", ""))
    if q.get("part") == 1:
        for o in q.get("options", []):
            o["text"] = clean_leftover_spaces(o.get("text", ""))
    elif q.get("part") == 2:
        for s in q.get("statements", []):
            s["text"] = clean_leftover_spaces(s.get("text", ""))
    return q

def check_question_health(q):
    """Kiểm tra xem câu hỏi và lời giải sau khi biên dịch có lỗi TikZ hay sót lệnh ex_test không"""
    sanitize_question_obj(q)
    issues = []
    full_rendered = q.get("stem", "") + " " + q.get("solution", "")
    if q.get("part") == 1:
        full_rendered += " " + " ".join(o.get("text", "") for o in q.get("options", []))
    elif q.get("part") == 2:
        full_rendered += " " + " ".join(s.get("text", "") for s in q.get("statements", []))

    if "Lỗi TikZ:" in full_rendered or "Lỗi hệ thống TikZ:" in full_rendered or "Lỗi biên dịch" in full_rendered:
        issues.append("❌ Lỗi hình TikZ")
    if not q.get("solution", "").strip():
        issues.append("⚠️ Trống lời giải")
    if re.search(r'\\(choice|choiceTF|shortans|loigiai|logiai|itemch|immini|lq|rq|allowdisplaybreaks)\b', full_rendered):
        issues.append("⚠️ Sót lệnh LaTeX")
    elif re.search(r'\\(begin|end)\{(?!(aligned|array|cases|matrix|pmatrix|bmatrix|vmatrix)\b)', full_rendered):
        issues.append("⚠️ Sót môi trường LaTeX")

    if not issues:
        return "✅ Hiển thị tốt"
    return " | ".join(issues)

def render_question_card(q, index_label):
    """Hiển thị đầy đủ 1 câu hỏi (Đề bài cỡ chữ to 20.5px + Phương án 18px + Lời giải)"""
    sanitize_question_obj(q)
    status_str = check_question_health(q)
    st_bg = "#dcfce7" if "✅" in status_str else "#fef2f2"
    st_fg = "#166534" if "✅" in status_str else "#991b1b"
    
    lvl_code = q.get("level_code", "N")
    lvl_bg, lvl_fg = LEVEL_COLORS.get(lvl_code, ("#f1f5f9", "#334155"))
    part_num = q.get("part", 1)

    st.markdown(
        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; background:#ffffff; padding:10px 16px; border-radius:12px; border:1px solid #cbd5e1; margin-bottom:10px; box-shadow:0 2px 4px rgba(0,0,0,0.03);">'
        f'<div style="display:flex; align-items:center; flex-wrap:wrap; gap:6px;">'
        f'<span class="q-badge">{index_label}</span>'
        f'<span class="tag-pill">🏷️ {q.get("tag_id", "Chưa gắn mã")}</span>'
        f'<span class="tag-pill">{PART_LABELS.get(part_num, f"Phần {part_num}")}</span>'
        f'<span style="background:{lvl_bg}; color:{lvl_fg}; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700;">{q.get("level_name", "Nhận biết")}</span>'
        f'<span style="font-size:13px; color:#475569; font-weight:500; margin-left:4px;">📚 {q.get("lesson_name", "")}</span>'
        f'</div>'
        f'<div style="background:{st_bg}; color:{st_fg}; padding:4px 12px; border-radius:999px; font-size:12px; font-weight:700;">{status_str}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    stem_disp = clean_leftover_spaces(q.get("stem", ""))
    st.markdown(f'<div class="q-stem-text">\n\n{stem_disp}\n\n</div>', unsafe_allow_html=True)

    if part_num == 1:
        labels = ["A", "B", "C", "D"]
        cols = st.columns(2)
        for idx, opt in enumerate(q.get("options", [])):
            is_t = opt.get("is_true")
            icon = "✅" if is_t else "⚪"
            lbl = labels[idx] if idx < 4 else str(idx + 1)
            box_cls = "opt-box-true" if is_t else "opt-box-false"
            opt_txt = clean_leftover_spaces(opt.get("text", ""))
            cols[idx % 2].markdown(
                f'<div class="{box_cls}">\n\n{icon} **{lbl}.** {opt_txt}\n\n</div>',
                unsafe_allow_html=True
            )
    elif part_num == 2:
        st_labels = ["a)", "b)", "c)", "d)"]
        for idx, st_i in enumerate(q.get("statements", [])):
            badge = "🟢 **[Đúng]**" if st_i.get("is_true") else "🔴 **[Sai]**"
            lbl = st_labels[idx] if idx < 4 else f"{idx+1})"
            st_txt = clean_leftover_spaces(st_i.get("text", ""))
            st.markdown(f"- **{lbl}** {st_txt} $\\longrightarrow$ {badge}", unsafe_allow_html=True)
    elif part_num == 3:
        st.markdown(f"🔑 **Đáp số trả lời ngắn:** `{q.get('short_ans', '')}`")
    elif part_num == 4:
        st.markdown("✍️ **Dạng câu hỏi:** *Bài tập Tự luận (Học sinh làm vào tập hoặc giấy đôi)*")

    sol_text = clean_leftover_spaces(q.get("solution", "").strip())
    if sol_text:
        st.markdown(
            f'<div class="solution-box">\n\n📖 **Lời giải chi tiết:**\n\n{sol_text}\n\n</div>',
            unsafe_allow_html=True
        )
    else:
        st.caption("*(Câu hỏi này chưa có nội dung lời giải)*")

def render_question_edit_controls(q_item, q_uid):
    """Hiển thị bộ điều khiển sửa Mã ID, Đề bài, CÁC PHƯƠNG ÁN / MỆNH ĐỀ, Đáp số và Lời giải"""
    u_tag = st.text_input("Nhập Mã ID chuẩn (VD: 10-C1-B1-N)", value=q_item.get("tag_id", ""), key=f"st_tag_{q_uid}")
    u_stem = st.text_area("Nội dung đề bài (Markdown / LaTeX)", value=q_item.get("stem", ""), height=100, key=f"st_stem_{q_uid}")

    part_num = q_item.get("part", 1)
    new_options = None
    new_statements = None
    u_sa = None

    if part_num == 1:
        st.markdown("**📝 Chỉnh sửa nội dung 4 phương án A, B, C, D & Chọn đáp án đúng:**")
        opts = q_item.get("options", [])
        while len(opts) < 4:
            opts.append({"id": len(opts), "text": "", "is_true": (len(opts) == 0)})
        labels = ["A", "B", "C", "D"]
        cur_true_idx = next((i for i, o in enumerate(opts[:4]) if o.get("is_true")), 0)
        oc1, oc2 = st.columns(2)
        edited_opt_texts = []
        for i in range(4):
            target_col = oc1 if i % 2 == 0 else oc2
            val_txt = target_col.text_input(
                f"Phương án {labels[i]}",
                value=opts[i].get("text", ""),
                key=f"st_opt_{i}_{q_uid}"
            )
            edited_opt_texts.append(val_txt)
        chosen_true_lbl = st.radio(
            "Đáp án đúng của câu này:",
            options=labels,
            index=cur_true_idx,
            horizontal=True,
            key=f"st_true_{q_uid}"
        )
        new_options = []
        for i in range(4):
            new_options.append({
                "id": opts[i].get("id", i),
                "text": clean_leftover_spaces(edited_opt_texts[i]),
                "is_true": (labels[i] == chosen_true_lbl)
            })

    elif part_num == 2:
        st.markdown("**📝 Chỉnh sửa nội dung 4 mệnh đề a), b), c), d) & Chọn Đúng/Sai:**")
        stmts = q_item.get("statements", [])
        while len(stmts) < 4:
            stmts.append({"id": len(stmts), "text": "", "is_true": True})
        st_labels = ["a)", "b)", "c)", "d)"]
        new_statements = []
        for i in range(4):
            sc_txt, sc_tf = st.columns([4.5, 1.5])
            s_val = sc_txt.text_input(
                f"Nội dung ý {st_labels[i]}",
                value=stmts[i].get("text", ""),
                key=f"st_opt_{i}_{q_uid}"
            )
            tf_val = sc_tf.radio(
                f"Đáp án ý {st_labels[i]}",
                options=["Đúng", "Sai"],
                index=0 if stmts[i].get("is_true") else 1,
                horizontal=True,
                key=f"st_tf_{i}_{q_uid}"
            )
            new_statements.append({
                "id": stmts[i].get("id", i),
                "text": clean_leftover_spaces(s_val),
                "is_true": (tf_val == "Đúng")
            })

    elif part_num == 3:
        u_sa = st.text_input("Đáp số trả lời ngắn (VD: -2,5 hoặc 23)", value=str(q_item.get("short_ans", "")), key=f"st_sa_{q_uid}")

    u_sol = st.text_area("Lời giải chi tiết", value=q_item.get("solution", ""), height=100, key=f"st_sol_{q_uid}")
    return u_tag, u_stem, new_options, new_statements, u_sa, u_sol

def apply_quick_edit_to_question(q, new_tag_str, new_stem_md, new_sol_md, new_short_ans=None, new_options=None, new_statements=None):
    """Cập nhật Mã ID, Đề bài, Các phương án chọn / mệnh đề Đúng-Sai, Đáp số và Lời giải cho câu hỏi"""
    meta = decode_kntt_tag(new_tag_str)
    if meta:
        q.update(meta)
    else:
        q["tag_id"] = new_tag_str.strip()
    q["stem"] = clean_leftover_spaces(new_stem_md.strip())
    q["solution"] = clean_leftover_spaces(new_sol_md.strip())
    if q.get("part") == 1 and new_options is not None:
        q["options"] = new_options
    elif q.get("part") == 2 and new_statements is not None:
        q["statements"] = new_statements
    elif q.get("part") == 3 and new_short_ans is not None:
        q["short_ans"] = new_short_ans.strip().replace(".", ",")

    q["_manually_edited"] = True
    q["raw_tex"] = question_to_latex_block(q)
    full_str = (
        q["stem"]
        + str(q.get("options", ""))
        + str(q.get("statements", ""))
        + str(q.get("short_ans", ""))
    )
    q["question_hash"] = hashlib.md5(full_str.encode("utf-8")).hexdigest()
    return q

# ================= HÀM HỖ TRỢ CHẤM ĐIỂM, THỜI GIAN LÀM BÀI, ĐẢO ĐỀ & XUẤT EXCEL CÓ ẢNH CAMERA =================
def extract_grade_from_class(class_name):
    m = re.match(r'^(\d+)', str(class_name).strip())
    return m.group(1) if m else "12"

def format_duration_vn(started_iso, submitted_iso):
    """Tính thời gian làm bài thực tế (phút, giây) từ lúc bắt đầu đến lúc nộp"""
    if not started_iso:
        return "Chưa xác định", "--", "--"
    try:
        st_dt = datetime.datetime.fromisoformat(str(started_iso).replace("Z", "+00:00"))
        vn_tz = datetime.timezone(datetime.timedelta(hours=7))
        st_local = st_dt.astimezone(vn_tz).strftime("%H:%M:%S %d/%m/%Y")
        if not submitted_iso:
            return "Đang làm bài", st_local, "--"
        sub_dt = datetime.datetime.fromisoformat(str(submitted_iso).replace("Z", "+00:00"))
        sub_local = sub_dt.astimezone(vn_tz).strftime("%H:%M:%S %d/%m/%Y")
        diff_sec = max(0, int((sub_dt - st_dt).total_seconds()))
        mins = diff_sec // 60
        secs = diff_sec % 60
        return f"{mins} phút {secs:02d} giây", st_local, sub_local
    except Exception:
        return "Không rõ", str(started_iso), str(submitted_iso or "")

def get_shuffled_exam(questions, seed):
    rng = random.Random(seed)
    p1 = [sanitize_question_obj(q.copy()) for q in questions if q.get("part") == 1]
    p2 = [sanitize_question_obj(q.copy()) for q in questions if q.get("part") == 2]
    p3 = [sanitize_question_obj(q.copy()) for q in questions if q.get("part") == 3]
    p4 = [sanitize_question_obj(q.copy()) for q in questions if q.get("part") == 4]

    rng.shuffle(p1)
    rng.shuffle(p2)
    rng.shuffle(p3)
    rng.shuffle(p4)

    for q in p1:
        opts = [o.copy() for o in q.get("options", [])]
        rng.shuffle(opts)
        q["shuffled_options"] = opts

    return p1, p2, p3, p4

def grade_exam(questions, answers, seed, scoring_cfg=None):
    if not scoring_cfg:
        scoring_cfg = {"p1": 0.25, "p2": 1.0, "p3": 0.5, "p4": 1.0}
    pt_p1 = float(scoring_cfg.get("p1", 0.25))
    pt_p2_max = float(scoring_cfg.get("p2", 1.0))
    pt_p3 = float(scoring_cfg.get("p3", 0.5))

    p1, p2, p3, _ = get_shuffled_exam(questions, seed)
    score_p1, score_p2, score_p3 = 0.0, 0.0, 0.0

    for q in p1:
        qid = q["id"]
        user_choice_id = answers.get(qid)
        for opt in q.get("options", []):
            if opt["is_true"] and str(opt["id"]) == str(user_choice_id):
                score_p1 += pt_p1

    tf_ratios = {0: 0.0, 1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}
    for q in p2:
        qid = q["id"]
        correct_count = 0
        for st_item in q.get("statements", []):
            sid = f"{qid}_s{st_item['id']}"
            user_tf = answers.get(sid)
            expected = "Đúng" if st_item["is_true"] else "Sai"
            if user_tf == expected:
                correct_count += 1
        score_p2 += pt_p2_max * tf_ratios.get(correct_count, 0.0)

    for q in p3:
        qid = q["id"]
        user_ans = str(answers.get(qid, "")).strip().replace(".", ",")
        correct_ans = str(q.get("short_ans", "")).strip().replace(".", ",")
        if user_ans != "" and user_ans == correct_ans:
            score_p3 += pt_p3

    score_p1 = round(score_p1, 2)
    score_p2 = round(score_p2, 2)
    score_p3 = round(score_p3, 2)
    total = round(score_p1 + score_p2 + score_p3, 2)
    return total, score_p1, score_p2, score_p3

def build_exam_report_xlsx(selected_exam, subs, item_stats):
    """Tạo file Excel (.xlsx) hoàn chỉnh lưu toàn bộ bảng điểm, thời gian làm bài, chi tiết câu sai và nhúng trực tiếp ảnh chụp Camera"""
    wb = openpyxl.Workbook()
    ws_scores = wb.active
    ws_scores.title = "Bang_diem_va_Anh_Camera"

    questions = selected_exam.get("questions", [])
    scoring_cfg = selected_exam.get("scoring_config") or {"p1": 0.25, "p2": 1.0, "p3": 0.5, "p4": 1.0}
    max_snaps = max([len(s.get("snapshots") or []) for s in subs] + [1])
    max_snaps = min(max_snaps, 12)

    headers = [
        "STT", "Tài khoản", "Họ và tên", "Lớp", "Trạng thái",
        "Điểm tổng", "Điểm Phần I", "Điểm Phần II", "Điểm Phần III",
        "Bắt đầu lúc", "Nộp bài lúc", "Thời gian làm bài",
        "Số lần rời màn hình", "Số ảnh Camera"
    ] + [f"Ảnh Camera #{i+1}" for i in range(max_snaps)]

    ws_scores.append(headers)
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws_scores.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws_scores.row_dimensions[1].height = 28

    col_widths = [6, 15, 24, 10, 13, 12, 12, 12, 12, 20, 20, 18, 16, 14] + [18] * max_snaps
    for idx_w, w in enumerate(col_widths, start=1):
        ws_scores.column_dimensions[get_column_letter(idx_w)].width = w

    for row_num, s in enumerate(subs, start=2):
        stu_info = s.get("students") or {}
        ans = s.get("answers") or {}
        seed = s.get("seed", 12345)
        _, s1, s2, s3 = grade_exam(questions, ans, seed, scoring_cfg)
        dur_str, st_time_str, sub_time_str = format_duration_vn(s.get("started_at"), s.get("submitted_at"))
        snaps = s.get("snapshots") or []

        row_vals = [
            row_num - 1,
            s.get("username", ""),
            stu_info.get("full_name", ""),
            stu_info.get("class_name", ""),
            "Đã nộp" if s.get("status") == "submitted" else "Đang làm",
            s.get("score", 0.0),
            s1, s2, s3,
            st_time_str,
            sub_time_str,
            dur_str,
            s.get("tab_switches", 0),
            len(snaps)
        ] + [s_item.get("time", "") for s_item in snaps[:max_snaps]] + [""] * max(0, max_snaps - len(snaps))

        ws_scores.append(row_vals)
        ws_scores.row_dimensions[row_num].height = 88 if snaps else 24

        for c_i in range(1, len(headers) + 1):
            c_cell = ws_scores.cell(row=row_num, column=c_i)
            c_cell.border = thin_border
            c_cell.alignment = Alignment(horizontal="center" if c_i != 3 else "left", vertical="center", wrap_text=True)

        for snap_idx, snap_obj in enumerate(snaps[:max_snaps]):
            img_b64 = snap_obj.get("img", "")
            if "," in img_b64:
                img_b64 = img_b64.split(",", 1)[1]
            if img_b64:
                try:
                    raw_img = base64.b64decode(img_b64)
                    pil_img = PILImage.open(io.BytesIO(raw_img))
                    pil_img.thumbnail((120, 90))
                    img_byte_arr = io.BytesIO()
                    pil_img.save(img_byte_arr, format="PNG")
                    img_byte_arr.seek(0)
                    xl_img = XLImage(img_byte_arr)
                    col_letter = get_column_letter(15 + snap_idx)
                    ws_scores.add_image(xl_img, f"{col_letter}{row_num}")
                except Exception:
                    pass

    ws_stats = wb.create_sheet(title="Thong_ke_cau_sai")
    if item_stats:
        stat_headers = ["Câu gốc", "Phần", "Mã ID", "Bài học", "Mức độ", "Số HS sai / Tổng", "Tỷ lệ sai (%)", "Chi tiết phân bố đáp án"]
        ws_stats.append(stat_headers)
        for c_i in range(1, len(stat_headers) + 1):
            cell = ws_stats.cell(row=1, column=c_i)
            cell.fill = header_fill
            cell.font = header_font
        for st_row in item_stats:
            ws_stats.append([st_row.get(k, "") for k in stat_headers])
        for col in ws_stats.columns:
            ws_stats.column_dimensions[col[0].column_letter].width = 22
        ws_stats.column_dimensions["H"].width = 55

    ws_detail = wb.create_sheet(title="Chi_tiet_bai_lam_HS")
    q_headers = ["Tài khoản", "Họ và tên", "Lớp", "Điểm số", "Thời gian làm bài"] + [
        f"Câu {i+1} ({q.get('tag_id','')})" for i, q in enumerate(questions)
    ]
    ws_detail.append(q_headers)
    for c_i in range(1, len(q_headers) + 1):
        cell = ws_detail.cell(row=1, column=c_i)
        cell.fill = header_fill
        cell.font = header_font

    for s in subs:
        stu_info = s.get("students") or {}
        ans = s.get("answers") or {}
        dur_str, _, _ = format_duration_vn(s.get("started_at"), s.get("submitted_at"))
        d_row = [
            s.get("username", ""),
            stu_info.get("full_name", ""),
            stu_info.get("class_name", ""),
            s.get("score", 0.0),
            dur_str
        ]
        for q in questions:
            qid = q["id"]
            part = q.get("part", 1)
            if part == 1:
                u_c = ans.get(qid)
                orig_labels = ["A", "B", "C", "D"]
                chosen_lbl = next((orig_labels[idx] for idx, o in enumerate(q.get("options", [])) if str(o["id"]) == str(u_c) and idx < 4), "Trống")
                d_row.append(chosen_lbl)
            elif part == 2:
                tf_ans = []
                for idx_s, st_i in enumerate(q.get("statements", [])):
                    sid = f"{qid}_s{st_i['id']}"
                    tf_ans.append(f"{['a','b','c','d'][idx_s]}:{ans.get(sid, '-')}")
                d_row.append(" | ".join(tf_ans))
            elif part == 3:
                d_row.append(str(ans.get(qid, "")))
            else:
                d_row.append("Làm trên giấy")
        ws_detail.append(d_row)

    out_buf = io.BytesIO()
    wb.save(out_buf)
    return out_buf.getvalue()

def analyze_exam_items(questions, submissions):
    """Phân tích tỷ lệ làm sai từng câu và xu hướng chọn phương án nhiễu của cả lớp"""
    submitted_subs = [s for s in submissions if s.get("status") == "submitted"]
    total_sub = len(submitted_subs)
    if total_sub == 0:
        return []

    analysis_list = []
    for idx, q in enumerate(questions):
        qid = q["id"]
        part = q.get("part", 1)
        tag_id = q.get("tag_id", "")
        lvl_name = q.get("level_name", "")
        lesson_name = q.get("lesson_name", "")

        if part == 1:
            correct_opt_id = str(next((o["id"] for o in q["options"] if o["is_true"]), "0"))
            wrong_cnt = 0
            opt_counts = {str(o["id"]): 0 for o in q["options"]}
            unanswered = 0
            for s in submitted_subs:
                ans = s.get("answers") or {}
                u_choice = ans.get(qid)
                if u_choice is None or str(u_choice) == "":
                    unanswered += 1
                    wrong_cnt += 1
                else:
                    u_str = str(u_choice)
                    if u_str in opt_counts:
                        opt_counts[u_str] += 1
                    if u_str != correct_opt_id:
                        wrong_cnt += 1

            wrong_rate = round((wrong_cnt / total_sub) * 100, 1)
            dist_details = []
            orig_labels = ["A (Gốc)", "B (Gốc)", "C (Gốc)", "D (Gốc)"]
            for o_idx, o in enumerate(q["options"]):
                cnt = opt_counts.get(str(o["id"]), 0)
                pct = round((cnt / total_sub) * 100, 1)
                mark = "✅ Đúng" if o["is_true"] else "❌ Nhiễu"
                dist_details.append(f"{orig_labels[o_idx]} [{mark}]: {cnt}/{total_sub} HS ({pct}%)")
            if unanswered > 0:
                dist_details.append(f"⚪ Bỏ trống: {unanswered} HS")

            analysis_list.append({
                "Câu gốc": f"Câu {idx+1}",
                "Phần": "Phần I (ABCD)",
                "Mã ID": tag_id,
                "Bài học": lesson_name,
                "Mức độ": lvl_name,
                "Số HS sai / Tổng": f"{wrong_cnt}/{total_sub}",
                "Tỷ lệ sai (%)": wrong_rate,
                "Chi tiết phân bố đáp án": " | ".join(dist_details),
                "q_obj": q
            })

        elif part == 2:
            st_labels = ["a)", "b)", "c)", "d)"]
            stmt_wrong_counts = []
            any_wrong_stu = 0
            for s in submitted_subs:
                ans = s.get("answers") or {}
                stu_has_wrong = False
                for st_i in q["statements"]:
                    sid = f"{qid}_s{st_i['id']}"
                    expected = "Đúng" if st_i["is_true"] else "Sai"
                    if ans.get(sid) != expected:
                        stu_has_wrong = True
                if stu_has_wrong:
                    any_wrong_stu += 1

            for s_idx, st_i in enumerate(q["statements"]):
                sid = f"{qid}_s{st_i['id']}"
                expected = "Đúng" if st_i["is_true"] else "Sai"
                w_c = sum(1 for s in submitted_subs if (s.get("answers") or {}).get(sid) != expected)
                w_pct = round((w_c / total_sub) * 100, 1)
                stmt_wrong_counts.append(f"Ý {st_labels[s_idx]} sai: {w_c}/{total_sub} ({w_pct}%)")

            wrong_rate = round((any_wrong_stu / total_sub) * 100, 1)
            analysis_list.append({
                "Câu gốc": f"Câu {idx+1}",
                "Phần": "Phần II (Đ/S)",
                "Mã ID": tag_id,
                "Bài học": lesson_name,
                "Mức độ": lvl_name,
                "Số HS sai / Tổng": f"{any_wrong_stu}/{total_sub} (chưa đạt tối đa)",
                "Tỷ lệ sai (%)": wrong_rate,
                "Chi tiết phân bố đáp án": " | ".join(stmt_wrong_counts),
                "q_obj": q
            })

        elif part == 3:
            correct_ans = str(q["short_ans"]).strip().replace(".", ",")
            wrong_cnt = 0
            wrong_values = {}
            for s in submitted_subs:
                ans = s.get("answers") or {}
                u_ans = str(ans.get(qid, "")).strip().replace(".", ",")
                if u_ans == "" or u_ans != correct_ans:
                    wrong_cnt += 1
                    lbl_val = u_ans if u_ans != "" else "Bỏ trống"
                    wrong_values[lbl_val] = wrong_values.get(lbl_val, 0) + 1

            wrong_rate = round((wrong_cnt / total_sub) * 100, 1)
            top_wrongs = sorted(wrong_values.items(), key=lambda x: x[1], reverse=True)[:4]
            wrong_str = ", ".join([f"'{k}' ({v} HS)" for k, v in top_wrongs]) if top_wrongs else "Không có"

            analysis_list.append({
                "Câu gốc": f"Câu {idx+1}",
                "Phần": "Phần III (TLN)",
                "Mã ID": tag_id,
                "Bài học": lesson_name,
                "Mức độ": lvl_name,
                "Số HS sai / Tổng": f"{wrong_cnt}/{total_sub}",
                "Tỷ lệ sai (%)": wrong_rate,
                "Chi tiết phân bố đáp án": f"Đáp số đúng: [{correct_ans}] | Các lỗi sai phổ biến: {wrong_str}",
                "q_obj": q
            })

        elif part == 4:
            analysis_list.append({
                "Câu gốc": f"Câu {idx+1}",
                "Phần": "Phần IV (Tự luận)",
                "Mã ID": tag_id,
                "Bài học": lesson_name,
                "Mức độ": lvl_name,
                "Số HS sai / Tổng": "Làm vào giấy",
                "Tỷ lệ sai (%)": 0.0,
                "Chi tiết phân bố đáp án": "Học sinh trình bày vào tập hoặc giấy đôi theo lời dặn của giáo viên",
                "q_obj": q
            })

    analysis_list.sort(key=lambda x: x["Tỷ lệ sai (%)"], reverse=True)
    return analysis_list

def find_replacement_question(current_q, all_exam_qs):
    """Tìm câu hỏi thay thế từ Ngân hàng có cùng Khối, Chương, Bài, Phần, Mức độ mà chưa có trong đề"""
    used_hashes = {
        q.get("question_hash") or hashlib.md5(q.get("stem", "").encode("utf-8")).hexdigest()
        for q in all_exam_qs
    }
    grade = str(current_q.get("grade", "12"))
    part = int(current_q.get("part", 1))
    chap = current_q.get("chapter_code", "C1")
    lesson = current_q.get("lesson_code", "B1")
    lvl = current_q.get("level_code", "N")

    pool = (
        supabase.table("question_bank")
        .select("*")
        .eq("grade", grade)
        .eq("part", part)
        .eq("lesson_code", lesson)
        .eq("level_code", lvl)
        .execute()
        .data
    )
    candidates = [item for item in pool if item["question_hash"] not in used_hashes]

    if not candidates:
        pool2 = (
            supabase.table("question_bank")
            .select("*")
            .eq("grade", grade)
            .eq("part", part)
            .eq("lesson_code", lesson)
            .execute()
            .data
        )
        candidates = [item for item in pool2 if item["question_hash"] not in used_hashes]

    if not candidates:
        pool3 = (
            supabase.table("question_bank")
            .select("*")
            .eq("grade", grade)
            .eq("part", part)
            .eq("chapter_code", chap)
            .eq("level_code", lvl)
            .execute()
            .data
        )
        candidates = [item for item in pool3 if item["question_hash"] not in used_hashes]

    if not candidates:
        return None

    chosen = sanitize_question_obj(random.choice(candidates)["question_data"].copy())
    chosen["id"] = current_q["id"]
    return chosen

def generate_feedback(total, s1, s2, s3, n1, n2, n3, scoring_cfg):
    max_total = n1 * scoring_cfg.get("p1", 0.25) + n2 * scoring_cfg.get("p2", 1.0) + n3 * scoring_cfg.get("p3", 0.5)
    ratio = (total / max_total) if max_total > 0 else 0

    comments = []
    if ratio >= 0.85:
        comments.append("🌟 **Đánh giá chung:** Nắm rất vững kiến thức và kỹ năng vận dụng giải toán.")
    elif ratio >= 0.65:
        comments.append("👍 **Đánh giá chung:** Nắm được kiến thức cơ bản nhưng cần cẩn thận hơn ở các câu vận dụng.")
    else:
        comments.append("⚠️ **Đánh giá chung:** Cần ôn tập lại các công thức nền tảng và rèn luyện thêm kỹ năng tính toán.")

    if n1 > 0 and s1 < (n1 * scoring_cfg.get("p1", 0.25) * 0.7):
        comments.append("- **Phần I (Trắc nghiệm ABCD):** Còn sai nhiều ở các câu nhận biết/thông hiểu công thức cơ bản.")
    if n2 > 0 and s2 < (n2 * scoring_cfg.get("p2", 1.0) * 0.6):
        comments.append("- **Phần II (Đúng/Sai):** Chưa đạt điểm tối đa ở các mệnh đề tổng hợp, cần đọc kỹ từng ý a, b, c, d.")
    if n3 > 0 and s3 < (n3 * scoring_cfg.get("p3", 0.5) * 0.5):
        comments.append("- **Phần III (Trả lời ngắn):** Cần rèn luyện thêm kỹ năng giải toán thực tế và làm tròn số chính xác.")
    return "\n".join(comments)

# ================= COMPONENT GIÁM SÁT & TỰ ĐỘNG NHẢY Ô TRẢ LỜI NGẮN (IPHONE & LAPTOP) =================
def render_proctor_bar(end_timestamp_ms, supabase_url, supabase_key, submission_id):
    html_code = f"""
    <div style="display:flex; align-items:center; justify-content:space-between; background:linear-gradient(90deg, #0f172a, #1e293b); color:white; padding:12px 20px; border-radius:12px; font-family:sans-serif; box-shadow:0 4px 12px rgba(0,0,0,0.12);">
        <div>
            <span style="font-size:15px;">⏱️ Thời gian còn lại: </span>
            <b id="timer" style="font-size:22px; color:#38bdf8;">--:--</b>
            <span id="warn_badge" style="margin-left:15px; background:#ef4444; padding:4px 10px; border-radius:6px; font-size:13px; display:none;">
                ⚠️ Rời màn hình: <span id="tab_count">0</span> lần
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:12px; color:#cbd5e1;" id="cam_status">🟢 Camera giám sát trực tuyến đang hoạt động</span>
            <video id="webcam" autoplay playsinline muted width="85" height="64" style="border-radius:8px; border:2px solid #22c55e; object-fit:cover;"></video>
            <canvas id="canvas" width="320" height="240" style="display:none;"></canvas>
        </div>
    </div>

    <script>
    const SUPABASE_URL = "{supabase_url}";
    const SUPABASE_KEY = "{supabase_key}";
    const SUB_ID = {submission_id};
    const END_TIME_MS = {int(end_timestamp_ms)};
    const INTERVAL_MS = 300000;
    const STORAGE_KEY = "last_snap_sub_" + SUB_ID;

    let tabSwitches = 0;
    let snapshots = [];

    async function fetchCurrentProctorData() {{
        try {{
            const res = await fetch(`${{SUPABASE_URL}}/rest/v1/submissions?id=eq.${{SUB_ID}}&select=tab_switches,snapshots`, {{
                headers: {{ "apikey": SUPABASE_KEY, "Authorization": `Bearer ${{SUPABASE_KEY}}` }}
            }});
            const data = await res.json();
            if (data && data.length > 0) {{
                tabSwitches = data[0].tab_switches || 0;
                snapshots = data[0].snapshots || [];
                if (tabSwitches > 0) {{
                    document.getElementById("warn_badge").style.display = "inline-block";
                    document.getElementById("tab_count").innerText = tabSwitches;
                }}
            }}
        }} catch (e) {{ console.error(e); }}
    }}
    fetchCurrentProctorData();

    async function updateSupabaseProctor(payload) {{
        try {{
            await fetch(`${{SUPABASE_URL}}/rest/v1/submissions?id=eq.${{SUB_ID}}`, {{
                method: "PATCH",
                headers: {{
                    "apikey": SUPABASE_KEY,
                    "Authorization": `Bearer ${{SUPABASE_KEY}}`,
                    "Content-Type": "application/json"
                }},
                body: JSON.stringify(payload)
            }});
        }} catch (e) {{ console.error(e); }}
    }}

    const timerEl = document.getElementById("timer");
    const countdown = setInterval(() => {{
        let timeLeft = Math.floor((END_TIME_MS - Date.now()) / 1000);
        if (timeLeft <= 0) {{
            clearInterval(countdown);
            timerEl.innerText = "00:00 (HẾT GIỜ)";
            timerEl.style.color = "#ef4444";
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {{
                if (btn.innerText.includes("NỘP BÀI HOÀN TẤT")) btn.click();
            }});
            return;
        }}
        let m = Math.floor(timeLeft / 60);
        let s = timeLeft % 60;
        timerEl.innerText = `${{String(m).padStart(2, '0')}}:${{String(s).padStart(2, '0')}}`;
        if (timeLeft < 300) timerEl.style.color = "#f97316";
    }}, 1000);

    document.addEventListener("visibilitychange", () => {{
        if (document.hidden) {{
            tabSwitches++;
            document.getElementById("warn_badge").style.display = "inline-block";
            document.getElementById("tab_count").innerText = tabSwitches;
            updateSupabaseProctor({{ tab_switches: tabSwitches }});
            alert("⚠️ CẢNH BÁO: Hệ thống vừa ghi nhận bạn rời khỏi màn hình làm bài! (Lần thứ " + tabSwitches + ")");
        }}
    }});

    const video = document.getElementById("webcam");
    const canvas = document.getElementById("canvas");
    const camStatus = document.getElementById("cam_status");

    navigator.mediaDevices.getUserMedia({{ video: true, audio: false }})
        .then(stream => {{
            video.srcObject = stream;
            setInterval(checkAndCapture, 5000);
        }})
        .catch(err => {{
            camStatus.innerText = "❌ Không tìm thấy Camera hoặc bị từ chối quyền!";
            camStatus.style.color = "#ef4444";
        }});

    function checkAndCapture() {{
        if (!video.srcObject || video.readyState < 2) return;
        const now = Date.now();
        const lastSnap = parseInt(localStorage.getItem(STORAGE_KEY) || "0", 10);

        if (lastSnap === 0 || (now - lastSnap) >= INTERVAL_MS) {{
            localStorage.setItem(STORAGE_KEY, now.toString());
            const ctx = canvas.getContext("2d");
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL("image/jpeg", 0.55);
            const nowStr = new Date().toLocaleTimeString("vi-VN");
            snapshots.push({{ time: nowStr, img: dataUrl }});
            updateSupabaseProctor({{ snapshots: snapshots }});
        }}
    }}

    // Nhận diện chính xác 4 ô trả lời ngắn qua aria-label, st-key và .sa-row-marker (vì Streamlit không gắn maxlength="1" vào DOM)
    function getShortAnsInputs(parentDoc) {{
        let list = Array.from(parentDoc.querySelectorAll('input[aria-label^="sa_box_"], [class*="st-key-sa_b"] input'));
        if (list.length === 0) {{
            const markers = parentDoc.querySelectorAll('.sa-row-marker');
            markers.forEach(m => {{
                let el = m.parentElement;
                while (el && el !== parentDoc.body) {{
                    if (el.nextElementSibling) {{
                        const found = el.nextElementSibling.querySelectorAll('input[type="text"]');
                        if (found.length === 4) {{
                            found.forEach(f => list.push(f));
                            break;
                        }}
                    }}
                    el = el.parentElement;
                }}
            }});
        }}
        return list;
    }}

    function isShortAnsInput(el) {{
        if (!el || el.tagName !== "INPUT") return false;
        const al = el.getAttribute("aria-label") || "";
        if (al.startsWith("sa_box_")) return true;
        if (el.getAttribute("data-sa-box") === "1") return true;
        if (el.closest && el.closest('[class*="st-key-sa_b"]')) return true;
        return false;
    }}

    // Tự động nhảy con trỏ NGAY LẬP TỨC (synchronous) qua ô tiếp theo khi điền 1 ký tự (hỗ trợ cả iPhone iOS Safari & Laptop)
    function setupParentShortAnsListeners() {{
        try {{
            const parentDoc = window.parent.document;
            if (!window.parent.__shortAnsDelegatedV2) {{
                window.parent.__shortAnsDelegatedV2 = true;

                parentDoc.addEventListener("input", (e) => {{
                    const t = e.target;
                    if (!isShortAnsInput(t)) return;
                    const allInps = getShortAnsInputs(parentDoc);
                    const curIdx = allInps.indexOf(t);
                    if (curIdx !== -1 && t.value && t.value.length >= 1) {{
                        if ((curIdx % 4) < 3) {{
                            const nextInp = allInps[curIdx + 1];
                            if (nextInp) {{
                                window.parent.__targetShortBoxIdx = curIdx + 1;
                                window.parent.__targetShortBoxTime = Date.now();
                                // Gọi focus() đồng bộ ngay trong sự kiện input để iPhone Safari giữ bàn phím và nhảy con trỏ tức thì
                                nextInp.focus();
                                try {{ nextInp.setSelectionRange(0, nextInp.value.length); }} catch (err) {{}}
                            }}
                        }} else {{
                            // Ô thứ 4: tự động blur để lưu đáp số ngay lập tức
                            window.parent.__targetShortBoxIdx = undefined;
                            t.blur();
                        }}
                    }}
                }}, false);

                parentDoc.addEventListener("keydown", (e) => {{
                    const t = e.target;
                    if (!isShortAnsInput(t)) return;
                    const allInps = getShortAnsInputs(parentDoc);
                    const curIdx = allInps.indexOf(t);
                    if (curIdx !== -1 && e.key === "Backspace" && (!t.value || t.value.length === 0) && (curIdx % 4) > 0) {{
                        const prevInp = allInps[curIdx - 1];
                        if (prevInp) {{
                            window.parent.__targetShortBoxIdx = curIdx - 1;
                            window.parent.__targetShortBoxTime = Date.now();
                            e.preventDefault();
                            prevInp.focus();
                            try {{ prevInp.setSelectionRange(0, prevInp.value.length); }} catch (err) {{}}
                        }}
                    }}
                }}, false);
            }}

            // Ép hàng chứa 4 ô vuông luôn hiển thị ngang trên iPhone & gắn thuộc tính chuẩn cho từng ô
            const allInps = getShortAnsInputs(parentDoc);
            allInps.forEach(inp => {{
                inp.setAttribute("data-sa-box", "1");
                inp.setAttribute("maxlength", "1");
                inp.setAttribute("autocapitalize", "off");
                inp.setAttribute("autocomplete", "off");
                inp.setAttribute("autocorrect", "off");
                inp.setAttribute("spellcheck", "false");

                const hBlock = inp.closest('[data-testid="stHorizontalBlock"]');
                if (hBlock) {{
                    hBlock.style.setProperty("display", "flex", "important");
                    hBlock.style.setProperty("flex-direction", "row", "important");
                    hBlock.style.setProperty("flex-wrap", "nowrap", "important");
                    hBlock.style.setProperty("align-items", "center", "important");
                    hBlock.style.setProperty("justify-content", "flex-start", "important");
                    hBlock.style.setProperty("gap", "8px", "important");
                    Array.from(hBlock.children).forEach(col => {{
                        col.style.setProperty("width", "60px", "important");
                        col.style.setProperty("min-width", "60px", "important");
                        col.style.setProperty("max-width", "60px", "important");
                        col.style.setProperty("flex", "0 0 60px", "important");
                        col.style.setProperty("padding", "0px", "important");
                    }});
                }}
            }});

            // Khôi phục focus nếu Streamlit rerun làm mới DOM sau khi rời ô trước
            if (window.parent.__targetShortBoxIdx !== undefined && (Date.now() - (window.parent.__targetShortBoxTime || 0)) < 1500) {{
                const targetInp = allInps[window.parent.__targetShortBoxIdx];
                if (targetInp && parentDoc.activeElement !== targetInp) {{
                    targetInp.focus();
                }}
            }}
        }} catch (err) {{}}
    }}
    setupParentShortAnsListeners();
    setInterval(setupParentShortAnsListeners, 150);
    </script>
    """
    components.html(html_code, height=110)

# ================= QUẢN LÝ ĐĂNG NHẬP & GIỮ PHIÊN ĐĂNG NHẬP KHI LÀM MỚI TRANG =================
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None

# Tự động khôi phục quyền Giáo viên nếu bấm F5 làm mới trình duyệt
if st.session_state.role is None:
    qp_auth = st.query_params.get("auth", "")
    if qp_auth == make_teacher_auth_token():
        st.session_state.role = "teacher"

if st.session_state.role is None:
    tab_hs, tab_gv = st.tabs(["👨‍🎓 Học sinh", "👨‍🏫 Giáo viên"])

    with tab_hs:
        with st.form("student_login"):
            u = st.text_input("Tài khoản học sinh")
            p = st.text_input("Mật khẩu", type="password")
            submit = st.form_submit_button("Đăng nhập vào phòng thi", type="primary")
            if submit:
                res = supabase.table("students").select("*").eq("username", u.strip()).eq("password", p.strip()).execute()
                if res.data:
                    st.session_state.role = "student"
                    st.session_state.user = res.data[0]
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")

    with tab_gv:
        with st.form("admin_login"):
            admin_pass = st.text_input("Mật khẩu Giáo viên", type="password")
            submit_gv = st.form_submit_button("Đăng nhập Quản trị")
            if submit_gv:
                expected_pass = st.secrets.get("ADMIN_PASSWORD", "123456")
                if admin_pass == expected_pass:
                    st.session_state.role = "teacher"
                    st.query_params["auth"] = make_teacher_auth_token()
                    st.rerun()
                else:
                    st.error("Sai mật khẩu Giáo viên!")
    st.stop()

with st.sidebar:
    if st.session_state.role == "student":
        stu_grade = extract_grade_from_class(st.session_state.user['class_name'])
        st.write(f"👤 Học sinh: **{st.session_state.user['full_name']}**")
        st.write(f"🏫 Lớp: **{st.session_state.user['class_name']}** (Khối {stu_grade})")
    else:
        st.write("👨‍🏫 **Chế độ Giáo viên Quản trị**")
        st.caption(f"⚙️ Bộ biên dịch: `{PARSER_VERSION}`")
        if st.button("🔄 Làm mới dữ liệu", use_container_width=True, type="primary"):
            st.toast("✅ Đã cập nhật dữ liệu mới nhất từ hệ thống!")
            st.rerun()
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.role = None
        st.session_state.user = None
        if "auth" in st.query_params:
            del st.query_params["auth"]
        st.rerun()

# =====================================================================
# PHÂN HỆ 1: GIAO DIỆN GIÁO VIÊN (4 TAB RÚT GỌN 2-4 CHỮ + NÚT LÀM MỚI NHANH)
# =====================================================================
if st.session_state.role == "teacher":
    top_c1, top_c2 = st.columns([5.2, 1.8])
    with top_c2:
        if st.button("🔄 Làm mới kết quả & dữ liệu", key="top_refresh_btn", type="primary", use_container_width=True):
            st.toast("✅ Đã tải lại kết quả thi và dữ liệu mới nhất!")
            st.rerun()

    t_bank, t_create, t_manage, t_stu = st.tabs([
        "🏦 Ngân hàng đề",
        "🎲 Tạo đề",
        "📂 Quản lý đề",
        "👥 Quản lý học sinh"
    ])

    # -----------------------------------------------------------------
    # TAB 1: NGÂN HÀNG ĐỀ
    # -----------------------------------------------------------------
    with t_bank:
        with st.expander("📊 0. Thống kê toàn bộ Ngân hàng câu hỏi & Lưu mã LaTeX (.tex) về máy", expanded=True):
            all_meta = fetch_all_bank_metadata()
            if not all_meta:
                st.info("📭 Ngân hàng câu hỏi hiện đang trống. Hãy nạp câu hỏi ở mục 1 bên dưới nhé!")
            else:
                total_q_all = len(all_meta)
                cnt_p1 = sum(1 for r in all_meta if r.get("part") == 1)
                cnt_p2 = sum(1 for r in all_meta if r.get("part") == 2)
                cnt_p3 = sum(1 for r in all_meta if r.get("part") == 3)
                cnt_p4 = sum(1 for r in all_meta if r.get("part") == 4)

                cnt_n = sum(1 for r in all_meta if r.get("level_code") == "N")
                cnt_h = sum(1 for r in all_meta if r.get("level_code") == "H")
                cnt_v = sum(1 for r in all_meta if r.get("level_code") == "V")
                cnt_c = sum(1 for r in all_meta if r.get("level_code") == "C")

                grades_present = sorted(list({str(r.get("grade", "12")) for r in all_meta}), key=lambda x: int(x) if x.isdigit() else 99, reverse=True)
                lessons_present = len({(str(r.get("grade")), r.get("lesson_code")) for r in all_meta})

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🏦 Tổng câu toàn Ngân hàng", f"{total_q_all} câu", f"{len(grades_present)} khối lớp | {lessons_present} bài học")
                m2.metric("📌 Phần I (ABCD) & Phần II (Đ/S)", f"P.I: {cnt_p1} | P.II: {cnt_p2}", "Trắc nghiệm khách quan")
                m3.metric("🎯 Phần III (TLN) & Phần IV (TL)", f"P.III: {cnt_p3} | P.IV: {cnt_p4}", "Trả lời ngắn & Tự luận")
                m4.metric("🧠 Phân bố Mức độ (N-H-V-C)", f"N:{cnt_n} | H:{cnt_h}", f"V: {cnt_v} | C: {cnt_c}")

                grade_summary_rows = []
                for g_val in ["12", "11", "10", "9", "8", "7", "6"]:
                    g_rows = [r for r in all_meta if str(r.get("grade")) == g_val]
                    if not g_rows:
                        continue
                    g_chaps = len({r.get("chapter_code") for r in g_rows})
                    g_lessons = len({r.get("lesson_code") for r in g_rows})
                    grade_summary_rows.append({
                        "Khối lớp": f"Khối {g_val}",
                        "Tổng số câu": len(g_rows),
                        "Số Chương có câu hỏi": g_chaps,
                        "Số Bài có câu hỏi": g_lessons,
                        "Phần I (ABCD)": sum(1 for r in g_rows if r.get("part") == 1),
                        "Phần II (Đ/S)": sum(1 for r in g_rows if r.get("part") == 2),
                        "Phần III (TLN)": sum(1 for r in g_rows if r.get("part") == 3),
                        "Phần IV (Tự luận)": sum(1 for r in g_rows if r.get("part") == 4),
                        "Nhận biết (N)": sum(1 for r in g_rows if r.get("level_code") == "N"),
                        "Thông hiểu (H)": sum(1 for r in g_rows if r.get("level_code") == "H"),
                        "Vận dụng (V)": sum(1 for r in g_rows if r.get("level_code") == "V"),
                        "Vận dụng cao (C)": sum(1 for r in g_rows if r.get("level_code") == "C")
                    })

                st.markdown("##### 📋 1. Bảng tổng hợp số lượng câu hỏi theo từng Khối lớp:")
                df_grade_sum = pd.DataFrame(grade_summary_rows)
                st.dataframe(df_grade_sum, use_container_width=True, hide_index=True)

                st.markdown("##### 📚 2. Thống kê chi tiết theo từng Chương & Bài học trong Ngân hàng:")
                stat_grade_filter = st.selectbox(
                    "Chọn Khối lớp muốn xem chi tiết từng Bài học:",
                    ["Tất cả các Khối"] + [f"Khối {g}" for g in grades_present],
                    key="stat_bank_grade_flt"
                )

                lesson_stat_rows = []
                target_grades = grades_present if stat_grade_filter == "Tất cả các Khối" else [stat_grade_filter.replace("Khối ", "").strip()]

                for g_val in target_grades:
                    g_rows = [r for r in all_meta if str(r.get("grade")) == g_val]
                    if not g_rows:
                        continue
                    known_lessons = KNTT_DATA.get(g_val, {}).get("lessons", {})
                    lesson_codes_in_g = sorted(
                        list({r.get("lesson_code", "B1") for r in g_rows}),
                        key=lambda b: int(re.sub(r'\D', '', b) or 0)
                    )
                    for b_code in lesson_codes_in_g:
                        b_rows = [r for r in g_rows if r.get("lesson_code") == b_code]
                        c_code = b_rows[0].get("chapter_code", "C1")
                        b_name = known_lessons.get(b_code, (c_code, b_rows[0].get("lesson_name", b_code)))[1]
                        p1_r = [r for r in b_rows if r.get("part") == 1]
                        p2_r = [r for r in b_rows if r.get("part") == 2]
                        p3_r = [r for r in b_rows if r.get("part") == 3]
                        p4_r = [r for r in b_rows if r.get("part") == 4]

                        def _fmt_lvl(rows_sub):
                            if not rows_sub:
                                return "0"
                            n_c = sum(1 for x in rows_sub if x.get("level_code") == "N")
                            h_c = sum(1 for x in rows_sub if x.get("level_code") == "H")
                            v_c = sum(1 for x in rows_sub if x.get("level_code") == "V")
                            c_c = sum(1 for x in rows_sub if x.get("level_code") == "C")
                            return f"{len(rows_sub)} (N:{n_c}|H:{h_c}|V:{v_c}|C:{c_c})"

                        lesson_stat_rows.append({
                            "Khối": f"Khối {g_val}",
                            "Chương": c_code,
                            "Mã Bài": b_code,
                            "Tên Bài học": b_name,
                            "Tổng số câu": len(b_rows),
                            "Phần I (ABCD)": _fmt_lvl(p1_r),
                            "Phần II (Đ/S)": _fmt_lvl(p2_r),
                            "Phần III (TLN)": _fmt_lvl(p3_r),
                            "Phần IV (Tự luận)": _fmt_lvl(p4_r),
                            "Tổng N / H / V / C": (
                                f"N:{sum(1 for x in b_rows if x.get('level_code')=='N')} | "
                                f"H:{sum(1 for x in b_rows if x.get('level_code')=='H')} | "
                                f"V:{sum(1 for x in b_rows if x.get('level_code')=='V')} | "
                                f"C:{sum(1 for x in b_rows if x.get('level_code')=='C')}"
                            )
                        })

                df_lesson_stat = pd.DataFrame(lesson_stat_rows)
                st.dataframe(df_lesson_stat, use_container_width=True, hide_index=True)

                stat_excel_buf = io.BytesIO()
                with pd.ExcelWriter(stat_excel_buf, engine="openpyxl") as writer:
                    df_grade_sum.to_excel(writer, sheet_name="Tong_hop_theo_Khoi", index=False)
                    df_lesson_stat.to_excel(writer, sheet_name="Chi_tiet_theo_Bai", index=False)

                exp_c1, exp_c2 = st.columns(2)
                exp_c1.download_button(
                    "📥 Xuất thống kê toàn Ngân hàng ra Excel (.xlsx)",
                    stat_excel_buf.getvalue(),
                    "thong_ke_ngan_hang_cau_hoi.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                if exp_c2.button("📦 Chuẩn bị file mã nguồn LaTeX (.tex) của toàn bộ Ngân hàng đang chọn", use_container_width=True):
                    target_g_Param = None if stat_grade_filter == "Tất cả các Khối" else stat_grade_filter.replace("Khối ", "").strip()
                    with st.spinner("Đang kết xuất mã nguồn LaTeX của Ngân hàng câu hỏi..."):
                        full_bank_rows = fetch_all_bank_full_questions(target_g_Param)
                        q_objs_for_tex = []
                        for r in full_bank_rows:
                            q_d = r.get("question_data") or {}
                            if r.get("raw_tex") and not q_d.get("raw_tex"):
                                q_d["raw_tex"] = r["raw_tex"]
                            q_d["tag_id"] = r.get("tag_id", q_d.get("tag_id", ""))
                            q_objs_for_tex.append(q_d)
                        st.session_state["exported_bank_tex_blocks"] = build_latex_export_content(q_objs_for_tex, title=f"NGÂN HÀNG CÂU HỎI ({stat_grade_filter})", full_document=False)
                        st.session_state["exported_bank_tex_full"] = build_latex_export_content(q_objs_for_tex, title=f"NGÂN HÀNG CÂU HỎI ({stat_grade_filter})", full_document=True)

                if st.session_state.get("exported_bank_tex_blocks"):
                    dl_tex1, dl_tex2 = st.columns(2)
                    dl_tex1.download_button(
                        "📄 Tải file .tex (Chỉ gồm các khối \\begin{ex}...\\end{ex})",
                        st.session_state["exported_bank_tex_blocks"].encode("utf-8"),
                        "ngan_hang_cau_hoi_ex_blocks.tex",
                        "text/plain",
                        use_container_width=True
                    )
                    dl_tex2.download_button(
                        "📘 Tải file .tex hoàn chỉnh (Có \\documentclass biên dịch ngay)",
                        st.session_state["exported_bank_tex_full"].encode("utf-8"),
                        "ngan_hang_cau_hoi_full_doc.tex",
                        "text/plain",
                        use_container_width=True
                    )

        st.divider()
        st.subheader("📥 1. Nạp câu hỏi từ file (.tex hoặc .txt) vào Ngân hàng")
        st.info("💡 Hỗ trợ nhận diện cả câu trắc nghiệm (`\\begin{ex}`) và bài tập Tự luận (`\\begin{bt}`). Bạn có thể chọn tự động loại bỏ câu thiếu mã ID, tự gán thủ công hoặc gán theo mặc định.")

        missing_id_mode = st.radio(
            "⚙️ Tùy chọn xử lý khi phát hiện câu hỏi KHÔNG có mã ID:",
            [
                "🗑️ Tự động loại bỏ các câu hỏi không có mã ID",
                "✍️ Giữ lại để tôi tự gán mã ID hoặc xóa thủ công ở bảng bên dưới",
                "📌 Tự động gán theo Khối / Chương / Bài / Mức độ mặc định"
            ],
            key="missing_id_policy"
        )

        fb_grade, fb_chap_code, fb_lesson_code, fb_lvl_code = "10", "C1", "B1", "N"
        if missing_id_mode.startswith("📌"):
            c_def1, c_def2, c_def3, c_def4 = st.columns([1, 2, 2, 1])
            fb_grade = c_def1.selectbox("Khối mặc định", ["12", "11", "10", "9", "8", "7", "6"], index=2, key="fb_g")
            fb_chaps = KNTT_DATA[fb_grade]["chapters"]
            fb_chap_code = c_def2.selectbox("Chương mặc định", list(fb_chaps.keys()), format_func=lambda k: fb_chaps[k], key="fb_c")
            fb_lessons = {bk: bv[1] for bk, bv in KNTT_DATA[fb_grade]["lessons"].items() if bv[0] == fb_chap_code}
            fb_lesson_code = c_def3.selectbox("Bài mặc định", list(fb_lessons.keys()), format_func=lambda k: fb_lessons[k], key="fb_b")
            fb_lvl_code = c_def4.selectbox("Mức độ mặc định", ["N", "H", "V", "C"], format_func=lambda k: f"{k} - {LEVEL_MAP[k]}", key="fb_lv")

        bank_tex_file = st.file_uploader("Chọn file .tex hoặc .txt chứa danh sách câu hỏi", type=["tex", "txt"], key="bank_up")

        if bank_tex_file:
            file_sig = f"{PARSER_VERSION}_{bank_tex_file.name}_{bank_tex_file.size}_{missing_id_mode}_{fb_grade}_{fb_chap_code}_{fb_lesson_code}_{fb_lvl_code}"
            if st.session_state.get("staged_file_sig") != file_sig:
                raw_bank_tex = bank_tex_file.read().decode("utf-8", errors="ignore")
                with st.spinner("Đang biên dịch LaTeX/TikZ và kiểm tra mã ID câu hỏi..."):
                    parsed_qs = parse_exam_tex(raw_bank_tex)
                    processed_qs = []
                    dropped_no_id = 0

                    for q in parsed_qs:
                        q["_uid"] = str(uuid.uuid4())[:8]
                        sanitize_question_obj(q)
                        if q.get("tag_id") == "Chưa gắn mã":
                            if missing_id_mode.startswith("🗑️"):
                                dropped_no_id += 1
                                continue
                            elif missing_id_mode.startswith("📌"):
                                default_tag = f"{fb_grade}-{fb_chap_code}-{fb_lesson_code}-{fb_lvl_code}"
                                meta = decode_kntt_tag(default_tag)
                                if meta:
                                    q.update(meta)
                        processed_qs.append(q)

                    clear_edit_widget_state()
                    st.session_state["staged_bank_qs"] = processed_qs
                    st.session_state["dropped_no_id_count"] = dropped_no_id
                    st.session_state["staged_file_sig"] = file_sig
                    st.session_state["staged_ver"] = st.session_state.get("staged_ver", 0) + 1

            staged_qs = st.session_state.get("staged_bank_qs", [])
            dropped_cnt = st.session_state.get("dropped_no_id_count", 0)
            staged_ver = st.session_state.get("staged_ver", 0)

            if dropped_cnt > 0:
                st.warning(f"🗑️ Đã tự động loại bỏ **{dropped_cnt} câu hỏi** không có mã ID theo tùy chọn của bạn.")

            if not staged_qs:
                st.warning("Không còn câu hỏi nào trong danh sách tạm (toàn bộ câu hỏi trong file đều thiếu mã ID và đã bị loại bỏ).")
            else:
                ok_count = sum(1 for q in staged_qs if "✅" in check_question_health(q))
                warn_count = len(staged_qs) - ok_count
                untagged_count = sum(1 for q in staged_qs if q.get("tag_id") == "Chưa gắn mã")

                st.success(
                    f"✅ Đang giữ trong bộ nhớ tạm **{len(staged_qs)} câu hỏi** — "
                    f"🟢 Hiển thị tốt: **{ok_count} câu** | 🟠 Cảnh báo hiển thị: **{warn_count} câu** | "
                    f"🏷️ Chưa gắn mã ID: **{untagged_count} câu**."
                )

                st.markdown("##### ⚡ Bảng sửa nhanh Mã ID & Tích chọn xóa câu hỏi:")
                edit_rows = []
                for idx, q in enumerate(staged_qs):
                    edit_rows.append({
                        "Xóa": False,
                        "STT": idx + 1,
                        "Mã gốc": q.get("id", f"q_{idx+1}"),
                        "Mã ID (Gõ để tự gán/sửa)": q.get("tag_id", ""),
                        "Trạng thái": check_question_health(q),
                        "Dạng thức": PART_LABELS.get(q.get("part", 1), ""),
                        "Khối": q.get("grade", "") if q.get("tag_id") != "Chưa gắn mã" else "-",
                        "Bài học": q.get("lesson_name", "") if q.get("tag_id") != "Chưa gắn mã" else "⚠️ Chưa xác định (Cần gán ID hoặc xóa)",
                        "Mức độ": q.get("level_name", "") if q.get("tag_id") != "Chưa gắn mã" else "-"
                    })
                edited_df = st.data_editor(
                    pd.DataFrame(edit_rows),
                    use_container_width=True,
                    hide_index=True,
                    disabled=["STT", "Mã gốc", "Trạng thái", "Dạng thức", "Khối", "Bài học", "Mức độ"],
                    key=f"staged_table_editor_{staged_ver}"
                )

                btn_col1, btn_col2 = st.columns(2)
                if btn_col1.button("🛠️ Áp dụng gán/sửa Mã ID & Xóa các dòng đã tích chọn", use_container_width=True):
                    new_staged = []
                    for idx, row in edited_df.iterrows():
                        if not row["Xóa"]:
                            q_obj = staged_qs[idx]
                            new_id_str = str(row["Mã ID (Gõ để tự gán/sửa)"]).strip()
                            if new_id_str != q_obj.get("tag_id"):
                                meta = decode_kntt_tag(new_id_str)
                                if meta:
                                    q_obj.update(meta)
                                else:
                                    q_obj["tag_id"] = new_id_str
                            new_staged.append(q_obj)
                    clear_edit_widget_state()
                    st.session_state["staged_bank_qs"] = new_staged
                    st.session_state["staged_ver"] = staged_ver + 1
                    st.toast("✅ Đã cập nhật danh sách câu hỏi tạm!")
                    st.rerun()

                if untagged_count > 0:
                    if btn_col2.button(f"🗑️ Xóa nhanh toàn bộ {untagged_count} câu chưa có mã ID", use_container_width=True):
                        clear_edit_widget_state()
                        st.session_state["staged_bank_qs"] = [q for q in staged_qs if q.get("tag_id") != "Chưa gắn mã"]
                        st.session_state["staged_ver"] = staged_ver + 1
                        st.toast(f"Đã loại bỏ {untagged_count} câu thiếu mã ID!")
                        st.rerun()

                with st.expander("👁️ Xem chi tiết, Sửa nội dung (Đề bài, Các phương án A-B-C-D / Đúng-Sai, Lời giải) hoặc Xóa nhanh từng câu hỏi", expanded=(warn_count > 0 or untagged_count > 0)):
                    flt_mode = st.radio(
                        "Chế độ lọc câu hỏi xem trước:",
                        [
                            "Xem tất cả câu hỏi",
                            "🏷️ Chỉ xem các câu CHƯA CÓ MÃ ID",
                            "⚠️ Chỉ xem các câu có cảnh báo (Lỗi TikZ / Trống lời giải)"
                        ],
                        horizontal=True,
                        key="pre_flt"
                    )
                    filtered_pre_qs = []
                    for i, q in enumerate(staged_qs):
                        if flt_mode.startswith("🏷️") and q.get("tag_id") != "Chưa gắn mã":
                            continue
                        if flt_mode.startswith("⚠️") and "✅" in check_question_health(q):
                            continue
                        filtered_pre_qs.append((i, q))

                    if not filtered_pre_qs:
                        st.info("🎉 Không có câu hỏi nào nằm trong bộ lọc này.")
                    else:
                        pg_c1, pg_c2 = st.columns([1.5, 2.5])
                        pre_page_opt = pg_c1.selectbox(
                            "Số câu hiển thị mỗi trang:",
                            [20, 50, 100, "Tất cả"],
                            index=1,
                            key="pre_page_size_sel"
                        )
                        page_size = len(filtered_pre_qs) if pre_page_opt == "Tất cả" else int(pre_page_opt)
                        total_pages = max(1, (len(filtered_pre_qs) + page_size - 1) // page_size)
                        cur_page = pg_c2.number_input(
                            f"Trang xem trước (1 - {total_pages}, tổng {len(filtered_pre_qs)} câu):",
                            min_value=1, max_value=total_pages, value=1, key="pre_page"
                        )
                        start_i = (cur_page - 1) * page_size
                        for orig_idx, q_item in filtered_pre_qs[start_i:start_i + page_size]:
                            q_uid = f"{q_item.get('_uid', q_item.get('id', orig_idx))}_{q_item.get('question_hash', '')[:8]}_v{staged_ver}"
                            orig_q_code = q_item.get("id", f"q_{orig_idx + 1}")
                            col_q, col_btn = st.columns([6, 1])
                            with col_q:
                                render_question_card(q_item, f"Câu {orig_idx + 1} ({orig_q_code})")
                            with col_btn:
                                if st.button("🗑️ Xóa ngay", key=f"del_stage_{q_uid}"):
                                    staged_qs.pop(orig_idx)
                                    clear_edit_widget_state()
                                    st.session_state["staged_bank_qs"] = staged_qs
                                    st.session_state["staged_ver"] = staged_ver + 1
                                    st.rerun()
                            with st.expander(f"✏️ Tự gán Mã ID / Sửa nội dung & phương án Câu {orig_idx + 1} [{orig_q_code} — {q_item.get('tag_id', 'Chưa gắn mã')}]"):
                                u_tag, u_stem, new_opts, new_stmts, u_sa, u_sol = render_question_edit_controls(q_item, q_uid)
                                if st.button("💾 Lưu chỉnh sửa câu này", key=f"btn_save_st_{q_uid}", type="primary"):
                                    staged_qs[orig_idx] = apply_quick_edit_to_question(
                                        q_item, u_tag, u_stem, u_sol, new_short_ans=u_sa, new_options=new_opts, new_statements=new_stmts
                                    )
                                    clear_edit_widget_state()
                                    st.session_state["staged_bank_qs"] = staged_qs
                                    st.session_state["staged_ver"] = staged_ver + 1
                                    st.success("Đã cập nhật câu hỏi!")
                                    st.rerun()
                            st.divider()

                if st.button("📥 Lưu các câu hỏi hợp lệ vào Ngân hàng", type="primary"):
                    valid_qs = [sanitize_question_obj(q) for q in staged_qs if q.get("tag_id") != "Chưa gắn mã"]
                    skipped_untagged = len(staged_qs) - len(valid_qs)
                    if not valid_qs:
                        st.error("⚠️ Không có câu hỏi nào có mã ID hợp lệ để lưu! Vui lòng gán mã ID trước khi lưu.")
                    else:
                        unique_records_map = {}
                        for q in valid_qs:
                            full_content_str = (
                                q["stem"]
                                + str(q.get("options", ""))
                                + str(q.get("statements", ""))
                                + str(q.get("short_ans", ""))
                            )
                            q_hash = hashlib.md5(full_content_str.encode("utf-8")).hexdigest()
                            q["question_hash"] = q_hash

                            unique_records_map[q_hash] = {
                                "tag_id": q["tag_id"],
                                "grade": str(q["grade"]),
                                "chapter_code": q["chapter_code"],
                                "chapter_name": q["chapter_name"],
                                "lesson_code": q["lesson_code"],
                                "lesson_name": q["lesson_name"],
                                "level_code": q["level_code"],
                                "level_name": q["level_name"],
                                "part": int(q["part"]),
                                "question_data": q,
                                "raw_tex": q.get("raw_tex", ""),
                                "question_hash": q_hash
                            }

                        db_records = list(unique_records_map.values())
                        try:
                            for i in range(0, len(db_records), 50):
                                batch = db_records[i:i + 50]
                                supabase.table("question_bank").upsert(batch, on_conflict="question_hash").execute()
                            msg = f"🎉 Đã nạp thành công {len(db_records)} câu hỏi có ID chuẩn vào Ngân hàng!"
                            if skipped_untagged > 0:
                                msg += f" (Đã tự động bỏ qua {skipped_untagged} câu chưa được gắn mã ID)."
                            st.success(msg)
                        except Exception as e:
                            st.error(f"⚠️ Chi tiết lỗi từ Supabase: {e}")

        st.divider()
        st.subheader("🔍 2. Duyệt, Kiểm tra hiển thị, Xuất LaTeX & Sửa/Xóa câu hỏi trong Ngân hàng")

        b_col1, b_col2, b_col3 = st.columns([1, 2, 2])
        b_sel_g = b_col1.selectbox("Lọc theo Khối:", ["12", "11", "10", "9", "8", "7", "6"], key="b_mgr_g")
        b_avail_chaps = KNTT_DATA[b_sel_g]["chapters"]
        b_sel_c = b_col2.selectbox("Lọc theo Chương:", list(b_avail_chaps.keys()), format_func=lambda k: b_avail_chaps[k], key="b_mgr_c")
        b_chap_lessons = {b_k: b_v[1] for b_k, b_v in KNTT_DATA[b_sel_g]["lessons"].items() if b_v[0] == b_sel_c}
        b_sel_lessons = b_col3.multiselect(
            "Lọc theo Bài học (Để trống = Cả chương):",
            options=list(b_chap_lessons.keys()),
            format_func=lambda k: b_chap_lessons[k],
            key="b_mgr_l"
        )

        bank_items = supabase.table("question_bank").select("*").eq("grade", b_sel_g).eq("chapter_code", b_sel_c).order("id").execute().data
        if b_sel_lessons:
            bank_items = [item for item in bank_items if item["lesson_code"] in b_sel_lessons]

        if not bank_items:
            st.info("Chưa có câu hỏi nào trong Ngân hàng thuộc Chương/Bài này.")
        else:
            ok_b = sum(1 for item in bank_items if "✅" in check_question_health(item["question_data"]))
            warn_b = len(bank_items) - ok_b
            st.write(
                f"📊 **Hiện có `{len(bank_items)}` câu hỏi trong mục đang chọn** "
                f"(🟢 `{ok_b}` câu hiển thị chuẩn | 🟠 `{warn_b}` câu có cảnh báo)"
            )

            q_list_filtered_for_tex = []
            for it in bank_items:
                qd_tmp = it.get("question_data") or {}
                if it.get("raw_tex") and not qd_tmp.get("raw_tex"):
                    qd_tmp["raw_tex"] = it["raw_tex"]
                qd_tmp["tag_id"] = it.get("tag_id", qd_tmp.get("tag_id", ""))
                q_list_filtered_for_tex.append(qd_tmp)

            tex_c1, tex_c2 = st.columns(2)
            tex_c1.download_button(
                f"📄 Tải mã LaTeX ({len(bank_items)} câu đang lọc - Khối \\begin{{ex}})",
                build_latex_export_content(q_list_filtered_for_tex, title=f"KHỐI {b_sel_g} - {b_avail_chaps[b_sel_c]}", full_document=False).encode("utf-8"),
                f"ngan_hang_K{b_sel_g}_{b_sel_c}_ex.tex",
                "text/plain",
                use_container_width=True
            )
            tex_c2.download_button(
                f"📘 Tải file .tex hoàn chỉnh ({len(bank_items)} câu đang lọc - Đủ \\documentclass)",
                build_latex_export_content(q_list_filtered_for_tex, title=f"KHỐI {b_sel_g} - {b_avail_chaps[b_sel_c]}", full_document=True).encode("utf-8"),
                f"ngan_hang_K{b_sel_g}_{b_sel_c}_full.tex",
                "text/plain",
                use_container_width=True
            )

            bank_flt1, bank_flt2, bank_flt3 = st.columns([2, 2, 1.5])
            b_status_filter = bank_flt1.selectbox(
                "Lọc theo trạng thái biên dịch:",
                ["Tất cả câu hỏi", "⚠️ Chỉ xem câu có cảnh báo", "✅ Chỉ xem câu hiển thị tốt"],
                key="bank_health_flt"
            )
            b_part_filter = bank_flt2.selectbox(
                "Lọc theo Phần:",
                ["Tất cả các phần", "Phần 1 (ABCD)", "Phần 2 (Đúng/Sai)", "Phần 3 (Trả lời ngắn)", "Phần 4 (Tự luận)"],
                key="bank_part_flt"
            )
            b_page_opt = bank_flt3.selectbox(
                "Số câu / trang:",
                [20, 50, 100, "Tất cả"],
                index=1,
                key="bank_page_size_sel"
            )

            inspect_list = []
            for item in bank_items:
                h_str = check_question_health(item["question_data"])
                if b_status_filter.startswith("⚠️") and "✅" in h_str:
                    continue
                if b_status_filter.startswith("✅") and "✅" not in h_str:
                    continue
                if b_part_filter.startswith("Phần 1") and item["part"] != 1:
                    continue
                if b_part_filter.startswith("Phần 2") and item["part"] != 2:
                    continue
                if b_part_filter.startswith("Phần 3") and item["part"] != 3:
                    continue
                if b_part_filter.startswith("Phần 4") and item["part"] != 4:
                    continue
                inspect_list.append(item)

            if not inspect_list:
                st.info("Không có câu hỏi nào khớp với bộ lọc.")
            else:
                db_ver = st.session_state.get("db_ver", 0)
                b_page_size = len(inspect_list) if b_page_opt == "Tất cả" else int(b_page_opt)
                b_total_pages = max(1, (len(inspect_list) + b_page_size - 1) // b_page_size)
                b_cur_page = st.number_input(
                    f"Trang danh sách câu hỏi (1 - {b_total_pages}, tổng {len(inspect_list)} câu):",
                    min_value=1, max_value=b_total_pages, value=1, key="bank_inspect_page"
                )
                b_start = (b_cur_page - 1) * b_page_size
                for item in inspect_list[b_start:b_start + b_page_size]:
                    qd = item["question_data"]
                    if item.get("raw_tex") and not qd.get("raw_tex"):
                        qd["raw_tex"] = item["raw_tex"]
                    db_uid = f"db_{item['id']}_{item.get('question_hash', '')[:8]}_v{db_ver}"
                    c_card, c_act = st.columns([6.2, 1])
                    with c_card:
                        render_question_card(qd, f"ID Kho #{item['id']}")
                    with c_act:
                        if st.button("🗑️ Xóa", key=f"del_qb_{db_uid}"):
                            supabase.table("question_bank").delete().eq("id", item["id"]).execute()
                            try:
                                supabase.rpc("sync_question_bank_seq").execute()
                            except Exception:
                                pass
                            clear_edit_widget_state()
                            st.session_state["db_ver"] = db_ver + 1
                            st.toast(f"Đã xóa câu #{item['id']} khỏi Ngân hàng!")
                            st.rerun()

                    with st.expander(f"✏️ Sửa Mã ID / Nội dung & phương án câu #{item['id']} [{item.get('tag_id', '')}]"):
                        db_tag, db_stem, db_opts, db_stmts, db_sa, db_sol = render_question_edit_controls(qd, db_uid)
                        if st.button("💾 Cập nhật vào Ngân hàng", key=f"btn_upd_qb_{db_uid}", type="primary"):
                            updated_q = apply_quick_edit_to_question(
                                qd, db_tag, db_stem, db_sol, new_short_ans=db_sa, new_options=db_opts, new_statements=db_stmts
                            )
                            supabase.table("question_bank").update({
                                "tag_id": updated_q["tag_id"],
                                "grade": str(updated_q["grade"]),
                                "chapter_code": updated_q["chapter_code"],
                                "chapter_name": updated_q["chapter_name"],
                                "lesson_code": updated_q["lesson_code"],
                                "lesson_name": updated_q["lesson_name"],
                                "level_code": updated_q["level_code"],
                                "level_name": updated_q["level_name"],
                                "question_data": updated_q,
                                "raw_tex": updated_q.get("raw_tex", ""),
                                "question_hash": updated_q["question_hash"]
                            }).eq("id", item["id"]).execute()
                            clear_edit_widget_state()
                            st.session_state["db_ver"] = db_ver + 1
                            st.success(f"Đã cập nhật câu #{item['id']} thành công!")
                            st.rerun()
                    st.divider()

        st.divider()
        with st.expander("🚨 3. Xóa sạch Ngân hàng câu hỏi & Đánh số lại ID Kho từ #1"):
            st.warning(
                "⚠️ **Cảnh báo quan trọng:** Hành động này sẽ xóa các câu hỏi trong bảng `question_bank` trên Supabase để giải phóng bộ nhớ và đặt lại bộ đếm ID Kho về lại từ `#1`. "
                "Các đề thi đã xuất bản sẽ không bị ảnh hưởng."
            )
            del_scope = st.radio(
                "Chọn phạm vi Ngân hàng muốn xóa:",
                [
                    "🔥 Xóa TOÀN BỘ Ngân hàng câu hỏi (Tất cả các Khối 6 - 12) & Reset ID Kho về #1",
                    f"🧹 Chỉ xóa câu hỏi thuộc Khối {b_sel_g} đang chọn ở trên"
                ],
                key="del_bank_scope"
            )
            confirm_chk = st.checkbox("Tôi đã hiểu và chắc chắn muốn xóa dữ liệu Ngân hàng câu hỏi đã chọn.", key="chk_wipe_bank")
            confirm_txt = st.text_input("Nhập chính xác cụm từ `XOA NGAN HANG` (viết hoa, không dấu) để mở khóa nút xóa:", key="txt_wipe_bank")

            can_wipe = confirm_chk and (confirm_txt.strip() == "XOA NGAN HANG")
            if st.button("🗑️ TIẾN HÀNH XÓA & ĐÁNH SỐ LẠI ID KHO", type="primary", disabled=not can_wipe):
                try:
                    if del_scope.startswith("🔥"):
                        try:
                            supabase.rpc("reset_question_bank_id").execute()
                        except Exception:
                            supabase.table("question_bank").delete().gt("id", 0).execute()
                        st.success("✅ Đã xóa sạch TOÀN BỘ Ngân hàng câu hỏi và đặt lại ID Kho bắt đầu từ #1!")
                    else:
                        supabase.table("question_bank").delete().eq("grade", b_sel_g).execute()
                        try:
                            supabase.rpc("sync_question_bank_seq").execute()
                        except Exception:
                            pass
                        st.success(f"✅ Đã xóa sạch toàn bộ câu hỏi thuộc Khối {b_sel_g} và đồng bộ lại bộ đếm ID!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi xóa ngân hàng: {e}")

    # -----------------------------------------------------------------
    # TAB 2: TẠO ĐỀ (GỘP TRỘN ĐỀ THEO MA TRẬN & TẠO ĐỀ NHANH TỪ FILE)
    # -----------------------------------------------------------------
    with t_create:
        sub_create_mat, sub_create_fast = st.tabs([
            "🎲 Trộn theo ma trận",
            "📄 Nạp đề từ file"
        ])

        with sub_create_mat:
            st.subheader("🎲 Thiết lập Ma trận & Rút câu hỏi ngẫu nhiên theo từng Bài học")
            st.info("💡 Chọn Chương và các Bài học đã dạy, sau đó nhập số lượng câu hỏi cần lấy riêng cho từng Bài học ở bên dưới.")

            f_col1, f_col2 = st.columns([1, 3])
            sel_g = f_col1.selectbox("1. Chọn Khối lớp", ["12", "11", "10", "9", "8", "7", "6"], key="mat_g")
            avail_chaps = KNTT_DATA[sel_g]["chapters"]
            chap_keys = list(avail_chaps.keys())

            sel_chaps = f_col2.multiselect(
                "2. Chọn 1 hoặc nhiều Chương cần kiểm tra:",
                options=chap_keys,
                default=[chap_keys[0]] if chap_keys else [],
                format_func=lambda k: avail_chaps[k],
                key="mat_multi_c"
            )

            if not sel_chaps:
                st.warning("👆 Vui lòng chọn ít nhất 1 Chương ở mục 2.")
            else:
                avail_lessons = {}
                for b_k, (c_k, b_name) in KNTT_DATA[sel_g]["lessons"].items():
                    if c_k in sel_chaps:
                        avail_lessons[b_k] = f"[{c_k}] {b_name}"

                sel_lessons = st.multiselect(
                    "3. Chọn các Bài học cần đưa vào Ma trận đề thi:",
                    options=list(avail_lessons.keys()),
                    default=list(avail_lessons.keys())[:2] if len(avail_lessons) >= 2 else list(avail_lessons.keys()),
                    format_func=lambda k: avail_lessons[k],
                    key=f"mat_multi_b_{sel_g}_{'_'.join(sel_chaps)}"
                )

                if not sel_lessons:
                    st.warning("👆 Vui lòng chọn ít nhất 1 Bài học ở mục 3 để hiển thị bảng ma trận từng bài.")
                else:
                    q_query = (
                        supabase.table("question_bank")
                        .select("*")
                        .eq("grade", sel_g)
                        .in_("chapter_code", sel_chaps)
                        .in_("lesson_code", sel_lessons)
                        .execute()
                        .data
                    )

                    if not q_query:
                        st.warning("Chưa có câu hỏi nào trong Ngân hàng thuộc các Bài học đang chọn. Hãy sang tab Ngân hàng đề để nạp câu hỏi trước nhé!")
                    else:
                        lesson_pools = {
                            b_code: {p: {"N": [], "H": [], "V": [], "C": []} for p in [1, 2, 3, 4]}
                            for b_code in sel_lessons
                        }
                        for item in q_query:
                            b_c = item.get("lesson_code")
                            p_v = item.get("part", 1)
                            l_v = item.get("level_code", "N")
                            if l_v not in ["N", "H", "V", "C"]:
                                l_v = "N"
                            if b_c in lesson_pools and p_v in lesson_pools[b_c]:
                                lesson_pools[b_c][p_v][l_v].append(item)

                        summary_rows = []
                        for b_code in sel_lessons:
                            b_pool = lesson_pools[b_code]
                            total_b = sum(len(b_pool[p][lv]) for p in [1, 2, 3, 4] for lv in ["N", "H", "V", "C"])
                            summary_rows.append({
                                "Mã Bài": b_code,
                                "Tên Bài học": avail_lessons[b_code],
                                "Tổng có trong kho": f"{total_b} câu",
                                "Phần I (ABCD)": f"N:{len(b_pool[1]['N'])} | H:{len(b_pool[1]['H'])} | V:{len(b_pool[1]['V'])} | C:{len(b_pool[1]['C'])}",
                                "Phần II (Đ/S)": f"N:{len(b_pool[2]['N'])} | H:{len(b_pool[2]['H'])} | V:{len(b_pool[2]['V'])} | C:{len(b_pool[2]['C'])}",
                                "Phần III (TLN)": f"N:{len(b_pool[3]['N'])} | H:{len(b_pool[3]['H'])} | V:{len(b_pool[3]['V'])} | C:{len(b_pool[3]['C'])}",
                                "Phần IV (Tự luận)": f"N:{len(b_pool[4]['N'])} | H:{len(b_pool[4]['H'])} | V:{len(b_pool[4]['V'])} | C:{len(b_pool[4]['C'])}"
                            })
                        st.markdown("##### 📊 Thống kê số lượng câu hỏi hiện có trong Ngân hàng theo từng Bài học đã chọn:")
                        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

                        st.markdown("#### 🎯 Nhập số lượng câu muốn bốc riêng cho TỪNG BÀI HỌC:")
                        picked_per_lesson = {}
                        total_by_part = {1: 0, 2: 0, 3: 0, 4: 0}

                        for b_code in sel_lessons:
                            b_pool = lesson_pools[b_code]
                            total_avail_in_b = sum(len(b_pool[p][lv]) for p in [1, 2, 3, 4] for lv in ["N", "H", "V", "C"])
                            with st.expander(f"📘 {avail_lessons[b_code]} (Trong kho hiện có: {total_avail_in_b} câu)", expanded=True):
                                if total_avail_in_b == 0:
                                    st.caption("*(Bài học này hiện chưa có câu hỏi nào trong Ngân hàng)*")
                                else:
                                    for p_idx in [1, 2, 3, 4]:
                                        max_n = len(b_pool[p_idx]["N"])
                                        max_h = len(b_pool[p_idx]["H"])
                                        max_v = len(b_pool[p_idx]["V"])
                                        max_c = len(b_pool[p_idx]["C"])
                                        if (max_n + max_h + max_v + max_c) == 0:
                                            for lv in ["N", "H", "V", "C"]:
                                                picked_per_lesson[(b_code, p_idx, lv)] = 0
                                            continue

                                        c_lbl, mc1, mc2, mc3, mc4 = st.columns([1.8, 1, 1, 1, 1])
                                        c_lbl.markdown(f"<div style='padding-top:28px;font-weight:600;'>{PART_LABELS[p_idx]}</div>", unsafe_allow_html=True)
                                        val_n = mc1.number_input(f"NB (Có {max_n})", 0, max_n, 0, key=f"pk_{sel_g}_{b_code}_{p_idx}_N")
                                        val_h = mc2.number_input(f"TH (Có {max_h})", 0, max_h, 0, key=f"pk_{sel_g}_{b_code}_{p_idx}_H")
                                        val_v = mc3.number_input(f"VD (Có {max_v})", 0, max_v, 0, key=f"pk_{sel_g}_{b_code}_{p_idx}_V")
                                        val_c = mc4.number_input(f"VDC (Có {max_c})", 0, max_c, 0, key=f"pk_{sel_g}_{b_code}_{p_idx}_C")

                                        picked_per_lesson[(b_code, p_idx, "N")] = val_n
                                        picked_per_lesson[(b_code, p_idx, "H")] = val_h
                                        picked_per_lesson[(b_code, p_idx, "V")] = val_v
                                        picked_per_lesson[(b_code, p_idx, "C")] = val_c
                                        total_by_part[p_idx] += (val_n + val_h + val_v + val_c)

                        grand_total_qs = sum(total_by_part.values())
                        st.info(
                            f"📌 **Tổng số câu đã chọn trên Ma trận:** **{grand_total_qs} câu** — "
                            f"Phần I: `{total_by_part[1]}` câu | Phần II: `{total_by_part[2]}` câu | "
                            f"Phần III: `{total_by_part[3]}` câu | Phần IV (Tự luận): `{total_by_part[4]}` câu."
                        )

                        if st.button("🎲 Bốc câu hỏi tạo Bản nháp Đề thi theo Ma trận trên", type="primary"):
                            selected_qs = []
                            for p_idx in [1, 2, 3, 4]:
                                for b_code in sel_lessons:
                                    for lvl in ["N", "H", "V", "C"]:
                                        need_cnt = picked_per_lesson.get((b_code, p_idx, lvl), 0)
                                        if need_cnt > 0:
                                            pool = lesson_pools[b_code][p_idx][lvl]
                                            chosen_items = random.sample(pool, need_cnt)
                                            for item in chosen_items:
                                                q_copy = sanitize_question_obj(item["question_data"].copy())
                                                if item.get("raw_tex") and not q_copy.get("raw_tex"):
                                                    q_copy["raw_tex"] = item["raw_tex"]
                                                q_copy["id"] = f"q_{len(selected_qs) + 1}"
                                                selected_qs.append(q_copy)

                            if not selected_qs:
                                st.warning("Bạn chưa chọn số lượng câu hỏi nào (> 0) ở ma trận các bài học phía trên!")
                            else:
                                st.session_state["draft_matrix_qs"] = selected_qs
                                st.session_state["draft_matrix_grade"] = sel_g
                                st.session_state["draft_matrix_chap"] = (
                                    avail_chaps[sel_chaps[0]] if len(sel_chaps) == 1 else "Ôn thi giữa học kì 1"
                                )
                                st.rerun()

                        if st.session_state.get("draft_matrix_qs"):
                            draft_qs = st.session_state["draft_matrix_qs"]
                            st.markdown("---")
                            st.subheader(f"🧐 Xem kỹ Bản nháp Đề thi ({len(draft_qs)} câu), Tải file LaTeX (.tex) & Đổi câu hỏi")

                            dr_dl1, dr_dl2 = st.columns(2)
                            dr_dl1.download_button(
                                "📄 Tải mã LaTeX đề nháp này (Chỉ khối \\begin{ex})",
                                build_latex_export_content(draft_qs, title="ĐỀ KIỂM TRA ĐÁNH GIÁ MÔN TOÁN", full_document=False).encode("utf-8"),
                                "de_nhap_ex_blocks.tex",
                                "text/plain",
                                use_container_width=True
                            )
                            dr_dl2.download_button(
                                "📘 Tải file .tex hoàn chỉnh của đề nháp này (Đủ \\documentclass)",
                                build_latex_export_content(draft_qs, title="ĐỀ KIỂM TRA ĐÁNH GIÁ MÔN TOÁN", full_document=True).encode("utf-8"),
                                "de_nhap_full_doc.tex",
                                "text/plain",
                                use_container_width=True
                            )

                            for d_idx, dq in enumerate(draft_qs):
                                col_dcard, col_dbtn = st.columns([5.8, 1.2])
                                with col_dcard:
                                    render_question_card(dq, f"Câu {d_idx + 1}")
                                with col_dbtn:
                                    if st.button("🔄 Đổi câu khác", key=f"swap_draft_{d_idx}", use_container_width=True):
                                        new_q = find_replacement_question(dq, draft_qs)
                                        if new_q:
                                            draft_qs[d_idx] = new_q
                                            st.session_state["draft_matrix_qs"] = draft_qs
                                            st.toast(f"✅ Đã đổi Câu {d_idx + 1} sang một câu hỏi mới!")
                                            st.rerun()
                                        else:
                                            st.warning("Kho không còn câu hỏi dự phòng nào khác cùng Bài/Mức độ này!")
                                    if st.button("🗑️ Xóa câu này", key=f"rm_draft_{d_idx}", use_container_width=True):
                                        draft_qs.pop(d_idx)
                                        for idx_re, q_re in enumerate(draft_qs):
                                            q_re["id"] = f"q_{idx_re + 1}"
                                        st.session_state["draft_matrix_qs"] = draft_qs
                                        st.rerun()
                                st.divider()

                            st.markdown("#### ⚙️ Thiết lập thông tin & Xuất bản chính thức Đề thi này:")
                            topic_opts_mat = get_topic_options_for_grade(st.session_state.get("draft_matrix_grade", sel_g))
                            default_topic_mat = st.session_state.get("draft_matrix_chap", topic_opts_mat[0])
                            def_t_idx = topic_opts_mat.index(default_topic_mat) if default_topic_mat in topic_opts_mat else 0

                            mt0, mt1, mt2 = st.columns([2, 2.2, 1])
                            mat_chap_choice = mt0.selectbox("Chọn Chương / Kỳ ôn thi:", topic_opts_mat, index=def_t_idx, key="pub_mat_chap_sel")
                            if mat_chap_choice.startswith("✍️"):
                                mat_chap_final = st.text_input("Nhập tên Chuyên đề / Kỳ thi tùy chỉnh:", value="Ôn thi giữa học kì 1", key="pub_mat_chap_custom")
                            else:
                                mat_chap_final = mat_chap_choice

                            mat_title = mt1.text_input("Tên đề thi mới", placeholder="VD: Đề ôn thi giữa học kì 1 - Đề số 01", key="pub_mat_title")
                            mat_dur = mt2.number_input("Thời gian (phút)", 5, 180, 45, key="pub_mat_dur")

                            ms1, ms2, ms3, ms4 = st.columns(4)
                            m_pt1 = ms1.number_input("Điểm mỗi câu Phần I", 0.0, 10.0, 0.25, 0.05, key="m_pt1")
                            m_pt2 = ms2.number_input("Điểm tối đa mỗi câu Phần II", 0.0, 10.0, 1.0, 0.25, key="m_pt2")
                            m_pt3 = ms3.number_input("Điểm mỗi câu Phần III", 0.0, 10.0, 0.5, 0.1, key="m_pt3")
                            m_pt4 = ms4.number_input("Điểm mỗi câu Tự luận (Phần IV)", 0.0, 10.0, 1.0, 0.25, key="m_pt4")

                            if st.button("🚀 XUẤT BẢN CHÍNH THỨC ĐỀ THI NÀY", type="primary"):
                                if not mat_title:
                                    st.warning("Vui lòng nhập Tên đề thi mới!")
                                else:
                                    supabase.table("exams").insert({
                                        "title": mat_title.strip(),
                                        "grade": st.session_state.get("draft_matrix_grade", sel_g),
                                        "chapter": mat_chap_final.strip(),
                                        "duration": mat_dur,
                                        "questions": draft_qs,
                                        "scoring_config": {"p1": m_pt1, "p2": m_pt2, "p3": m_pt3, "p4": m_pt4},
                                        "show_solutions": False,
                                        "is_active": True
                                    }).execute()
                                    del st.session_state["draft_matrix_qs"]
                                    st.success(f"🎉 Đã xuất bản đề thi **{mat_title}** thành công! Bạn có thể xem ở tab **Quản lý đề**.")
                                    st.rerun()

        with sub_create_fast:
            st.subheader("📄 Tải lên trực tiếp 1 đề thi hoàn chỉnh (.tex hoặc .txt)")
            c_grade, c_chap = st.columns([1, 2.5])
            grade_sel = c_grade.selectbox("Chọn Khối lớp áp dụng", ["12", "11", "10", "9", "8", "7", "6"])
            topic_options = get_topic_options_for_grade(grade_sel)
            chapter_choice = c_chap.selectbox("Chọn Chương / Chuyên đề / Kỳ ôn thi:", topic_options)
            if chapter_choice.startswith("✍️"):
                chapter_sel = st.text_input("Nhập tên Chuyên đề / Kỳ thi:", value="Ôn thi giữa học kì 1")
            else:
                chapter_sel = chapter_choice

            c_title, c_dur = st.columns([3, 1])
            exam_title = c_title.text_input("Tên bài kiểm tra", placeholder="VD: Đề ôn thi giữa học kì 1 - Đề số 01")
            duration = c_dur.number_input("Thời gian (phút)", min_value=5, max_value=180, value=45)

            st.markdown("**⚖️ Thiết lập thang điểm cho từng phần:**")
            sc1, sc2, sc3, sc4 = st.columns(4)
            pt_p1 = sc1.number_input("Điểm mỗi câu Phần I (ABCD)", min_value=0.0, max_value=10.0, value=0.25, step=0.05)
            pt_p2 = sc2.number_input("Điểm tối đa mỗi câu Phần II (Đ/S)", min_value=0.0, max_value=10.0, value=1.0, step=0.25)
            pt_p3 = sc3.number_input("Điểm mỗi câu Phần III (TLN)", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
            pt_p4 = sc4.number_input("Điểm mỗi câu Phần IV (Tự luận)", min_value=0.0, max_value=10.0, value=1.0, step=0.25)

            tex_file = st.file_uploader("Chọn file .tex hoặc .txt của bạn", type=["tex", "txt"])

            if tex_file:
                raw_tex = tex_file.read().decode("utf-8", errors="ignore")
                with st.spinner("Đang phân tích cấu trúc LaTeX và biên dịch hình vẽ TikZ..."):
                    parsed_questions = [sanitize_question_obj(q) for q in parse_exam_tex(raw_tex)]

                p1_cnt = sum(1 for q in parsed_questions if q["part"] == 1)
                p2_cnt = sum(1 for q in parsed_questions if q["part"] == 2)
                p3_cnt = sum(1 for q in parsed_questions if q["part"] == 3)
                p4_cnt = sum(1 for q in parsed_questions if q["part"] == 4)
                total_max_score = round(p1_cnt * pt_p1 + p2_cnt * pt_p2 + p3_cnt * pt_p3 + p4_cnt * pt_p4, 2)

                st.success(
                    f"✅ Đã đọc **{len(parsed_questions)} câu hỏi**: Phần I ({p1_cnt} câu), "
                    f"Phần II ({p2_cnt} câu), Phần III ({p3_cnt} câu), Phần IV Tự luận ({p4_cnt} câu) "
                    f"$\\rightarrow$ **Tổng điểm: {total_max_score} điểm**."
                )

                with st.expander("👁️ Xem trước đề thi & lời giải sau khi biên dịch", expanded=True):
                    for idx, q in enumerate(parsed_questions):
                        render_question_card(q, f"Câu {idx + 1}")
                        st.divider()

                if st.button("💾 Lưu và Xuất bản Đề Thi", type="primary"):
                    if not exam_title:
                        st.warning("Vui lòng nhập Tên bài kiểm tra!")
                    else:
                        supabase.table("exams").insert({
                            "title": exam_title.strip(),
                            "grade": grade_sel,
                            "chapter": chapter_sel.strip(),
                            "duration": duration,
                            "questions": parsed_questions,
                            "scoring_config": {"p1": pt_p1, "p2": pt_p2, "p3": pt_p3, "p4": pt_p4},
                            "show_solutions": False,
                            "is_active": True
                        }).execute()
                        st.success("🎉 Đã tạo đề thi thành công! Bạn có thể quản lý ở tab **Quản lý đề**.")
                        st.rerun()

    # -----------------------------------------------------------------
    # TAB 3: QUẢN LÝ ĐỀ (GỘP KHO ĐỀ THI ĐÃ SOẠN & BẢNG ĐIỂM / GIÁM SÁT / THỐNG KÊ)
    # -----------------------------------------------------------------
    with t_manage:
        sub_mgr_list, sub_mgr_res = st.tabs([
            "📚 Kho đề thi",
            "📊 Điểm & Giám sát"
        ])

        with sub_mgr_list:
            st.subheader("📚 Danh sách Đề thi đã soạn (Tải LaTeX .tex, Sửa phương án, Đổi câu hỏi & Mở lời giải)")
            exams_data = supabase.table("exams").select("*").order("grade", desc=True).order("chapter").order("id", desc=True).execute().data
            if not exams_data:
                st.info("Chưa có đề thi nào trong hệ thống.")
            else:
                grouped_exams = {}
                for ex in exams_data:
                    g = ex.get("grade") or "12"
                    ch = ex.get("chapter") or "Chương chung"
                    grouped_exams.setdefault(g, {}).setdefault(ch, []).append(ex)

                for g, chaps in grouped_exams.items():
                    with st.expander(f"📁 KHỐI {g} ({sum(len(v) for v in chaps.values())} đề thi)", expanded=True):
                        for ch, ex_list in chaps.items():
                            st.markdown(f"##### 📌 {ch}")
                            for ex in ex_list:
                                ex_qs = ex.get("questions", [])
                                c1, c2, c3, c4, c5 = st.columns([3.2, 1.5, 1.5, 1.6, 1.2])
                                c1.write(f"**#{ex['id']} - {ex['title']}** ({ex['duration']}p — {len(ex_qs)} câu)")
                                show_sol = c2.toggle("Mở lời giải", value=ex["show_solutions"], key=f"sol_{ex['id']}")
                                is_act = c3.toggle("Mở phòng thi", value=ex["is_active"], key=f"act_{ex['id']}")
                                if show_sol != ex["show_solutions"] or is_act != ex["is_active"]:
                                    supabase.table("exams").update({"show_solutions": show_sol, "is_active": is_act}).eq("id", ex["id"]).execute()
                                    st.rerun()
                                c4.download_button(
                                    "📥 Tải .tex",
                                    build_latex_export_content(ex_qs, title=ex["title"], full_document=True).encode("utf-8"),
                                    f"de_thi_{ex['id']}.tex",
                                    "text/plain",
                                    key=f"dl_tex_ex_{ex['id']}",
                                    use_container_width=True
                                )
                                if c5.button("🗑️ Xóa đề", key=f"del_{ex['id']}", use_container_width=True):
                                    supabase.table("exams").delete().eq("id", ex["id"]).execute()
                                    st.rerun()

                                with st.expander(f"👁️ Xem toàn bộ đề, Tải LaTeX, Sửa phương án & Đổi câu hỏi của đề #{ex['id']} - {ex['title']}"):
                                    ex_dl1, ex_dl2 = st.columns(2)
                                    ex_dl1.download_button(
                                        "📄 Tải file .tex (Chỉ gồm các khối \\begin{ex}...\\end{ex})",
                                        build_latex_export_content(ex_qs, title=ex["title"], full_document=False).encode("utf-8"),
                                        f"de_{ex['id']}_ex_blocks.tex",
                                        "text/plain",
                                        key=f"dl_blk_{ex['id']}",
                                        use_container_width=True
                                    )
                                    ex_dl2.download_button(
                                        "📘 Tải file .tex hoàn chỉnh (Đủ \\documentclass biên dịch ngay)",
                                        build_latex_export_content(ex_qs, title=ex["title"], full_document=True).encode("utf-8"),
                                        f"de_{ex['id']}_full_doc.tex",
                                        "text/plain",
                                        key=f"dl_full_{ex['id']}",
                                        use_container_width=True
                                    )
                                    st.divider()
                                    for q_idx, q_item in enumerate(ex_qs):
                                        ec1, ec2 = st.columns([5.8, 1.2])
                                        with ec1:
                                            render_question_card(q_item, f"Câu {q_idx + 1}")
                                        with ec2:
                                            if st.button("🔄 Đổi câu khác", key=f"swap_pub_{ex['id']}_{q_idx}", use_container_width=True):
                                                rep_q = find_replacement_question(q_item, ex_qs)
                                                if rep_q:
                                                    ex_qs[q_idx] = rep_q
                                                    supabase.table("exams").update({"questions": ex_qs}).eq("id", ex["id"]).execute()
                                                    st.toast(f"✅ Đã đổi Câu {q_idx + 1} trong đề #{ex['id']}!")
                                                    st.rerun()
                                                else:
                                                    st.warning("Không tìm thấy câu hỏi khác cùng Bài/Mức độ trong Ngân hàng!")
                                            if st.button("🗑️ Xóa câu", key=f"del_q_pub_{ex['id']}_{q_idx}", use_container_width=True):
                                                ex_qs.pop(q_idx)
                                                for r_i, r_q in enumerate(ex_qs):
                                                    r_q["id"] = f"q_{r_i + 1}"
                                                supabase.table("exams").update({"questions": ex_qs}).eq("id", ex["id"]).execute()
                                                st.rerun()

                                        pub_uid = f"pub_{ex['id']}_{q_idx}_{q_item.get('question_hash', '')[:6]}"
                                        with st.expander(f"✏️ Sửa nội dung & các phương án Câu {q_idx + 1} của đề #{ex['id']}"):
                                            p_tag, p_stem, p_opts, p_stmts, p_sa, p_sol = render_question_edit_controls(q_item, pub_uid)
                                            if st.button("💾 Lưu sửa câu này vào Đề thi", key=f"save_pub_{pub_uid}", type="primary"):
                                                ex_qs[q_idx] = apply_quick_edit_to_question(
                                                    q_item, p_tag, p_stem, p_sol, new_short_ans=p_sa, new_options=p_opts, new_statements=p_stmts
                                                )
                                                supabase.table("exams").update({"questions": ex_qs}).eq("id", ex["id"]).execute()
                                                st.success(f"Đã cập nhật Câu {q_idx + 1} trong đề #{ex['id']}!")
                                                st.rerun()
                                        st.divider()

        with sub_mgr_res:
            exams_list = supabase.table("exams").select("*").order("id", desc=True).execute().data
            if not exams_list:
                st.info("Chưa có đề thi nào.")
            else:
                sel_c1, sel_c2 = st.columns([4.5, 1.5])
                selected_exam = sel_c1.selectbox(
                    "📌 Chọn đề thi để xem bảng điểm, thống kê & giám sát:",
                    exams_list,
                    format_func=lambda x: f"[Khối {x.get('grade','12')} - {x.get('chapter','')}] #{x['id']} - {x['title']}"
                )
                with sel_c2:
                    st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)
                    if st.button("🔄 Cập nhật điểm mới nhất", key="refresh_scores_btn", use_container_width=True):
                        st.toast("✅ Đã làm mới bảng điểm của đề thi!")
                        st.rerun()

                subs = supabase.table("submissions").select("*, students(full_name, class_name)").eq("exam_id", selected_exam["id"]).execute().data

                if not subs:
                    st.warning("Chưa có học sinh nào làm đề này.")
                else:
                    item_stats = analyze_exam_items(selected_exam["questions"], subs)

                    xlsx_report_bytes = build_exam_report_xlsx(selected_exam, subs, item_stats)
                    st.download_button(
                        "📥 TẢI TOÀN BỘ DỮ LIỆU BÀI THI & HÌNH ẢNH CAMERA RA FILE EXCEL (.XLSX)",
                        xlsx_report_bytes,
                        f"bao_cao_ket_qua_va_anh_camera_de_{selected_exam['id']}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )

                    sub_tab1, sub_tab2, sub_tab3 = st.tabs([
                        "📋 Bảng điểm",
                        "📉 Thống kê sai",
                        "📷 Giám sát thi"
                    ])

                    with sub_tab1:
                        rows = []
                        for s in subs:
                            stu_info = s.get("students") or {}
                            dur_str, st_time_str, sub_time_str = format_duration_vn(s.get("started_at"), s.get("submitted_at"))
                            rows.append({
                                "Tài khoản": s["username"],
                                "Họ tên": stu_info.get("full_name", ""),
                                "Lớp": stu_info.get("class_name", ""),
                                "Trạng thái": "Đã nộp" if s["status"] == "submitted" else "Đang làm",
                                "Điểm số": s["score"],
                                "Bắt đầu lúc": st_time_str,
                                "Nộp bài lúc": sub_time_str,
                                "Thời gian làm bài": dur_str,
                                "Số lần rời màn hình": s["tab_switches"],
                                "Số ảnh Camera": len(s.get("snapshots") or [])
                            })
                        df_res = pd.DataFrame(rows)
                        st.dataframe(df_res, use_container_width=True, hide_index=True)

                    with sub_tab2:
                        st.subheader("📉 Xếp hạng các câu hỏi học sinh làm sai nhiều nhất")
                        if not item_stats:
                            st.info("Chưa có bài làm nào ở trạng thái 'Đã nộp' để thống kê.")
                        else:
                            df_stats = pd.DataFrame(item_stats).drop(columns=["q_obj"])
                            st.dataframe(df_stats, use_container_width=True, hide_index=True)

                            st.markdown("#### 🔍 Xem chi tiết đề bài & lời giải các câu học sinh hay sai:")
                            for st_row in item_stats:
                                q_obj = st_row["q_obj"]
                                w_rate = st_row["Tỷ lệ sai (%)"]
                                badge_color = "🔴" if w_rate >= 50 else ("🟠" if w_rate >= 25 else "🟢")
                                with st.expander(
                                    f"{badge_color} {st_row['Câu gốc']} ({st_row['Phần']}) — Tỷ lệ sai: {w_rate}% "
                                    f"({st_row['Số HS sai / Tổng']}) | [{st_row['Mã ID']}] {st_row['Bài học']}"
                                ):
                                    st.info(f"📊 **Phân tích phương án học sinh đã chọn:** {st_row['Chi tiết phân bố đáp án']}")
                                    render_question_card(q_obj, st_row["Câu gốc"])

                    with sub_tab3:
                        chosen_sub = st.selectbox(
                            "Chọn học sinh cần kiểm tra",
                            subs,
                            format_func=lambda x: f"{x['username']} - {(x.get('students') or {}).get('full_name', '')} (Lớp {(x.get('students') or {}).get('class_name', '')} | Rời màn hình: {x['tab_switches']} lần)"
                        )
                        if chosen_sub:
                            dur_s, st_s, sub_s = format_duration_vn(chosen_sub.get("started_at"), chosen_sub.get("submitted_at"))
                            st.write(f"⏱️ **Bắt đầu:** `{st_s}` | **Nộp bài:** `{sub_s}` | **Thời gian làm bài:** `{dur_s}`")

                            new_total_score = st.number_input("Cập nhật tổng điểm (nếu cộng thêm điểm Tự luận trên giấy):", 0.0, 20.0, float(chosen_sub.get("score") or 0.0), 0.25)
                            if st.button("💾 Lưu tổng điểm mới"):
                                supabase.table("submissions").update({"score": new_total_score}).eq("id", chosen_sub["id"]).execute()
                                st.success("Đã cập nhật điểm số!")
                                st.rerun()

                            if st.button("🔄 Xóa lượt làm bài này (Cho phép học sinh thi lại)"):
                                supabase.table("submissions").delete().eq("id", chosen_sub["id"]).execute()
                                st.success("Đã xóa lượt làm bài! Học sinh có thể vào thi lại.")
                                st.rerun()

                            snaps = chosen_sub.get("snapshots") or []
                            if not snaps:
                                st.info("Học sinh này chưa có ảnh chụp camera nào.")
                            else:
                                cols = st.columns(4)
                                for i, snap in enumerate(snaps):
                                    with cols[i % 4]:
                                        st.image(snap["img"], caption=f"Lúc: {snap['time']}")

    # -----------------------------------------------------------------
    # TAB 4: QUẢN LÝ HỌC SINH (ĐÃ FIX LỖI STREAMLITWIDGETALREADYINSTANTIATEDERROR)
    # -----------------------------------------------------------------
    with t_stu:
        st.subheader("1. Thêm Học sinh vào Lớp")

        add_tab_excel, add_tab_manual = st.tabs([
            "📥 Nhập từ Excel",
            "✍️ Thêm thủ công"
        ])

        with add_tab_excel:
            st.info("💡 Khuyến nghị sử dụng **file Excel (`.xlsx`)** gồm 4 cột: `Họ tên`, `Lớp` (VD: 12A1, 10A2), `Tài khoản`, `Mật khẩu` để không bị lỗi font tiếng Việt.")
            sample_df = pd.DataFrame([
                {"Họ tên": "Nguyễn Văn An", "Lớp": "12A1", "Tài khoản": "12a1_01", "Mật khẩu": "123"},
                {"Họ tên": "Trần Thị Bình", "Lớp": "12A1", "Tài khoản": "12a1_02", "Mật khẩu": "123"},
                {"Họ tên": "Lê Hoàng Cường", "Lớp": "10A1", "Tài khoản": "10a1_01", "Mật khẩu": "123"}
            ])
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                sample_df.to_excel(writer, index=False)
            st.download_button(
                "📥 Tải file Excel (.xlsx) mẫu chuẩn",
                excel_buf.getvalue(),
                "danh_sach_lop_mau.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            stu_file = st.file_uploader("Chọn file Excel (.xlsx)", type=["xlsx", "xls", "csv"])
            if stu_file:
                try:
                    df = read_student_file_safe(stu_file)
                    df.columns = [str(c).strip() for c in df.columns]
                    st.dataframe(df.head(15), use_container_width=True)

                    if st.button("➕ Nhập toàn bộ danh sách vào hệ thống", type="primary"):
                        records = []
                        cols = list(df.columns)
                        col_name = "Họ tên" if "Họ tên" in cols else cols[0]
                        col_cls = "Lớp" if "Lớp" in cols else cols[1]
                        col_usr = "Tài khoản" if "Tài khoản" in cols else cols[2]
                        col_pwd = "Mật khẩu" if "Mật khẩu" in cols else cols[3]

                        for _, row in df.iterrows():
                            u_val = str(row[col_usr]).strip()
                            if not u_val or u_val.lower() == "nan":
                                continue
                            records.append({
                                "full_name": str(row[col_name]).strip(),
                                "class_name": str(row[col_cls]).strip().upper(),
                                "username": u_val,
                                "password": str(row[col_pwd]).strip()
                            })
                        supabase.table("students").upsert(records, on_conflict="username").execute()
                        st.success(f"🎉 Đã cập nhật thành công {len(records)} tài khoản học sinh!")
                        st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Không thể đọc file danh sách lớp: {e}")

        with add_tab_manual:
            mc1, mc2, mc3, mc4 = st.columns([2.2, 1.2, 1.5, 1.2])
            m_name = mc1.text_input("Họ và tên học sinh", placeholder="VD: Nguyễn Minh Khôi", key="m_stu_name")
            m_cls = mc2.text_input("Lớp", placeholder="VD: 10A1", key="m_stu_cls")
            m_user = mc3.text_input("Tài khoản đăng nhập", placeholder="VD: 10a1_45", key="m_stu_user")
            m_pass = mc4.text_input("Mật khẩu", value="123", key="m_stu_pass")
            if st.button("➕ Thêm học sinh này vào Lớp", type="primary"):
                if not m_name.strip() or not m_cls.strip() or not m_user.strip():
                    st.warning("Vui lòng nhập đầy đủ Họ tên, Lớp và Tài khoản!")
                else:
                    supabase.table("students").upsert([{
                        "full_name": m_name.strip(),
                        "class_name": m_cls.strip().upper(),
                        "username": m_user.strip(),
                        "password": m_pass.strip() or "123"
                    }], on_conflict="username").execute()
                    st.success(f"✅ Đã thêm học sinh **{m_name.strip()}** vào lớp **{m_cls.strip().upper()}**!")
                    st.rerun()

        st.divider()
        st.subheader("2. Danh sách Học sinh theo từng Lớp (Chọn cả lớp, Sửa hoặc Xóa nhanh)")
        all_stu = supabase.table("students").select("*").order("class_name").order("username").execute().data
        if not all_stu:
            st.info("Chưa có học sinh nào trong hệ thống.")
        else:
            classes = sorted(list(set(s["class_name"] for s in all_stu)))
            st.write(f"📊 Hệ thống hiện có **{len(classes)} lớp** với tổng cộng **{len(all_stu)} học sinh**:")

            for cls_name in classes:
                cls_students = [s for s in all_stu if s["class_name"] == cls_name]
                cls_ver = st.session_state.get(f"cls_ver_{cls_name}", 0)

                with st.expander(f"🏫 Lớp {cls_name} — Sĩ số: {len(cls_students)} học sinh (Khối {extract_grade_from_class(cls_name)})", expanded=False):
                    # Dùng key có gắn phiên bản _v{cls_ver} để không bao giờ gây lỗi StreamlitWidgetAlreadyInstantiatedError khi reset sau xóa
                    tick_all_cls = st.checkbox(
                        f"☑️ Chọn cả lớp {cls_name} (Tích chọn toàn bộ {len(cls_students)} học sinh)",
                        key=f"chk_all_stu_{cls_name}_v{cls_ver}"
                    )

                    stu_rows = []
                    for idx_s, s_obj in enumerate(cls_students):
                        stu_rows.append({
                            "Chọn xóa": bool(tick_all_cls),
                            "STT": idx_s + 1,
                            "Tài khoản": s_obj["username"],
                            "Họ và tên": s_obj["full_name"],
                            "Lớp": s_obj["class_name"],
                            "Mật khẩu": s_obj["password"]
                        })
                    edited_stu_df = st.data_editor(
                        pd.DataFrame(stu_rows),
                        use_container_width=True,
                        hide_index=True,
                        disabled=["STT", "Tài khoản"],
                        key=f"stu_editor_{cls_name}_{int(tick_all_cls)}_v{cls_ver}"
                    )

                    act_c1, act_c2 = st.columns([3, 1.5])
                    if act_c1.button(f"🛠️ Lưu chỉnh sửa & 🗑️ Xóa các học sinh đã tích chọn ({cls_name})", key=f"btn_batch_stu_{cls_name}_v{cls_ver}", type="primary", use_container_width=True):
                        to_delete_users = []
                        to_update_records = []
                        for _, r_stu in edited_stu_df.iterrows():
                            if r_stu["Chọn xóa"]:
                                to_delete_users.append(str(r_stu["Tài khoản"]).strip())
                            else:
                                to_update_records.append({
                                    "username": str(r_stu["Tài khoản"]).strip(),
                                    "full_name": str(r_stu["Họ và tên"]).strip(),
                                    "class_name": str(r_stu["Lớp"]).strip().upper(),
                                    "password": str(r_stu["Mật khẩu"]).strip()
                                })
                        if to_delete_users:
                            supabase.table("students").delete().in_("username", to_delete_users).execute()
                        if to_update_records:
                            supabase.table("students").upsert(to_update_records, on_conflict="username").execute()
                        # Tăng bộ đếm cls_ver thay vì gán lại key của checkbox đang hiển thị
                        st.session_state[f"cls_ver_{cls_name}"] = cls_ver + 1
                        st.toast(f"✅ Đã xóa {len(to_delete_users)} học sinh và cập nhật lớp {cls_name}!")
                        st.rerun()

                    cls_excel_buf = io.BytesIO()
                    with pd.ExcelWriter(cls_excel_buf, engine="openpyxl") as writer:
                        pd.DataFrame(stu_rows).drop(columns=["Chọn xóa"]).to_excel(writer, index=False, sheet_name=f"Lop_{cls_name}")
                    act_c2.download_button(
                        f"📥 Xuất Lớp {cls_name} (.xlsx)",
                        cls_excel_buf.getvalue(),
                        f"danh_sach_lop_{cls_name}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_cls_{cls_name}",
                        use_container_width=True
                    )

# =====================================================================
# PHÂN HỆ 2: GIAO DIỆN HỌC SINH LÀM BÀI (HIỆN ĐẠI & TƯƠNG THÍCH IPHONE / LAPTOP)
# =====================================================================
elif st.session_state.role == "student":
    stu = st.session_state.user
    stu_grade = extract_grade_from_class(stu["class_name"])

    active_exams = supabase.table("exams").select("*").eq("is_active", True).eq("grade", stu_grade).order("chapter").order("id", desc=True).execute().data

    if not active_exams:
        st.info(f"Hiện tại chưa có bài kiểm tra nào đang mở cho **Khối {stu_grade}**.")
        st.stop()

    chapters = sorted(list(set(e.get("chapter") or "Chương chung" for e in active_exams)))
    c_sel1, c_sel2 = st.columns([1.2, 2])
    chosen_chap = c_sel1.selectbox("📂 Chọn Chương / Chuyên đề / Kỳ ôn thi:", chapters)
    chap_exams = [e for e in active_exams if (e.get("chapter") or "Chương chung") == chosen_chap]
    exam = c_sel2.selectbox("📝 Chọn Bài kiểm tra:", chap_exams, format_func=lambda x: f"{x['title']} ({x['duration']} phút)")

    sub_res = supabase.table("submissions").select("*").eq("exam_id", exam["id"]).eq("username", stu["username"]).execute().data

    if not sub_res:
        sc_cfg = exam.get("scoring_config") or {"p1": 0.25, "p2": 1.0, "p3": 0.5, "p4": 1.0}
        st.markdown(f"""
        <div class="question-card">
            <h3>📋 Thông tin bài kiểm tra: <span style="color:#2563eb;">{exam['title']}</span></h3>
            <ul>
                <li><b>Khối / Chuyên đề:</b> Khối {stu_grade} — {chosen_chap}</li>
                <li><b>Thời gian làm bài:</b> <b>{exam['duration']} phút</b> (Hệ thống tự động thu bài khi hết giờ).</li>
                <li><b>Thang điểm:</b> Phần I: <code>{sc_cfg.get('p1', 0.25)}đ</code>/câu | Phần II: tối đa <code>{sc_cfg.get('p2', 1.0)}đ</code>/câu | Phần III: <code>{sc_cfg.get('p3', 0.5)}đ</code>/câu | Phần IV (Tự luận): <code>{sc_cfg.get('p4', 1.0)}đ</code>/câu.</li>
                <li><b>Quy định phòng thi:</b> Vui lòng bật quyền Camera khi trình duyệt yêu cầu và giữ toàn màn hình làm bài.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 BẮT ĐẦU LÀM BÀI NGAY", type="primary"):
            seed_val = random.randint(10000, 99999)
            supabase.table("submissions").insert({
                "exam_id": exam["id"],
                "username": stu["username"],
                "seed": seed_val,
                "status": "in_progress"
            }).execute()
            st.rerun()
        st.stop()

    submission = sub_res[0]
    questions = exam["questions"]
    scoring_cfg = exam.get("scoring_config") or {"p1": 0.25, "p2": 1.0, "p3": 0.5, "p4": 1.0}
    seed = submission["seed"]
    saved_answers = submission.get("answers") or {}

    started_at = datetime.datetime.fromisoformat(submission["started_at"].replace("Z", "+00:00"))
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    elapsed_sec = (now_utc - started_at).total_seconds()
    remaining_sec = (exam["duration"] * 60) - elapsed_sec

    if submission["status"] == "in_progress" and remaining_sec <= 0:
        total_score, _, _, _ = grade_exam(questions, saved_answers, seed, scoring_cfg)
        supabase.table("submissions").update({
            "status": "submitted",
            "score": total_score,
            "submitted_at": now_utc.isoformat()
        }).eq("id", submission["id"]).execute()
        st.rerun()

    # ---------------- TRƯỜNG HỢP 1: ĐANG LÀM BÀI ----------------
    if submission["status"] == "in_progress":
        end_timestamp_ms = int((started_at.timestamp() + exam["duration"] * 60) * 1000)
        render_proctor_bar(
            end_timestamp_ms,
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
            submission["id"]
        )

        p1, p2, p3, p4 = get_shuffled_exam(questions, seed)
        current_answers = saved_answers.copy()

        def auto_save():
            supabase.table("submissions").update({"answers": current_answers}).eq("id", submission["id"]).execute()

        if p1:
            st.markdown(
                f'<div class="section-banner-p1">📌 PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn ({scoring_cfg.get("p1", 0.25)} điểm/câu)</div>',
                unsafe_allow_html=True
            )
            for idx, q in enumerate(p1):
                qid = q["id"]
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge">Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-stem-text">\n\n{q["stem"]}\n\n</div>', unsafe_allow_html=True)

                    opts = q["shuffled_options"]
                    labels = ["A", "B", "C", "D"]
                    opt_ids = [str(o["id"]) for o in opts]
                    opt_map = {str(o["id"]): f"**{lbl}.** {o['text']}" for lbl, o in zip(labels, opts)}

                    default_idx = opt_ids.index(str(current_answers[qid])) if str(current_answers.get(qid)) in opt_ids else None
                    choice = st.radio(
                        f"Chọn đáp án Câu {idx+1}",
                        options=opt_ids,
                        index=default_idx,
                        format_func=lambda x, m=opt_map: m[x],
                        key=f"ui_{qid}",
                        label_visibility="collapsed"
                    )
                    if choice is not None:
                        current_answers[qid] = choice

        if p2:
            st.markdown(
                f'<div class="section-banner-p2">📌 PHẦN II. Câu trắc nghiệm Đúng / Sai (Tối đa {scoring_cfg.get("p2", 1.0)} điểm/câu)</div>',
                unsafe_allow_html=True
            )
            for idx, q in enumerate(p2):
                qid = q["id"]
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:linear-gradient(135deg,#7c3aed,#5b21b6);">Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-stem-text">\n\n{q["stem"]}\n\n</div>', unsafe_allow_html=True)

                    st_labels = ["a)", "b)", "c)", "d)"]
                    for s_idx, st_item in enumerate(q["statements"]):
                        sid = f"{qid}_s{st_item['id']}"
                        with st.container(border=True):
                            c_text, c_radio = st.columns([4.5, 1.5])
                            c_text.markdown(f"**{st_labels[s_idx]}** {st_item['text']}", unsafe_allow_html=True)
                            prev_val = current_answers.get(sid)
                            r_idx = ["Đúng", "Sai"].index(prev_val) if prev_val in ["Đúng", "Sai"] else None
                            val = c_radio.radio(
                                f"Đánh giá ý {st_labels[s_idx]}",
                                options=["Đúng", "Sai"],
                                index=r_idx,
                                horizontal=True,
                                key=f"ui_{sid}",
                                label_visibility="collapsed"
                            )
                            if val is not None:
                                current_answers[sid] = val

        if p3:
            st.markdown(
                f'<div class="section-banner-p3">📌 PHẦN III. Câu trắc nghiệm trả lời ngắn ({scoring_cfg.get("p3", 0.5)} điểm/câu)</div>',
                unsafe_allow_html=True
            )
            st.info("💡 **Hướng dẫn:** Điền đáp số lần lượt từ trái sang phải.")
            allowed_box1 = set("-0123456789")
            allowed_box23 = set(",0123456789")
            allowed_box4 = set("0123456789")

            for idx, q in enumerate(p3):
                qid = q["id"]
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:linear-gradient(135deg,#d97706,#b45309);">Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-stem-text">\n\n{q["stem"]}\n\n</div>', unsafe_allow_html=True)

                    prev_short = str(current_answers.get(qid, ""))
                    d1 = prev_short[0] if len(prev_short) >= 1 else ""
                    d2 = prev_short[1] if len(prev_short) >= 2 else ""
                    d3 = prev_short[2] if len(prev_short) >= 3 else ""
                    d4 = prev_short[3] if len(prev_short) >= 4 else ""

                    # Đánh dấu khối 4 ô vuông trả lời ngắn + 4 cột ngang cố định trên iPhone & Laptop
                    st.markdown(f'<div class="sa-row-marker" data-qid="{qid}" style="display:none;"></div>', unsafe_allow_html=True)
                    bc1, bc2, bc3, bc4 = st.columns(4, gap="small")
                    b1 = bc1.text_input("sa_box_1", value=d1, max_chars=1, key=f"sa_b1_{qid}", placeholder="", label_visibility="collapsed")
                    b2 = bc2.text_input("sa_box_2", value=d2, max_chars=1, key=f"sa_b2_{qid}", placeholder="", label_visibility="collapsed")
                    b3 = bc3.text_input("sa_box_3", value=d3, max_chars=1, key=f"sa_b3_{qid}", placeholder="", label_visibility="collapsed")
                    b4 = bc4.text_input("sa_box_4", value=d4, max_chars=1, key=f"sa_b4_{qid}", placeholder="", label_visibility="collapsed")

                    b1, b2, b3, b4 = b1.strip(), b2.strip(), b3.strip(), b4.strip()
                    box_errors = []

                    if (b1 == "" and (b2 != "" or b3 != "" or b4 != "")) or (b2 == "" and (b3 != "" or b4 != "")) or (b3 == "" and b4 != ""):
                        box_errors.append("⚠️ Vui lòng điền lần lượt từ trái sang phải (không bỏ trống ô phía trước)!")

                    if b1 != "" and b1 not in allowed_box1:
                        box_errors.append("⚠️ Ô thứ 1 chỉ được điền dấu '-' hoặc chữ số (0-9).")
                    if b2 != "" and b2 not in allowed_box23:
                        box_errors.append("⚠️ Ô thứ 2 chỉ được điền dấu ',' hoặc chữ số (0-9).")
                    if b3 != "" and b3 not in allowed_box23:
                        box_errors.append("⚠️ Ô thứ 3 chỉ được điền dấu ',' hoặc chữ số (0-9).")
                    if b4 != "" and b4 not in allowed_box4:
                        box_errors.append("⚠️ Ô thứ 4 chỉ được điền chữ số (0-9).")
                    if b2 == "," and b3 == ",":
                        box_errors.append("⚠️ Không được điền 2 dấu phẩy (,) trong cùng một đáp số!")

                    if box_errors:
                        for err_m in box_errors:
                            st.error(err_m)
                    else:
                        combined_ans = b1 + b2 + b3 + b4
                        current_answers[qid] = combined_ans
                        if combined_ans:
                            st.markdown(f"<div style='padding-top:4px;color:#065f46;font-weight:700;font-size:18px;'>✅ Đáp số: <code style='font-size:20px;'>{combined_ans}</code></div>", unsafe_allow_html=True)

        if p4:
            st.markdown(
                f'<div class="section-banner-p4">📌 PHẦN IV. Bài tập Tự luận ({scoring_cfg.get("p4", 1.0)} điểm/câu)</div>',
                unsafe_allow_html=True
            )
            for idx, q in enumerate(p4):
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:linear-gradient(135deg,#059669,#047857);">Bài {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-stem-text">\n\n{q["stem"]}\n\n</div>', unsafe_allow_html=True)
                    st.markdown(
                        '<div class="essay-notice-box">✍️ Làm vào tập hoặc giấy đôi theo lời dặn từ giáo viên trên lớp</div>',
                        unsafe_allow_html=True
                    )

        if current_answers != saved_answers:
            auto_save()

        st.markdown("<br>", unsafe_allow_html=True)
        col_save, col_sub = st.columns(2)
        if col_save.button("💾 Lưu bài làm tạm thời", use_container_width=True):
            auto_save()
            st.toast("✅ Đã lưu đáp án an toàn lên hệ thống!")

        if col_sub.button("📤 NỘP BÀI HOÀN TẤT", type="primary", use_container_width=True):
            total_score, _, _, _ = grade_exam(questions, current_answers, seed, scoring_cfg)
            supabase.table("submissions").update({
                "answers": current_answers,
                "status": "submitted",
                "score": total_score,
                "submitted_at": now_utc.isoformat()
            }).eq("id", submission["id"]).execute()
            st.rerun()

    # ---------------- TRƯỜNG HỢP 2: ĐÃ NỘP BÀI ----------------
    else:
        total, s1, s2, s3 = grade_exam(questions, saved_answers, seed, scoring_cfg)
        p1, p2, p3, p4 = get_shuffled_exam(questions, seed)
        max_total = round(
            len(p1) * scoring_cfg.get("p1", 0.25)
            + len(p2) * scoring_cfg.get("p2", 1.0)
            + len(p3) * scoring_cfg.get("p3", 0.5)
            + len(p4) * scoring_cfg.get("p4", 1.0),
            2
        )
        dur_str, st_str, sub_str = format_duration_vn(submission.get("started_at"), submission.get("submitted_at"))

        st.success(f"🎉 Bạn đã hoàn thành bài kiểm tra! Điểm số hiện tại: **{submission.get('score', total)} / {max_total} điểm** (⏱️ Thời gian làm bài: **{dur_str}**)")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Phần I (Trắc nghiệm ABCD)", f"{s1} điểm")
        c2.metric("Phần II (Đúng / Sai)", f"{s2} điểm")
        c3.metric("Phần III (Trả lời ngắn)", f"{s3} điểm")
        c4.metric("Phần IV (Tự luận)", f"{len(p4)} câu (Làm trên giấy)")

        st.markdown("#### 💡 Nhận xét & Đánh giá kết quả:")
        st.info(generate_feedback(total, s1, s2, s3, len(p1), len(p2), len(p3), scoring_cfg))

        if not exam["show_solutions"]:
            st.warning("🔒 Hiện tại Giáo viên đang khóa đáp án và lời giải chi tiết. Khi Giáo viên mở khóa, bạn hãy tải lại trang để xem lời giải nhé!")
        else:
            st.subheader("📖 Đáp án & Lời giải chi tiết")
            for idx, q in enumerate(p1):
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge">Phần I - Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-stem-text">\n\n{q["stem"]}\n\n</div>', unsafe_allow_html=True)
                    user_c = str(saved_answers.get(q["id"]))
                    for opt in q["shuffled_options"]:
                        is_u = (str(opt["id"]) == user_c)
                        badge = " 👈 *(Bạn chọn)*" if is_u else ""
                        icon = "✅" if opt["is_true"] else ("❌" if is_u else "⚪")
                        st.markdown(f"{icon} {opt['text']}{badge}", unsafe_allow_html=True)
                    if q.get("solution"):
                        st.markdown(f'<div class="solution-box">\n\n📖 **Lời giải chi tiết:**\n\n{q["solution"]}\n\n</div>', unsafe_allow_html=True)

            for idx, q in enumerate(p2):
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:#6d28d9;">Phần II - Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-stem-text">\n\n{q["stem"]}\n\n</div>', unsafe_allow_html=True)
                    st_labels = ["a)", "b)", "c)", "d)"]
                    for s_idx, st_i in enumerate(q["statements"]):
                        sid = f"{q['id']}_s{st_i['id']}"
                        u_tf = saved_answers.get(sid, "Chưa chọn")
                        corr_tf = "Đúng" if st_i["is_true"] else "Sai"
                        icon = "✅" if u_tf == corr_tf else "❌"
                        st.markdown(f"{icon} **{st_labels[s_idx]}** {st_i['text']} — **Đáp án: {corr_tf}** *(Bạn chọn: {u_tf})*", unsafe_allow_html=True)
                    if q.get("solution"):
                        st.markdown(f'<div class="solution-box">\n\n📖 **Lời giải chi tiết:**\n\n{q["solution"]}\n\n</div>', unsafe_allow_html=True)

            for idx, q in enumerate(p3):
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:#d97706;">Phần III - Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-stem-text">\n\n{q["stem"]}\n\n</div>', unsafe_allow_html=True)
                    u_sa = saved_answers.get(q["id"], "Chưa điền")
                    st.write(f"🔑 **Đáp số đúng:** `{q['short_ans']}` | **Bạn điền:** `{u_sa}`")
                    if q.get("solution"):
                        st.markdown(f'<div class="solution-box">\n\n📖 **Lời giải chi tiết:**\n\n{q["solution"]}\n\n</div>', unsafe_allow_html=True)

            for idx, q in enumerate(p4):
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:#047857;">Phần IV (Tự luận) - Bài {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-stem-text">\n\n{q["stem"]}\n\n</div>', unsafe_allow_html=True)
                    st.markdown('<div class="essay-notice-box">✍️ Làm vào tập hoặc giấy đôi theo lời dặn từ giáo viên trên lớp</div>', unsafe_allow_html=True)
                    if q.get("solution"):
                        st.markdown(f'<div class="solution-box">\n\n📖 **Lời giải chuẩn:**\n\n{q["solution"]}\n\n</div>', unsafe_allow_html=True)