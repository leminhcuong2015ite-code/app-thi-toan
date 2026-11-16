import re
import os
import base64
import hashlib
import subprocess
import tempfile
import shutil
import urllib.request

_TIKZ_CACHE = {}

# Tự động tải các file .sty lẻ cần thiết (nhẹ vài chục KB) mà không cần cài texlive-latex-extra 1.5GB
_EXTRA_FILES = {
    "tkz-tab.sty": "https://mirrors.ctan.org/macros/latex/contrib/tkz/tkz-tab/latex/tkz-tab.sty",
}
for fname, url in _EXTRA_FILES.items():
    fpath = f"/tmp/{fname}"
    if not os.path.exists(fpath):
        try:
            urllib.request.urlretrieve(url, fpath)
        except Exception:
            pass


def extract_braced_args(text, start_pos, num_args):
    r"""Tách chính xác các cặp ngoặc nhọn {...} có lồng nhau trong LaTeX"""
    args = []
    pos = start_pos
    n = len(text)
    for _ in range(num_args):
        while pos < n and text[pos].isspace():
            pos += 1
        if pos < n and text[pos] == '[':
            bracket_depth = 0
            while pos < n:
                if text[pos] == '[':
                    bracket_depth += 1
                elif text[pos] == ']':
                    bracket_depth -= 1
                    if bracket_depth == 0:
                        pos += 1
                        break
                pos += 1
            while pos < n and text[pos].isspace():
                pos += 1
        while pos < n and text[pos] == '%':
            nl = text.find('\n', pos)
            pos = nl + 1 if nl != -1 else n
            while pos < n and text[pos].isspace():
                pos += 1
        if pos >= n or text[pos] != '{':
            break
        depth = 0
        arg_start = pos + 1
        while pos < n:
            if text[pos] == '\\':
                pos += 2
                continue
            if text[pos] == '{':
                depth += 1
            elif text[pos] == '}':
                depth -= 1
                if depth == 0:
                    args.append(text[arg_start:pos].strip())
                    pos += 1
                    break
            pos += 1
    return args, pos


