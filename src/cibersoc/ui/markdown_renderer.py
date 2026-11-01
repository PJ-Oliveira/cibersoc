from __future__ import annotations

import html
from pathlib import Path
import re


def render_latex_math(latex: str) -> str:
    s = latex.strip()
    s = re.sub(r"\\displaystyle(?=[^a-zA-Z]|$)\s*", "", s)
    s = re.sub(r"\\[bB]ig[lr]?(?=[^a-zA-Z]|$)\s*", "", s)
    s = re.sub(r"\\(?:left|right)(?=[^a-zA-Z]|$)\s*", "", s)
    s = re.sub(r"\\[,;!]\s*", " ", s)

    replacements = (
        (r"\\mathbb\{E\}", "𝔼"),
        (r"\\mathbb\{R\}", "ℝ"),
        (r"\\mathbb\{N\}", "ℕ"),
        (r"\\mathbb\{Z\}", "ℤ"),
        (r"\\mathbb\{P\}", "ℙ"),
        (r"\\mathbb\{C\}", "ℂ"),
        (r"\\text\{([^}]+)\}", r"\1"),
        (r"\\mathrm\{([^}]+)\}", r"\1"),
        (r"\\mathbf\{([^}]+)\}", r"<b>\1</b>"),
        (r"\\mathit\{([^}]+)\}", r"<i>\1</i>"),
        (r"\\alpha(?=[^a-zA-Z]|$)", "α"),
        (r"\\beta(?=[^a-zA-Z]|$)", "β"),
        (r"\\gamma(?=[^a-zA-Z]|$)", "γ"),
        (r"\\Delta(?=[^a-zA-Z]|$)", "Δ"),
        (r"\\delta(?=[^a-zA-Z]|$)", "δ"),
        (r"\\epsilon(?=[^a-zA-Z]|$)", "ε"),
        (r"\\theta(?=[^a-zA-Z]|$)", "θ"),
        (r"\\lambda(?=[^a-zA-Z]|$)", "λ"),
        (r"\\mu(?=[^a-zA-Z]|$)", "μ"),
        (r"\\pi(?=[^a-zA-Z]|$)", "π"),
        (r"\\sigma(?=[^a-zA-Z]|$)", "σ"),
        (r"\\phi(?=[^a-zA-Z]|$)", "φ"),
        (r"\\omega(?=[^a-zA-Z]|$)", "ω"),
        (r"\\Omega(?=[^a-zA-Z]|$)", "Ω"),
        (r"\\partial(?=[^a-zA-Z]|$)", "∂"),
        (r"\\times(?=[^a-zA-Z]|$)", "×"),
        (r"\\le(?:q)?(?=[^a-zA-Z]|$)", "≤"),
        (r"\\ge(?:q)?(?=[^a-zA-Z]|$)", "≥"),
        (r"\\ne(?:q)?(?=[^a-zA-Z]|$)", "≠"),
        (r"\\approx(?=[^a-zA-Z]|$)", "≈"),
        (r"\\equiv(?=[^a-zA-Z]|$)", "≡"),
        (r"\\in(?=[^a-zA-Z]|$)", "∈"),
        (r"\\notin(?=[^a-zA-Z]|$)", "∉"),
        (r"\\subset(?:eq)?(?=[^a-zA-Z]|$)", "⊆"),
        (r"\\cup(?=[^a-zA-Z]|$)", "∪"),
        (r"\\cap(?=[^a-zA-Z]|$)", "∩"),
        (r"\\cdot(?=[^a-zA-Z]|$)", "·"),
        (r"\\pm(?=[^a-zA-Z]|$)", "±"),
        (r"\\mp(?=[^a-zA-Z]|$)", "∓"),
        (r"\\rightarrow(?=[^a-zA-Z]|$)", "→"),
        (r"\\to(?=[^a-zA-Z]|$)", "→"),
        (r"\\leftarrow(?=[^a-zA-Z]|$)", "←"),
        (r"\\Rightarrow(?=[^a-zA-Z]|$)", "⇒"),
        (r"\\infty(?=[^a-zA-Z]|$)", "∞"),
        (r"\\forall(?=[^a-zA-Z]|$)", "∀"),
        (r"\\exists(?=[^a-zA-Z]|$)", "∃"),
        (r"\\mid(?=[^a-zA-Z]|$)", "|"),
        (r"\\exp(?=[^a-zA-Z]|$)", "exp"),
        (r"\\ln(?=[^a-zA-Z]|$)", "ln"),
        (r"\\log(?=[^a-zA-Z]|$)", "log"),
        (r"\\max(?=[^a-zA-Z]|$)", "max"),
        (r"\\min(?=[^a-zA-Z]|$)", "min"),
        (r"\\det(?=[^a-zA-Z]|$)", "det"),
        (r"\\sum(?=[^a-zA-Z]|$)", "∑"),
        (r"\\prod(?=[^a-zA-Z]|$)", "∏"),
        (r"\\int(?=[^a-zA-Z]|$)", "∫"),
    )
    for pattern, repl in replacements:
        s = re.sub(pattern, repl, s)

    while r"\frac{" in s:
        new_s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1 / \2)", s)
        if new_s == s:
            s = s.replace(r"\frac{", "(")
            break
        s = new_s

    while r"\sqrt{" in s:
        new_s = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", s)
        if new_s == s:
            s = s.replace(r"\sqrt{", "√(")
            break
        s = new_s

    s = re.sub(r"_\{([^{}]+)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"_([a-zA-Z0-9α-ωΑ-Ω])", r"<sub>\1</sub>", s)
    s = re.sub(r"\^\{([^{}]+)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"\^([a-zA-Z0-9α-ωΑ-Ω])", r"<sup>\1</sup>", s)
    return s


def resolve_html_images(content: str, project_root: Path | None = None) -> str:
    root = project_root or Path(__file__).resolve().parents[3]

    def _remote_img_replace(match: re.Match[str]) -> str:
        alt = match.group(1) or "Badge"
        return f'<span class="badge-pill">{html.escape(alt)}</span>'

    content = re.sub(
        r"<img[^>]*src=[\"\']https?://[^\"]+[\"\'][^>]*alt=[\"\']([^\"]*)[\"\'][^>]*/?>",
        _remote_img_replace,
        content,
    )
    content = re.sub(
        r"<img[^>]*alt=[\"\']([^\"]*)[\"\'][^>]*src=[\"\']https?://[^\"]+[\"\'][^>]*/?>",
        _remote_img_replace,
        content,
    )

    def _replace_src(match: re.Match[str]) -> str:
        src = match.group(1)
        if src.startswith("http://") or src.startswith("https://") or src.startswith("file://"):
            return match.group(0)
        clean = src.lstrip("./")
        target = (root / clean).resolve()
        if target.exists():
            return f'src="{target.as_uri()}"'
        return match.group(0)

    return re.sub(r'src=["\']([^"\']+)["\']', _replace_src, content)


def render_inline_markdown(text: str, project_root: Path | None = None) -> str:
    code_tokens: list[str] = []

    def _code_stash(match: re.Match[str]) -> str:
        code_tokens.append(match.group(1))
        return f"\x00CODE{len(code_tokens) - 1}\x00"

    s = re.sub(r"`([^`]+)`", _code_stash, text)

    def _math_sub(match: re.Match[str]) -> str:
        return f'<span class="math-inline">{render_latex_math(match.group(1))}</span>'

    s = re.sub(r"\$([^$\n]+)\$", _math_sub, s)

    def _img_sub(match: re.Match[str]) -> str:
        alt = match.group(1)
        src = match.group(2)
        if src.startswith("http://") or src.startswith("https://"):
            return f'<span class="badge-pill">{html.escape(alt)}</span>'
        root = project_root or Path(__file__).resolve().parents[3]
        clean_src = src.lstrip("./")
        target_file = (root / clean_src).resolve()
        if target_file.exists():
            return f'<img src="{target_file.as_uri()}" alt="{html.escape(alt)}"/>'
        return f'<img src="{src}" alt="{html.escape(alt)}"/>'

    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _img_sub, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"__(.+?)__", r"<b>\1</b>", s)
    s = re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)
    s = re.sub(r"(?<![a-zA-Z0-9])_(.+?)_(?![a-zA-Z0-9])", r"<i>\1</i>", s)
    s = re.sub(r"~~(.+?)~~", r"<s>\1</s>", s)

    for idx, token in enumerate(code_tokens):
        s = s.replace(f"\x00CODE{idx}\x00", f"<code>{html.escape(token)}</code>")

    return s


