import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any
import structlog

from email_service.core.exceptions import TemplateError


logger = structlog.get_logger(__name__)


class Jinja2Renderer:
    """Renders email templates using Jinja2"""
    
    def __init__(self, template_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add global functions
        self._add_globals()
    
    def _add_globals(self):
        """Add global functions to Jinja2 environment"""
        from datetime import datetime
        import urllib.parse
        
        def format_datetime(value, format='%B %d, %Y'):
            if isinstance(value, datetime):
                return value.strftime(format)
            return value
        
        def url_encode(value):
            return urllib.parse.quote(value)
        
        def frontend_url(path=""):
            from email_service.config import settings
            return f"{settings.frontend_url.rstrip('/')}/{path.lstrip('/')}"
        
        self.env.globals.update({
            'format_datetime': format_datetime,
            'url_encode': url_encode,
            'frontend_url': frontend_url,
            'now': datetime.utcnow
        })
    
    def render_html(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render HTML template"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error("HTML template rendering failed", 
                        template=template_name, 
                        error=str(e))
            raise TemplateError(f"Failed to render HTML template {template_name}: {str(e)}")
    
    def render_text(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render plain text template"""
        try:
            # Try to find text version
            base_name = os.path.splitext(template_name)[0]
            text_template_name = f"plain_text/{os.path.basename(base_name)}.txt"
            
            template = self.env.get_template(text_template_name)
            return template.render(**context)
        except Exception as e:
            logger.warning("Text template not found, creating from HTML", 
                          template=template_name,
                          error=str(e))
            # Fallback: render HTML and convert to text
            html = self.render_html(template_name, context)
            return self._html_to_text(html)
    
    def _html_to_text(self, html: str) -> str:
        """Simple HTML to text conversion"""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Replace multiple spaces/newlines with single ones
        text = re.sub(r'\s+', ' ', text)
        
        # Common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text.strip()