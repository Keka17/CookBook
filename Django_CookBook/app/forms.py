
from django import forms
from .models import Recipe, Category, User
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


class SignUpForm(forms.ModelForm):
    """Форма регистрации нового пользователя;
    используется также для редактирования профиля в ЛК"""
    class Meta:
        model = User
        fields = ["email", "nickname", "bio", "avatar"]

        widgets = {
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Введите ваш email"
            }),
            "nickname": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите ваш уникальный никнейм. "
                               "Впоследствии вы не сможете его изменить."
            }),
            "bio": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Расскажите о себе, ваших кулинарных интересах",
                "rows": 4
            }),
            "avatar": forms.FileInput(attrs={
                "class": "form-control",
                "placeholder": "Загрузите изображение (до 1 МБ)"
            })
        }

    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def clean_nickname(self):
        """Проверка, что первая буква никнейма заглавная + уникальность"""
        nickname = self.cleaned_data.get('nickname')

        if nickname and not nickname[0].isupper():
            raise ValidationError('Первая буква должна быть заглавной.')

        if User.objects.filter(nickname=nickname).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Этот никнейм уже занят.")

        return nickname

    def clean_bio(self):
        """Проверка, что первая буква биографии заглавная"""
        bio = self.cleaned_data.get('bio')
        if bio and not bio[0].isupper():
            raise ValidationError('Первая буква должна быть заглавной.')
        return bio

    def clean_avatar(self):
        """Проверка размера изображения (не более 1 МБ)"""
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 1024 * 1024:
            raise ValidationError('Размер изображения превышает 1 МБ!')
        return avatar





