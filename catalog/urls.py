from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import CatalogLoginForm

app_name = "catalog"

urlpatterns = [
    path("", views.HomeRedirectView.as_view(), name="home"),
    path("books/", views.BookListView.as_view(), name="book-list"),
    path("books/new/", views.BookCreateView.as_view(), name="book-create"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book-detail"),
    path("books/<int:pk>/edit/", views.BookUpdateView.as_view(), name="book-update"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book-delete"),
    path("authors/", views.AuthorListView.as_view(), name="author-list"),
    path("authors/new/", views.AuthorCreateView.as_view(), name="author-create"),
    path("authors/<int:pk>/", views.AuthorDetailView.as_view(), name="author-detail"),
    path("authors/<int:pk>/edit/", views.AuthorUpdateView.as_view(), name="author-update"),
    path("authors/<int:pk>/delete/", views.AuthorDeleteView.as_view(), name="author-delete"),
    path("copies/", views.BookCopyListView.as_view(), name="bookcopy-list"),
    path("copies/new/", views.BookCopyCreateView.as_view(), name="bookcopy-create"),
    path("copies/<int:pk>/edit/", views.BookCopyUpdateView.as_view(), name="bookcopy-update"),
    path("copies/<int:pk>/delete/", views.BookCopyDeleteView.as_view(), name="bookcopy-delete"),
    path("loans/", views.LoanListView.as_view(), name="loan-list"),
    path("loans/checkout/", views.LoanCheckoutView.as_view(), name="loan-checkout"),
    path("loans/<int:pk>/return/", views.LoanReturnView.as_view(), name="loan-return"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=CatalogLoginForm,
        ),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("staff/openlibrary/", views.OpenLibraryLookupView.as_view(), name="openlibrary-lookup"),
]
