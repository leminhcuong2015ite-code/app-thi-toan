import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client
import pandas as pd
import random
import datetime
from latex_parser import parse_exam_tex

st.set_page_config(page_title="Hệ thống Kiểm tra Trực tuyến", layout="wide")

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

# ================= HÀM HỖ TRỢ CHẤM ĐIỂM & ĐẢO ĐỀ =================
def get_shuffled_exam(questions, seed):
    """Đảo câu hỏi trong từng phần và đảo phương án ABCD dựa theo seed cố định của HS"""
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

def grade_exam(questions, answers, seed):
    """Chấm điểm theo chuẩn cấu trúc mới (Phần I: 0.25đ, Phần II: lũy tiến 0.1->1.0đ, Phần III: 0.5đ)"""
    p1, p2, p3 = get_shuffled_exam(questions, seed)
    score_p1, score_p2, score_p3 = 0.0, 0.0, 0.0

    # Chấm Phần I
    for q in p1:
        qid = q["id"]
        user_choice_id = answers.get(qid)
        for opt in q["options"]:
            if opt["is_true"] and str(opt["id"]) == str(user_choice_id):
                score_p1 += 0.25

    # Chấm Phần II (4 ý Đúng/Sai)
    tf_points = {0: 0.0, 1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}
    for q in p2:
        qid = q["id"]
        correct_count = 0
        for st_item in q["statements"]:
            sid = f"{qid}_s{st_item['id']}"
            user_tf = answers.get(sid)
            expected = "Đúng" if st_item["is_true"] else "Sai"
            if user_tf == expected:
                correct_count += 1
        score_p2 += tf_points.get(correct_count, 0.0)

    # Chấm Phần III (Trả lời ngắn)
    for q in p3:
        qid = q["id"]
        user_ans = str(answers.get(qid, "")).strip().replace(".", ",")
        correct_ans = str(q["short_ans"]).strip().replace(".", ",")
        if user_ans != "" and user_ans == correct_ans:
            score_p3 += 0.5

    total = round(score_p1 + score_p2 + score_p3, 2)
    return total, score_p1, score_p2, score_p3

def generate_feedback(total, s1, s2, s3, n1, n2, n3):
    """Nhận xét tự động không tốn API Key"""
    comments = []
    if total >= 8.5:
        comments.append("🌟 **Đánh giá chung:** Nắm rất vững kiến thức và kỹ năng vận dụng giải toán.")
    elif total >= 6.5:
        comments.append("👍 **Đánh giá chung:** Nắm được kiến thức cơ bản nhưng cần cẩn thận hơn ở các câu vận dụng.")
    else:
        comments.append("⚠️ **Đánh giá chung:** Cần ôn tập lại các công thức nền tảng và rèn luyện thêm kỹ năng tính toán.")

    if n1 > 0 and s1 < (n1 * 0.25 * 0.7):
        comments.append("- **Phần I (Trắc nghiệm ABCD):** Còn sai nhiều ở các câu nhận biết/thông hiểu công thức cơ bản.")
    if n2 > 0 and s2 < (n2 * 1.0 * 0.6):
        comments.append("- **Phần II (Đúng/Sai):** Chưa đạt điểm tối đa ở các mệnh đề tổng hợp, cần đọc kỹ từng ý a, b, c, d.")
    if n3 > 0 and s3 < (n3 * 0.5 * 0.5):
        comments.append("- **Phần III (Trả lời ngắn):** Cần rèn luyện thêm kỹ năng giải toán thực tế và làm tròn số chính xác.")
    return "\n".join(comments)

