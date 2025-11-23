"""
Security utilities for internal chat
Provides HTML sanitization and content filtering to prevent XSS attacks
"""
import bleach
import logging
import re
import os
from html import unescape
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Whitelist of allowed HTML tags (very restrictive for security)
ALLOWED_TAGS = [
    'b', 'i', 'u', 'strong', 'em', 'code', 'pre', 'a',
    'br', 'p', 'span', 'div', 'blockquote',
    'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
]

# Allowed attributes for specific tags
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'span': ['class'],
    'div': ['class'],
    'code': ['class'],
}

# Allowed protocols in links (prevent javascript: and data: URLs)
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

# CSS properties whitelist (if we decide to allow style attributes)
ALLOWED_STYLES = []

# Dangerous tags that should have their content removed entirely
DANGEROUS_TAGS = ['script', 'style', 'iframe', 'object', 'embed', 'applet']


def sanitize_message_content(content):
    """
    Sanitize message content to prevent XSS attacks.
    
    This function removes all potentially dangerous HTML/JavaScript while
    preserving safe formatting tags for better user experience.
    
    Args:
        content (str): Raw message content from user
        
    Returns:
        str: Sanitized content safe for rendering
        
    Examples:
        >>> sanitize_message_content('<script>alert("XSS")</script>Hello')
        'Hello'
        
        >>> sanitize_message_content('<b>Bold text</b>')
        '<b>Bold text</b>'
        
        >>> sanitize_message_content('<a href="javascript:alert(1)">Click</a>')
        '<a>Click</a>'
    """
    if not content:
        return content
    
    # Log original content length for monitoring
    original_length = len(content)
    
    # First pass: Remove dangerous tags and their content using regex
    # This prevents script/style content from appearing in output
    for tag in DANGEROUS_TAGS:
        # Remove opening and closing tags with content
        pattern = f'<{tag}[^>]*>.*?</{tag}>'
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        # Remove self-closing tags
        pattern = f'<{tag}[^>]*/?>'
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Second pass: Use bleach to clean remaining HTML with strict whitelist
    cleaned = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True  # Strip any remaining disallowed tags
    )
    
    # Strip whitespace
    cleaned = cleaned.strip()
    
    # Log if significant content was removed (potential attack attempt)
    cleaned_length = len(cleaned)
    if original_length > 0 and (original_length - cleaned_length) > original_length * 0.3:
        logger.warning(
            f"Significant content removed during sanitization: "
            f"{original_length} -> {cleaned_length} bytes "
            f"({((original_length - cleaned_length) / original_length * 100):.1f}% removed)"
        )
    
    return cleaned


def sanitize_caption(caption):
    """
    Sanitize attachment caption text.
    More restrictive than message content - only allows basic formatting.
    
    Args:
        caption (str): Raw caption text
        
    Returns:
        str: Sanitized caption safe for rendering
    """
    if not caption:
        return caption
    
    # Remove dangerous tags and their content first
    for tag in DANGEROUS_TAGS:
        pattern = f'<{tag}[^>]*>.*?</{tag}>'
        caption = re.sub(pattern, '', caption, flags=re.IGNORECASE | re.DOTALL)
        pattern = f'<{tag}[^>]*/?>'
        caption = re.sub(pattern, '', caption, flags=re.IGNORECASE)
    
    # For captions, use a more restrictive tag list
    caption_tags = ['b', 'i', 'u', 'strong', 'em', 'code']
    
    cleaned = bleach.clean(
        caption,
        tags=caption_tags,
        attributes={},  # No attributes allowed in captions
        protocols=ALLOWED_PROTOCOLS,
        strip=True  # Completely remove disallowed tags
    )
    
    return cleaned.strip()


def validate_emoji(emoji):
    """
    Validate emoji input to prevent abuse.
    
    Args:
        emoji (str): Emoji string to validate
        
    Returns:
        bool: True if emoji is valid
        
    Raises:
        ValueError: If emoji is invalid
    """
    if not emoji:
        raise ValueError("Emoji cannot be empty")
    
    # Check length (emoji should be short)
    if len(emoji) > 10:
        raise ValueError("Emoji string too long")
    
    # Basic validation - no HTML tags
    if '<' in emoji or '>' in emoji:
        raise ValueError("Invalid characters in emoji")
    
    return True


# =============================================================================
# FILE UPLOAD VALIDATION
# =============================================================================

# Allowed MIME types (actual file types based on content, not headers)
ALLOWED_MIME_TYPES = {
    # Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    'image/tiff',
    # Documents
    'application/pdf',
    'application/msword',  # .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/vnd.ms-excel',  # .xls
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-powerpoint',  # .ppt
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
    # Text
    'text/plain',
    'text/csv',
    # Archives (with caution - may want to disable in production)
    'application/zip',
    'application/x-rar-compressed',
    'application/x-7z-compressed',
}

# Allowed file extensions (must match MIME type)
ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif',  # Images
    '.pdf',  # Documents
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Office
    '.txt', '.csv',  # Text
    '.zip', '.rar', '.7z',  # Archives
}

# Dangerous extensions that should NEVER be allowed
FORBIDDEN_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.vbe',  # Executables/Scripts
    '.php', '.py', '.rb', '.pl', '.js', '.asp', '.aspx', '.jsp',  # Web scripts
    '.html', '.htm', '.svg', '.xml',  # Can contain scripts
    '.jar', '.war', '.class',  # Java executables
    '.msi', '.app', '.deb', '.rpm', '.dmg',  # Installers
    '.scr', '.com', '.pif', '.cpl',  # System files
    '.hta', '.chm', '.hlp',  # Help files that can execute code
}

