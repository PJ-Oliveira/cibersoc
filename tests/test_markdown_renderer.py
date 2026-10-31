from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import QTextBrowser

from cibersoc.ui.markdown_renderer import (
    build_markdown_document_css,
    render_inline_markdown,
    render_latex_math,
    render_markdown_table,
    render_markdown_to_html,
    resolve_html_images,
)


def test_latex_math_rendering_comprehensive() -> None:
    latex_sample = (
        r"\displaystyle \bigl( \left( \mathbb{E}[\Delta\text{Outcome}\mid \text{vote}_i] "
        r"+ \mathbb{R} + \mathbb{N} + \mathbb{Z} + \mathbb{P} + \mathbb{C} "
        r"+ \mathbf{bold} + \mathit{italic} + \mathrm{roman} "
        r"+ \alpha + \beta + \gamma + \Delta + \delta + \epsilon + \theta + \lambda + \mu "
        r"+ \pi + \sigma + \phi + \omega + \Omega + \partial "
        r"+ \times + \le + \leq + \ge + \geq + \ne + \neq + \approx + \equiv "
        r"+ \in + \notin + \subset + \subseteq + \cup + \cap + \cdot + \pm + \mp "
        r"+ \rightarrow + \to + \leftarrow + \Rightarrow + \infty + \forall + \exists "
        r"+ \exp(x) + \ln(x) + \log(x) + \max(x) + \min(x) + \det(A) "
        r"+ \sum_{i=1}^n + \prod_{j=1}^m + \int_a^b "
        r"+ \frac{\partial \Delta}{\partial v_i} + \sqrt{N} + U_{\text{politician}} "
        r"+ 10^{-13\,723} + e^{-31\,600} \right) \bigr)"
    )
    rendered = render_latex_math(latex_sample)
    assert "𝔼" in rendered
    assert "ℝ" in rendered
    assert "<b>bold</b>" in rendered
    assert "<i>italic</i>" in rendered
    assert "α" in rendered
    assert "β" in rendered
    assert "γ" in rendered
    assert "Δ" in rendered
    assert "∂" in rendered
    assert "≤" in rendered
    assert "≥" in rendered
    assert "≠" in rendered
    assert "≈" in rendered
    assert "∈" in rendered
    assert "∑" in rendered
    assert "∏" in rendered
    assert "∫" in rendered
    assert "<sub>politician</sub>" in rendered
    assert "<sup>-13 723</sup>" in rendered

    malformed_frac = r"\frac{incomplete"
    assert "(" in render_latex_math(malformed_frac)
    malformed_sqrt = r"\sqrt{incomplete"
    assert "√(" in render_latex_math(malformed_sqrt)


def test_inline_markdown_formatting() -> None:
    text = (
        "Inline `code_sample` and $t \\in [1, 3]$ with "
        "![Alt Text](icon.png) and [Link Label](doc.md). "
        "***bold_italic***, **bold_text**, __alt_bold__, "
        "*italic_text*, _alt_italic_, and ~~strikethrough~~."
    )
    html_output = render_inline_markdown(text)
    assert "<code>code_sample</code>" in html_output
    assert '<span class="math-inline">' in html_output
    assert "t ∈ [1, 3]" in html_output
    assert '<img src="icon.png" alt="Alt Text"/>' in html_output
    assert '<a href="doc.md">Link Label</a>' in html_output
    assert "<b><i>bold_italic</i></b>" in html_output
    assert "<b>bold_text</b>" in html_output
    assert "<b>alt_bold</b>" in html_output
    assert "<i>italic_text</i>" in html_output
    assert "<i>alt_italic</i>" in html_output
    assert "<s>strikethrough</s>" in html_output


def test_markdown_table_rendering() -> None:
    empty_result = render_markdown_table([])
    assert empty_result == ""

    table_lines = [
        "| Portfolio | Seats | Ratio |",
        "| :--- | :---: | ---: |",
        "| Justice | 4 | 0.20 |",
        "| Defense | 3 | 0.15 |",
    ]
    rendered = render_markdown_table(table_lines)
    assert '<table class="md-table">' in rendered
    assert "<th>Portfolio</th>" in rendered
    assert "<td>Justice</td>" in rendered

    raw_table_no_delimiter = [
        "Header1 | Header2",
        "Value1 | Value2",
    ]
    no_delim_rendered = render_markdown_table(raw_table_no_delimiter)
    assert "<th>Header1</th>" in no_delim_rendered
    assert "<td>Value1</td>" in no_delim_rendered


def test_build_markdown_document_css_scaling() -> None:
    css_14 = build_markdown_document_css(14)
    assert "font-size: 14pt;" in css_14
    css_min = build_markdown_document_css(8)
    assert "font-size: 12pt;" in css_min


