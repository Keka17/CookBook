
from django import forms
from .models import Recipe, Category
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget


class RecipeForm(forms.ModelForm):
    """Форма создания рецепта"""
    class Meta:
        model = Recipe
        fields = ["dish_name", "category", "picture",
                  "description", "text"]
        widgets = {
            "dish_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите название блюда. Первая буква — заглавная."
            }),
            "category": forms.Select(attrs={"class": "form-control"}),
            "picture": forms.FileInput(attrs={
                "class": "form-control",
                "placeholder": "Загрузите изображение (до 1 МБ)"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "style": "resize: vertical;",
                "placeholder": "Краткое описание блюда (до 500 символов). Первая буква — заглавная."
            }),
            "text": CKEditor5Widget(attrs={
                "class": "django_ckeditor_5",
                "placeholder": "Опишите шаги приготовления..."
            }, config_name="default")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Дополнительные атрибуты для полей
        self.fields['category'].queryset = Category.objects.all()
        self.fields['text'].required = True  # Поле обязательно

    def clean_dish_name(self):
        """Проверка, что первая буква названия заглавная"""
        dish_name = self.cleaned_data.get('dish_name')
        if dish_name and not dish_name[0].isupper():
            raise ValidationError('Первая буква должна быть заглавной.')
        return dish_name

    def clean_description(self):
        """Проверка, что первая буква описания заглавная"""
        description = self.cleaned_data.get('description')
        if description and not description[0].isupper():
            raise ValidationError('Первая буква должна быть заглавной.')
        return description

    def clean_picture(self):
        """Проверка размера изображения (не более 1 МБ)"""
        picture = self.cleaned_data.get('picture')
        if picture and picture.size > 1024 * 1024:
            raise ValidationError('Размер изображения превышает 1 МБ!')
        return picture

