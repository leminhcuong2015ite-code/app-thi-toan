import re
import os
import base64
import hashlib
import subprocess
import tempfile
import shutil
import urllib.request
from kntt_mapping import decode_kntt_tag

PARSER_VERSION = "V5.1 - Fix lq/rq Quotes & Support Tự Luận (bt/ex)"

_TKZ_TAB_PATH = "/tmp/tkz-tab.sty"
if not os.path.exists(_TKZ_TAB_PATH):
    try:
        urllib.request.urlretrieve(
            "https://mirrors.ctan.org/macros/latex/contrib/tkz/tkz-tab/latex/tkz-tab.sty",
            _TKZ_TAB_PATH
        )
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


def compile_latex_snippet_to_svg(latex_snippet):
    r"""Biên dịch TikZ bằng pdflatex + tự động co khổ giấy PDF vừa khít hình vẽ + pdf2svg"""
    if not shutil.which("pdflatex") or not shutil.which("pdf2svg"):
        return '<div style="padding:10px;background:#fff3cd;border:1px solid #ffecb5;border-radius:6px;">⚠️ Máy chủ đang thiếu pdflatex hoặc pdf2svg.</div>'

    snippet_fixed = latex_snippet
    snippet_fixed = re.sub(r'\\(vec|vv)\b', r'\\overrightarrow', snippet_fixed)
    snippet_fixed = snippet_fixed.replace(r'\ch@p', 'black')
    snippet_fixed = re.sub(r'\\lq\s*\\lq\s*', '``', snippet_fixed)
    snippet_fixed = re.sub(r'\\rq\s*\\rq\s*', "''", snippet_fixed)
    snippet_fixed = re.sub(r'\\lq\b\s*', '`', snippet_fixed)
    snippet_fixed = re.sub(r'\\rq\b\s*', "'", snippet_fixed)

    extra_pkg = r"\usepackage{tkz-tab}" if ("tkzTab" in snippet_fixed and os.path.exists(_TKZ_TAB_PATH)) else ""

    tex_doc = (
        r"\documentclass[11pt]{article}" + "\n"
        r"\usepackage[utf8]{vietnam}" + "\n"
        r"\usepackage{amsmath,amssymb,amsfonts,xcolor,graphicx}" + "\n"
        r"\usepackage{tikz}" + "\n"
        + extra_pkg + "\n"
        r"\usetikzlibrary{shapes.geometric,arrows,calc,intersections,angles,patterns,snakes,positioning,arrows.meta,quotes,backgrounds,decorations,decorations.markings,decorations.pathreplacing,decorations.pathmorphing,shadows,matrix,fit}" + "\n"
        r"\def\tkzDrawXY{\tkzDrawX\tkzDrawY[>=latex]}" + "\n"
        r"\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}" + "\n"
        r"\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}" + "\n"
        r"\providecommand{\wideparen}[1]{\widehat{#1}}" + "\n"
        r"\providecommand{\mathscr}[1]{\mathcal{#1}}" + "\n"
        r"\providecommand{\lq}{`}" + "\n"
        r"\providecommand{\rq}{'}" + "\n"
        r"\providecommand{\R}{\mathbb{R}}" + "\n"
        r"\providecommand{\N}{\mathbb{N}}" + "\n"
        r"\providecommand{\Z}{\mathbb{Z}}" + "\n"
        r"\providecommand{\Q}{\mathbb{Q}}" + "\n"
        r"\providecommand{\C}{\mathbb{C}}" + "\n"
        r"\pagestyle{empty}" + "\n"
        r"\newsavebox{\mybox}" + "\n"
        r"\begin{document}" + "\n"
        r"\begin{lrbox}{\mybox}" + "\n"
        + snippet_fixed + "\n"
        r"\end{lrbox}" + "\n"
        r"\pdfpagewidth=\dimexpr\wd\mybox+12pt\relax" + "\n"
        r"\pdfpageheight=\dimexpr\ht\mybox+\dp\mybox+12pt\relax" + "\n"
        r"\hoffset=-1in" + "\n"
        r"\voffset=-1in" + "\n"
        r"\setlength{\topmargin}{0pt}" + "\n"
        r"\setlength{\headheight}{0pt}" + "\n"
        r"\setlength{\headsep}{0pt}" + "\n"
        r"\setlength{\oddsidemargin}{0pt}" + "\n"
        r"\setlength{\evensidemargin}{0pt}" + "\n"
        r"\setlength{\parindent}{0pt}" + "\n"
        r"\vbox to \pdfpageheight{\vfill\hbox to \pdfpagewidth{\hfill\usebox{\mybox}\hfill}\vfill}" + "\n"
        r"\end{document}"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        if os.path.exists(_TKZ_TAB_PATH):
            shutil.copy(_TKZ_TAB_PATH, os.path.join(tmpdir, "tkz-tab.sty"))

        tex_file = os.path.join(tmpdir, "fig.tex")
        pdf_file = os.path.join(tmpdir, "fig.pdf")
        svg_file = os.path.join(tmpdir, "fig.svg")
        log_file = os.path.join(tmpdir, "fig.log")

        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(tex_doc)
        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "fig.tex"],
                cwd=tmpdir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20
            )
            if os.path.exists(pdf_file):
                subprocess.run(["pdf2svg", pdf_file, svg_file], cwd=tmpdir, check=True, timeout=10)
                with open(svg_file, "rb") as f:
                    b64_svg = base64.b64encode(f.read()).decode("utf-8")
                return (
                    f'<div style="text-align:center; margin: 14px 0; overflow-x:auto;">'
                    f'<img src="data:image/svg+xml;base64,{b64_svg}" '
                    f'style="max-width:100%; height:auto; background:white; padding:10px; border-radius:10px; border:1px solid #e2e8f0; box-shadow:0 2px 6px rgba(0,0,0,0.05);" />'
                    f'</div>'
                )
            else:
                err_lines = []
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as lf:
                        for line in lf:
                            if line.startswith("!"):
                                err_lines.append(line.strip())
                err_msg = " | ".join(err_lines[:2]) if err_lines else "Không rõ nguyên nhân"
                return f'<div style="color:#b91c1c;background:#fef2f2;padding:8px;border-radius:6px;font-size:13px;">⚠️ Lỗi TikZ: <code>{err_msg}</code></div>'
        except Exception as e:
            return f'<div style="color:red;font-size:13px;">Lỗi hệ thống TikZ: {e}</div>'


