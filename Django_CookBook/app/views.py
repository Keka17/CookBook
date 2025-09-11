from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.mail import send_mail


from .models import Recipe, User, Category, RecipeRating, Favorite
from .forms import RecipeForm, SignUpForm
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import (ListView, DetailView,
                                  CreateView, UpdateView, DeleteView)
from django.db.models import Avg, Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class BestRecipes(ListView):
    """Страница с лучшими рецептами"""
    model = Recipe
    template_name = "best.html"
    context_object_name = "recipes"
    paginate_by = 10

    def get_queryset(self):
        """Фильтрация рецептов с рейтингом > 4.7
        Сортировка по убыванию; возможность фильтрации по категориям"""

        # Базовый queryset с аннотациями среднего рейтинга и количества оценок
        queryset = super().get_queryset().annotate(
            average_rating=Avg("ratings__rating"),
            rating_count=Count("ratings")
        ).filter(
            average_rating__gte=4.7).order_by("-created_at")

        # Фильтрацию по категориям через GET-запрос
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        """Добавление всех категорий в контекст для фильтрации"""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class SearchRecipe(ListView):
    """Класс поиска рецептов"""
    model = Recipe
    template_name = "search.html"
    context_object_name = "recipes"
    paginate_by = 10

    def get_queryset(self):
        """Функция возвращает queryset рецептов, отфильтрованных по
        названию блюда, никнейму автора  и категории (выбор через sidebar)"""
        queryset = Recipe.objects.all().order_by('-created_at')

        # Получение данных из GET-запроса
        query = self.request.GET.get("q", "").strip()  # Удаление пробелов в поисковом запросе
        category_id = self.request.GET.get("category")

        # Фильтрация по названию и никнейму автора
        # Нормализация запроса: первая буква заглавная, остальные — маленькие
        if query:
            normalized_query = query.capitalize()

            queryset = queryset.filter(
                Q(dish_name__icontains=normalized_query) |
                Q(author__nickname__icontains=normalized_query)
            )

        # Фильтрация по категории
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        """Добавление в контекст всех категорий, поисковой запрос
        и выбранную категорию"""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')

        return context


class CreateRecipe(LoginRequiredMixin, CreateView):
    """Создание рецепта авторизованным пользователем"""
    model = Recipe
    form_class = RecipeForm
    template_name = "create.html"

    def form_valid(self, form):
        form.instance.author = self.request.user  # Автоматическое добавление автора
        return super().form_valid(form)

    # Перенаправление на созданный рецепт
    def get_success_url(self):
        return reverse_lazy("recipe_detail", kwargs={"pk": self.object.pk})


