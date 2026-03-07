from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

templates_dir = Path("templates/")

env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
    enable_async=True,
)


async def render_template(template_name: str, **context: Any) -> str:
    """Рендерит шаблон с переданными параметрами"""
    template = env.get_template(template_name)
    return await template.render_async(**context)
