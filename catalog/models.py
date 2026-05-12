"""Library domain models: authors, books, copies, members, loans."""
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    Q,
)
from django.utils import timezone


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class BookQuerySet(models.QuerySet):
    def with_inventory(self):
        return self.annotate(
            total_copies=Count("copies", distinct=True),
            on_loan_copies=Count(
                "copies",
                filter=Q(copies__loans__returned_at__isnull=True),
                distinct=True,
            ),
            available_copies=ExpressionWrapper(
                F("total_copies") - F("on_loan_copies"),
                output_field=IntegerField(),
            ),
        )


class BookManager(models.Manager.from_queryset(BookQuerySet)):
    pass


class Book(models.Model):
    title = models.CharField(max_length=300)
    isbn = models.CharField(
        max_length=20,
        blank=True,
        help_text="Optional; used for Open Library lookup.",
    )
    publication_year = models.PositiveIntegerField(null=True, blank=True)
    authors = models.ManyToManyField(Author, related_name="books", blank=True)

    objects = BookManager()

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class BookCopy(models.Model):
    class Condition(models.TextChoices):
        NEW = "new", "New"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        POOR = "poor", "Poor"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")
    copy_code = models.CharField(max_length=64, unique=True)
    condition = models.CharField(
        max_length=10,
        choices=Condition.choices,
        default=Condition.GOOD,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["copy_code"]
        verbose_name_plural = "book copies"

    def __str__(self) -> str:
        return f"{self.copy_code} ({self.book})"

    def is_on_loan(self) -> bool:
        return self.loans.filter(returned_at__isnull=True).exists()


class MemberProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_profile",
    )
    phone = models.CharField(max_length=32, blank=True)
    max_active_loans = models.PositiveSmallIntegerField(default=5)

    def __str__(self) -> str:
        return self.user.get_username()

    def active_loan_count(self) -> int:
        return self.loans.filter(returned_at__isnull=True).count()


class Loan(models.Model):
    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name="loans")
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name="loans")
    checked_out_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-checked_out_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["book_copy"],
                condition=Q(returned_at__isnull=True),
                name="unique_active_loan_per_copy",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.member} — {self.book_copy}"

    def clean(self) -> None:
        if self.returned_at and self.checked_out_at and self.returned_at < self.checked_out_at:
            raise ValidationError({"returned_at": "Return time cannot be before checkout."})
        if self.due_at and self.checked_out_at and self.due_at < self.checked_out_at:
            raise ValidationError({"due_at": "Due date cannot be before checkout."})

        if self.returned_at is not None:
            return

        qs_copy = Loan.objects.filter(book_copy=self.book_copy, returned_at__isnull=True)
        if self.pk:
            qs_copy = qs_copy.exclude(pk=self.pk)
        if qs_copy.exists():
            raise ValidationError({"book_copy": "This copy already has an active loan."})

        if self.member_id:
            active_for_member = Loan.objects.filter(member=self.member, returned_at__isnull=True)
            if self.pk:
                active_for_member = active_for_member.exclude(pk=self.pk)
            if active_for_member.count() >= self.member.max_active_loans:
                raise ValidationError(
                    {
                        "member": (
                            f"Maximum of {self.member.max_active_loans} active loans reached "
                            "for this member."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        if self.due_at is None and self.checked_out_at:
            self.due_at = self.checked_out_at + timedelta(days=14)
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        return self.returned_at is None

    @property
    def is_overdue(self) -> bool:
        if not self.is_active or self.due_at is None:
            return False
        return timezone.now() > self.due_at