def compile_tikz_to_svg(tikz_code):
    r"""Biên dịch TikZ sang SVG dùng lớp article chuẩn + dvisvgm cắt sát viền (không cần standalone.cls)"""
    code_hash = hashlib.md5(tikz_code.encode("utf-8")).hexdigest()
    if code_hash in _TIKZ_CACHE:
        return _TIKZ_CACHE[code_hash]

    if not shutil.which("latex"):
        return '<div style="padding:10px;background:#fff3cd;border:1px solid #ffecb5;border-radius:6px;">⚠️ Máy chủ đang thiếu bộ biên dịch LaTeX.</div>'

    tikz_code_fixed = tikz_code.replace(r'\vec', r'\overrightarrow')

    use_tkz_tab = ("tkzTab" in tikz_code_fixed) and os.path.exists("/tmp/tkz-tab.sty")
    extra_pkg = r"\usepackage{tkz-tab}" if use_tkz_tab else ""

    # Dùng \documentclass{article} mặc định luôn có sẵn trong texlive-latex-base
    tex_doc = (
        r"\documentclass[11pt]{article}" + "\n"
        r"\usepackage[utf8]{vietnam}" + "\n"
        r"\usepackage{amsmath,amssymb,amsfonts}" + "\n"
        r"\usepackage{tikz}" + "\n"
        + extra_pkg + "\n"
        r"\usetikzlibrary{arrows,arrows.meta,calc,intersections,shapes.geometric,patterns,positioning,angles,quotes,decorations.markings,decorations.pathreplacing}" + "\n"
        r"\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}" + "\n"
        r"\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}" + "\n"
        r"\pagestyle{empty}" + "\n"
        r"\begin{document}" + "\n"
        r"\noindent" + "\n"
        + tikz_code_fixed + "\n"
        r"\end{document}"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        if use_tkz_tab:
            shutil.copy("/tmp/tkz-tab.sty", os.path.join(tmpdir, "tkz-tab.sty"))

        tex_file = os.path.join(tmpdir, "fig.tex")
        dvi_file = os.path.join(tmpdir, "fig.dvi")
        pdf_file = os.path.join(tmpdir, "fig.pdf")
        svg_file = os.path.join(tmpdir, "fig.svg")
        log_file = os.path.join(tmpdir, "fig.log")

        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(tex_doc)
        try:
            # Ưu tiên 1: Dùng latex -> dvisvgm (cắt sát khung hình chuẩn xác bằng --bbox=min, nhúng thẳng font)
            if shutil.which("dvisvgm"):
                subprocess.run(
                    ["latex", "-interaction=nonstopmode", "fig.tex"],
                    cwd=tmpdir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=20
                )
                if os.path.exists(dvi_file):
                    subprocess.run(
                        ["dvisvgm", "--no-fonts", "--bbox=min", "--scale=1.25", dvi_file, "-o", svg_file],
                        cwd=tmpdir,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=15
                    )

            # Ưu tiên 2 (Dự phòng): Nếu dvisvgm chưa tạo được file, dùng pdflatex + pdf2svg
            if not os.path.exists(svg_file) and shutil.which("pdflatex") and shutil.which("pdf2svg"):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "fig.tex"],
                    cwd=tmpdir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=20
                )
                if os.path.exists(pdf_file):
                    subprocess.run(["pdf2svg", pdf_file, svg_file], cwd=tmpdir, check=True, timeout=10)

            if os.path.exists(svg_file):
                with open(svg_file, "rb") as f:
                    b64_svg = base64.b64encode(f.read()).decode("utf-8")
                res_html = (
                    f'<div style="text-align:center; margin: 12px 0;">'
                    f'<img src="data:image/svg+xml;base64,{b64_svg}" '
                    f'style="max-width:100%; height:auto; background:white; padding:10px; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,0.08);" />'
                    f'</div>'
                )
                _TIKZ_CACHE[code_hash] = res_html
                return res_html
            else:
                err_lines = []
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as lf:
                        for line in lf:
                            if line.startswith("!"):
                                err_lines.append(line.strip())
                err_msg = " | ".join(err_lines[:2]) if err_lines else "Không rõ nguyên nhân"
                return f'<div style="color:#b91c1c;background:#fef2f2;padding:8px;border-radius:6px;font-size:13px;">⚠️ Lỗi biên dịch TikZ: <code>{err_msg}</code></div>'
        except Exception as e:
            return f'<div style="color:red;font-size:13px;">Lỗi hệ thống khi vẽ TikZ: {e}</div>'


def unwrap_immini(text):
    r"""Tách cấu trúc immini của gói ex_test"""
    pattern = re.compile(r'\\immini(?![a-zA-Z])')
    search_pos = 0
    while True:
        m = pattern.search(text, search_pos)
        if not m:
            break
        args, end_pos = extract_braced_args(text, m.end(), 2)
        if len(args) < 2:
            search_pos = m.end()
            continue
        combined = args[0] + "\n\n" + args[1]
        text = text[:m.start()] + combined + text[end_pos:]
        search_pos = m.start() + len(combined)
    return text


def replace_macro_one_arg(text, macro_name, prefix, suffix):
    r"""Thay thế các macro có 1 đối số (an toàn, không lặp vô tận)"""
    pattern = re.compile(r'\\' + macro_name + r'(?![a-zA-Z])')
    search_pos = 0
    while True:
        m = pattern.search(text, search_pos)
        if not m:
            break
        args, end_pos = extract_braced_args(text, m.end(), 1)
        if not args:
            search_pos = m.end()
            continue
        inner = args[0]
        if macro_name in ('heva', 'hoac'):
            inner = re.sub(r'&\s*', '', inner)
        replacement = prefix + inner + suffix
        text = text[:m.start()] + replacement + text[end_pos:]
        search_pos = m.start() + len(replacement)
    return text