def unwrap_immini(text):
    r"""Tách cấu trúc \immini và \immini[thm] của gói ex_test"""
    pattern = re.compile(r'\\immini(thm)?(?![a-zA-Z])')
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
    r"""Thay thế các macro có 1 đối số"""
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
            inner = re.sub(r'(\\\\)\s*$', '', inner.strip())
        replacement = prefix + inner + suffix
        text = text[:m.start()] + replacement + text[end_pos:]
        search_pos = m.start() + len(replacement)
    return text


def normalize_math_internals(math_str):
    r"""Chuẩn hóa mọi ký hiệu toán bên trong $...$ hoặc $$...$$ sang chuẩn MathJax"""
    math_str = re.sub(r'\\(allowdisplaybreaks|displaystyle|limits|nolimits|boldmath)\b', '', math_str)
    math_str = math_str.replace('{,}', ',')
    math_str = math_str.replace(r'\mathrm{~d}', r'\,\mathrm{d}')
    math_str = math_str.replace('~', r'\,')

    math_str = re.sub(r'\\vv\*?\s*\{', r'\\overrightarrow{', math_str)
    math_str = re.sub(r'\\vec\b', r'\\overrightarrow', math_str)
    math_str = re.sub(r'\\wideparen\s*\{', r'\\widehat{', math_str)
    math_str = re.sub(r'\\mathscr\s*\{', r'\\mathcal{', math_str)

    math_str = re.sub(r'\\tg\b', r'\\tan', math_str)
    math_str = re.sub(r'\\cotg\b', r'\\cot', math_str)
    math_str = re.sub(r'\\arctg\b', r'\\arctan', math_str)
    math_str = re.sub(r'\\arccotg\b', r'\\operatorname{arccot}', math_str)
    math_str = re.sub(r'\\R\b', r'\\mathbb{R}', math_str)
    math_str = re.sub(r'\\N\b', r'\\mathbb{N}', math_str)
    math_str = re.sub(r'\\Z\b', r'\\mathbb{Z}', math_str)
    math_str = re.sub(r'\\Q\b', r'\\mathbb{Q}', math_str)
    math_str = re.sub(r'\\C\b', r'\\mathbb{C}', math_str)

    for _ in range(3):
        math_str = replace_macro_one_arg(math_str, 'heva', r'\left\{\begin{aligned}', r'\end{aligned}\right.')
        math_str = replace_macro_one_arg(math_str, 'hoac', r'\left[\begin{aligned}', r'\end{aligned}\right.')

    math_str = re.sub(r'\\begin\{(eqnarray\*|eqnarray|align\*|align)\}', r'\\begin{aligned}', math_str)
    math_str = re.sub(r'\\end\{(eqnarray\*|eqnarray|align\*|align)\}', r'\\end{aligned}', math_str)
    return math_str


