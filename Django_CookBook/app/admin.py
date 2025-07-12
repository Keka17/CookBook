from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Recipe, Category

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "nickname", "is_staff", "is_superuser")
    ordering = ("email",)
    search_fields = ("email", "nickname")

    # Настройка невозможности редактирования/удаления
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'dish_name', 'text', 'author', 'category', 'created_at', 'rating')
    list_filter = ('category', 'created_at')
    search_fields = ('dish_name', 'description', 'author__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "category")
    search_fields = ("category",)
    ordering = ("category",)