def _extract_mermaid_node(raw_token: str, node_labels: dict[str, str]) -> str:
    token = raw_token.strip()
    match = re.match(r'^([A-Za-z0-9_.-]+)\s*(?:\[\s*"?([^"\]]+)"?\s*\]|\(\s*"?([^"\)]+)"?\s*\))$', token)
    if match:
        node_id = match.group(1)
        label = (match.group(2) or match.group(3) or node_id).strip()
        node_labels[node_id] = label
        return node_id
    node_labels.setdefault(token, token)
    return token


def render_mermaid_diagram(code_lines: list[str]) -> str:
    node_labels: dict[str, str] = {}
    edges: list[tuple[str, str, str]] = []
    fallback_lines: list[str] = []
    for raw_line in code_lines:
        stripped = raw_line.strip().rstrip(";")
        if not stripped or re.match(r"^(?:flowchart|graph|sequenceDiagram|stateDiagram)", stripped):
            continue
        edge_match = re.match(
            r"^(.+?)\s*(?:-->|--|==>|->>)\s*(?:\|([^|]+)\|\s*)?(.+)$",
            stripped,
        )
        if edge_match:
            src_id = _extract_mermaid_node(edge_match.group(1), node_labels)
            edge_label = (edge_match.group(2) or "").strip()
            dst_id = _extract_mermaid_node(edge_match.group(3), node_labels)
            edges.append((src_id, dst_id, edge_label))
        else:
            fallback_lines.append(stripped)
    if not edges:
        items_html = "".join(
            f'<div class="mermaid-step"><span class="mermaid-node">{html.escape(item)}</span></div>'
            for item in fallback_lines
        )
        return f'<div class="mermaid-diagram">{items_html}</div>'
    steps_html: list[str] = []
    for src_id, dst_id, edge_label in edges:
        src_html = html.escape(node_labels[src_id])
        dst_html = html.escape(node_labels[dst_id])
        arrow_text = f"→ {html.escape(edge_label)} →" if edge_label else "→"
        steps_html.append(
            f'<div class="mermaid-step">'
            f'<span class="mermaid-node">{src_html}</span>'
            f'<span class="mermaid-arrow">{arrow_text}</span>'
            f'<span class="mermaid-node">{dst_html}</span>'
            f"</div>"
        )
    return f'<div class="mermaid-diagram">{"".join(steps_html)}</div>'


