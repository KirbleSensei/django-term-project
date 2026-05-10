"""HTML views for catalog, loans, auth, and Open Library helper."""
import json
from urllib.parse import urlencode

import requests
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    RedirectView,
    UpdateView,
)

from .forms import AuthorForm, BookCopyForm, BookForm, LoanCheckoutForm, SignUpForm
from .models import Author, Book, BookCopy, Loan, MemberProfile


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff


class BookFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    available_only = forms.BooleanField(
        required=False,
        label="Only books with available copies",
    )


class HomeRedirectView(RedirectView):
    pattern_name = "catalog:book-list"
    permanent = False


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "catalog/signup.html"
    success_url = reverse_lazy("catalog:login")

    def form_valid(self, form):
        messages.success(self.request, "Account created. Please log in.")
        return super().form_valid(form)


class BookListView(ListView):
    model = Book
    template_name = "catalog/book_list.html"
    context_object_name = "books"
    paginate_by = 10

    def get_queryset(self):
        qs = Book.objects.with_inventory().prefetch_related("authors").order_by("title")
        self.filter_form = BookFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get("q")
            if q:
                qs = qs.filter(
                    Q(title__icontains=q)
                    | Q(isbn__icontains=q)
                    | Q(authors__name__icontains=q)
                ).distinct()
            if self.filter_form.cleaned_data.get("available_only"):
                qs = qs.filter(available_copies__gt=0)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = getattr(self, "filter_form", BookFilterForm(self.request.GET))
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_querystring"] = urlencode(params)
        return ctx


class BookDetailView(DetailView):
    model = Book
    template_name = "catalog/book_detail.html"
    context_object_name = "book"

    def get_queryset(self):
        return (
            Book.objects.with_inventory()
            .prefetch_related("authors")
            .prefetch_related(
                Prefetch(
                    "copies",
                    queryset=BookCopy.objects.select_related("book"),
                )
            )
        )


