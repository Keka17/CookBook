from django.shortcuts import render, redirect
from .models import Recipe, User, Category, RecipeRating
from django.shortcuts import render, get_object_or_404
from django.views.generic import (ListView, DetailView,
                                  CreateView, UpdateView, DeleteView, TemplateView)
from django.db.models import Avg, Count
from django.contrib.auth.decorators import login_required


class BestRecipes(ListView):
    """Страница с лучиши рецептами"""
    model = Recipe
    template_name = "best.html"
    context_object_name = "recipes"
    paginate_by = 6

    def get_queryset(self):
        """Фильтрация по категориям"""
        queryset = super().get_queryset().annotate(
            average_rating=Avg("ratings__rating"),
            rating_count=Count("ratings")
        ).filter(
            average_rating__gte=4.7).order_by("-average_rating")

        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        """Добавление категорий в контекст для фильтрации"""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


def recipe(request, pk):
    """Конкретный рецепт"""
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, "recipe.html",
                  {"recipe": recipe})

@login_required
def rate_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    rating_value = int(request.POST.get("rating"))
    rating_obj, created = RecipeRating.objects.update_or_create(
        user=request.user, recipe=recipe,
        defaults={"rating": rating_value}
    )

    return redirect('recipe', pk=recipe.pk)