def normalize_math_internals(math_str):
    r"""Làm sạch các lệnh bên trong môi trường toán học để MathJax hiển thị 100%"""
    math_str = re.sub(r'\\(allowdisplaybreaks|displaystyle|limits|nolimits)\b', '', math_str)
    math_str = math_str.replace('{,}', ',')
    math_str = math_str.replace(r'\mathrm{~d}', r'\,\mathrm{d}')
    math_str = math_str.replace('~', r'\,')
    math_str = re.sub(r'\\tg\b', r'\\tan', math_str)
    math_str = re.sub(r'\\cotg\b', r'\\cot', math_str)
    math_str = re.sub(r'\\arctg\b', r'\\arctan', math_str)
    math_str = re.sub(r'\\arccotg\b', r'\\operatorname{arccot}', math_str)
    math_str = re.sub(r'\\wideparen\s*\{', r'\\widehat{', math_str)
    math_str = re.sub(r'\\vec\b', r'\\overrightarrow', math_str)
    math_str = replace_macro_one_arg(math_str, 'heva', r'\left\{\begin{aligned}', r'\end{aligned}\right.')
    math_str = replace_macro_one_arg(math_str, 'hoac', r'\left[\begin{aligned}', r'\end{aligned}\right.')
    math_str = re.sub(r'\\begin\{(eqnarray\*|eqnarray|align\*|align)\}', r'\\begin{aligned}', math_str)
    math_str = re.sub(r'\\end\{(eqnarray\*|eqnarray|align\*|align)\}', r'\\end{aligned}', math_str)
    return math_str