def clean_latex_to_markdown(text):
    r"""Chuẩn hóa toàn bộ cú pháp LaTeX sang Markdown + MathJax"""
    if not text:
        return ""

    text = text.replace('\t', ' ').replace('\xa0', ' ')
    text = "\n".join(line.strip() for line in text.splitlines())

    # Xử lý các dấu ngoặc kép \lq\lq và \rq\rq ngay từ đầu
    text = re.sub(r'\\lq\s*\\lq\s*', '"', text)
    text = re.sub(r'\\rq\s*\\rq\s*', '"', text)
    text = re.sub(r'\\lq\b\s*', "'", text)
    text = re.sub(r'\\rq\b\s*', "'", text)

    text = unwrap_immini(text)
    text = re.sub(r'\\begin\{multicols\}\{\d+\}|\\end\{multicols\}', '', text)

    visual_pattern = re.compile(
        r'\\begin\{(tikzpicture|tabular|tabularx|tabvar)\}.*?\\end\{\1\}',
        re.DOTALL
    )
    visual_placeholders = {}

    def _visual_repl(match):
        code = match.group(0)
        key = f"@@VISUAL_{len(visual_placeholders)}@@"
        visual_placeholders[key] = compile_latex_snippet_to_svg(code)
        return key

    text = visual_pattern.sub(_visual_repl, text)

    text = re.sub(r'\\begin\{(center|flushleft|flushright)\}|\\end\{(center|flushleft|flushright)\}', '', text)
    text = re.sub(r'\\(noindent|par|centering|leavevmode|vfill|hfill|newpage|clearpage)\b', '', text)
    text = re.sub(r'\\(vspace|hspace)\*?\{.*?\}', ' ', text)

    text = re.sub(r'\\\[(.*?)\\\]', r'\n$$\1$$\n', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)

    for env in ['aligned', 'align*', 'align', 'eqnarray*', 'eqnarray', 'gather*', 'gather']:
        esc_env = re.escape(env)
        text = re.sub(
            r'(?<!\$\$)\s*\\begin\{' + esc_env + r'\}(.*?)\\end\{' + esc_env + r'\}\s*(?!\$\$)',
            r'\n$$\n\\begin{aligned}\1\\end{aligned}\n$$\n',
            text,
            flags=re.DOTALL
        )

    if r'\begin{itemchoice}' in text:
        text = text.replace(r'\begin{itemchoice}', '').replace(r'\end{itemchoice}', '')
        parts = re.split(r'\\itemch\b', text)
        labels = ['a)', 'b)', 'c)', 'd)']
        new_text = parts[0].strip()
        for idx, p in enumerate(parts[1:]):
            lbl = labels[idx] if idx < 4 else f"{idx+1})"
            p_clean = " ".join(line.strip() for line in p.strip().splitlines() if line.strip())
            new_text += f"\n\n- **{lbl}** {p_clean}"
        text = new_text

    text = re.sub(r'\\begin\{(enumerate|itemize)\}(\[.*?\])?', '', text)
    text = re.sub(r'\\end\{(enumerate|itemize)\}', '', text)
    text = re.sub(r'\\item\b(\s*\[.*?\])?', '\n- ', text)

    for _ in range(2):
        text = replace_macro_one_arg(text, 'textbf', '**', '**')
        text = replace_macro_one_arg(text, 'indam', '**', '**')
        text = replace_macro_one_arg(text, 'textit', '*', '*')
        text = replace_macro_one_arg(text, 'innghieng', '*', '*')
        text = replace_macro_one_arg(text, 'emph', '*', '*')
        text = replace_macro_one_arg(text, 'underline', '<u>', '</u>')
        text = replace_macro_one_arg(text, 'fbox', '`', '`')

    math_blocks = {}

    def _save_display_math(m):
        k = f"@@DMATH_{len(math_blocks)}@@"
        inner = normalize_math_internals(m.group(1))
        inner_clean = "\n".join(line.strip() for line in inner.strip().splitlines() if line.strip())
        math_blocks[k] = f"\n\n$$\n{inner_clean}\n$$\n\n"
        return k

    def _save_inline_math(m):
        k = f"@@IMATH_{len(math_blocks)}@@"
        inner = normalize_math_internals(m.group(1))
        inner_single_line = " ".join(line.strip() for line in inner.strip().splitlines() if line.strip())
        math_blocks[k] = f"${inner_single_line}$"
        return k

    text = re.sub(r'\$\$(.*?)\$\$', _save_display_math, text, flags=re.DOTALL)
    text = re.sub(r'\$(?!\$)(.*?)\$', _save_inline_math, text, flags=re.DOTALL)

    if r'\heva' in text or r'\hoac' in text:
        text = replace_macro_one_arg(text, 'heva', r'$$\left\{\begin{aligned}', r'\end{aligned}\right.$$')
        text = replace_macro_one_arg(text, 'hoac', r'$$\left[\begin{aligned}', r'\end{aligned}\right.$$')

    text = text.replace('{,}', ',').replace('~', ' ')
    text = text.replace('``', '"').replace("''", '"')
    text = re.sub(r'\\\\(\s*\[.*?\])?', '\n\n', text)
    text = text.replace(r'\%', '%').replace(r'\&', '&')

    text = "\n".join(line.strip() for line in text.splitlines())

    for k, val in math_blocks.items():
        text = text.replace(k, val)

    for key, svg_html in visual_placeholders.items():
        text = text.replace(key, f"\n\n{svg_html}\n\n")

    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_single_block(block_body_with_comments, index, env_type="ex"):
    r"""Phân tích 1 khối ex hoặc bt kèm theo mã định danh KNTT %[12-C4-B11-V]"""
    first_line = block_body_with_comments.split('\n', 1)[0]
    meta = decode_kntt_tag(first_line)
    if not meta:
        meta = decode_kntt_tag(block_body_with_comments[:250])

    ex_body = re.sub(r'(?<!\\)%.*', '', block_body_with_comments)

    loigiai_raw = ""
    lg_match = re.search(r'\\loi?giai\s*\{', ex_body)
    if lg_match:
        lg_args, lg_end = extract_braced_args(ex_body, lg_match.end() - 1, 1)
        if lg_args:
            loigiai_raw = lg_args[0]
            ex_body = ex_body[:lg_match.start()] + ex_body[lg_end:]

    parsed_q = None

    tf_match = re.search(r'\\choiceTF(?![a-zA-Z])', ex_body)
    mc_match = re.search(r'\\(choice|motcot|haicot|boncot)(?![a-zA-Z])', ex_body)
    sa_match = re.search(r'\\shortans\s*(\[.*?\])?\s*\{', ex_body)

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
        parsed_q = {
            "id": f"q_{index}",
            "part": 2,
            "stem": clean_latex_to_markdown(stem_raw),
            "statements": statements,
            "solution": clean_latex_to_markdown(loigiai_raw)
        }

    elif mc_match:
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
        parsed_q = {
            "id": f"q_{index}",
            "part": 1,
            "stem": clean_latex_to_markdown(stem_raw),
            "options": options,
            "solution": clean_latex_to_markdown(loigiai_raw)
        }

    elif sa_match:
        brace_pos = ex_body.find('{', sa_match.start())
        sa_args, sa_end = extract_braced_args(ex_body, brace_pos, 1)
        ans_raw = sa_args[0] if sa_args else ""
        ans_clean = ans_raw.replace('$', '').replace('{,}', ',').replace('.', ',').strip()
        stem_raw = ex_body[:sa_match.start()] + ex_body[sa_end:]
        parsed_q = {
            "id": f"q_{index}",
            "part": 3,
            "stem": clean_latex_to_markdown(stem_raw),
            "short_ans": ans_clean,
            "solution": clean_latex_to_markdown(loigiai_raw)
        }

    else:
        stem_clean = clean_latex_to_markdown(ex_body)
        if stem_clean:
            parsed_q = {
                "id": f"q_{index}",
                "part": 4,
                "stem": stem_clean,
                "solution": clean_latex_to_markdown(loigiai_raw)
            }

    if parsed_q:
        parsed_q["raw_tex"] = f"\\begin{{{env_type}}}" + block_body_with_comments + f"\\end{{{env_type}}}"
        full_str = (
            parsed_q["stem"]
            + str(parsed_q.get("options", ""))
            + str(parsed_q.get("statements", ""))
            + str(parsed_q.get("short_ans", ""))
        )
        parsed_q["question_hash"] = hashlib.md5(full_str.encode("utf-8")).hexdigest()
        if meta:
            parsed_q.update(meta)
        else:
            parsed_q.update({
                "tag_id": "Chưa gắn mã",
                "grade": "12",
                "chapter_code": "C1",
                "chapter_name": "Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số",
                "lesson_code": "B1",
                "lesson_name": "Bài 1. Tính đơn điệu và cực trị của hàm số",
                "level_code": "N",
                "level_name": "Nhận biết"
            })
    return parsed_q


def parse_exam_tex(tex_content):
    r"""Đọc toàn bộ file .tex/.txt (cả môi trường ex và bt) theo đúng thứ tự xuất hiện"""
    pattern = re.compile(r'\\begin\{(ex|bt)\}(.*?)\\end\{\1\}', flags=re.DOTALL)
    questions = []
    for idx, match in enumerate(pattern.finditer(tex_content)):
        env_type = match.group(1)
        block_body = match.group(2)
        parsed = parse_single_block(block_body, idx + 1, env_type=env_type)
        if parsed:
            questions.append(parsed)
    return questions
