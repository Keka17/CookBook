from django.urls import path
from django.views.generic import TemplateView

from .views import (BestRecipes, SearchRecipe, CreateRecipe, FavoritesListView,
                    recipe, rate_recipe, add_to_favorites, UserProfileView, profile_view )

urlpatterns = [
    path("", TemplateView.as_view(template_name="main.html"), name="main"),
    path("best/", BestRecipes.as_view(), name="best"),
    path("recipe/<int:pk>/", recipe, name="recipe_detail"),
    path("recipe/<int:pk>/rate/", rate_recipe, name="rate_recipe"),
    path("recipe/<int:pk>/toggle/", add_to_favorites, name='add_to_favorites'),
    path("search/", SearchRecipe.as_view(), name="recipe_search"),
    path("recipe/create/", CreateRecipe.as_view(), name="create_recipe"),

    # Публичный профиль пользователя
    path("profile/<int:pk>/", UserProfileView.as_view(), name="user_profile"),

    # Личный кабинет
    path("personal_account/<str:nickname>/", profile_view, name="account"),
    path("<str:nickname>/favorites/", FavoritesListView.as_view(), name="favorite_recipes")
]