def clean_latex_to_markdown(text):
    r"""Chuẩn hóa toàn bộ cú pháp LaTeX sang Markdown + MathJax hoàn chỉnh"""
    if not text:
        return ""

    text = unwrap_immini(text)

    tikz_pattern = re.compile(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', re.DOTALL)
    tikz_placeholders = {}

    def _tikz_repl(match):
        code = match.group(0)
        key = f"@@TIKZ_{hashlib.md5(code.encode()).hexdigest()}@@"
        tikz_placeholders[key] = compile_tikz_to_svg(code)
        return key

    text = tikz_pattern.sub(_tikz_repl, text)

    text = re.sub(r'\\begin\{center\}|\\end\{center\}', '', text)
    text = re.sub(r'\\noindent|\\par\b|\\allowdisplaybreaks', '', text)

    for env in ['aligned', 'align*', 'align', 'eqnarray*', 'eqnarray', 'gather*', 'gather']:
        esc_env = re.escape(env)
        text = re.sub(
            r'(?<!\$\$)\s*\\begin\{' + esc_env + r'\}(.*?)\\end\{' + esc_env + r'\}\s*(?!\$\$)',
            r'\n$$\n\\begin{aligned}\1\\end{aligned}\n$$\n',
            text,
            flags=re.DOTALL
        )

    text = re.sub(r'\\\[(.*?)\\\]', r'\n$$\1$$\n', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)

    if r'\begin{itemchoice}' in text:
        text = text.replace(r'\begin{itemchoice}', '').replace(r'\end{itemchoice}', '')
        parts = re.split(r'\\itemch\b', text)
        labels = ['a)', 'b)', 'c)', 'd)']
        new_text = parts[0]
        for idx, p in enumerate(parts[1:]):
            lbl = labels[idx] if idx < 4 else f"{idx+1})"
            new_text += f"\n\n- **{lbl}** {p.strip()}"
        text = new_text

    text = re.sub(r'\\begin\{(enumerate|itemize)\}(\[.*?\])?', '', text)
    text = re.sub(r'\\end\{(enumerate|itemize)\}', '', text)
    text = re.sub(r'\\item\b', '\n- ', text)

    text = replace_macro_one_arg(text, 'textbf', '**', '**')
    text = replace_macro_one_arg(text, 'textit', '*', '*')
    text = replace_macro_one_arg(text, 'underline', '<u>', '</u>')

    math_blocks = {}

    def _save_display_math(m):
        k = f"@@DMATH_{len(math_blocks)}@@"
        inner = normalize_math_internals(m.group(1))
        math_blocks[k] = f"\n$$\n{inner.strip()}\n$$\n"
        return k

    def _save_inline_math(m):
        k = f"@@IMATH_{len(math_blocks)}@@"
        inner = normalize_math_internals(m.group(1))
        math_blocks[k] = f"${inner.strip()}$"
        return k

    text = re.sub(r'\$\$(.*?)\$\$', _save_display_math, text, flags=re.DOTALL)
    text = re.sub(r'\$(?!\$)(.*?)\$', _save_inline_math, text, flags=re.DOTALL)

    text = text.replace('{,}', ',').replace('~', ' ')
    text = re.sub(r'\\\\(\s*\[.*?\])?', '  \n', text)
    text = text.replace(r'\%', '%').replace(r'\&', '&')

    for k, val in math_blocks.items():
        text = text.replace(k, val)

    for key, svg_html in tikz_placeholders.items():
        text = text.replace(key, f"\n\n{svg_html}\n\n")

    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_single_ex(ex_body, index):
    r"""Phân tích 1 khối ex"""
    loigiai_raw = ""
    lg_match = re.search(r'\\loigiai\s*\{', ex_body)
    if lg_match:
        lg_args, lg_end = extract_braced_args(ex_body, lg_match.end() - 1, 1)
        if lg_args:
            loigiai_raw = lg_args[0]
            ex_body = ex_body[:lg_match.start()] + ex_body[lg_end:]

    tf_match = re.search(r'\\choiceTF(?![a-zA-Z])', ex_body)
    if tf_match:
        stem_raw = ex_body[:tf_match.start()]
        opts_raw, _ = extract_braced_args(ex_body, tf_match.end(), 4)
        statements = []
        for idx, opt in enumerate(opts_raw):
            is_true = bool(re.search(r'\\True\b', opt))
            clean_opt = re.sub(r'\\True\b', '', opt).strip()
            statements.append({
                "id": idx,
                "text": clean_latex_to_markdown(clean_opt),
                "is_true": is_true
            })
        return {
            "id": f"q_{index}",
            "part": 2,
            "stem": clean_latex_to_markdown(stem_raw),
            "statements": statements,
            "solution": clean_latex_to_markdown(loigiai_raw)
        }

    mc_match = re.search(r'\\(choice|motcot|haicot|boncot)(?![a-zA-Z])', ex_body)
    if mc_match:
        stem_raw = ex_body[:mc_match.start()]
        opts_raw, _ = extract_braced_args(ex_body, mc_match.end(), 4)
        options = []
        for idx, opt in enumerate(opts_raw):
            is_true = bool(re.search(r'\\True\b', opt))
            clean_opt = re.sub(r'\\True\b', '', opt).strip()
            options.append({
                "id": idx,
                "text": clean_latex_to_markdown(clean_opt),
                "is_true": is_true
            })
        return {
            "id": f"q_{index}",
            "part": 1,
            "stem": clean_latex_to_markdown(stem_raw),
            "options": options,
            "solution": clean_latex_to_markdown(loigiai_raw)
        }

    sa_match = re.search(r'\\shortans\s*(\[.*?\])?\s*\{', ex_body)
    if sa_match:
        brace_pos = ex_body.find('{', sa_match.start())
        sa_args, sa_end = extract_braced_args(ex_body, brace_pos, 1)
        ans_raw = sa_args[0] if sa_args else ""
        ans_clean = ans_raw.replace('$', '').replace('{,}', ',').replace('.', ',').strip()
        stem_raw = ex_body[:sa_match.start()] + ex_body[sa_end:]
        return {
            "id": f"q_{index}",
            "part": 3,
            "stem": clean_latex_to_markdown(stem_raw),
            "short_ans": ans_clean,
            "solution": clean_latex_to_markdown(loigiai_raw)
        }

    return None


def parse_exam_tex(tex_content):
    r"""Đọc toàn bộ file .tex và trả về danh sách câu hỏi"""
    tex_content = re.sub(r'(?<!\\)%.*', '', tex_content)
    ex_blocks = re.findall(r'\\begin\{ex\}(.*?)\\end\{ex\}', tex_content, flags=re.DOTALL)
    questions = []
    for idx, block in enumerate(ex_blocks):
        parsed = parse_single_ex(block, idx + 1)
        if parsed:
            questions.append(parsed)
    return questions
