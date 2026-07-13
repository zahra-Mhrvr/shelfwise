from rest_framework.routers import DefaultRouter

from .views import BookViewSet, LoanViewSet, MemberViewSet

router = DefaultRouter()
router.register("books", BookViewSet)
router.register("members", MemberViewSet)
router.register("loans", LoanViewSet)

urlpatterns = router.urls
