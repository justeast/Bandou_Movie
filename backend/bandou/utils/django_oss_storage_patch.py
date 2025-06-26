"""
django-oss-storage包修补脚本,修复后端文件中的force_text和utc导入问题，修复后才支持django4以上
"""

import os
# 获取django-oss-storage包的路径
import django_oss_storage

package_path = os.path.dirname(django_oss_storage.__file__)
backends_file = os.path.join(package_path, 'backends.py')

print(f"正在修补 {backends_file}")

# 读取backends.py文件内容
with open(backends_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换force_text为force_str
if 'force_text' in content:
    content = content.replace('from django.utils.encoding import force_text',
                              'from django.utils.encoding import force_str as force_text')
    content = content.replace('from django.utils.encoding import force_text, force_bytes',
                              'from django.utils.encoding import force_str as force_text, force_bytes')

    # 写回文件
    with open(backends_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("成功修补django-oss-storage包，将force_text替换为force_str")
else:
    print("文件中未找到force_text，可能已经修复或使用了其他导入方式")

# 修复utc导入问题
if 'from django.utils.timezone import utc' in content:
    content = content.replace('from django.utils.timezone import utc',
                              'from datetime import timezone\nutc = timezone.utc')

    # 写回文件
    with open(backends_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("成功修补django-oss-storage包，修复utc导入问题")
else:
    print("文件中未找到utc导入，可能已经修复或使用了其他导入方式")

# 检查是否有其他文件也需要修补
for root, dirs, files in os.walk(package_path):
    for file in files:
        if file.endswith('.py') and file != 'backends.py':
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'force_text' in content:
                    content = content.replace('from django.utils.encoding import force_text',
                                              'from django.utils.encoding import force_str as force_text')
                    content = content.replace('from django.utils.encoding import force_text, force_bytes',
                                              'from django.utils.encoding import force_str as force_text, force_bytes')

                    # 写回文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    print(f"成功修补 {file_path}")
                if 'from django.utils.timezone import utc' in content:
                    content = content.replace('from django.utils.timezone import utc',
                                              'from datetime import timezone\nutc = timezone.utc')

                    # 写回文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    print(f"成功修补 {file_path}，修复utc导入问题")
            except Exception as e:
                print(f"修补 {file_path} 时出错: {e}")

print("修补完成，请重启Django服务器")
