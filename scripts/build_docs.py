"""Render the student handouts with markdown-pdf and the shared CSS theme."""

import argparse
from html import escape
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = {'student-assignment.md': 'README.pdf', 'Background.md': 'Background.pdf'}


def build_docs(output_dir: Path) -> dict[str, Path]:
    """Build both PDFs before publishing either; return archive names and paths."""
    try:
        from markdown_pdf import MarkdownPdf, Section
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_by_name, TextLexer
        from pygments.util import ClassNotFound
        import pymupdf
        from PIL import Image
    except ImportError as error:
        raise RuntimeError(
            'PDF dependencies are missing. Run: python -m pip install -r '
            'scripts/requirements-docs.txt (or package with --skip-pdf).') from error

    def highlight_code(code, language, attributes):
        try:
            lexer = get_lexer_by_name(language) if language else TextLexer()
        except ClassNotFound:
            lexer = TextLexer()
        return highlight(code, lexer, HtmlFormatter(nowrap=True, noclasses=True, style='friendly'))

    def inline_code(tokens, index, options, env):
        # Give the PDF engine break opportunities in long signatures/table cells.
        text = '\u200b'.join(tokens[index].content)
        return '<code>' + escape(text) + '</code>'

    def link_open(tokens, index, options, env):
        token = tokens[index]
        target = token.attrGet('href')
        if target in DOCUMENTS:
            token.attrSet('href', DOCUMENTS[target])
        return renderer.renderToken(tokens, index, options, env)

    css = (ROOT / 'scripts/pdf.css').read_text(encoding='utf-8')
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pycman-docs-') as temporary:
        work = Path(temporary)
        shutil.copytree(ROOT / 'imgs', work / 'imgs')
        # MuPDF Story does not render WebP; keep the source asset unchanged.
        image_replacements = {}
        for image in (work / 'imgs').glob('*.webp'):
            converted = image.with_suffix('.png')
            with Image.open(image) as bitmap:
                bitmap.save(converted)
            image_replacements[image.relative_to(work).as_posix()] = converted.relative_to(work).as_posix()
        for source, target in DOCUMENTS.items():
            pdf = MarkdownPdf(toc_level=3, optimize=True)
            renderer = pdf.m_d.renderer
            pdf.m_d.options['highlight'] = highlight_code
            renderer.rules['code_inline'] = inline_code
            renderer.rules['link_open'] = link_open
            pdf.meta['title'] = 'PycMan · ' + ('学生任务说明' if source.startswith('student') else '预备知识')
            text = (ROOT / source).read_text(encoding='utf-8')
            for original, converted in image_replacements.items():
                text = text.replace(original, converted)
            try:
                pdf.add_section(Section(text, root=str(work), paper_size='A4',
                                        borders=(42, 42, -42, -44)), user_css=css)
                pdf.save(str(work / target))
                # Page numbers sit outside the content rectangle.
                with pymupdf.open(work / target) as document:
                    for page in document:
                        page.insert_textbox(
                            pymupdf.Rect(42, page.rect.height - 30, page.rect.width - 42,
                                         page.rect.height - 16),
                            str(page.number + 1), fontsize=8, fontname='helv',
                            color=(0.4, 0.45, 0.5), align=1)
                    document.save(str(work / ('numbered-' + target)), garbage=4, deflate=True)
                (work / ('numbered-' + target)).replace(work / target)
            except Exception as error:
                raise RuntimeError(f'PDF rendering failed for {source}: {error}') from error
        for target in DOCUMENTS.values():
            shutil.copy2(work / target, output_dir / target)
    return {target: output_dir / target for target in DOCUMENTS.values()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist/pdf')
    args = parser.parse_args()
    try:
        files = build_docs(args.output_dir.resolve())
    except RuntimeError as error:
        parser.exit(1, f'{error}\n')
    for path in files.values():
        print(f'Created {path}')


if __name__ == '__main__':
    main()