def test_render_markdown_to_html_all_blocks(qapp) -> None:
    markdown = """
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6

---

```python
def solve():
    return 42
```

```
plain preformatted block
```

$$
P_{\\text{pivotal}} \\le 10^{-13\\,723}
$$

$$ e^{i\\pi} + 1 = 0 $$

> [!NOTE]
> Note callout body line.

> [!IMPORTANT]
> Urgent mandate security constraint.

> [!WARNING]
> Warning on oligarchic capture.

> [!CAUTION]
> Cautionary measure.

> Simple quotation block.

| Tier | Seats |
| --- | --- |
| Municipal | 20 |

- Bullet A
- Bullet B with `item`

1. First step
2. Second step

Paragraph with $x = 1$ and regular sentences.

***

___
"""
    doc_html = render_markdown_to_html(markdown, base_font_points=15)
    assert "<!DOCTYPE html>" in doc_html
    assert "<h1>Heading 1</h1>" in doc_html
    assert "<h2>Heading 2</h2>" in doc_html
    assert "<h3>Heading 3</h3>" in doc_html
    assert "<h4>Heading 4</h4>" in doc_html
    assert "<h5>Heading 5</h5>" in doc_html
    assert "<h6>Heading 6</h6>" in doc_html
    assert '<pre><code class="language-python">' in doc_html
    assert "<pre><code>plain preformatted block</code></pre>" in doc_html
    assert '<div class="math-display">' in doc_html
    assert '<blockquote class="alert-note">' in doc_html
    assert '<blockquote class="alert-important">' in doc_html
    assert '<blockquote class="alert-warning">' in doc_html
    assert '<table class="md-table">' in doc_html
    assert "<ul><li>Bullet A</li>" in doc_html
    assert "<ol><li>First step</li>" in doc_html
    assert "<p>" in doc_html
    assert '<hr class="md-hr"/>' in doc_html

    browser = QTextBrowser()
    browser.setHtml(doc_html)
    assert len(browser.toPlainText()) > 50


def test_render_markdown_edge_cases_and_unclosed_blocks() -> None:
    unclosed_code = "```python\ndef incomplete():\n    pass"
    html_code = render_markdown_to_html(unclosed_code)
    assert "incomplete" in html_code

    unclosed_math = "$$\n\\Delta x = 0"
    html_math = render_markdown_to_html(unclosed_math)
    assert "Δ x = 0" in html_math

    empty_html = render_markdown_to_html("   \n\n   ")
    assert "<!DOCTYPE html>" in empty_html

    trailing_ol = "1. Only one item"
    html_ol = render_markdown_to_html(trailing_ol)
    assert "<ol><li>Only one item</li></ol>" in html_ol

    trailing_ul = "- Only one bullet"
    html_ul = render_markdown_to_html(trailing_ul)
    assert "<ul><li>Only one bullet</li></ul>" in html_ul


def test_render_all_project_documentation_files(qapp) -> None:
    project_root = Path(__file__).resolve().parents[1]
    browser = QTextBrowser()

    readme_path = project_root / "README.md"
    assert readme_path.exists()
    readme_html = render_markdown_to_html(readme_path.read_text(encoding="utf-8"))
    browser.setHtml(readme_html)
    assert len(browser.toPlainText()) > 100

    docs_dir = project_root / "docs"
    for md_file in docs_dir.glob("**/*.md"):
        content = md_file.read_text(encoding="utf-8")
        html_page = render_markdown_to_html(content)
        browser.setHtml(html_page)
        assert len(browser.toPlainText()) > 100


def test_resolve_html_images_and_markdown_badges() -> None:
    project_root = Path(__file__).resolve().parents[1]

    raw_html = (
        '<p><img src="https://img.shields.io/badge/Test-blue.svg" alt="Test Badge"/></p>'
        '<p><img alt="Coverage Badge" src="http://example.com/cov.png"/></p>'
        '<p><img src="file:///already/resolved/image.png"/></p>'
        '<p><img src="http://example.com/noalt.png"/></p>'
        '<p><img src="assets/images/cibersoc_emblem_hd.png"/></p>'
        '<p><img src="assets/nonexistent/missing_file.png"/></p>'
    )
    resolved = resolve_html_images(raw_html, project_root=project_root)
    assert '<span class="badge-pill">Test Badge</span>' in resolved
    assert '<span class="badge-pill">Coverage Badge</span>' in resolved
    assert 'src="file:///already/resolved/image.png"' in resolved
    assert 'src="http://example.com/noalt.png"' in resolved
    assert "file:///" in resolved
    assert "cibersoc_emblem_hd.png" in resolved
    assert 'src="assets/nonexistent/missing_file.png"' in resolved

    remote_md = "Here is ![Shield](https://img.shields.io/badge/status-active.svg)"
    rendered_remote = render_inline_markdown(remote_md, project_root=project_root)
    assert '<span class="badge-pill">Shield</span>' in rendered_remote

    local_md = "Here is ![Emblem](assets/images/cibersoc_emblem_hd.png)"
    rendered_local = render_inline_markdown(local_md, project_root=project_root)
    assert 'src="file:///' in rendered_local
    assert 'alt="Emblem"' in rendered_local

    missing_md = "Here is ![Missing](assets/nonexistent_relative_file.png)"
    rendered_missing = render_inline_markdown(missing_md, project_root=project_root)
    assert '<img src="assets/nonexistent_relative_file.png" alt="Missing"/>' in rendered_missing
