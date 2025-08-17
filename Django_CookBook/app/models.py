from django.db import models 
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User, AbstractUser
from django_ckeditor_5.fields import CKEditor5Field
from django.db.models import Avg

class Category(models.Model):
    category = models.CharField(max_length=30, unique=True)
    
    def __str__(self):
        return self.category


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата редактирования")
    category = models.ForeignKey(Category, null=False, on_delete=models.PROTECT, verbose_name="Категория")  # 1 блюдо - 1 категория
    dish_name = models.CharField(max_length=100, verbose_name="Название блюда")
    picture = models.ImageField(upload_to="pictures/", blank=False, null=False, 
                                verbose_name="Изображение блюда")
    description = models.CharField(max_length=500, blank=False, null=False,
                                   verbose_name="Описание блюда")
    text = CKEditor5Field(verbose_name="Шаги приготовления")

    def __str__(self):
        return self.dish_name

    def like(self):
        if self.rating < 5:
            self.rating += 1
            self.save()

    def dislike(self):
        if self.rating > 1:
            self.rating -= 1
            self.save()

    def average_rating(self):
        average = self.ratings.aggregate(avg_rating=Avg("rating"))["avg_rating"]
        return round(average, 1) if average else 0.0

    def preview(self):
        return f"{self.description[:100]}..." if len(self.description) > 100 else self.description

    def get_absolute_url(self):
        return reverse("recipe_detail", args=[str(self.id)])


class RecipeRating(models.Model):
    """Модель оценки рецепта пользователем"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name="ratings")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        unique_together = ("user", "recipe")  # 1 пользователь - 1 оценка

    def __str__(self):
        return f"{self.user.email} - {self.recipe.dish_name}: {self.rating}"

class Favorite(models.Model):
    """Модель сохраненного пользователем рецепта"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "recipe")  # 1 пользователь - 1 сохранение

    def __str__(self):
        return f"{self.user} → {self.recipe}"
    

class UserManager(BaseUserManager):
    """Менеджер пользователей для кастомной модели User"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Создание стафа (на случай, если захочется расширить для него
         права доступа) и суперпользователя"""
        extra_fields.setdefault('is_staff', True)  # Доступ в админку
        extra_fields.setdefault('is_superuser', True)  # Полный доступ

        return self.create_user(email, password, **extra_fields)
    

class User(AbstractUser):
    """Кастомная модель пользователя"""
    username = None  # Убираем стандартный username
    email = models.EmailField(unique=True)  # Email как основной логин
    nickname = models.CharField(max_length=60, unique=True, verbose_name="Никнейм")
    bio = models.TextField(blank=True, verbose_name="Биография")
    avatar = models.ImageField(upload_to="avatars/", default="avatars/default.png",
                               verbose_name="Аватар")
    is_staff = models.BooleanField(default=False)  # Доступ в админку 
    is_superuser = models.BooleanField(default=False)  # Полный доступ

    objects = UserManager()  # Подключаем кастомный менеджер

    USERNAME_FIELD = 'email'  # Логинимся по email
    REQUIRED_FIELDS = []  # Django больше не требует username

    def __str__(self):
        return self.email




    
    
    
