import bleach
import re
from html.parser import HTMLParser
from django.conf import settings


# Default allowed tags and attributes
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
    'p', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr',
    'div', 'span', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'caption'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel', 'target'],
    'abbr': ['title'],
    'acronym': ['title'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'table': ['width', 'border', 'align', 'cellpadding', 'cellspacing'],
    'th': ['scope', 'colspan', 'rowspan', 'width'],
    'td': ['colspan', 'rowspan', 'width'],
    '*': ['class']
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


class URLValidator(HTMLParser):
    """
    Custom HTML parser to validate URLs in HTML attributes.
    """
    def __init__(self):
        super().__init__()
        self.invalid_urls = []
    
    def handle_starttag(self, tag, attrs):
        for attr, value in attrs:
            if attr == 'href' or attr == 'src':
                # Check for malicious URLs
                if (
                    value.startswith('javascript:') or 
                    value.startswith('data:') or 
                    value.startswith('vbscript:')
                ):
                    self.invalid_urls.append(value)


def sanitize_html(html_content, tags=None, attributes=None, protocols=None):
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        html_content (str): The HTML content to sanitize
        tags (list): List of allowed HTML tags (defaults to ALLOWED_TAGS)
        attributes (dict): Dict of allowed attributes (defaults to ALLOWED_ATTRIBUTES)
        protocols (list): List of allowed URL protocols (defaults to ALLOWED_PROTOCOLS)
    
    Returns:
        str: Sanitized HTML content
    """
    if html_content is None:
        return ''
    
    if tags is None:
        tags = ALLOWED_TAGS
    
    if attributes is None:
        attributes = ALLOWED_ATTRIBUTES
    
    if protocols is None:
        protocols = ALLOWED_PROTOCOLS
    
    # First, check for any suspicious URLs
    url_validator = URLValidator()
    url_validator.feed(html_content)
    
    if url_validator.invalid_urls:
        # Strip out any potentially malicious URLs completely
        for url in url_validator.invalid_urls:
            html_content = html_content.replace(url, '#')
    
    # Use bleach to sanitize HTML
    clean_html = bleach.clean(
        html_content,
        tags=tags,
        attributes=attributes,
        protocols=protocols,
        strip=True
    )
    
    # Additional security measures
    # Strip out any inline JavaScript events (onclick, onload, etc.)
    clean_html = re.sub(r'on\w+="[^"]*"', '', clean_html)
    
    # Check for suspicious CSS (could be used for XSS)
    clean_html = re.sub(r'style="[^"]*expression[^"]*"', '', clean_html)
    clean_html = re.sub(r'style="[^"]*javascript[^"]*"', '', clean_html)
    
    return clean_html


def sanitize_user_input(text):
    """
    Sanitize plain text user input (non-HTML).
    
    Args:
        text (str): The text to sanitize
    
    Returns:
        str: Sanitized text
    """
    if text is None:
        return ''
    
    # Strip all HTML tags
    return bleach.clean(text, tags=[], strip=True)


def escape_text(text):
    """
    Escape text for safe display in HTML.
    
    Args:
        text (str): The text to escape
    
    Returns:
        str: Escaped text
    """
    if text is None:
        return ''
    
    return bleach.clean(text, tags=[], strip=True) 