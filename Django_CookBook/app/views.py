
from django.shortcuts import render, redirect
from .models import Recipe, User, Category, RecipeRating
from django.shortcuts import render, get_object_or_404
from django.views.generic import (ListView, DetailView,
                                  CreateView, UpdateView, DeleteView, TemplateView)
from django.db.models import Avg, Count
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower


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
            average_rating__gte=4.7).order_by("-average_rating")

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


class SearchRecipes(ListView):
    """Класс поиска рецептов"""
    model = Recipe
    template_name = "search.html"
    context_object_name = "recipes"
    paginate_by = 6

    def get_queryset(self):
        """Функция возвращает queryset рецептов, отфильтрованных по
        названию блюда и категории (выбор через sidebar)"""
        queryset = Recipe.objects.all()

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


def recipe(request, pk):
    """Конкретный рецепт; авторизованные пользователи
    видят свою оценку рецепта"""
    recipe = get_object_or_404(Recipe, pk=pk)  # Безопасное извлечение объекта

    user_rating = None

    # Провека авторизациид для показа оценки
    if request.user.is_authenticated:
        try:
            rating_obj = RecipeRating.objects.get(user=request.user, recipe=recipe)
            user_rating = int(rating_obj.rating) if rating_obj else None
        except RecipeRating.DoesNotExist:
            pass

    context = {
        "recipe": recipe,
        "user_rating": user_rating,  # Оценка текущего пользователя
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