from django.contrib import admin

from .models import Author, Book, BookCopy, Loan, MemberProfile


class BookCopyInline(admin.TabularInline):
    model = BookCopy
    extra = 0


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "isbn", "publication_year")
    search_fields = ("title", "isbn")
    filter_horizontal = ("authors",)
    inlines = [BookCopyInline]


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ("copy_code", "book", "condition", "created_at")
    list_filter = ("condition",)
    search_fields = ("copy_code", "book__title")


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "max_active_loans")
    search_fields = ("user__username", "phone")


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("book_copy", "member", "checked_out_at", "due_at", "returned_at")
    list_filter = ("returned_at",)
    autocomplete_fields = ("book_copy", "member")
