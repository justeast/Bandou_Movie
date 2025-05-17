from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from bandou.models import User, LoginRecord

admin.site.site_header = 'Bandou后台用户管理'  # 登录页和管理页顶部标题
admin.site.site_title = 'Bandou User Admin'  # 浏览器标签显示标题


class LoginRecordInline(admin.TabularInline):
    """用户登录记录内联显示"""
    model = LoginRecord
    extra = 0
    readonly_fields = ('login_time', 'login_ip',)
    can_delete = False
    verbose_name = "登录记录"
    verbose_name_plural = "登录记录"
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


class CustomUserAdmin(BaseUserAdmin):
    """自定义用户管理"""
    list_display = ('username', 'email', 'phone', 'is_active', 'is_staff', 'last_login', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-date_joined',)
    actions = ['ban_users', 'unban_users']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {'fields': ('email', 'phone')}),
        (_('权限'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
    )
    inlines = [LoginRecordInline]


    def ban_users(self, request, queryset):
        """封禁用户"""
        queryset.update(is_active=False)
        self.message_user(request, f"成功封禁 {queryset.count()} 个用户")

    ban_users.short_description = "封禁选中的用户"

    def unban_users(self, request, queryset):
        """解封用户"""
        queryset.update(is_active=True)
        self.message_user(request, f"成功解封 {queryset.count()} 个用户")

    unban_users.short_description = "解封选中的用户"


class LoginRecordAdmin(admin.ModelAdmin):
    """登录记录管理"""
    list_display = ('user', 'login_time', 'login_ip',)
    list_filter = ('login_time', 'user')
    search_fields = ('user__username', 'login_ip')
    readonly_fields = ('user', 'login_time', 'login_ip',)
    date_hierarchy = 'login_time'

    def has_add_permission(self, request):
        """禁止手动添加登录记录"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁止修改登录记录"""
        return False

    def has_delete_permission(self, request, obj=None):
        """禁止删除登录记录"""
        return False


# 只注册用户相关模型到admin
admin.site.register(User, CustomUserAdmin)
admin.site.register(LoginRecord, LoginRecordAdmin)
