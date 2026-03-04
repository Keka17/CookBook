from celery import shared_task
from .models import Recipe
from django.core.mail import send_mail
from django.contrib.sites.models import Site

import logging

logger = logging.getLogger(__name__)


def send_email(user, subject, message):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email="noreply@recipesite.com",
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Письмо успешно отправлено {user.email}")
        return True
    except Exception as e:
        logger.exception(f"Ошибка при отправке письма {user.email}: {e}")
        return False


@shared_task
def notify_recipe_saved(recipe_id):
    """Уведомление на почту: рецепт сохранило более 500 человек"""
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        logger.error(f"Рецепт с id={recipe_id} не найден")
        return False

    if not recipe.notified_saved and recipe.favorite_set.count() > 500:
        current_site = Site.objects.get_current()
        url = f"https://{current_site.domain}{recipe.get_absolute_url()}"
        subject = "Поздравляем с безупречным рецептом!"
        message = (
            f'Дорогой кулинар, ваш рецепт "{recipe.dish_name}" был сохранен более 500 раз!'
            f"Это несомненно говорит о вашем выдающемся вкусе. 💫"
            f"\nСтраница рецепта: {url}"
        )

        if send_email(recipe.author, subject, message):
            recipe.notified_saved = True
            recipe.save(update_fields=["notified_saved"])
            return True
    return False


@shared_task
def notify_recipe_top_rated(recipe_id):
    """Уведомление на почту: рецепт попал в топ (рейтинг > 4.7)"""
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        logger.error(f"Рецепт с id={recipe_id} не найден")
        return False

    avg_rating = recipe.average_rating()
    if not recipe.notified_top and avg_rating > 4.7:
        current_site = Site.objects.get_current()
        url = f"https://{current_site.domain}{recipe.get_absolute_url()}"
        subject = "Ваш рецепт сияет среди лучших!"
        message = (
            f'Поздравляем! Ваш рецепт "{recipe.dish_name}" достиг исключительного рейтинга {avg_rating} ⭐️ '
            f"и занял почётное место в нашей коллекции избранного. Это просто безупречно!"
            f"\nСтраница рецепта: {url}"
        )

        if send_email(recipe.author, subject, message):
            recipe.notified_top = True
            recipe.save(update_fields=["notified_top"])
            return True
    return False