# ================= COMPONENT GIÁM SÁT (WEBCAM 5 PHÚT & ĐẾM GIỜ & CHỐNG CHUYỂN TAB) =================
def render_proctor_bar(remaining_seconds, supabase_url, supabase_key, submission_id):
    """Nhúng đồng hồ đếm ngược, cảnh báo chuyển tab và tự động chụp webcam mỗi 5 phút gửi thẳng về Supabase"""
    html_code = f"""
    <div style="display:flex; align-items:center; justify-content:space-between; background:#1e293b; color:white; padding:10px 18px; border-radius:8px; font-family:sans-serif;">
        <div>
            <span style="font-size:15px;">⏱️ Thời gian còn lại: </span>
            <b id="timer" style="font-size:20px; color:#38bdf8;">--:--</b>
            <span id="warn_badge" style="margin-left:15px; background:#ef4444; padding:4px 8px; border-radius:4px; font-size:13px; display:none;">
                ⚠️ Chuyển tab: <span id="tab_count">0</span> lần
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:12px; color:#94a3b8;" id="cam_status">📷 Camera giám sát: Đang bật (tự động lưu mỗi 5 phút)</span>
            <video id="webcam" autoplay playsinline muted width="85" height="64" style="border-radius:6px; border:2px solid #22c55e; object-fit:cover;"></video>
            <canvas id="canvas" width="320" height="240" style="display:none;"></canvas>
        </div>
    </div>

    <script>
    const SUPABASE_URL = "{supabase_url}";
    const SUPABASE_KEY = "{supabase_key}";
    const SUB_ID = {submission_id};
    let timeLeft = {int(remaining_seconds)};
    let tabSwitches = 0;
    let snapshots = [];

    // 1. Lấy dữ liệu hiện tại từ Supabase
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

    // 2. Cập nhật lên Supabase
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

    // 3. Đồng hồ đếm ngược
    const timerEl = document.getElementById("timer");
    const countdown = setInterval(() => {{
        if (timeLeft <= 0) {{
            clearInterval(countdown);
            timerEl.innerText = "00:00 (HẾT GIỜ)";
            timerEl.style.color = "#ef4444";
            // Tự động bấm nút Nộp bài trên giao diện Streamlit
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
        timeLeft--;
    }}, 1000);

    // 4. Phát hiện chuyển Tab / Thu nhỏ cửa sổ
    document.addEventListener("visibilitychange", () => {{
        if (document.hidden) {{
            tabSwitches++;
            document.getElementById("warn_badge").style.display = "inline-block";
            document.getElementById("tab_count").innerText = tabSwitches;
            updateSupabaseProctor({{ tab_switches: tabSwitches }});
            alert("⚠️ CẢNH BÁO: Hệ thống vừa ghi nhận bạn rời khỏi màn hình làm bài! (Lần thứ " + tabSwitches + ")");
        }}
    }});

    // 5. Khởi tạo Webcam & Chụp tự động mỗi 5 phút (300.000 ms)
    const video = document.getElementById("webcam");
    const canvas = document.getElementById("canvas");
    const camStatus = document.getElementById("cam_status");

    navigator.mediaDevices.getUserMedia({{ video: true, audio: false }})
        .then(stream => {{
            video.srcObject = stream;
            // Chụp tấm đầu tiên sau 5 giây khi vừa vào thi
            setTimeout(captureFrame, 5000);
            // Sau đó cứ mỗi 5 phút (300000ms) chụp 1 lần
            setInterval(captureFrame, 300000);
        }})
        .catch(err => {{
            camStatus.innerText = "❌ Không tìm thấy Camera hoặc bị từ chối quyền!";
            camStatus.style.color = "#ef4444";
        }});

    function captureFrame() {{
        if (!video.srcObject) return;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL("image/jpeg", 0.55); // Nén nhẹ JPEG để lưu nhanh
        const nowStr = new Date().toLocaleTimeString("vi-VN");
        snapshots.push({{ time: nowStr, img: dataUrl }});
        updateSupabaseProctor({{ snapshots: snapshots }});
        camStatus.innerText = "📷 Đã chụp tự động lúc " + nowStr;
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

# Nút Đăng xuất ở Sidebar
with st.sidebar:
    if st.session_state.role == "student":
        st.write(f"👤 Học sinh: **{st.session_state.user['full_name']}**")
        st.write(f"🏫 Lớp: **{st.session_state.user['class_name']}**")
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
    t1, t2, t3 = st.tabs(["📄 1. Tạo đề thi từ LaTeX", "👥 2. Quản lý Học sinh (Excel/CSV)", "📊 3. Kết quả & Giám sát Camera"])

    # --- TAB 1: UPLOAD LATEX ---
    with t1:
        st.subheader("Tải lên file đề thi LaTeX (cấu trúc ex_test)")
        exam_title = st.text_input("Tên bài kiểm tra", placeholder="VD: Kiểm tra 45 phút - Nguyên hàm, Tích phân & Oxyz")
        duration = st.number_input("Thời gian làm bài (phút)", min_value=5, max_value=180, value=45)
        tex_file = st.file_uploader("Chọn file .tex của bạn", type=["tex"])

        if tex_file:
            raw_tex = tex_file.read().decode("utf-8")
            with st.spinner("Đang phân tích cấu trúc LaTeX và biên dịch hình vẽ TikZ..."):
                parsed_questions = parse_exam_tex(raw_tex)

            p1_cnt = sum(1 for q in parsed_questions if q["part"] == 1)
            p2_cnt = sum(1 for q in parsed_questions if q["part"] == 2)
            p3_cnt = sum(1 for q in parsed_questions if q["part"] == 3)
            st.success(f"✅ Đã đọc thành công **{len(parsed_questions)} câu hỏi**: Phần I ({p1_cnt} câu), Phần II ({p2_cnt} câu), Phần III ({p3_cnt} câu).")

            with st.expander("👁️ Xem trước đề thi & hình vẽ TikZ sau khi biên dịch"):
                for idx, q in enumerate(parsed_questions):
                    st.markdown(f"**Câu {idx+1} (Phần {q['part']}):**")
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
                    st.divider()

            if st.button("💾 Lưu và Xuất bản Đề Thi", type="primary"):
                if not exam_title:
                    st.warning("Vui lòng nhập Tên bài kiểm tra!")
                else:
                    supabase.table("exams").insert({
                        "title": exam_title,
                        "duration": duration,
                        "questions": parsed_questions,
                        "show_solutions": False,
                        "is_active": True
                    }).execute()
                    st.success("🎉 Đã tạo đề thi thành công! Học sinh có thể đăng nhập để làm bài.")

        st.divider()
        st.subheader("Danh sách đề thi đã tạo")
        exams_data = supabase.table("exams").select("id, title, duration, show_solutions, is_active, created_at").order("id", desc=True).execute().data
        for ex in exams_data:
            c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
            c1.write(f"**#{ex['id']} - {ex['title']}** ({ex['duration']} phút)")
            show_sol = c2.toggle("Mở lời giải cho HS", value=ex["show_solutions"], key=f"sol_{ex['id']}")
            is_act = c3.toggle("Cho phép thi", value=ex["is_active"], key=f"act_{ex['id']}")
            if show_sol != ex["show_solutions"] or is_act != ex["is_active"]:
                supabase.table("exams").update({"show_solutions": show_sol, "is_active": is_act}).eq("id", ex["id"]).execute()
                st.rerun()
            if c4.button("🗑️ Xóa đề", key=f"del_{ex['id']}"):
                supabase.table("exams").delete().eq("id", ex["id"]).execute()
                st.rerun()

    # --- TAB 2: QUẢN LÝ HỌC SINH ---
    with t2:
        st.subheader("Tải lên danh sách lớp (Excel / CSV)")
        st.info("File Excel/CSV cần có 4 cột: `Họ tên`, `Lớp`, `Tài khoản`, `Mật khẩu`")
        
        sample_df = pd.DataFrame([
            {"Họ tên": "Nguyễn Văn An", "Lớp": "12A1", "Tài khoản": "hs01", "Mật khẩu": "123"},
            {"Họ tên": "Trần Thị Bình", "Lớp": "12A1", "Tài khoản": "hs02", "Mật khẩu": "123"}
        ])
        st.download_button("📥 Tải file CSV mẫu", sample_df.to_csv(index=False).encode("utf-8-sig"), "danh_sach_mau.csv", "text/csv")

        stu_file = st.file_uploader("Chọn file Excel (.xlsx) hoặc CSV (.csv)", type=["xlsx", "csv"])
        if stu_file:
            df = pd.read_csv(stu_file) if stu_file.name.endswith(".csv") else pd.read_excel(stu_file)
            st.dataframe(df.head())
            if st.button("➕ Nhập toàn bộ học sinh vào hệ thống", type="primary"):
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "full_name": str(row["Họ tên"]).strip(),
                        "class_name": str(row["Lớp"]).strip(),
                        "username": str(row["Tài khoản"]).strip(),
                        "password": str(row["Mật khẩu"]).strip()
                    })
                supabase.table("students").upsert(records).execute()
                st.success(f"Đã cập nhật {len(records)} tài khoản học sinh!")

        st.divider()
        all_stu = supabase.table("students").select("*").execute().data
        if all_stu:
            st.write(f"Tổng số học sinh hiện có: **{len(all_stu)}**")
            st.dataframe(pd.DataFrame(all_stu))

    # --- TAB 3: KẾT QUẢ & GIÁM SÁT CAMERA ---
    with t3:
        st.subheader("Bảng điểm & Hình ảnh Giám sát")
        exams_list = supabase.table("exams").select("id, title").order("id", desc=True).execute().data
        if not exams_list:
            st.info("Chưa có đề thi nào.")
        else:
            selected_exam = st.selectbox("Chọn đề thi để xem kết quả", exams_list, format_func=lambda x: f"#{x['id']} - {x['title']}")
            subs = supabase.table("submissions").select("*, students(full_name, class_name)").eq("exam_id", selected_exam["id"]).execute().data

            if not subs:
                st.warning("Chưa có học sinh nào làm đề này.")
            else:
                rows = []
                for s in subs:
                    stu_info = s.get("students") or {}
                    rows.append({
                        "ID Phiên": s["id"],
                        "Tài khoản": s["username"],
                        "Họ tên": stu_info.get("full_name", ""),
                        "Lớp": stu_info.get("class_name", ""),
                        "Trạng thái": "Đã nộp" if s["status"] == "submitted" else "Đang làm",
                        "Điểm số": s["score"],
                        "Số lần chuyển Tab": s["tab_switches"],
                        "Số ảnh Camera": len(s.get("snapshots") or [])
                    })
                df_res = pd.DataFrame(rows)
                st.dataframe(df_res, use_container_width=True)
                st.download_button("📥 Xuất bảng điểm ra Excel (CSV)", df_res.to_csv(index=False).encode("utf-8-sig"), "bang_diem.csv", "text/csv")

                st.divider()
                st.subheader("🔍 Xem ảnh chụp Camera 5 phút/lần của từng học sinh")
                chosen_sub = st.selectbox("Chọn học sinh cần kiểm tra", subs, format_func=lambda x: f"{x['username']} - {(x.get('students') or {}).get('full_name', '')} (Chuyển tab: {x['tab_switches']} lần)")
                if chosen_sub:
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
    active_exams = supabase.table("exams").select("*").eq("is_active", True).order("id", desc=True).execute().data

    if not active_exams:
        st.info("Hiện tại chưa có bài kiểm tra nào đang mở.")
        st.stop()

    exam = st.selectbox("📌 Chọn bài kiểm tra:", active_exams, format_func=lambda x: f"{x['title']} ({x['duration']} phút)")
    
    # Kiểm tra phiên làm bài trong DB (Hỗ trợ làm tiếp nếu rớt mạng)
    sub_res = supabase.table("submissions").select("*").eq("exam_id", exam["id"]).eq("username", stu["username"]).execute().data

    if not sub_res:
        st.markdown(f"""
        ### 📋 Quy định phòng thi: **{exam['title']}**
        - **Thời gian làm bài:** {exam['duration']} phút (Hệ thống tự động thu bài khi hết giờ).
        - **Giám sát Camera:** Trình duyệt sẽ yêu cầu quyền truy cập Camera và tự động ghi hình mỗi 5 phút.
        - **Chống gian lận:** Mọi hành vi chuyển tab hoặc thu nhỏ màn hình đều bị cảnh báo và ghi nhận vào hồ sơ.
        - **An toàn kết nối:** Nếu rớt mạng hoặc lỡ bấm tải lại trang, đáp án đã lưu vẫn được giữ nguyên để làm tiếp.
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
    seed = submission["seed"]
    saved_answers = submission.get("answers") or {}

    # Tính thời gian còn lại
    started_at = datetime.datetime.fromisoformat(submission["started_at"].replace("Z", "+00:00"))
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    elapsed_sec = (now_utc - started_at).total_seconds()
    remaining_sec = (exam["duration"] * 60) - elapsed_sec

    # Nếu đã hết giờ mà trạng thái vẫn là in_progress -> Tự động chấm và khóa bài
    if submission["status"] == "in_progress" and remaining_sec <= 0:
        total_score, _, _, _ = grade_exam(questions, saved_answers, seed)
        supabase.table("submissions").update({
            "status": "submitted",
            "score": total_score,
            "submitted_at": now_utc.isoformat()
        }).eq("id", submission["id"]).execute()
        st.rerun()

    # ---------------- TRƯỜNG HỢP 1: ĐANG LÀM BÀI ----------------
    if submission["status"] == "in_progress":
        render_proctor_bar(
            remaining_sec,
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
            submission["id"]
        )

        p1, p2, p3 = get_shuffled_exam(questions, seed)
        current_answers = saved_answers.copy()

        def auto_save():
            """Lưu tạm đáp án ngay khi học sinh vừa bấm chọn (chống rớt mạng)"""
            supabase.table("submissions").update({"answers": current_answers}).eq("id", submission["id"]).execute()

        # Hiển thị Phần I
        if p1:
            st.markdown("### PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn")
            for idx, q in enumerate(p1):
                qid = q["id"]
                st.markdown(f"**Câu {idx+1}.**", unsafe_allow_html=True)
                st.markdown(q["stem"], unsafe_allow_html=True)
                opts = q["shuffled_options"]
                labels = ["A", "B", "C", "D"]
                opt_ids = [str(o["id"]) for o in opts]
                
                for lbl, o in zip(labels, opts):
                    st.markdown(f"**{lbl}.** {o['text']}", unsafe_allow_html=True)

                default_idx = opt_ids.index(str(current_answers[qid])) if str(current_answers.get(qid)) in opt_ids else None
                choice = st.radio(
                    f"Chọn đáp án Câu {idx+1}:",
                    options=opt_ids,
                    index=default_idx,
                    format_func=lambda x, opt_ids=opt_ids, labels=labels: f"Phương án {labels[opt_ids.index(x)]}",
                    horizontal=True,
                    key=f"ui_{qid}"
                )
                if choice is not None:
                    current_answers[qid] = choice
                st.divider()

        # Hiển thị Phần II
        if p2:
            st.markdown("### PHẦN II. Câu trắc nghiệm đúng sai")
            for idx, q in enumerate(p2):
                qid = q["id"]
                st.markdown(f"**Câu {idx+1}.**", unsafe_allow_html=True)
                st.markdown(q["stem"], unsafe_allow_html=True)
                st_labels = ["a)", "b)", "c)", "d)"]
                for s_idx, st_item in enumerate(q["statements"]):
                    sid = f"{qid}_s{st_item['id']}"
                    c_text, c_radio = st.columns([4, 2])
                    c_text.markdown(f"**{st_labels[s_idx]}** {st_item['text']}", unsafe_allow_html=True)
                    prev_val = current_answers.get(sid)
                    r_idx = ["Đúng", "Sai"].index(prev_val) if prev_val in ["Đúng", "Sai"] else None
                    val = c_radio.radio(
                        f"Chọn {st_labels[s_idx]}",
                        options=["Đúng", "Sai"],
                        index=r_idx,
                        horizontal=True,
                        key=f"ui_{sid}",
                        label_visibility="collapsed"
                    )
                    if val is not None:
                        current_answers[sid] = val
                st.divider()

        # Hiển thị Phần III
        if p3:
            st.markdown("### PHẦN III. Câu trắc nghiệm trả lời ngắn")
            for idx, q in enumerate(p3):
                qid = q["id"]
                st.markdown(f"**Câu {idx+1}.**", unsafe_allow_html=True)
                st.markdown(q["stem"], unsafe_allow_html=True)
                prev_short = current_answers.get(qid, "")
                ans_text = st.text_input(f"Điền đáp số Câu {idx+1} (dùng dấu phẩy cho số thập phân, VD: 4,5):", value=prev_short, key=f"ui_{qid}")
                if ans_text != "":
                    current_answers[qid] = ans_text.strip()
                st.divider()

        # Tự động lưu nếu có thay đổi đáp án
        if current_answers != saved_answers:
            auto_save()

        col_save, col_sub = st.columns(2)
        if col_save.button("💾 Lưu bài làm tạm thời"):
            auto_save()
            st.toast("✅ Đã lưu đáp án an toàn lên đám mây!")

        if col_sub.button("📤 NỘP BÀI HOÀN TẤT", type="primary"):
            total_score, _, _, _ = grade_exam(questions, current_answers, seed)
            supabase.table("submissions").update({
                "answers": current_answers,
                "status": "submitted",
                "score": total_score,
                "submitted_at": now_utc.isoformat()
            }).eq("id", submission["id"]).execute()
            st.rerun()

    # ---------------- TRƯỜNG HỢP 2: ĐÃ NỘP BÀI ----------------
    else:
        total, s1, s2, s3 = grade_exam(questions, saved_answers, seed)
        p1, p2, p3 = get_shuffled_exam(questions, seed)
        st.success(f"🎉 Bạn đã hoàn thành bài kiểm tra! Tổng điểm của bạn: **{total} / 10 điểm**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Phần I (Trắc nghiệm ABCD)", f"{s1} điểm")
        c2.metric("Phần II (Đúng / Sai)", f"{s2} điểm")
        c3.metric("Phần III (Trả lời ngắn)", f"{s3} điểm")

        st.markdown("#### 💡 Nhận xét & Đánh giá kết quả:")
        st.info(generate_feedback(total, s1, s2, s3, len(p1), len(p2), len(p3)))

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