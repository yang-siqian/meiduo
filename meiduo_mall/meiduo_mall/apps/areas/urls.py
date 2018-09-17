from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'areas', views.AreasViewSet, base_name='areas')

urlpatterns = []

urlpatterns += router.urls