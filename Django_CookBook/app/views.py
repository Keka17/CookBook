from audioop import reverse
from lib2to3.fixes.fix_input import context

from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from .models import Recipe, User, Category, RecipeRating, Favorite
from .forms import RecipeForm
from django.shortcuts import render, get_object_or_404
from django.views.generic import (ListView, DetailView,
                                  CreateView, UpdateView, DeleteView, TemplateView)
from django.db.models import Avg, Count
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class BestRecipes(ListView):
    """Страница с лучшими рецептами"""
    model = Recipe
    template_name = "best.html"
    context_object_name = "recipes"
    paginate_by = 6

    def get_queryset(self):
        """Фильтрация рецептов с рейтингом >= 4.7.
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
    paginate_by = 6

    def get_queryset(self):
        """Функция возвращает queryset рецептов, отфильтрованных по
        названию блюда и категории (выбор через sidebar)"""
        queryset = Recipe.objects.all().order_by('-created_at')

        # Получение данных из GET-запроса
        query = self.request.GET.get("q", "").strip()  # Удаление пробелов в поисковом запросе
        category_id = self.request.GET.get("category")

        # Фильтрация по названию
        if query:
            queryset = queryset.filter(dish_name__icontains=query)

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


class UpdateRecipe(UserPassesTestMixin, UpdateView):
    """Редактирование рецепта только его автором"""
    model = Recipe
    form_class = RecipeForm
    template_name = "create.html"

    # Перенаправление на отредактированный рецепт
    def get_success_url(self):
        return reverse_lazy("recipe_detail", kwargs={"pk": self.object.pk})

    def test_func(self):
        """Проверка, является ли пользователь автором рецепта"""
        ad = self.get_object()
        return self.request.user == ad.author

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


class DeleteRecipe(UserPassesTestMixin, DeleteView):
    """Удаление рецепта только его автором"""
    model = Recipe
    template_name = "recipe_delete.html"
    success_url = reverse_lazy("my_recipes")

    def test_func(self):
        """Проверка авторства"""
        ad = self.get_object()
        return self.request.user == ad.author

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





