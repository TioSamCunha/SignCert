import os
import re
from jinja2 import Environment, FileSystemLoader, BaseLoader
from flask import current_app


def load_template_html(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_variables(html_content: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r'\{\{\s*(\w+)\s*\}\}', html_content)))


def render_to_html(html_content: str, variables: dict) -> str:
    env = Environment(loader=BaseLoader())
    tpl = env.from_string(html_content)
    return tpl.render(**variables)


def html_to_pdf(html_content: str, output_path: str) -> str:
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(output_path)
    except Exception:
        _html_to_pdf_xhtml2pdf(html_content, output_path)
    return output_path


def _html_to_pdf_xhtml2pdf(html_content: str, output_path: str) -> None:
    from xhtml2pdf import pisa
    with open(output_path, 'wb') as f:
        result = pisa.CreatePDF(html_content.encode('utf-8'), dest=f,
                                encoding='utf-8')
    if result.err:
        raise RuntimeError(f'xhtml2pdf error: {result.err}')


def save_template_file(template_id: int, html_content: str) -> str:
    templates_dir = current_app.config.get('DOCUMENT_TEMPLATES_DIR', 'app/document_templates')
    os.makedirs(templates_dir, exist_ok=True)
    path = os.path.join(templates_dir, f'template_{template_id}.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return path
