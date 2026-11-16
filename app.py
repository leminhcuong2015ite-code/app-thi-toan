import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client
import pandas as pd
import random
import datetime
import re
from latex_parser import parse_exam_tex
from kntt_mapping import KNTT_DATA, LEVEL_MAP

st.set_page_config(page_title="Hệ thống Kiểm tra Trực tuyến", layout="wide")

# ================= CSS TÙY CHỈNH GIAO DIỆN CHUYÊN NGHIỆP =================
st.markdown("""
<style>
div[role="radiogroup"] > label {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    width: 100%;
    transition: all 0.15s ease;
    cursor: pointer;
}
div[role="radiogroup"] > label:hover {
    background-color: #eff6ff;
    border-color: #3b82f6;
}
.q-header {
    background-color: #e0f2fe;
    color: #0369a1;
    padding: 5px 12px;
    border-radius: 6px;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 8px;
}
.tag-badge {
    background-color: #f1f5f9;
    color: #334155;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 8px;
    border: 1px solid #cbd5e1;
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

# ================= HÀM HỖ TRỢ CHẤM ĐIỂM, ĐẢO ĐỀ & THỐNG KÊ =================
def extract_grade_from_class(class_name):
    m = re.match(r'^(\d+)', str(class_name).strip())
    return m.group(1) if m else "12"

def get_shuffled_exam(questions, seed):
    rng = random.Random(seed)
    p1 = [q.copy() for q in questions if q["part"] == 1]
    p2 = [q.copy() for q in questions if q["part"] == 2]
    p3 = [q.copy() for q in questions if q["part"] == 3]

    rng.shuffle(p1)
    rng.shuffle(p2)
    rng.shuffle(p3)

    for q in p1:
        opts = [o.copy() for o in q["options"]]
        rng.shuffle(opts)
        q["shuffled_options"] = opts

    return p1, p2, p3

def grade_exam(questions, answers, seed, scoring_cfg=None):
    if not scoring_cfg:
        scoring_cfg = {"p1": 0.25, "p2": 1.0, "p3": 0.5}
    pt_p1 = float(scoring_cfg.get("p1", 0.25))
    pt_p2_max = float(scoring_cfg.get("p2", 1.0))
    pt_p3 = float(scoring_cfg.get("p3", 0.5))

    p1, p2, p3 = get_shuffled_exam(questions, seed)
    score_p1, score_p2, score_p3 = 0.0, 0.0, 0.0

    for q in p1:
        qid = q["id"]
        user_choice_id = answers.get(qid)
        for opt in q["options"]:
            if opt["is_true"] and str(opt["id"]) == str(user_choice_id):
                score_p1 += pt_p1

    tf_ratios = {0: 0.0, 1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}
    for q in p2:
        qid = q["id"]
        correct_count = 0
        for st_item in q["statements"]:
            sid = f"{qid}_s{st_item['id']}"
            user_tf = answers.get(sid)
            expected = "Đúng" if st_item["is_true"] else "Sai"
            if user_tf == expected:
                correct_count += 1
        score_p2 += pt_p2_max * tf_ratios.get(correct_count, 0.0)

    for q in p3:
        qid = q["id"]
        user_ans = str(answers.get(qid, "")).strip().replace(".", ",")
        correct_ans = str(q["short_ans"]).strip().replace(".", ",")
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
        part = q["part"]
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

    analysis_list.sort(key=lambda x: x["Tỷ lệ sai (%)"], reverse=True)
    return analysis_list

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
    <div style="display:flex; align-items:center; justify-content:space-between; background:#1e293b; color:white; padding:10px 18px; border-radius:8px; font-family:sans-serif;">
        <div>
            <span style="font-size:15px;">⏱️ Thời gian còn lại: </span>
            <b id="timer" style="font-size:20px; color:#38bdf8;">--:--</b>
            <span id="warn_badge" style="margin-left:15px; background:#ef4444; padding:4px 8px; border-radius:4px; font-size:13px; display:none;">
                ⚠️ Rời màn hình: <span id="tab_count">0</span> lần
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:12px; color:#94a3b8;" id="cam_status">🟢 Camera giám sát trực tuyến đang hoạt động</span>
            <video id="webcam" autoplay playsinline muted width="85" height="64" style="border-radius:6px; border:2px solid #22c55e; object-fit:cover;"></video>
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
    components.html(html_code, height=105)

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
# PHÂN HỆ 1: GIAO DIỆN GIÁO VIÊN
# =====================================================================
if st.session_state.role == "teacher":
    st.title("👨‍🏫 Bảng Điều Khiển Giáo Viên")
    t_bank, t_exam, t_stu, t_res = st.tabs([
        "🏦 1. Ngân hàng Câu hỏi & Trộn đề (KNTT)",
        "📄 2. Tạo đề nhanh & Quản lý Đề thi",
        "👥 3. Quản lý Học sinh theo Lớp",
        "📊 4. Bảng điểm, Giám sát & Thống kê câu sai"
    ])

    # -----------------------------------------------------------------
    # TAB 1: NGÂN HÀNG CÂU HỎI & TRỘN ĐỀ MA TRẬN (SÁCH KẾT NỐI TRI THỨC)
    # -----------------------------------------------------------------
    with t_bank:
        st.subheader("📥 Nạp câu hỏi từ file LaTeX vào Ngân hàng")
        st.info("💡 Các câu hỏi có gắn mã `%[12-C4-B11-V]` từ Skill Gemini sẽ được tự động phân vào đúng Khối, Chương, Bài và Mức độ.")

        c_def_g, c_def_c = st.columns([1, 2])
        fb_grade = c_def_g.selectbox("Khối mặc định (nếu câu hỏi thiếu mã ID)", ["12", "11", "10", "9", "8", "7", "6"], key="fb_g")
        fb_chaps = KNTT_DATA[fb_grade]["chapters"]
        fb_chap_code = c_def_c.selectbox("Chương mặc định (nếu thiếu mã ID)", list(fb_chaps.keys()), format_func=lambda k: fb_chaps[k], key="fb_c")

        bank_tex_file = st.file_uploader("Chọn file .tex chứa danh sách câu hỏi để nạp vào Ngân hàng", type=["tex"], key="bank_up")
        if bank_tex_file:
            raw_bank_tex = bank_tex_file.read().decode("utf-8")
            with st.spinner("Đang biên dịch LaTeX/TikZ và nhận diện mã ID Kết nối tri thức..."):
                parsed_bank_qs = parse_exam_tex(raw_bank_tex)

            st.success(f"✅ Đã phân tích thành công **{len(parsed_bank_qs)} câu hỏi**!")
            preview_rows = []
            for idx, q in enumerate(parsed_bank_qs):
                if q["tag_id"] == "Chưa gắn mã":
                    q["grade"] = fb_grade
                    q["chapter_code"] = fb_chap_code
                    q["chapter_name"] = fb_chaps[fb_chap_code]
                preview_rows.append({
                    "STT": idx + 1,
                    "Mã ID": q["tag_id"],
                    "Khối": q["grade"],
                    "Chương": q["chapter_name"],
                    "Bài học": q["lesson_name"],
                    "Mức độ": q["level_name"],
                    "Dạng thức": f"Phần {q['part']}"
                })
            st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

            if st.button("📥 Lưu toàn bộ vào Ngân hàng câu hỏi", type="primary"):
                db_records = []
                for q in parsed_bank_qs:
                    db_records.append({
                        "tag_id": q["tag_id"],
                        "grade": q["grade"],
                        "chapter_code": q["chapter_code"],
                        "chapter_name": q["chapter_name"],
                        "lesson_code": q["lesson_code"],
                        "lesson_name": q["lesson_name"],
                        "level_code": q["level_code"],
                        "level_name": q["level_name"],
                        "part": q["part"],
                        "question_data": q,
                        "raw_tex": q.get("raw_tex", ""),
                        "question_hash": q["question_hash"]
                    })
                supabase.table("question_bank").upsert(db_records, on_conflict="question_hash").execute()
                st.success(f"🎉 Đã nạp {len(db_records)} câu hỏi vào Ngân hàng thành công!")
                st.rerun()

        st.divider()
        st.subheader("🎲 Rút câu hỏi & Trộn đề thi từ Ngân hàng (Theo Ma trận)")

        f_col1, f_col2, f_col3 = st.columns([1, 2, 2])
        sel_g = f_col1.selectbox("1. Chọn Khối", ["12", "11", "10", "9", "8", "7", "6"], key="mat_g")
        avail_chaps = KNTT_DATA[sel_g]["chapters"]
        sel_c = f_col2.selectbox("2. Chọn Chương", list(avail_chaps.keys()), format_func=lambda k: avail_chaps[k], key="mat_c")

        # Lọc danh sách bài học thuộc chương đã chọn
        chap_lessons = {b_k: b_v[1] for b_k, b_v in KNTT_DATA[sel_g]["lessons"].items() if b_v[0] == sel_c}
        sel_lessons = f_col3.multiselect(
            "3. Lọc theo Bài học (Để trống = Lấy cả chương)",
            options=list(chap_lessons.keys()),
            format_func=lambda k: chap_lessons[k]
        )

        # Truy vấn ngân hàng câu hỏi theo bộ lọc
        q_query = supabase.table("question_bank").select("*").eq("grade", sel_g).eq("chapter_code", sel_c).execute().data
        if sel_lessons:
            q_query = [item for item in q_query if item["lesson_code"] in sel_lessons]

        if not q_query:
            st.warning("Chưa có câu hỏi nào trong Ngân hàng thuộc Chương/Bài này. Hãy nạp file .tex ở phía trên trước nhé!")
        else:
            st.write(f"📊 **Số lượng câu hỏi hiện có trong kho theo bộ lọc ({len(q_query)} câu):**")
            # Thống kê số câu hiện có theo Phần x Mức độ
            matrix_counts = {p: {"N": [], "H": [], "V": [], "C": []} for p in [1, 2, 3]}
            for item in q_query:
                p_val = item["part"]
                l_val = item["level_code"] if item["level_code"] in ["N", "H", "V", "C"] else "N"
                if p_val in matrix_counts:
                    matrix_counts[p_val][l_val].append(item)

            stat_df = pd.DataFrame([
                {
                    "Dạng câu hỏi": "Phần I (Trắc nghiệm ABCD)",
                    "Nhận biết (N)": len(matrix_counts[1]["N"]),
                    "Thông hiểu (H)": len(matrix_counts[1]["H"]),
                    "Vận dụng (V)": len(matrix_counts[1]["V"]),
                    "Vận dụng cao (C)": len(matrix_counts[1]["C"])
                },
                {
                    "Dạng câu hỏi": "Phần II (Đúng / Sai)",
                    "Nhận biết (N)": len(matrix_counts[2]["N"]),
                    "Thông hiểu (H)": len(matrix_counts[2]["H"]),
                    "Vận dụng (V)": len(matrix_counts[2]["V"]),
                    "Vận dụng cao (C)": len(matrix_counts[2]["C"])
                },
                {
                    "Dạng câu hỏi": "Phần III (Trả lời ngắn)",
                    "Nhận biết (N)": len(matrix_counts[3]["N"]),
                    "Thông hiểu (H)": len(matrix_counts[3]["H"]),
                    "Vận dụng (V)": len(matrix_counts[3]["V"]),
                    "Vận dụng cao (C)": len(matrix_counts[3]["C"])
                }
            ])
            st.dataframe(stat_df, use_container_width=True, hide_index=True)

            st.markdown("#### 🎯 Nhập số lượng câu muốn bốc ngẫu nhiên cho đề thi:")
            picked_Config = {}
            part_names = {1: "Phần I (ABCD)", 2: "Phần II (Đúng/Sai)", 3: "Phần III (Trả lời ngắn)"}
            for p_idx in [1, 2, 3]:
                st.markdown(f"**{part_names[p_idx]}:**")
                mc1, mc2, mc3, mc4 = st.columns(4)
                max_n = len(matrix_counts[p_idx]["N"])
                max_h = len(matrix_counts[p_idx]["H"])
                max_v = len(matrix_counts[p_idx]["V"])
                max_c = len(matrix_counts[p_idx]["C"])
                picked_Config[(p_idx, "N")] = mc1.number_input(f"Nhận biết (Tối đa {max_n})", 0, max_n, 0, key=f"pk_{p_idx}_N")
                picked_Config[(p_idx, "H")] = mc2.number_input(f"Thông hiểu (Tối đa {max_h})", 0, max_h, 0, key=f"pk_{p_idx}_H")
                picked_Config[(p_idx, "V")] = mc3.number_input(f"Vận dụng (Tối đa {max_v})", 0, max_v, 0, key=f"pk_{p_idx}_V")
                picked_Config[(p_idx, "C")] = mc4.number_input(f"Vận dụng cao (Tối đa {max_c})", 0, max_c, 0, key=f"pk_{p_idx}_C")

            st.markdown("#### ⚙️ Thông tin Đề thi & Thang điểm:")
            mt1, mt2 = st.columns([3, 1])
            mat_title = mt1.text_input("Tên đề thi mới", placeholder="VD: Kiểm tra 45 phút - Nguyên hàm & Tích phân")
            mat_dur = mt2.number_input("Thời gian (phút)", 5, 180, 45, key="mat_dur")

            ms1, ms2, ms3 = st.columns(3)
            m_pt1 = ms1.number_input("Điểm mỗi câu Phần I", 0.0, 10.0, 0.25, 0.05, key="m_pt1")
            m_pt2 = ms2.number_input("Điểm tối đa mỗi câu Phần II", 0.0, 10.0, 1.0, 0.25, key="m_pt2")
            m_pt3 = ms3.number_input("Điểm mỗi câu Phần III", 0.0, 10.0, 0.5, 0.1, key="m_pt3")

            if st.button("🚀 Rút câu hỏi ngẫu nhiên & Xuất bản Đề Thi", type="primary"):
                selected_qs = []
                for p_idx in [1, 2, 3]:
                    for lvl in ["N", "H", "V", "C"]:
                        need_cnt = picked_Config[(p_idx, lvl)]
                        if need_cnt > 0:
                            pool = matrix_counts[p_idx][lvl]
                            chosen_items = random.sample(pool, need_cnt)
                            for item in chosen_items:
                                q_copy = item["question_data"].copy()
                                q_copy["id"] = f"q_{len(selected_qs) + 1}"
                                selected_qs.append(q_copy)

                if not selected_qs:
                    st.warning("Bạn chưa chọn số lượng câu hỏi nào (> 0) ở ma trận trên!")
                elif not mat_title:
                    st.warning("Vui lòng nhập Tên đề thi mới!")
                else:
                    supabase.table("exams").insert({
                        "title": mat_title.strip(),
                        "grade": sel_g,
                        "chapter": avail_chaps[sel_c],
                        "duration": mat_dur,
                        "questions": selected_qs,
                        "scoring_config": {"p1": m_pt1, "p2": m_pt2, "p3": m_pt3},
                        "show_solutions": False,
                        "is_active": True
                    }).execute()
                    st.success(f"🎉 Đã trộn và xuất bản đề thi **{mat_title}** gồm {len(selected_qs)} câu hỏi thành công!")

            with st.expander("🔍 Xem chi tiết / Xóa từng câu hỏi trong Ngân hàng"):
                for item in q_query:
                    qd = item["question_data"]
                    c_q, c_del = st.columns([6, 1])
                    c_q.markdown(
                        f"**#{item['id']}** `<{item['tag_id']}>` — **{item['lesson_name']}** "
                        f"*(Phần {item['part']} - {item['level_name']})*"
                    )
                    c_q.markdown(qd["stem"], unsafe_allow_html=True)
                    if c_del.button("🗑️ Xóa", key=f"del_qb_{item['id']}"):
                        supabase.table("question_bank").delete().eq("id", item["id"]).execute()
                        st.rerun()
                    st.divider()

    # -----------------------------------------------------------------
    # TAB 2: TẠO ĐỀ TRỰC TIẾP TỪ FILE .TEX & DANH SÁCH ĐỀ THI
    # -----------------------------------------------------------------
    with t_exam:
        st.subheader("Tải lên trực tiếp 1 đề thi hoàn chỉnh (.tex)")
        c_grade, c_chap = st.columns([1, 2])
        grade_sel = c_grade.selectbox("Chọn Khối lớp áp dụng", ["12", "11", "10", "9", "8", "7", "6"])
        chap_dict = KNTT_DATA[grade_sel]["chapters"]
        chapter_sel = c_chap.selectbox("Chọn Chương (SGK Kết nối tri thức)", list(chap_dict.values()))

        c_title, c_dur = st.columns([3, 1])
        exam_title = c_title.text_input("Tên bài kiểm tra", placeholder="VD: Đề kiểm tra giữa kỳ 2 - Đề số 01")
        duration = c_dur.number_input("Thời gian (phút)", min_value=5, max_value=180, value=45)

        st.markdown("**⚖️ Thiết lập thang điểm cho từng phần:**")
        sc1, sc2, sc3 = st.columns(3)
        pt_p1 = sc1.number_input("Điểm mỗi câu Phần I (ABCD)", min_value=0.0, max_value=10.0, value=0.25, step=0.05)
        pt_p2 = sc2.number_input("Điểm tối đa mỗi câu Phần II (Đúng/Sai)", min_value=0.0, max_value=10.0, value=1.0, step=0.25)
        pt_p3 = sc3.number_input("Điểm mỗi câu Phần III (Trả lời ngắn)", min_value=0.0, max_value=10.0, value=0.5, step=0.1)

        tex_file = st.file_uploader("Chọn file .tex của bạn", type=["tex"])

        if tex_file:
            raw_tex = tex_file.read().decode("utf-8")
            with st.spinner("Đang phân tích cấu trúc LaTeX và biên dịch hình vẽ TikZ..."):
                parsed_questions = parse_exam_tex(raw_tex)

            p1_cnt = sum(1 for q in parsed_questions if q["part"] == 1)
            p2_cnt = sum(1 for q in parsed_questions if q["part"] == 2)
            p3_cnt = sum(1 for q in parsed_questions if q["part"] == 3)
            total_max_score = round(p1_cnt * pt_p1 + p2_cnt * pt_p2 + p3_cnt * pt_p3, 2)

            st.success(
                f"✅ Đã đọc **{len(parsed_questions)} câu hỏi**: Phần I ({p1_cnt} câu × {pt_p1}đ), "
                f"Phần II ({p2_cnt} câu × {pt_p2}đ), Phần III ({p3_cnt} câu × {pt_p3}đ) $\\rightarrow$ **Tổng điểm tối đa: {total_max_score} điểm**."
            )

            with st.expander("👁️ Xem trước đề thi & lời giải sau khi biên dịch"):
                for idx, q in enumerate(parsed_questions):
                    st.markdown(f"**Câu {idx+1} (Phần {q['part']} - Mã: `{q.get('tag_id', '')}` - {q.get('level_name', '')}):**")
                    st.markdown(q["stem"], unsafe_allow_html=True)
                    if q["part"] == 1:
                        for opt in q["options"]:
                            prefix = "✅" if opt["is_true"] else "⚪"
                            st.markdown(f"{prefix} {opt['text']}", unsafe_allow_html=True)
                    elif q["part"] == 2:
                        for st_i in q["statements"]:
                            ans_str = "Đúng" if st_i["is_true"] else "Sai"
                            st.markdown(f"- ({ans_str}) {st_i['text']}", unsafe_allow_html=True)
                    elif q["part"] == 3:
                        st.markdown(f"🔑 **Đáp số:** `{q['short_ans']}`")
                    st.markdown("*Lời giải:*")
                    st.markdown(q["solution"], unsafe_allow_html=True)
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
                        "scoring_config": {"p1": pt_p1, "p2": pt_p2, "p3": pt_p3},
                        "show_solutions": False,
                        "is_active": True
                    }).execute()
                    st.success("🎉 Đã tạo đề thi thành công!")
                    st.rerun()

        st.divider()
        st.subheader("📚 Mục lục Đề thi theo Khối & Chương")
        exams_data = supabase.table("exams").select("id, title, grade, chapter, duration, show_solutions, is_active").order("grade", desc=True).order("chapter").order("id", desc=True).execute().data
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
                            c1.write(f"**#{ex['id']} - {ex['title']}** ({ex['duration']}p)")
                            show_sol = c2.toggle("Mở lời giải", value=ex["show_solutions"], key=f"sol_{ex['id']}")
                            is_act = c3.toggle("Mở phòng thi", value=ex["is_active"], key=f"act_{ex['id']}")
                            if show_sol != ex["show_solutions"] or is_act != ex["is_active"]:
                                supabase.table("exams").update({"show_solutions": show_sol, "is_active": is_act}).eq("id", ex["id"]).execute()
                                st.rerun()
                            if c4.button("🗑️ Xóa", key=f"del_{ex['id']}"):
                                supabase.table("exams").delete().eq("id", ex["id"]).execute()
                                st.rerun()

    # -----------------------------------------------------------------
    # TAB 3: QUẢN LÝ HỌC SINH THEO LỚP
    # -----------------------------------------------------------------
    with t_stu:
        st.subheader("1. Nhập danh sách lớp từ Excel / CSV")
        st.info("File Excel/CSV cần có 4 cột: `Họ tên`, `Lớp` (VD: 12A1, 11B2), `Tài khoản`, `Mật khẩu`")

        sample_df = pd.DataFrame([
            {"Họ tên": "Nguyễn Văn An", "Lớp": "12A1", "Tài khoản": "12a1_01", "Mật khẩu": "123"},
            {"Họ tên": "Trần Thị Bình", "Lớp": "12A1", "Tài khoản": "12a1_02", "Mật khẩu": "123"},
            {"Họ tên": "Lê Hoàng Cường", "Lớp": "11A2", "Tài khoản": "11a2_01", "Mật khẩu": "123"}
        ])
        st.download_button("📥 Tải file CSV mẫu", sample_df.to_csv(index=False).encode("utf-8-sig"), "danh_sach_lop_mau.csv", "text/csv")

        stu_file = st.file_uploader("Chọn file Excel (.xlsx) hoặc CSV (.csv)", type=["xlsx", "csv"])
        if stu_file:
            df = pd.read_csv(stu_file) if stu_file.name.endswith(".csv") else pd.read_excel(stu_file)
            st.dataframe(df.head())
            if st.button("➕ Nhập toàn bộ danh sách vào hệ thống", type="primary"):
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "full_name": str(row["Họ tên"]).strip(),
                        "class_name": str(row["Lớp"]).strip().upper(),
                        "username": str(row["Tài khoản"]).strip(),
                        "password": str(row["Mật khẩu"]).strip()
                    })
                supabase.table("students").upsert(records).execute()
                st.success(f"Đã cập nhật {len(records)} tài khoản học sinh!")
                st.rerun()

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
    # TAB 4: BẢNG ĐIỂM, GIÁM SÁT CAMERA & THỐNG KÊ TỶ LỆ LÀM SAI TỪNG CÂU
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
                    "📷 3. Giám sát Camera & Cho phép thi lại"
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
                                st.markdown("**Nội dung câu hỏi:**")
                                st.markdown(q_obj["stem"], unsafe_allow_html=True)
                                if q_obj["part"] == 1:
                                    orig_lbl = ["A", "B", "C", "D"]
                                    for o_i, opt in enumerate(q_obj["options"]):
                                        ic = "✅" if opt["is_true"] else "⚪"
                                        st.markdown(f"{ic} **{orig_lbl[o_i]}.** {opt['text']}", unsafe_allow_html=True)
                                elif q_obj["part"] == 2:
                                    for st_i in q_obj["statements"]:
                                        ans_s = "Đúng" if st_i["is_true"] else "Sai"
                                        st.markdown(f"- **({ans_s})** {st_i['text']}", unsafe_allow_html=True)
                                elif q_obj["part"] == 3:
                                    st.markdown(f"🔑 **Đáp số đúng:** `{q_obj['short_ans']}`")
                                st.markdown("---")
                                st.markdown("**Lời giải chi tiết:**")
                                st.markdown(q_obj["solution"], unsafe_allow_html=True)

                with sub_tab3:
                    chosen_sub = st.selectbox(
                        "Chọn học sinh cần kiểm tra",
                        subs,
                        format_func=lambda x: f"{x['username']} - {(x.get('students') or {}).get('full_name', '')} (Lớp {(x.get('students') or {}).get('class_name', '')} | Rời màn hình: {x['tab_switches']} lần)"
                    )
                    if chosen_sub:
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
# PHÂN HỆ 2: GIAO DIỆN HỌC SINH LÀM BÀI
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
        sc_cfg = exam.get("scoring_config") or {"p1": 0.25, "p2": 1.0, "p3": 0.5}
        st.markdown(f"""
        ### 📋 Thông tin bài kiểm tra: **{exam['title']}**
        - **Khối / Chuyên đề:** Khối {stu_grade} — {chosen_chap}
        - **Thời gian làm bài:** {exam['duration']} phút (Hệ thống tự động thu bài khi hết giờ).
        - **Thang điểm:** Phần I: `{sc_cfg.get('p1', 0.25)}đ`/câu | Phần II: tối đa `{sc_cfg.get('p2', 1.0)}đ`/câu | Phần III: `{sc_cfg.get('p3', 0.5)}đ`/câu.
        - **Quy định giám sát:** Vui lòng cấp quyền Camera khi được hỏi và không rời khỏi màn hình làm bài.
        """)
        if st.button("🚀 BẮT ĐẦU LÀM BÀI", type="primary"):
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
    scoring_cfg = exam.get("scoring_config") or {"p1": 0.25, "p2": 1.0, "p3": 0.5}
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

        p1, p2, p3 = get_shuffled_exam(questions, seed)
        current_answers = saved_answers.copy()

        def auto_save():
            supabase.table("submissions").update({"answers": current_answers}).eq("id", submission["id"]).execute()

        if p1:
            st.markdown(f"### PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn ({scoring_cfg.get('p1', 0.25)} điểm/câu)")
            for idx, q in enumerate(p1):
                qid = q["id"]
                st.markdown(f'<div class="q-header">Câu {idx+1}</div>', unsafe_allow_html=True)
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
                st.divider()

        if p2:
            st.markdown(f"### PHẦN II. Câu trắc nghiệm đúng sai (Tối đa {scoring_cfg.get('p2', 1.0)} điểm/câu)")
            for idx, q in enumerate(p2):
                qid = q["id"]
                st.markdown(f'<div class="q-header">Câu {idx+1}</div>', unsafe_allow_html=True)
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
                st.divider()

        if p3:
            st.markdown(f"### PHẦN III. Câu trắc nghiệm trả lời ngắn ({scoring_cfg.get('p3', 0.5)} điểm/câu)")
            for idx, q in enumerate(p3):
                qid = q["id"]
                st.markdown(f'<div class="q-header">Câu {idx+1}</div>', unsafe_allow_html=True)
                st.markdown(q["stem"], unsafe_allow_html=True)

                with st.container(border=True):
                    c_lbl, c_inp = st.columns([1.5, 3.5])
                    c_lbl.markdown("**✍️ Nhập đáp số:**")
                    prev_short = current_answers.get(qid, "")
                    ans_text = c_inp.text_input(
                        f"Đáp số Câu {idx+1}",
                        value=prev_short,
                        placeholder="Nhập kết quả (dùng dấu phẩy cho số thập phân, VD: 4,5)",
                        key=f"ui_{qid}",
                        label_visibility="collapsed"
                    )
                    if ans_text != "":
                        current_answers[qid] = ans_text.strip()
                st.divider()

        if current_answers != saved_answers:
            auto_save()

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
        p1, p2, p3 = get_shuffled_exam(questions, seed)
        max_total = round(len(p1) * scoring_cfg.get("p1", 0.25) + len(p2) * scoring_cfg.get("p2", 1.0) + len(p3) * scoring_cfg.get("p3", 0.5), 2)

        st.success(f"🎉 Bạn đã hoàn thành bài kiểm tra! Tổng điểm của bạn: **{total} / {max_total} điểm**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Phần I (Trắc nghiệm ABCD)", f"{s1} điểm")
        c2.metric("Phần II (Đúng / Sai)", f"{s2} điểm")
        c3.metric("Phần III (Trả lời ngắn)", f"{s3} điểm")

        st.markdown("#### 💡 Nhận xét & Đánh giá kết quả:")
        st.info(generate_feedback(total, s1, s2, s3, len(p1), len(p2), len(p3), scoring_cfg))

        if not exam["show_solutions"]:
            st.warning("🔒 Hiện tại Giáo viên đang khóa đáp án và lời giải chi tiết. Khi Giáo viên mở khóa, bạn hãy tải lại trang để xem lời giải nhé!")
        else:
            st.subheader("📖 Đáp án & Lời giải chi tiết")
            for idx, q in enumerate(p1):
                st.markdown(f"**Phần I - Câu {idx+1}:**", unsafe_allow_html=True)
                st.markdown(q["stem"], unsafe_allow_html=True)
                user_c = str(saved_answers.get(q["id"]))
                for opt in q["shuffled_options"]:
                    is_u = (str(opt["id"]) == user_c)
                    badge = " 👈 *(Bạn chọn)*" if is_u else ""
                    icon = "✅" if opt["is_true"] else ("❌" if is_u else "⚪")
                    st.markdown(f"{icon} {opt['text']}{badge}", unsafe_allow_html=True)
                with st.expander("Xem lời giải chi tiết"):
                    st.markdown(q["solution"], unsafe_allow_html=True)
                st.divider()

            for idx, q in enumerate(p2):
                st.markdown(f"**Phần II - Câu {idx+1}:**", unsafe_allow_html=True)
                st.markdown(q["stem"], unsafe_allow_html=True)
                for st_i in q["statements"]:
                    sid = f"{q['id']}_s{st_i['id']}"
                    u_tf = saved_answers.get(sid, "Chưa chọn")
                    corr_tf = "Đúng" if st_i["is_true"] else "Sai"
                    icon = "✅" if u_tf == corr_tf else "❌"
                    st.markdown(f"{icon} {st_i['text']} — **Đáp án: {corr_tf}** *(Bạn chọn: {u_tf})*", unsafe_allow_html=True)
                with st.expander("Xem lời giải chi tiết"):
                    st.markdown(q["solution"], unsafe_allow_html=True)
                st.divider()

            for idx, q in enumerate(p3):
                st.markdown(f"**Phần III - Câu {idx+1}:**", unsafe_allow_html=True)
                st.markdown(q["stem"], unsafe_allow_html=True)
                u_sa = saved_answers.get(q["id"], "Chưa điền")
                st.write(f"🔑 **Đáp số đúng:** `{q['short_ans']}` | **Bạn điền:** `{u_sa}`")
                with st.expander("Xem lời giải chi tiết"):
                    st.markdown(q["solution"], unsafe_allow_html=True)
                st.divider()
