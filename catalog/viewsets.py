from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Book, Loan
from .serializers import BookSerializer, LoanSerializer


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.prefetch_related("authors").all()
    serializer_class = BookSerializer
    permission_classes = [IsStaffOrReadOnly]


class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Loan.objects.select_related("book_copy__book", "member__user").all()
        user = self.request.user
        if not user.is_staff:
            profile = getattr(user, "member_profile", None)
            if profile is None:
                return Loan.objects.none()
            qs = qs.filter(member=profile)
        return qs

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            profile = getattr(self.request.user, "member_profile", None)
            if profile is None:
                raise PermissionDenied("Member profile required.")
            serializer.save(member=profile)
        else:
            serializer.save()

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only staff can update loans via API.")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only staff can delete loans via API.")
        instance.delete()
