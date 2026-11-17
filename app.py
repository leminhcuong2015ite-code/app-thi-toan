import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client
import pandas as pd
import random
import datetime
import re
import hashlib
import io
from latex_parser import parse_exam_tex, clean_latex_to_markdown
from kntt_mapping import KNTT_DATA, LEVEL_MAP, decode_kntt_tag

st.set_page_config(page_title="Hệ thống Kiểm tra Trực tuyến - Toán Phổ Thông", layout="wide", page_icon="📐")

# ================= CSS GIAO DIỆN HIỆN ĐẠI, TRỰC QUAN CHO HỌC SINH THCS & THPT =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.question-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.question-card:hover {
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.08);
    border-color: #cbd5e1;
}

.section-banner-p1 {
    background: linear-gradient(90deg, #1d4ed8 0%, #3b82f6 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 18px;
    margin: 20px 0 14px 0;
    box-shadow: 0 3px 10px rgba(37, 99, 235, 0.2);
}
.section-banner-p2 {
    background: linear-gradient(90deg, #6d28d9 0%, #8b5cf6 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 18px;
    margin: 20px 0 14px 0;
    box-shadow: 0 3px 10px rgba(109, 40, 217, 0.2);
}
.section-banner-p3 {
    background: linear-gradient(90deg, #d97706 0%, #f59e0b 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 18px;
    margin: 20px 0 14px 0;
    box-shadow: 0 3px 10px rgba(217, 119, 6, 0.2);
}
.section-banner-p4 {
    background: linear-gradient(90deg, #047857 0%, #10b981 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 18px;
    margin: 20px 0 14px 0;
    box-shadow: 0 3px 10px rgba(4, 120, 87, 0.2);
}

.q-badge {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: #ffffff;
    padding: 5px 14px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 14px;
    display: inline-block;
    box-shadow: 0 2px 5px rgba(37, 99, 235, 0.25);
}

.tag-pill {
    background-color: #f1f5f9;
    color: #334155;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 8px;
    border: 1px solid #cbd5e1;
}

div[role="radiogroup"] > label {
    background-color: #ffffff !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    margin-bottom: 10px !important;
    width: 100%;
    transition: all 0.18s ease !important;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}
div[role="radiogroup"] > label:hover {
    background-color: #eff6ff !important;
    border-color: #3b82f6 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(59, 130, 246, 0.1);
}

.solution-box {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border-left: 5px solid #16a34a;
    padding: 14px 18px;
    border-radius: 10px;
    margin-top: 12px;
    color: #1e293b;
}

.opt-box-true {
    background-color: #ecfdf5;
    border: 1.5px solid #10b981;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    color: #065f46;
    font-weight: 600;
}
.opt-box-false {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    color: #334155;
}
.opt-box-true p, .opt-box-false p {
    margin: 0 !important;
}
</style>
""", unsafe_allow_html=True)

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

# ================= HÀM ĐỌC FILE CSV / EXCEL AN TOÀN (CHỐNG LỖI UNICODEDECODEERROR) =================
def read_student_file_safe(uploaded_file):
    """Đọc file danh sách học sinh (.csv hoặc .xlsx) tự động nhận diện bảng mã tiếng Việt và dấu phân cách"""
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

# ================= HÀM KIỂM TRA TRẠNG THÁI HIỂN THỊ & DỰNG THẺ CÂU HỎI =================
def check_question_health(q):
    """Kiểm tra xem câu hỏi và lời giải sau khi biên dịch có lỗi TikZ hay sót lệnh ex_test không"""
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
    if re.search(r'\\(choice|choiceTF|shortans|loigiai|logiai|itemch|immini|lq|rq)\b', full_rendered):
        issues.append("⚠️ Sót lệnh LaTeX")
    elif re.search(r'\\(begin|end)\{(?!(aligned|array|cases|matrix|pmatrix|bmatrix|vmatrix)\b)', full_rendered):
        issues.append("⚠️ Sót môi trường LaTeX")

    if not issues:
        return "✅ Hiển thị tốt"
    return " | ".join(issues)

def render_question_card(q, index_label):
    """Hiển thị đầy đủ 1 câu hỏi (Đề bài + Phương án + Lời giải) đảm bảo dịch MathJax 100%"""
    status_str = check_question_health(q)
    st_bg = "#dcfce7" if "✅" in status_str else "#fef2f2"
    st_fg = "#166534" if "✅" in status_str else "#991b1b"
    def clean_leftover_spaces(txt):
    """Làm sạch các lệnh khoảng trắng LaTeX (\ , \, , \quad) bị sót ngoài công thức toán"""
    if not txt:
        return ""
    txt = re.sub(r'\\lq\s*\\lq\s*|\\rq\s*\\rq\s*', '"', txt)
    # Thay thế "\ " bằng khoảng trắng thường (nếu ngoài $) hoặc \, (nếu trong $)
    txt = re.sub(r'\\(\s+)', ' ', txt)
    return txt
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

    stem_disp = re.sub(r'\\lq\s*\\lq\s*|\\rq\s*\\rq\s*', '"', q.get("stem", ""))
    st.markdown(stem_disp, unsafe_allow_html=True)

    if part_num == 1:
        labels = ["A", "B", "C", "D"]
        cols = st.columns(2)
        for idx, opt in enumerate(q.get("options", [])):
            is_t = opt.get("is_true")
            icon = "✅" if is_t else "⚪"
            lbl = labels[idx] if idx < 4 else str(idx + 1)
            box_cls = "opt-box-true" if is_t else "opt-box-false"
            opt_txt = re.sub(r'\\lq\s*\\lq\s*|\\rq\s*\\rq\s*', '"', opt.get("text", ""))
            cols[idx % 2].markdown(
                f'<div class="{box_cls}">\n\n{icon} **{lbl}.** {opt_txt}\n\n</div>',
                unsafe_allow_html=True
            )
    elif part_num == 2:
        st_labels = ["a)", "b)", "c)", "d)"]
        for idx, st_i in enumerate(q.get("statements", [])):
            badge = "🟢 **[Đúng]**" if st_i.get("is_true") else "🔴 **[Sai]**"
            lbl = st_labels[idx] if idx < 4 else f"{idx+1})"
            st_txt = re.sub(r'\\lq\s*\\lq\s*|\\rq\s*\\rq\s*', '"', st_i.get("text", ""))
            st.markdown(f"- **{lbl}** {st_txt} $\\longrightarrow$ {badge}", unsafe_allow_html=True)
    elif part_num == 3:
        st.markdown(f"🔑 **Đáp số trả lời ngắn:** `{q.get('short_ans', '')}`")
    elif part_num == 4:
        st.markdown("✍️ **Dạng câu hỏi:** *Bài tập Tự luận (Trình bày lời giải chi tiết)*")

    sol_text = re.sub(r'\\lq\s*\\lq\s*|\\rq\s*\\rq\s*', '"', q.get("solution", "").strip())
    if sol_text:
        st.markdown(
            f'<div class="solution-box">\n\n📖 **Lời giải chi tiết:**\n\n{sol_text}\n\n</div>',
            unsafe_allow_html=True
        )
    else:
        st.caption("*(Câu hỏi này chưa có nội dung lời giải)*")

def apply_quick_edit_to_question(q, new_tag_str, new_stem_md, new_sol_md, new_short_ans=None):
    """Cập nhật nhanh Mã ID, Đề bài và Lời giải cho 1 đối tượng câu hỏi"""
    meta = decode_kntt_tag(new_tag_str)
    if meta:
        q.update(meta)
    else:
        q["tag_id"] = new_tag_str.strip()
    q["stem"] = new_stem_md.strip()
    q["solution"] = new_sol_md.strip()
    if q.get("part") == 3 and new_short_ans is not None:
        q["short_ans"] = new_short_ans.strip().replace(".", ",")
    full_str = (
        q["stem"]
        + str(q.get("options", ""))
        + str(q.get("statements", ""))
        + str(q.get("short_ans", ""))
    )
    q["question_hash"] = hashlib.md5(full_str.encode("utf-8")).hexdigest()
    return q

# ================= HÀM HỖ TRỢ CHẤM ĐIỂM, ĐẢO ĐỀ & THỐNG KÊ =================
def extract_grade_from_class(class_name):
    m = re.match(r'^(\d+)', str(class_name).strip())
    return m.group(1) if m else "12"

def get_shuffled_exam(questions, seed):
    rng = random.Random(seed)
    p1 = [q.copy() for q in questions if q.get("part") == 1]
    p2 = [q.copy() for q in questions if q.get("part") == 2]
    p3 = [q.copy() for q in questions if q.get("part") == 3]
    p4 = [q.copy() for q in questions if q.get("part") == 4]

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
            empty_cnt = sum(1 for s in submitted_subs if not str((s.get("answers") or {}).get(qid, "")).strip())
            empty_rate = round((empty_cnt / total_sub) * 100, 1)
            analysis_list.append({
                "Câu gốc": f"Câu {idx+1}",
                "Phần": "Phần IV (Tự luận)",
                "Mã ID": tag_id,
                "Bài học": lesson_name,
                "Mức độ": lvl_name,
                "Số HS sai / Tổng": f"{empty_cnt}/{total_sub} bỏ trống",
                "Tỷ lệ sai (%)": empty_rate,
                "Chi tiết phân bố đáp án": f"Có {total_sub - empty_cnt}/{total_sub} HS đã nộp bài làm tự luận",
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

    chosen = random.choice(candidates)["question_data"].copy()
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

# ================= COMPONENT GIÁM SÁT =================
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
    </script>
    """
    components.html(html_code, height=110)

# ================= QUẢN LÝ ĐĂNG NHẬP =================
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.role is None:
    st.title("🎓 Hệ Thống Kiểm Tra Đánh Giá Môn Toán")
    tab_hs, tab_gv = st.tabs(["👨‍🎓 Học sinh Đăng nhập", "👨‍🏫 Giáo viên Quản trị"])

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
    if st.button("🚪 Đăng xuất"):
        st.session_state.role = None
        st.session_state.user = None
        st.rerun()

# =====================================================================
# PHÂN HỆ 1: GIAO DIỆN GIÁO VIÊN (5 TAB ĐỘC LẬP)
# =====================================================================
if st.session_state.role == "teacher":
    st.title("👨‍🏫 Bảng Điều Khiển Giáo Viên")
    t_bank, t_matrix, t_exam, t_stu, t_res = st.tabs([
        "🏦 1. Quản lý Ngân hàng Câu hỏi",
        "🎲 2. Trộn đề theo Ma trận từng Bài",
        "📄 3. Tạo đề nhanh & Quản lý Đề thi",
        "👥 4. Quản lý Học sinh theo Lớp",
        "📊 5. Bảng điểm, Giám sát & Thống kê"
    ])

    # -----------------------------------------------------------------
    # TAB 1: QUẢN LÝ NGÂN HÀNG CÂU HỎI (NẠP, DUYỆT, SỬA/XÓA & DỌN SẠCH KHO)
    # -----------------------------------------------------------------
    with t_bank:
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
            file_sig = f"{bank_tex_file.name}_{bank_tex_file.size}_{missing_id_mode}_{fb_grade}_{fb_chap_code}_{fb_lesson_code}_{fb_lvl_code}"
            if st.session_state.get("staged_file_sig") != file_sig:
                raw_bank_tex = bank_tex_file.read().decode("utf-8", errors="ignore")
                with st.spinner("Đang biên dịch LaTeX/TikZ và kiểm tra mã ID câu hỏi..."):
                    parsed_qs = parse_exam_tex(raw_bank_tex)
                    processed_qs = []
                    dropped_no_id = 0

                    for q in parsed_qs:
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

                    st.session_state["staged_bank_qs"] = processed_qs
                    st.session_state["dropped_no_id_count"] = dropped_no_id
                    st.session_state["staged_file_sig"] = file_sig

            staged_qs = st.session_state.get("staged_bank_qs", [])
            dropped_cnt = st.session_state.get("dropped_no_id_count", 0)

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
                    disabled=["STT", "Trạng thái", "Dạng thức", "Khối", "Bài học", "Mức độ"],
                    key="staged_table_editor"
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
                    st.session_state["staged_bank_qs"] = new_staged
                    st.toast("✅ Đã cập nhật danh sách câu hỏi tạm!")
                    st.rerun()

                if untagged_count > 0:
                    if btn_col2.button(f"🗑️ Xóa nhanh toàn bộ {untagged_count} câu chưa có mã ID", use_container_width=True):
                        st.session_state["staged_bank_qs"] = [q for q in staged_qs if q.get("tag_id") != "Chưa gắn mã"]
                        st.toast(f"Đã loại bỏ {untagged_count} câu thiếu mã ID!")
                        st.rerun()

                with st.expander("👁️ Xem chi tiết, Sửa nội dung hoặc Xóa nhanh từng câu hỏi trước khi lưu", expanded=(warn_count > 0 or untagged_count > 0)):
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
                            col_q, col_btn = st.columns([6, 1])
                            with col_q:
                                render_question_card(q_item, f"Câu {orig_idx + 1}")
                            with col_btn:
                                if st.button("🗑️ Xóa ngay", key=f"del_stage_{orig_idx}"):
                                    staged_qs.pop(orig_idx)
                                    st.session_state["staged_bank_qs"] = staged_qs
                                    st.rerun()
                            with st.expander(f"✏️ Tự gán Mã ID / Sửa nội dung Câu {orig_idx + 1}"):
                                u_tag = st.text_input("Nhập Mã ID chuẩn (VD: 10-C1-B1-N)", value=q_item.get("tag_id", ""), key=f"st_tag_{orig_idx}")
                                u_stem = st.text_area("Nội dung đề bài (Markdown / LaTeX)", value=q_item.get("stem", ""), height=100, key=f"st_stem_{orig_idx}")
                                u_sa = None
                                if q_item.get("part") == 3:
                                    u_sa = st.text_input("Đáp số trả lời ngắn", value=str(q_item.get("short_ans", "")), key=f"st_sa_{orig_idx}")
                                u_sol = st.text_area("Lời giải chi tiết", value=q_item.get("solution", ""), height=100, key=f"st_sol_{orig_idx}")
                                if st.button("💾 Lưu chỉnh sửa câu này", key=f"btn_save_st_{orig_idx}"):
                                    staged_qs[orig_idx] = apply_quick_edit_to_question(q_item, u_tag, u_stem, u_sol, u_sa)
                                    st.session_state["staged_bank_qs"] = staged_qs
                                    st.success("Đã cập nhật câu hỏi!")
                                    st.rerun()
                            st.divider()

                if st.button("📥 Lưu các câu hỏi hợp lệ vào Ngân hàng", type="primary"):
                    valid_qs = [q for q in staged_qs if q.get("tag_id") != "Chưa gắn mã"]
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
        st.subheader("🔍 2. Duyệt, Kiểm tra hiển thị & Sửa/Xóa câu hỏi trong Ngân hàng")

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
                b_page_size = len(inspect_list) if b_page_opt == "Tất cả" else int(b_page_opt)
                b_total_pages = max(1, (len(inspect_list) + b_page_size - 1) // b_page_size)
                b_cur_page = st.number_input(
                    f"Trang danh sách câu hỏi (1 - {b_total_pages}, tổng {len(inspect_list)} câu):",
                    min_value=1, max_value=b_total_pages, value=1, key="bank_inspect_page"
                )
                b_start = (b_cur_page - 1) * b_page_size
                for item in inspect_list[b_start:b_start + b_page_size]:
                    qd = item["question_data"]
                    c_card, c_act = st.columns([6.2, 1])
                    with c_card:
                        render_question_card(qd, f"ID Kho #{item['id']}")
                    with c_act:
                        if st.button("🗑️ Xóa", key=f"del_qb_{item['id']}"):
                            supabase.table("question_bank").delete().eq("id", item["id"]).execute()
                            try:
                                supabase.rpc("sync_question_bank_seq").execute()
                            except Exception:
                                pass
                            st.toast(f"Đã xóa câu #{item['id']} khỏi Ngân hàng!")
                            st.rerun()

                    with st.expander(f"✏️ Sửa Mã ID / Nội dung câu #{item['id']}"):
                        db_tag = st.text_input("Mã ID (VD: 10-C1-B1-N)", value=item.get("tag_id", ""), key=f"db_tag_{item['id']}")
                        db_stem = st.text_area("Nội dung đề bài", value=qd.get("stem", ""), height=100, key=f"db_stem_{item['id']}")
                        db_sa = None
                        if item["part"] == 3:
                            db_sa = st.text_input("Đáp số trả lời ngắn", value=str(qd.get("short_ans", "")), key=f"db_sa_{item['id']}")
                        db_sol = st.text_area("Lời giải chi tiết", value=qd.get("solution", ""), height=100, key=f"db_sol_{item['id']}")
                        if st.button("💾 Cập nhật vào Ngân hàng", key=f"btn_upd_qb_{item['id']}", type="primary"):
                            updated_q = apply_quick_edit_to_question(qd, db_tag, db_stem, db_sol, db_sa)
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
                                "question_hash": updated_q["question_hash"]
                            }).eq("id", item["id"]).execute()
                            st.success(f"Đã cập nhật câu #{item['id']} thành công!")
                            st.rerun()
                    st.divider()

        st.divider()
        # KHU VỰC XÓA SẠCH NGÂN HÀNG CÂU HỎI & ĐÁNH SỐ LẠI ID KHO TỪ 1
        with st.expander("🚨 3. Xóa sạch Ngân hàng câu hỏi & Đánh số lại ID Kho từ #1"):
            st.warning(
                "⚠️ **Cảnh báo quan trọng:** Hành động này sẽ xóa các câu hỏi trong bảng `question_bank` trên Supabase để giải phóng bộ nhớ và đặt lại bộ đếm ID Kho về lại từ `#1`. "
                "Các đề thi đã xuất bản ở Tab 3 sẽ không bị ảnh hưởng."
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
    # TAB 2: TRỘN ĐỀ THI THEO MA TRẬN CHI TIẾT TỪNG BÀI HỌC
    # -----------------------------------------------------------------
    with t_matrix:
        st.subheader("🎲 Thiết lập Ma trận & Rút câu hỏi ngẫu nhiên theo từng Bài học")
        st.info("💡 Bạn có thể chọn nhiều Chương, tích chọn các Bài học đã dạy và **nhập số lượng câu hỏi cần lấy riêng cho từng Bài học** ở bên dưới.")

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
                "3. Chọn các Bài học cần đưa vào Ma trận đề thi (VD: Chỉ chọn Bài 1, Bài 2):",
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
                    st.warning("Chưa có câu hỏi nào trong Ngân hàng thuộc các Bài học đang chọn. Hãy sang Tab 1 để nạp câu hỏi trước nhé!")
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
                                            q_copy = item["question_data"].copy()
                                            q_copy["id"] = f"q_{len(selected_qs) + 1}"
                                            selected_qs.append(q_copy)

                        if not selected_qs:
                            st.warning("Bạn chưa chọn số lượng câu hỏi nào (> 0) ở ma trận các bài học phía trên!")
                        else:
                            st.session_state["draft_matrix_qs"] = selected_qs
                            st.session_state["draft_matrix_grade"] = sel_g
                            st.session_state["draft_matrix_chap"] = (
                                avail_chaps[sel_chaps[0]] if len(sel_chaps) == 1 else ("Tổng hợp: " + ", ".join(sel_chaps))
                            )
                            st.rerun()

                    if st.session_state.get("draft_matrix_qs"):
                        draft_qs = st.session_state["draft_matrix_qs"]
                        st.markdown("---")
                        st.subheader(f"🧐 Xem kỹ Bản nháp Đề thi ({len(draft_qs)} câu) & Đổi câu hỏi")
                        st.info("💡 Bạn có thể xem chi tiết từng câu hỏi + lời giải dưới đây. Nếu thấy câu nào chưa ưng ý, hãy bấm **🔄 Đổi câu khác** để hệ thống tự rút 1 câu khác cùng Bài & Mức độ từ Ngân hàng.")

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
                        mt1, mt2 = st.columns([3, 1])
                        mat_title = mt1.text_input("Tên đề thi mới", placeholder="VD: Kiểm tra 45 phút - Chương 1 (Bài 1 & Bài 2)", key="pub_mat_title")
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
                                    "chapter": st.session_state.get("draft_matrix_chap", ""),
                                    "duration": mat_dur,
                                    "questions": draft_qs,
                                    "scoring_config": {"p1": m_pt1, "p2": m_pt2, "p3": m_pt3, "p4": m_pt4},
                                    "show_solutions": False,
                                    "is_active": True
                                }).execute()
                                del st.session_state["draft_matrix_qs"]
                                st.success(f"🎉 Đã xuất bản đề thi **{mat_title}** thành công! Bạn có thể quản lý đề ở Tab 3.")
                                st.rerun()

    # -----------------------------------------------------------------
    # TAB 3: TẠO ĐỀ TRỰC TIẾP TỪ FILE & XEM / ĐỔI CÂU HỎI ĐỀ ĐÃ SOẠN
    # -----------------------------------------------------------------
    with t_exam:
        st.subheader("1. Tải lên trực tiếp 1 đề thi hoàn chỉnh (.tex hoặc .txt)")
        c_grade, c_chap = st.columns([1, 2])
        grade_sel = c_grade.selectbox("Chọn Khối lớp áp dụng", ["12", "11", "10", "9", "8", "7", "6"])
        chap_dict = KNTT_DATA[grade_sel]["chapters"]
        chapter_sel = c_chap.selectbox("Chọn Chương (SGK Kết nối tri thức)", list(chap_dict.values()))

        c_title, c_dur = st.columns([3, 1])
        exam_title = c_title.text_input("Tên bài kiểm tra", placeholder="VD: Đề kiểm tra giữa kỳ 2 - Đề số 01")
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
                parsed_questions = parse_exam_tex(raw_tex)

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
                        "chapter": chapter_sel,
                        "duration": duration,
                        "questions": parsed_questions,
                        "scoring_config": {"p1": pt_p1, "p2": pt_p2, "p3": pt_p3, "p4": pt_p4},
                        "show_solutions": False,
                        "is_active": True
                    }).execute()
                    st.success("🎉 Đã tạo đề thi thành công!")
                    st.rerun()

        st.divider()
        st.subheader("📚 2. Quản lý Đề thi đã soạn (Xem toàn bộ đề, Đổi câu hỏi khác & Mở lời giải)")
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
                            c1, c2, c3, c4 = st.columns([4, 2, 2, 1.5])
                            c1.write(f"**#{ex['id']} - {ex['title']}** ({ex['duration']}p — {len(ex.get('questions', []))} câu)")
                            show_sol = c2.toggle("Mở lời giải", value=ex["show_solutions"], key=f"sol_{ex['id']}")
                            is_act = c3.toggle("Mở phòng thi", value=ex["is_active"], key=f"act_{ex['id']}")
                            if show_sol != ex["show_solutions"] or is_act != ex["is_active"]:
                                supabase.table("exams").update({"show_solutions": show_sol, "is_active": is_act}).eq("id", ex["id"]).execute()
                                st.rerun()
                            if c4.button("🗑️ Xóa đề", key=f"del_{ex['id']}"):
                                supabase.table("exams").delete().eq("id", ex["id"]).execute()
                                st.rerun()

                            with st.expander(f"👁️ Xem toàn bộ đề, Lời giải & Đổi câu hỏi của đề #{ex['id']} - {ex['title']}"):
                                ex_qs = ex.get("questions", [])
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
                                    st.divider()

    # -----------------------------------------------------------------
    # TAB 4: QUẢN LÝ HỌC SINH THEO LỚP (ĐỌC MỌI BẢNG MÃ CSV / EXCEL AN TOÀN)
    # -----------------------------------------------------------------
    with t_stu:
        st.subheader("1. Nhập danh sách lớp từ Excel / CSV")
        st.info("File Excel/CSV cần có 4 cột: `Họ tên`, `Lớp` (VD: 12A1, 11B2), `Tài khoản`, `Mật khẩu`")

        sample_df = pd.DataFrame([
            {"Họ tên": "Nguyễn Văn An", "Lớp": "12A1", "Tài khoản": "12a1_01", "Mật khẩu": "123"},
            {"Họ tên": "Trần Thị Bình", "Lớp": "12A1", "Tài khoản": "12a1_02", "Mật khẩu": "123"},
            {"Họ tên": "Lê Hoàng Cường", "Lớp": "11A2", "Tài khoản": "11a2_01", "Mật khẩu": "123"}
        ])

        dl_c1, dl_c2 = st.columns(2)
        dl_c1.download_button(
            "📥 Tải file CSV mẫu (UTF-8)",
            sample_df.to_csv(index=False).encode("utf-8-sig"),
            "danh_sach_lop_mau.csv",
            "text/csv",
            use_container_width=True
        )
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
            sample_df.to_excel(writer, index=False)
        dl_c2.download_button(
            "📥 Tải file Excel (.xlsx) mẫu",
            excel_buf.getvalue(),
            "danh_sach_lop_mau.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        stu_file = st.file_uploader("Chọn file Excel (.xlsx) hoặc CSV (.csv)", type=["xlsx", "csv"])
        if stu_file:
            try:
                df = read_student_file_safe(stu_file)
                df.columns = [str(c).strip() for c in df.columns]
                st.dataframe(df.head(10), use_container_width=True)

                if st.button("➕ Nhập toàn bộ danh sách vào hệ thống", type="primary"):
                    records = []
                    # Hỗ trợ nhận diện cột theo tên hoặc theo vị trí 4 cột đầu tiên nếu cột bị lệch dấu
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

        st.divider()
        st.subheader("2. Danh sách Học sinh theo từng Lớp")
        all_stu = supabase.table("students").select("*").order("class_name").order("username").execute().data
        if not all_stu:
            st.info("Chưa có học sinh nào.")
        else:
            classes = sorted(list(set(s["class_name"] for s in all_stu)))
            st.write(f"Hệ thống hiện có **{len(classes)} lớp** với tổng cộng **{len(all_stu)} học sinh**:")

            for cls_name in classes:
                cls_students = [s for s in all_stu if s["class_name"] == cls_name]
                with st.expander(f"🏫 Lớp {cls_name} — Sĩ số: {len(cls_students)} học sinh (Khối {extract_grade_from_class(cls_name)})"):
                    df_cls = pd.DataFrame(cls_students)[["username", "full_name", "class_name", "password"]]
                    df_cls.columns = ["Tài khoản", "Họ và tên", "Lớp", "Mật khẩu"]
                    st.dataframe(df_cls, use_container_width=True, hide_index=True)

                    c_del1, c_del2 = st.columns([3, 1])
                    stu_to_del = c_del1.selectbox(
                        f"Chọn học sinh lớp {cls_name} để xóa:",
                        cls_students,
                        format_func=lambda x: f"{x['username']} - {x['full_name']}",
                        key=f"sel_del_{cls_name}"
                    )
                    if c_del2.button("🗑️ Xóa học sinh này", key=f"btn_del_stu_{cls_name}"):
                        supabase.table("students").delete().eq("username", stu_to_del["username"]).execute()
                        st.rerun()

    # -----------------------------------------------------------------
    # TAB 5: BẢNG ĐIỂM, GIÁM SÁT CAMERA & THỐNG KÊ TỶ LỆ LÀM SAI TỪNG CÂU
    # -----------------------------------------------------------------
    with t_res:
        exams_list = supabase.table("exams").select("*").order("id", desc=True).execute().data
        if not exams_list:
            st.info("Chưa có đề thi nào.")
        else:
            selected_exam = st.selectbox(
                "📌 Chọn đề thi để xem báo cáo",
                exams_list,
                format_func=lambda x: f"[Khối {x.get('grade','12')} - {x.get('chapter','')}] #{x['id']} - {x['title']}"
            )
            subs = supabase.table("submissions").select("*, students(full_name, class_name)").eq("exam_id", selected_exam["id"]).execute().data

            if not subs:
                st.warning("Chưa có học sinh nào làm đề này.")
            else:
                sub_tab1, sub_tab2, sub_tab3 = st.tabs([
                    "📋 1. Bảng điểm tổng hợp",
                    "📉 2. Thống kê tỷ lệ làm sai từng câu (Item Analysis)",
                    "📷 3. Giám sát Camera, Bài tự luận & Cho phép thi lại"
                ])

                with sub_tab1:
                    rows = []
                    for s in subs:
                        stu_info = s.get("students") or {}
                        rows.append({
                            "Tài khoản": s["username"],
                            "Họ tên": stu_info.get("full_name", ""),
                            "Lớp": stu_info.get("class_name", ""),
                            "Trạng thái": "Đã nộp" if s["status"] == "submitted" else "Đang làm",
                            "Điểm số": s["score"],
                            "Số lần rời màn hình": s["tab_switches"],
                            "Số ảnh Camera": len(s.get("snapshots") or [])
                        })
                    df_res = pd.DataFrame(rows)
                    st.dataframe(df_res, use_container_width=True, hide_index=True)
                    st.download_button("📥 Xuất bảng điểm ra Excel (CSV)", df_res.to_csv(index=False).encode("utf-8-sig"), "bang_diem.csv", "text/csv")

                with sub_tab2:
                    st.subheader("📉 Xếp hạng các câu hỏi học sinh làm sai nhiều nhất")
                    item_stats = analyze_exam_items(selected_exam["questions"], subs)
                    if not item_stats:
                        st.info("Chưa có bài làm nào ở trạng thái 'Đã nộp' để thống kê.")
                    else:
                        df_stats = pd.DataFrame(item_stats).drop(columns=["q_obj"])
                        st.dataframe(df_stats, use_container_width=True, hide_index=True)
                        st.download_button(
                            "📥 Xuất thống kê câu sai ra Excel (CSV)",
                            df_stats.to_csv(index=False).encode("utf-8-sig"),
                            "thong_ke_cau_sai.csv",
                            "text/csv"
                        )

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
                        p4_qs = [q for q in selected_exam["questions"] if q.get("part") == 4]
                        if p4_qs:
                            st.markdown("#### ✍️ Bài làm Tự luận của học sinh:")
                            stu_ans = chosen_sub.get("answers") or {}
                            for idx4, q4 in enumerate(p4_qs):
                                st.markdown(f"**Tự luận - Câu {idx4 + 1}:**")
                                st.markdown(q4["stem"], unsafe_allow_html=True)
                                st.info(f"**Bài trình bày của HS:**\n\n{stu_ans.get(q4['id'], '*(Bỏ trống)*')}")
                            new_total_score = st.number_input("Cập nhật tổng điểm (sau khi chấm thêm Tự luận):", 0.0, 20.0, float(chosen_sub.get("score") or 0.0), 0.25)
                            if st.button("💾 Lưu điểm đã chấm Tự luận"):
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

# =====================================================================
# PHÂN HỆ 2: GIAO DIỆN HỌC SINH LÀM BÀI (HIỆN ĐẠI & TRỰC QUAN)
# =====================================================================
elif st.session_state.role == "student":
    stu = st.session_state.user
    stu_grade = extract_grade_from_class(stu["class_name"])

    active_exams = supabase.table("exams").select("*").eq("is_active", True).eq("grade", stu_grade).order("chapter").order("id", desc=True).execute().data

    if not active_exams:
        st.info(f"Hiện tại chưa có bài kiểm tra nào đang mở cho **Khối {stu_grade}**.")
        st.stop()

    chapters = sorted(list(set(e.get("chapter") or "Chương chung" for e in active_exams)))
    c_sel1, c_sel2 = st.columns([1, 2])
    chosen_chap = c_sel1.selectbox("📂 Chọn Chương / Chuyên đề:", chapters)
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
                    st.markdown(q["stem"], unsafe_allow_html=True)

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
                    st.markdown(q["stem"], unsafe_allow_html=True)

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
            for idx, q in enumerate(p3):
                qid = q["id"]
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:linear-gradient(135deg,#d97706,#b45309);">Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(q["stem"], unsafe_allow_html=True)

                    c_lbl, c_inp = st.columns([1.5, 3.5])
                    c_lbl.markdown("🎯 **Nhập đáp số:**")
                    prev_short = current_answers.get(qid, "")
                    ans_text = c_inp.text_input(
                        f"Đáp số Câu {idx+1}",
                        value=prev_short,
                        placeholder="Nhập kết quả số (dùng dấu phẩy cho số thập phân, VD: 4,5)",
                        key=f"ui_{qid}",
                        label_visibility="collapsed"
                    )
                    if ans_text != "":
                        current_answers[qid] = ans_text.strip()

        if p4:
            st.markdown(
                f'<div class="section-banner-p4">📌 PHẦN IV. Bài tập Tự luận ({scoring_cfg.get("p4", 1.0)} điểm/câu)</div>',
                unsafe_allow_html=True
            )
            for idx, q in enumerate(p4):
                qid = q["id"]
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:linear-gradient(135deg,#059669,#047857);">Bài {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(q["stem"], unsafe_allow_html=True)
                    prev_essay = current_answers.get(qid, "")
                    essay_text = st.text_area(
                        f"Trình bày lời giải Bài {idx+1}",
                        value=prev_essay,
                        placeholder="Nhập tóm tắt các bước giải và kết quả cuối cùng của em vào đây...",
                        height=130,
                        key=f"ui_{qid}"
                    )
                    if essay_text != "":
                        current_answers[qid] = essay_text.strip()

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

        st.success(f"🎉 Bạn đã hoàn thành bài kiểm tra! Điểm số hiện tại: **{submission.get('score', total)} / {max_total} điểm**")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Phần I (Trắc nghiệm ABCD)", f"{s1} điểm")
        c2.metric("Phần II (Đúng / Sai)", f"{s2} điểm")
        c3.metric("Phần III (Trả lời ngắn)", f"{s3} điểm")
        c4.metric("Phần IV (Tự luận)", f"{len(p4)} câu")

        st.markdown("#### 💡 Nhận xét & Đánh giá kết quả:")
        st.info(generate_feedback(total, s1, s2, s3, len(p1), len(p2), len(p3), scoring_cfg))

        if not exam["show_solutions"]:
            st.warning("🔒 Hiện tại Giáo viên đang khóa đáp án và lời giải chi tiết. Khi Giáo viên mở khóa, bạn hãy tải lại trang để xem lời giải nhé!")
        else:
            st.subheader("📖 Đáp án & Lời giải chi tiết")
            for idx, q in enumerate(p1):
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge">Phần I - Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(q["stem"], unsafe_allow_html=True)
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
                    st.markdown(q["stem"], unsafe_allow_html=True)
                    for st_i in q["statements"]:
                        sid = f"{q['id']}_s{st_i['id']}"
                        u_tf = saved_answers.get(sid, "Chưa chọn")
                        corr_tf = "Đúng" if st_i["is_true"] else "Sai"
                        icon = "✅" if u_tf == corr_tf else "❌"
                        st.markdown(f"{icon} {st_i['text']} — **Đáp án: {corr_tf}** *(Bạn chọn: {u_tf})*", unsafe_allow_html=True)
                    if q.get("solution"):
                        st.markdown(f'<div class="solution-box">\n\n📖 **Lời giải chi tiết:**\n\n{q["solution"]}\n\n</div>', unsafe_allow_html=True)

            for idx, q in enumerate(p3):
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:#d97706;">Phần III - Câu {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(q["stem"], unsafe_allow_html=True)
                    u_sa = saved_answers.get(q["id"], "Chưa điền")
                    st.write(f"🔑 **Đáp số đúng:** `{q['short_ans']}` | **Bạn điền:** `{u_sa}`")
                    if q.get("solution"):
                        st.markdown(f'<div class="solution-box">\n\n📖 **Lời giải chi tiết:**\n\n{q["solution"]}\n\n</div>', unsafe_allow_html=True)

            for idx, q in enumerate(p4):
                with st.container(border=True):
                    st.markdown(f'<span class="q-badge" style="background:#047857;">Phần IV (Tự luận) - Bài {idx+1}</span>', unsafe_allow_html=True)
                    st.markdown(q["stem"], unsafe_allow_html=True)
                    u_es = saved_answers.get(q["id"], "Chưa trình bày")
                    st.info(f"**Bài làm của bạn:**\n\n{u_es}")
                    if q.get("solution"):
                        st.markdown(f'<div class="solution-box">\n\n📖 **Lời giải chuẩn:**\n\n{q["solution"]}\n\n</div>', unsafe_allow_html=True)
