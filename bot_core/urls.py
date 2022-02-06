from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from bot_core.views import TutorialBotView

urlpatterns = [
    path('expense/', csrf_exempt(TutorialBotView.as_view())),
]
