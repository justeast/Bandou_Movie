from django.core.exceptions import ValidationError


def validate_image_file(value, max_size_mb=5, valid_extensions=None):
    """通用图片文件验证"""
    if not value:
        return None

    if valid_extensions is None:
        valid_extensions = ['jpg', 'jpeg', 'png']

    extension = value.name.split('.')[-1].lower()
    if extension not in valid_extensions:
        raise ValidationError(f"不支持的文件格式，仅支持 {', '.join(valid_extensions)}")

    max_size = max_size_mb * 1024 * 1024
    if value.size > max_size:
        raise ValidationError(f"文件大小超过限制（最大 {max_size_mb}MB）")

    return value