def render_markdown_table(lines: list[str]) -> str:
    rows: list[list[str]] = []
    for line in lines:
        raw = line.strip()
        if raw.startswith("|"):
            raw = raw[1:]
        if raw.endswith("|"):
            raw = raw[:-1]
        cells = [c.strip() for c in raw.split("|")]
        rows.append(cells)
    if not rows:
        return ""
    header = rows[0]
    data_rows = (
        rows[2:]
        if len(rows) > 2 and all(set(c).issubset({"-", ":", " "}) for c in rows[1])
        else rows[1:]
    )

    parts: list[str] = ['<table class="md-table"><thead><tr>']
    for h in header:
        parts.append(f"<th>{render_inline_markdown(h)}</th>")
    parts.append("</tr></thead><tbody>")
    for r in data_rows:
        parts.append("<tr>")
        for c in r:
            parts.append(f"<td>{render_inline_markdown(c)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def build_markdown_document_css(base_font_points: int = 14) -> str:
    body_size = max(12, int(base_font_points))
    h1_size = int(round(body_size * 1.55))
    h2_size = int(round(body_size * 1.30))
    h3_size = int(round(body_size * 1.15))
    h4_size = int(round(body_size * 1.05))
    code_size = max(11, int(round(body_size * 0.92)))
    math_size = int(round(body_size * 1.08))

    return f"""
body {{
    background-color: #1F1814;
    color: #F4EAD8;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: {body_size}pt;
    line-height: 1.55;
    margin: 14px;
}}
h1 {{
    color: #F4EAD8;
    font-size: {h1_size}pt;
    font-weight: bold;
    border-bottom: 2px solid #C89B6D;
    padding-bottom: 4px;
    margin-top: 14px;
    margin-bottom: 10px;
}}
h2 {{
    color: #DFB589;
    font-size: {h2_size}pt;
    font-weight: bold;
    border-bottom: 1px solid #5C4335;
    padding-bottom: 3px;
    margin-top: 22px;
    margin-bottom: 8px;
}}
h3 {{
    color: #C89B6D;
    font-size: {h3_size}pt;
    font-weight: bold;
    margin-top: 18px;
    margin-bottom: 6px;
}}
h4, h5, h6 {{
    color: #DFB589;
    font-size: {h4_size}pt;
    font-weight: bold;
    margin-top: 14px;
    margin-bottom: 4px;
}}
p {{
    margin-top: 6px;
    margin-bottom: 8px;
}}
a {{
    color: #DFB589;
    text-decoration: underline;
}}
b, strong {{
    color: #F4EAD8;
    font-weight: bold;
}}
i, em {{
    color: #DFB589;
    font-style: italic;
}}
img {{
    max-width: 100%;
    height: auto;
    display: inline-block;
    margin: 8px auto;
}}
.badge-pill {{
    display: inline-block;
    background-color: #29201B;
    color: #DFB589;
    border: 1px solid #5C4335;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11pt;
    font-weight: bold;
    margin: 2px 4px;
}}
hr {{
    border: 0;
    height: 1px;
    background-color: #5C4335;
    margin: 18px 0;
}}
blockquote {{
    border-left: 4px solid #C89B6D;
    background-color: #29201B;
    margin: 10px 0;
    padding: 8px 12px;
    color: #F4EAD8;
}}
blockquote.alert-important {{
    border-left: 4px solid #C26653;
    background-color: #291B18;
}}
blockquote.alert-warning {{
    border-left: 4px solid #DFB589;
    background-color: #2B2117;
}}
blockquote.alert-note {{
    border-left: 4px solid #C89B6D;
    background-color: #29201B;
}}
code {{
    background-color: #16110E;
    color: #DFB589;
    font-family: Menlo, Monaco, "Courier New", monospace;
    font-size: {code_size}pt;
    border: 1px solid #36251B;
    padding: 2px 4px;
}}
pre {{
    background-color: #16110E;
    color: #DFB589;
    font-family: Menlo, Monaco, "Courier New", monospace;
    font-size: {code_size}pt;
    border: 1px solid #5C4335;
    padding: 10px;
    margin: 10px 0;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 14px 0;
    border: 1px solid #5C4335;
}}
th {{
    background-color: #29201B;
    color: #DFB589;
    border: 1px solid #5C4335;
    padding: 7px 10px;
    font-weight: bold;
    text-align: left;
}}
td {{
    border: 1px solid #36251B;
    padding: 6px 10px;
    background-color: #1F1814;
}}
tr:nth-child(even) td {{
    background-color: #261D17;
}}
ul, ol {{
    margin-top: 6px;
    margin-bottom: 8px;
    padding-left: 24px;
}}
li {{
    margin-top: 3px;
    margin-bottom: 3px;
}}
.math-display {{
    background-color: #16110E;
    border: 1px solid #5C4335;
    border-left: 4px solid #C89B6D;
    padding: 8px 14px;
    margin: 10px 0;
    font-size: {math_size}pt;
    color: #DFB589;
    text-align: center;
}}
.math-inline {{
    background-color: #261D17;
    color: #DFB589;
    padding: 1px 4px;
    border-radius: 2px;
}}
.mermaid-diagram {{
    background-color: #16110E;
    border: 1px solid #5C4335;
    border-left: 4px solid #C89B6D;
    padding: 10px 12px;
    margin: 12px 0;
}}
.mermaid-step {{
    margin: 5px 0;
    line-height: 1.5;
}}
.mermaid-node {{
    background-color: #29201B;
    color: #F4EAD8;
    border: 1px solid #4A3930;
    padding: 2px 8px;
    font-weight: bold;
}}
.mermaid-arrow {{
    color: #C89B6D;
    font-weight: bold;
    padding: 0 8px;
}}
"""


def render_markdown_to_html(
    markdown_text: str,
    base_font_points: int = 14,
    project_root: Path | None = None,
) -> str:
    lines = markdown_text.splitlines()
    html_parts: list[str] = []
    index = 0
    total_lines = len(lines)

    while index < total_lines:
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            code_lines: list[str] = []
            index += 1
            while index < total_lines:
                if lines[index].strip().startswith("```"):
                    index += 1
                    break
                code_lines.append(lines[index])
                index += 1
            if lang.lower() == "mermaid":
                html_parts.append(render_mermaid_diagram(code_lines))
                continue
            lang_attr = f' class="language-{html.escape(lang)}"' if lang else ""
            escaped_code = html.escape("\n".join(code_lines))
            html_parts.append(f"<pre><code{lang_attr}>{escaped_code}</code></pre>")
            continue

        if stripped.startswith("$$"):
            second_dollars = stripped.find("$$", 2)
            if second_dollars != -1:
                math_content = stripped[2:second_dollars]
                index += 1
            else:
                math_lines: list[str] = [stripped[2:]]
                index += 1
                while index < total_lines:
                    curr_line = lines[index]
                    pos = curr_line.find("$$")
                    if pos != -1:
                        math_lines.append(curr_line[:pos])
                        index += 1
                        break
                    math_lines.append(curr_line)
                    index += 1
                math_content = "\n".join(math_lines)
            rendered = render_latex_math(math_content)
            html_parts.append(f'<div class="math-display">{rendered}</div>')
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines: list[str] = []
            while (
                index < total_lines
                and lines[index].strip().startswith("|")
                and lines[index].strip().endswith("|")
            ):
                table_lines.append(lines[index])
                index += 1
            html_parts.append(render_markdown_table(table_lines))
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            alert_class = ""
            while index < total_lines and lines[index].strip().startswith(">"):
                raw_quote = lines[index].strip()[1:].strip()
                if raw_quote.startswith("[!NOTE]"):
                    alert_class = "alert-note"
                    raw_quote = raw_quote[7:].strip()
                elif raw_quote.startswith("[!IMPORTANT]"):
                    alert_class = "alert-important"
                    raw_quote = raw_quote[12:].strip()
                elif raw_quote.startswith("[!WARNING]") or raw_quote.startswith("[!CAUTION]"):
                    alert_class = "alert-warning"
                    raw_quote = raw_quote[10:].strip()
                if raw_quote:
                    quote_lines.append(raw_quote)
                index += 1
            cls_attr = f' class="{alert_class}"' if alert_class else ""
            quote_body = render_inline_markdown(
                "<br/>".join(quote_lines), project_root=project_root
            )
            html_parts.append(f"<blockquote{cls_attr}>{quote_body}</blockquote>")
            continue

        header_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if header_match:
            level = len(header_match.group(1))
            heading_content = render_inline_markdown(
                header_match.group(2).strip(), project_root=project_root
            )
            html_parts.append(f"<h{level}>{heading_content}</h{level}>")
            index += 1
            continue

        if re.match(r"^(?:---|---|\*\*\*|___)\s*$", stripped):
            html_parts.append('<hr class="md-hr"/>')
            index += 1
            continue

        ul_match = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if ul_match:
            list_items: list[str] = []
            while index < total_lines:
                item_match = re.match(r"^\s*[-*+]\s+(.*)$", lines[index])
                if not item_match:
                    break
                list_items.append(item_match.group(1).strip())
                index += 1
            items_html = "".join(
                f"<li>{render_inline_markdown(item, project_root=project_root)}</li>"
                for item in list_items
            )
            html_parts.append(f"<ul>{items_html}</ul>")
            continue

        ol_match = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if ol_match:
            list_items = []
            while index < total_lines:
                item_match = re.match(r"^\s*\d+\.\s+(.*)$", lines[index])
                if not item_match:
                    break
                list_items.append(item_match.group(1).strip())
                index += 1
            items_html = "".join(
                f"<li>{render_inline_markdown(item, project_root=project_root)}</li>"
                for item in list_items
            )
            html_parts.append(f"<ol>{items_html}</ol>")
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < total_lines:
            curr = lines[index]
            curr_stripped = curr.strip()
            if not curr_stripped:
                break
            if (
                curr_stripped.startswith("```")
                or curr_stripped.startswith("$$")
                or (curr_stripped.startswith("|") and curr_stripped.endswith("|"))
                or curr_stripped.startswith(">")
                or re.match(r"^#{1,6}\s+", curr_stripped)
                or re.match(r"^(?:---|---|\*\*\*|___)\s*$", curr_stripped)
                or re.match(r"^\s*[-*+]\s+", curr)
                or re.match(r"^\s*\d+\.\s+", curr)
            ):
                break
            paragraph_lines.append(curr_stripped)
            index += 1

        raw_body = " ".join(paragraph_lines)
        if raw_body.startswith("<p") or raw_body.startswith("<div"):
            html_parts.append(raw_body)
        else:
            p_body = render_inline_markdown(raw_body, project_root=project_root)
            html_parts.append(f"<p>{p_body}</p>")

    css = build_markdown_document_css(base_font_points=base_font_points)
    body_content = resolve_html_images("\n".join(html_parts), project_root=project_root)
    return (
        f'<!DOCTYPE html><html><head><meta charset="utf-8"/><style>{css}</style></head>'
        f"<body>{body_content}</body></html>"
    )
