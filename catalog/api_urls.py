from rest_framework.routers import DefaultRouter

from .viewsets import BookViewSet, LoanViewSet

router = DefaultRouter()
router.register(r"books", BookViewSet, basename="api-book")
router.register(r"loans", LoanViewSet, basename="api-loan")

urlpatterns = router.urls