class BookCreateView(StaffRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "catalog/book_form.html"
    success_url = reverse_lazy("catalog:book-list")

    def form_valid(self, form):
        messages.success(self.request, "Book created.")
        return super().form_valid(form)


class BookUpdateView(StaffRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "catalog/book_form.html"
    success_url = reverse_lazy("catalog:book-list")

    def form_valid(self, form):
        messages.success(self.request, "Book updated.")
        return super().form_valid(form)


class BookDeleteView(StaffRequiredMixin, DeleteView):
    model = Book
    template_name = "catalog/book_confirm_delete.html"
    success_url = reverse_lazy("catalog:book-list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Book deleted.")
        return super().delete(request, *args, **kwargs)


class AuthorListView(ListView):
    model = Author
    template_name = "catalog/author_list.html"
    context_object_name = "authors"
    paginate_by = 15

    def get_queryset(self):
        return Author.objects.annotate(book_count=Count("books", distinct=True)).order_by("name")


class AuthorDetailView(DetailView):
    model = Author
    template_name = "catalog/author_detail.html"
    context_object_name = "author"

    def get_queryset(self):
        return Author.objects.prefetch_related("books")


class AuthorCreateView(StaffRequiredMixin, CreateView):
    model = Author
    form_class = AuthorForm
    template_name = "catalog/author_form.html"
    success_url = reverse_lazy("catalog:author-list")

    def form_valid(self, form):
        messages.success(self.request, "Author created.")
        return super().form_valid(form)


class AuthorUpdateView(StaffRequiredMixin, UpdateView):
    model = Author
    form_class = AuthorForm
    template_name = "catalog/author_form.html"
    success_url = reverse_lazy("catalog:author-list")

    def form_valid(self, form):
        messages.success(self.request, "Author updated.")
        return super().form_valid(form)


class AuthorDeleteView(StaffRequiredMixin, DeleteView):
    model = Author
    template_name = "catalog/author_confirm_delete.html"
    success_url = reverse_lazy("catalog:author-list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Author deleted.")
        return super().delete(request, *args, **kwargs)


class BookCopyListView(StaffRequiredMixin, ListView):
    model = BookCopy
    template_name = "catalog/bookcopy_list.html"
    context_object_name = "copies"
    paginate_by = 20

    def get_queryset(self):
        qs = BookCopy.objects.select_related("book").order_by("copy_code")
        book_id = self.request.GET.get("book")
        if book_id:
            qs = qs.filter(book_id=book_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["book_filter"] = self.request.GET.get("book", "")
        return ctx


class BookCopyCreateView(StaffRequiredMixin, CreateView):
    model = BookCopy
    form_class = BookCopyForm
    template_name = "catalog/bookcopy_form.html"

    def get_initial(self):
        initial = super().get_initial()
        book_id = self.request.GET.get("book")
        if book_id:
            initial["book"] = book_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Copy added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("catalog:book-detail", kwargs={"pk": self.object.book_id})


class BookCopyUpdateView(StaffRequiredMixin, UpdateView):
    model = BookCopy
    form_class = BookCopyForm
    template_name = "catalog/bookcopy_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Copy updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("catalog:book-detail", kwargs={"pk": self.object.book_id})


class BookCopyDeleteView(StaffRequiredMixin, DeleteView):
    model = BookCopy
    template_name = "catalog/bookcopy_confirm_delete.html"

    def get_success_url(self):
        return reverse("catalog:book-detail", kwargs={"pk": self.object.book_id})

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Copy deleted.")
        return super().delete(request, *args, **kwargs)


class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = "catalog/loan_list.html"
    context_object_name = "loans"
    paginate_by = 15

    def get_queryset(self):
        qs = (
            Loan.objects.select_related("book_copy__book", "member__user")
            .order_by("-checked_out_at")
        )
        if not self.request.user.is_staff:
            profile = getattr(self.request.user, "member_profile", None)
            if profile is None:
                return Loan.objects.none()
            qs = qs.filter(member=profile)
        return qs


class LoanCheckoutView(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanCheckoutForm
    template_name = "catalog/loan_checkout.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        copy_id = self.request.GET.get("copy")
        if copy_id:
            initial["book_copy"] = copy_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Book checked out.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("catalog:loan-list")


class LoanReturnView(LoginRequiredMixin, View):
    """POST to return a copy; supports AJAX (JSON) for in-place updates."""

    def post(self, request, pk):
        loan = get_object_or_404(
            Loan.objects.select_related("member__user"),
            pk=pk,
        )
        if not request.user.is_staff and loan.member.user_id != request.user.id:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
            messages.error(request, "You cannot return this loan.")
            return redirect("catalog:loan-list")

        if loan.returned_at:
            msg = "This loan is already returned."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": msg}, status=400)
            messages.warning(request, msg)
            return redirect("catalog:loan-list")

        loan.returned_at = timezone.now()
        loan.save(update_fields=["returned_at"])
        msg = "Book returned."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "message": msg})
        messages.success(request, msg)
        return redirect("catalog:loan-list")


class OpenLibraryLookupView(StaffRequiredMixin, View):
    """Fetch title from Open Library by ISBN (JSON for book form AJAX)."""

    def get(self, request):
        isbn = (request.GET.get("isbn") or "").replace("-", "").strip()
        if len(isbn) < 10:
            return JsonResponse({"error": "Enter a valid ISBN."}, status=400)
        url = f"https://openlibrary.org/isbn/{isbn}.json"
        try:
            resp = requests.get(url, timeout=8)
        except requests.RequestException:
            return JsonResponse({"error": "Could not reach Open Library."}, status=502)
        if resp.status_code == 404:
            return JsonResponse({"error": "ISBN not found."}, status=404)
        if not resp.ok:
            return JsonResponse({"error": "Unexpected response from Open Library."}, status=502)
        try:
            data = resp.json()
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON from Open Library."}, status=502)
        title = data.get("title", "")
        authors = []
        for a in data.get("authors", [])[:10]:
            key = a.get("key")
            if not key:
                continue
            try:
                ar = requests.get(f"https://openlibrary.org{key}.json", timeout=8)
                if ar.ok:
                    authors.append(ar.json().get("name", ""))
            except requests.RequestException:
                continue
        return JsonResponse({"title": title, "authors": [x for x in authors if x]})
