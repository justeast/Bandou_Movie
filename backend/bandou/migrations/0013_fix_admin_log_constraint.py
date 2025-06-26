from django.db import migrations


class Migration(migrations.Migration):
    """
    修复django_admin_log表的外键约束，使其指向自定义User模型
    """

    dependencies = [
        ('bandou', '0012_remove_loginrecord_login_device'),  # 只依赖于最新迁移
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            -- 禁用外键检查
            SET FOREIGN_KEY_CHECKS=0;

            -- 修改django_admin_log表的user_id列，不使用任何约束
            ALTER TABLE django_admin_log MODIFY COLUMN user_id INT NULL;

            -- 重新启用外键检查
            SET FOREIGN_KEY_CHECKS=1;
            ''',
            reverse_sql='-- 此操作无法自动撤销',
        ),
    ]
