from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from .models import Favorite, RecipeRating
from .tasks import notify_recipe_saved, notify_recipe_top_rated


@receiver(post_save, sender=Favorite)
def favorite_added(sender, instance, created, **kwargs):
    if created:
        notify_recipe_saved(instance.recipe.id)


@receiver(post_save, sender=RecipeRating)
def rating_added_or_updated(sender, instance, created, **kwargs):
    notify_recipe_top_rated.delay(instance.recipe.id)