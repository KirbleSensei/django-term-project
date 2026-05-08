from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Author, Book, BookCopy, Loan, MemberProfile


class CatalogLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("username", "password"):
            self.fields[name].widget.attrs.setdefault("class", "form-control")


def _available_copies_queryset():
    on_loan_ids = Loan.objects.filter(returned_at__isnull=True).values_list(
        "book_copy_id", flat=True
    )
    return BookCopy.objects.exclude(pk__in=on_loan_ids).select_related("book")


class SignUpForm(UserCreationForm):
    phone = forms.CharField(
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("username", "password1", "password2"):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and user.pk:
            profile, _ = MemberProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get("phone", "")
            profile.save(update_fields=["phone"])
        return user


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ("name", "bio")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ("title", "isbn", "publication_year", "authors")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "isbn": forms.TextInput(attrs={"class": "form-control"}),
            "publication_year": forms.NumberInput(attrs={"class": "form-control"}),
            "authors": forms.SelectMultiple(attrs={"class": "form-select", "size": "8"}),
        }


class BookCopyForm(forms.ModelForm):
    class Meta:
        model = BookCopy
        fields = ("book", "copy_code", "condition")
        widgets = {
            "book": forms.Select(attrs={"class": "form-select"}),
            "copy_code": forms.TextInput(attrs={"class": "form-control"}),
            "condition": forms.Select(attrs={"class": "form-select"}),
        }


class LoanCheckoutForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ("book_copy", "member", "due_at")
        widgets = {
            "book_copy": forms.Select(attrs={"class": "form-select"}),
            "member": forms.Select(attrs={"class": "form-select"}),
            "due_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["book_copy"].queryset = _available_copies_queryset()
        self.fields["member"].queryset = MemberProfile.objects.select_related("user")
        if self.user and not self.user.is_staff:
            self.fields.pop("member", None)

    def save(self, commit=True):
        loan = super().save(commit=False)
        if self.user and not self.user.is_staff:
            loan.member = self.user.member_profile
        if commit:
            loan.save()
        return loan
