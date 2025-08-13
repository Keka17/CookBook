from django.urls import path
from django.views.generic import TemplateView

from .views import BestRecipes, SearchRecipes, recipe, rate_recipe

urlpatterns = [
    path("", TemplateView.as_view(template_name="main.html"), name="main"),
    path("best", BestRecipes.as_view(), name="best"),
    path("recipe/<int:pk>", recipe, name="recipe_detail"),
    path("recipe/<int:pk>/rate/", rate_recipe, name="rate_recipe"),
    path("search", SearchRecipes.as_view(), name="recipe_search")

]