# MIME type to extension mapping for strict validation
MIME_EXTENSION_MAP = {
    'image/jpeg': {'.jpg', '.jpeg'},
    'image/png': {'.png'},
    'image/gif': {'.gif'},
    'image/webp': {'.webp'},
    'image/bmp': {'.bmp'},
    'image/tiff': {'.tiff', '.tif'},
    'application/pdf': {'.pdf'},
    'text/plain': {'.txt'},
    'text/csv': {'.csv'},
    'application/zip': {'.zip'},
    'application/x-rar-compressed': {'.rar'},
    'application/x-7z-compressed': {'.7z'},
    'application/msword': {'.doc'},
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {'.docx'},
    'application/vnd.ms-excel': {'.xls'},
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {'.xlsx'},
    'application/vnd.ms-powerpoint': {'.ppt'},
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': {'.pptx'},
}


def validate_file_type(file):
    """
    Validate file type using magic bytes (file signature).
    
    This function reads the file's actual content (magic bytes) to determine
    its real type, preventing attackers from uploading malicious files by
    simply changing the extension or Content-Type header.
    
    Args:
        file: Django UploadedFile object
        
    Raises:
        ValidationError: If file type is not allowed or doesn't match extension
        
    Returns:
        str: Detected MIME type
        
    Examples:
        >>> # Upload malware.exe renamed to image.jpg
        >>> validate_file_type(fake_image)  # Raises ValidationError
        
        >>> # Upload real image.jpg
        >>> validate_file_type(real_image)  # Returns 'image/jpeg'
    """
    try:
        import magic
    except ImportError:
        logger.error("python-magic not installed. File validation disabled!")
        raise ValidationError(
            "File type validation is currently unavailable. Please contact support."
        )
    
    # Read first 2KB for magic byte detection (sufficient for most file types)
    file_start = file.read(2048)
    file.seek(0)  # Reset file pointer for later use
    
    # Detect actual MIME type from file content (not from headers!)
    try:
        mime = magic.from_buffer(file_start, mime=True)
    except Exception as e:
        logger.error(f"Magic byte detection failed: {str(e)}")
        raise ValidationError(
            f"Unable to detect file type. The file may be corrupted or invalid."
        )
    
    # Normalize MIME type (handle variations)
    mime = mime.lower().strip()
    
    # Log detected MIME type for monitoring
    logger.info(f"File upload detected: {mime} for file: {file.name}")
    
    # Check if detected MIME type is allowed
    if mime not in ALLOWED_MIME_TYPES:
        logger.warning(
            f"Rejected file upload - disallowed MIME type: {mime} "
            f"(file: {file.name}, claimed type: {getattr(file, 'content_type', 'unknown')})"
        )
        raise ValidationError(
            f"File type '{mime}' is not allowed. "
            f"Allowed types: images (JPEG, PNG, GIF, WebP), PDFs, "
            f"Office documents (Word, Excel, PowerPoint), text files, and archives."
        )
    
    # Validate file extension
    file_ext = os.path.splitext(file.name)[1].lower()
    
    # Check forbidden extensions first (absolute no-go)
    if file_ext in FORBIDDEN_EXTENSIONS:
        logger.warning(
            f"Rejected file upload - forbidden extension: {file_ext} "
            f"(file: {file.name}, detected type: {mime})"
        )
        raise ValidationError(
            f"File extension '{file_ext}' is forbidden for security reasons. "
            f"Executable files and scripts are not allowed."
        )
    
    # Check if extension is in allowed list
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(
            f"Rejected file upload - disallowed extension: {file_ext} "
            f"(file: {file.name}, detected type: {mime})"
        )
        raise ValidationError(
            f"File extension '{file_ext}' is not allowed."
        )
    
    # Additional MIME/extension consistency check
    # This prevents attacks like: malware.exe renamed to document.pdf
    if mime in MIME_EXTENSION_MAP:
        expected_extensions = MIME_EXTENSION_MAP[mime]
        if file_ext not in expected_extensions:
            logger.warning(
                f"Rejected file upload - extension mismatch: "
                f"extension={file_ext}, detected_mime={mime}, expected={expected_extensions} "
                f"(file: {file.name})"
            )
            raise ValidationError(
                f"File extension '{file_ext}' does not match detected file type '{mime}'. "
                f"Expected one of: {', '.join(sorted(expected_extensions))}. "
                f"This may indicate a spoofed or corrupted file."
            )
    
    # Success - file passed all validation checks
    logger.info(f"File upload validated successfully: {file.name} ({mime})")
    return mime


def validate_file_size(file, max_size_mb=10):
    """
    Validate file size to prevent DoS attacks and storage abuse.
    
    Args:
        file: Django UploadedFile object
        max_size_mb: Maximum allowed size in megabytes (default: 10MB)
        
    Raises:
        ValidationError: If file exceeds size limit
        
    Returns:
        int: File size in bytes
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file.size > max_size_bytes:
        logger.warning(
            f"Rejected file upload - size exceeded: "
            f"{file.size / 1024 / 1024:.2f}MB > {max_size_mb}MB "
            f"(file: {file.name})"
        )
        raise ValidationError(
            f"File size ({file.size / 1024 / 1024:.2f}MB) exceeds "
            f"maximum allowed size ({max_size_mb}MB). "
            f"Please upload a smaller file."
        )
    
    logger.debug(f"File size validated: {file.size / 1024 / 1024:.2f}MB for {file.name}")
    return file.size