class UpdateRecipe(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование рецепта только его автором"""
    model = Recipe
    form_class = RecipeForm
    template_name = "create.html"
    raise_exception = True  # Ошибка 403 - Fordbidden

    # Перенаправление на отредактированный рецепт
    def get_success_url(self):
        return reverse_lazy("recipe_detail", kwargs={"pk": self.object.pk})

    def test_func(self):
        """Проверка, является ли пользователь автором рецепта"""
        recipe = self.get_object()
        return self.request.user == recipe.author

    def get_form(self, form_class=None):
        """Ограничение на редактируемые поля"""
        form = super().get_form(form_class)

        # Разрешенные поля
        allowed_fields = self.request.GET.get(
            "fields", "description,picture,text").split(",")

        for field_name in list(form.fields.keys()):
            if field_name not in allowed_fields:
                form.fields.pop(field_name)

        return form


class DeleteRecipe(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление рецепта только его автором"""
    model = Recipe
    template_name = "recipe_delete.html"
    success_url = reverse_lazy("my_recipes")
    raise_exception = True  # Ошибка 403 - Fordbidden

    def test_func(self):
        """Проверка авторства"""
        recipe = self.get_object()
        return self.request.user == recipe.author

    def get_success_url(self):
        nickname = self.kwargs.get("nickname")
        return reverse_lazy("my_recipes", kwargs={"nickname": nickname})


def recipe(request, pk):
    """Конкретный рецепт; авторизованные пользователи
    видят свою оценку рецепта"""
    recipe = get_object_or_404(Recipe, pk=pk)  # Безопасное извлечение объекта

    user_rating = None
    is_favorite = False

    # Провека авторизациид для показа оценки
    if request.user.is_authenticated:
        try:
            rating_obj = RecipeRating.objects.get(user=request.user, recipe=recipe)
            user_rating = int(rating_obj.rating) if rating_obj else None
        except RecipeRating.DoesNotExist:
            pass

        # Проверка факта сохранения в Избранном
        is_favorite = Favorite.objects.filter(user=request.user, recipe=recipe).exists()

    context = {
        "recipe": recipe,
        "user_rating": user_rating,  # Оценка текущего пользователя
        "is_favorite": is_favorite,  # Передача в шаблон
    }

    return render(request, "recipe.html", context)


@login_required
def rate_recipe(request, pk):
    """Обработка оценки рецепта авторизованным пользователем;
    функция создает или обновляет оценку"""
    recipe = get_object_or_404(Recipe, pk=pk)

    # Получение оценки из POST-запроса
    rating_value = int(request.POST.get("rating"))

    # Создание/обновление оценки
    rating_obj, created = RecipeRating.objects.update_or_create(
        user=request.user, recipe=recipe,
        defaults={"rating": rating_value}
    )

    # Перенаправление на страницу рецепта
    return redirect('recipe_detail', pk=recipe.pk)


@login_required
def add_to_favorites(request, pk):
    """Обработка AJAX-запроса для добавления/удаления рецепта из изрбанного
    с проверкой на авторизованность"""
    recipe = get_object_or_404(Recipe, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)

    if not created:
        favorite.delete()  # Удаление из избранного, если ранее добавлен
        return JsonResponse({"status": "removed"})
    else:
        # Добавлен в избранное
        return JsonResponse({"status": "added"})


class UserProfileView(DetailView):
    """Публичный профиль пользователя с возможностью
    фильтрации опубликованных рецептов по категориям"""
    model = User
    template_name = "user_profile.html"
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Все рецепты пользователя
        recipes_qs = Recipe.objects.filter(author=self.object).order_by("-created_at")

        # Фильтрацию по категориям через GET-запрос
        category_id = self.request.GET.get("category")
        if category_id:
            recipes_qs = recipes_qs.filter(category__id=category_id)
            context["current_category"] = Category.objects.get(pk=category_id)
        else:
            context["current_category"] = None

        context["recipes"] = recipes_qs

        # Список всех категорий (sidbar)
        context["categories"] = Category.objects.all()

        return context


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирования профиля в ЛК;
    доступно только владельцу аккаунта, никнейм неизменяем """
    model = User
    form_class = SignUpForm
    template_name = "account/edit_account.html"

    # Поиск пользователя по никнейму (slug), а не pk
    slug_field = "nickname"  #
    slug_url_kwarg = "nickname"

    raise_exception = True  # Ошибка 403 - Fordbidden, если test_func = False

    def test_func(self):
        """Проверка на возможность редактирования - только обладатель аккаунта"""
        user = self.get_object()  # Получение пользоваиеля по slug из URL
        return self.request.user == user

    def get_form(self, form_class=None):
        """Никнейм только для чтения - неизменяемое поле"""
        form = super().get_form(form_class)
        form.fields["nickname"].disabled = True
        return form

    def form_valid(self, form):
        """Обработка удаления аватара, если нажата кнопка 'Удалить аватар'"""
        response = super().form_valid(form)
        if self.request.POST.get("delete_avatar") == "1":
            self.object.avatar.delete(save=False)  # удалить файл с диска
            self.object.avatar = None  # сохранение в базе как None
            self.object.save()
        return response

    def get_success_url(self):
        """После успешного редактирования профиля - возврат в ЛК"""
        return reverse_lazy("account", kwargs={
            "nickname": self.request.user.nickname})


@login_required
def profile_view(request, nickname):
    """"Личный кабинет пользователя"""
    profile_user = get_object_or_404(User, nickname=nickname)

    # Опубликованные пользователем рецепты (последние 4)
    my_recipes = Recipe.objects.filter(author=profile_user).order_by("-created_at")[:4]

    # Избранные рецепты (последние 4)
    favorite_recipes = Recipe.objects.filter(
        favorite__user=profile_user).order_by("-favorite__created_at")[:4]

    context = {
        "profile_user": profile_user,
        "my_recipes": my_recipes,
        "favorite_recipes": favorite_recipes,
    }

    return render(request, "account/personal_account.html", context)

@login_required
def delete_account(request):
    """Удаление аккаунта через POST-запрос, AJAX не перегружает страницу"""
    if request.method == "POST" and request.user.is_authenticated:
        request.user.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

class FavoritesListView(ListView):
    """Избранные рецепты пользователя с фильтрацией по категориям"""
    model = Recipe
    template_name = "account/favorites.html"
    context_object_name = "recipes"
    paginate_by = 8

    def get_queryset(self):
        """Выбор избранных рецептов с фильтрацией по категориям"""
        nickname = self.kwargs.get("nickname")
        profile_user = get_object_or_404(User, nickname=nickname)

        # Все сохраненные рецепты
        queryset = Recipe.objects.filter(
            favorite__user=profile_user).order_by("-favorite__created_at")

        # Фильтрацию по категориям через GET-запрос
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        """Добавление в контекст категорий и владельца профиля"""
        context = super().get_context_data(**kwargs)
        nickname = self.kwargs.get("nickname")
        profile_user = get_object_or_404(User, nickname=nickname)

        context["categories"] = Category.objects.all()
        context["profile_user"] = profile_user
        return context


class MyRecipesListView(ListView):
    """Опубликованные рецепты пользователя с фильтрацией по категориям"""
    model = Recipe
    template_name = "account/my_recipes.html"
    context_object_name = "recipes"
    paginate_by = 8

    def get_queryset(self):
        """Опубликованные рецепты с фильтрацией по категориям"""
        nickname = self.kwargs.get("nickname")
        profile_user = get_object_or_404(User, nickname=nickname)

        # Все опубликованные рецепты
        queryset = Recipe.objects.filter(author=profile_user).order_by("-created_at")

        # Фильтрацию по категориям через GET-запрос
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        """Добавление в контекст категорий и владельца профиля"""
        context = super().get_context_data(**kwargs)
        nickname = self.kwargs.get("nickname")
        profile_user = get_object_or_404(User, nickname=nickname)

        context["categories"] = Category.objects.all()
        context["profile_user"] = profile_user
        return context


# Процесс регистрации с верификацией почты через сгенерированный код
# Модуль secrets предпочтительнее random, так как являтеся криптографичечки надежнее
import secrets

verification_codes = {}

def generate_verification_code():
    """Генерация 6-значного кода"""
    random_int = secrets.randbelow(1000000)
    return str(f"{random_int:06d}")


def save_verification_data(email, form_data, code_expiry=300, data_expire=1800):
    """
    Сохранение кода и данных формы в Redis.
    - code_expire: время жизни кода (300 сек = 5 мин)
    - data_expire: время жизни данных формы (1800 сек = 30 минут)
    """

    code = generate_verification_code()

    # Словарь для хранения формы
    data = {"form_data": form_data}

    # Если загружен аватар  → сохранение во временной директории tmp
    # default_storage.save возвращает путь к сохраненному файлу
    avatar_file = form_data.get("avatar")
    if avatar_file:
        avatar_path = default_storage.save(
            f"tmp/{avatar_file.name}", ContentFile(avatar_file.read())
        )
        data["avatar_path"] = avatar_path
        # Убираем файл из form_data, чтобы он не хранился в Redis
        data["form_data"].pop("avatar", None)

    # Сохранение кода и данных формы на заданное время
    cache.set(f"form:{email}", data, timeout=data_expire)
    cache.set(f"code:{email}", code, timeout=code_expiry)

    return code


def load_verification_data(email):
    """Функция возвращает кортеж (form_data, code) из Redis"""
    form_data = cache.get(f"form:{email}")
    code = cache.get(f"code:{email}")
    return form_data, code


def delete_verification_data(email):
    """Удаление данных и кода после успешной верификации или истечения сроков"""
    data = cache.get(f"form:{email}")

    # Удаление временного аватара
    if data and "avatar_path" in data:
        try:
            default_storage.delete(data["avatar_path"])
        except Exception as e:
            print(f"Ошибка при удалении временного аватара: {e}")

    cache.delete(f"form:{email}")
    cache.delete(f"code:{email}")


class SignUpView(View):
    """Регистрация нового пользователя с подтверждением email-а"""
    def get(self, request):
        form = SignUpForm()
        return render(request, "auth/signup.html", {"form": form})

    def post(self, request):
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # Генерация кода и сохранение данных формы в Redis
            code = save_verification_data(email, form.cleaned_data)

            send_mail(
                subject="Подтверждение регистрации",
                message=f"Ваш код подтверждения: {code}."
                        f" Код действителен в течение 5 минут.",
                from_email="noreply@recipesite.com",
                recipient_list=[email],
            )

            messages.info(request, "Код подтверждения был отправлен на ваш email.")
            return redirect("verify_email", email=email)

        return render(request, "auth/signup.html", {"form": form})


class VerifyEmailView(View):
    """Проверка введённого кода для подтверждения email-а"""
    def get(self, request, email):
        """Отображение страницы для ввода кода"""
        return render(request, "auth/verify_email.html", {"email": email})

    def post(self, request, email):
        """Обработка введенного кода и создание пользователя в случае совпадения"""
        entered_code = request.POST.get("code")
        stored_data, saved_code = load_verification_data(email)  # Получение кода и данных из Redis

        # Проверка наличия формы
        if not stored_data:
            avatar_path = request.POST.get("avatar_path")
            if avatar_path:
                try:
                    default_storage.delete(avatar_path)
                except Exception as e:
                    print(f"Ошибка при удалении временного аватара: {e}")

            return JsonResponse({
                "success": False,
                "error": "Данные формы не найдены. Попробуйте зарегестрироваться снова."
            })

        form_data = stored_data.get("form_data", {})

        # Проверка наличия кода
        if not saved_code:
            return JsonResponse({
                "success": False,
                "error": "Срок действия кода истек. Запросите новый."})

        # Проверка совпадения кодов
        if entered_code != saved_code:
            return JsonResponse({
                "success": False,
                "error": "Неверный код. Попробуйте еще раз."})

        # Создание пользователя с основными полями, без аватара
        # create_user хэширует пароль и сохраняет объект в базе
        user = User.objects.create_user(
            email=form_data["email"],
            nickname=form_data["nickname"],
            bio=form_data.get("bio", ""),
            password=form_data["password1"]
        )
        # Удаляем данные формы и код из Redis
        delete_verification_data(email)

        return JsonResponse({"success": True})

class ResendCodeView(View):
    """Повторная отправка кода подтверждения по истечении 5 минут"""
    def post(self, request, email):
        form_data = cache.get(f"form:{email}")

        if not form_data:
            return JsonResponse({
                "success": False,
                "error": "Данные формы не найдены. Попробуйте зарегестрироваться снова."})

        # Генерация нового кода и обновления Redis (форма остается)
        code = save_verification_data(email, form_data["form_data"], code_expiry=300)

        send_mail(
            subject="Подтверждение регистрации",
            message=f"Ваш код подтверждения: {code}."
                    f" Код действителен в течение 5 минут.",
            from_email="noreply@recipesite.com",
            recipient_list=[email],
        )

        return JsonResponse({
            "success": True,
            "message": "",
        })


# Вьюхи для проверки уникальности никнейма и email-а на фронте
def check_nickname(request):
    nickname = request.GET.get("nickname", "").strip()
    exists = User.objects.filter(nickname__iexact=nickname).exists()
    return JsonResponse({"exists": exists})

def check_email(request):
    email = request.GET.get("email", "").strip()
    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({"exists": exists})


class CustomPasswordResetView(PasswordResetView):
    """Отправка ссылки на сброс пароля"""
    email_template_name = "auth/password_reset_email.html"
    subject_template_name = "auth/password_reset_subject.txt"
    success_url = reverse_lazy("login")  # Перенаправляем после успешного сброса пароля

    def post(self, request, *args, **kwargs):
        # Получение email-а из POST-запроса
        email = request.POST.get("email")

        if not email:
            return JsonResponse({
                "success": False,
                "error": "Введите email"})

        # Проверка на существование пользователя с таким email в БД
        # Возвращаем успех даже если  пользователя с таким email не существует
        # Безопасный ход - не раскрываются зарегестрированные email

        if User.objects.filter(email=email).exists():
            # Если email есть в базе — шлём письмо через стандартную механику
            super().post(request, *args, **kwargs)

        return JsonResponse({"success": True})


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "auth/password_reset_confirm.html"
    success_url = reverse_lazy("login")