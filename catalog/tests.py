from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import Author, Book, BookCopy, Loan, MemberProfile


class LoanModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass12345")
        self.member = MemberProfile.objects.get(user=self.user)
        self.author = Author.objects.create(name="Test Author")
        self.book = Book.objects.create(title="Test Book", isbn="")
        self.book.authors.add(self.author)
        self.copy = BookCopy.objects.create(book=self.book, copy_code="T-001")

    def test_cannot_double_loan_copy(self):
        Loan.objects.create(
            book_copy=self.copy,
            member=self.member,
            due_at=timezone.now() + timedelta(days=7),
        )
        dup = Loan(
            book_copy=self.copy,
            member=self.member,
            due_at=timezone.now() + timedelta(days=7),
        )
        with self.assertRaises(ValidationError):
            dup.full_clean()

    def test_max_active_loans(self):
        self.member.max_active_loans = 1
        self.member.save()
        copy2 = BookCopy.objects.create(book=self.book, copy_code="T-002")
        Loan.objects.create(
            book_copy=self.copy,
            member=self.member,
            due_at=timezone.now() + timedelta(days=7),
        )
        second = Loan(
            book_copy=copy2,
            member=self.member,
            due_at=timezone.now() + timedelta(days=7),
        )
        with self.assertRaises(ValidationError):
            second.full_clean()


class BookListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("catalog:book-list")

    def test_book_list_ok(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class StaffBookTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("lib", password="pass12345", is_staff=True)
        self.client.login(username="lib", password="pass12345")

    def test_create_book(self):
        a = Author.objects.create(name="A")
        response = self.client.post(
            reverse("catalog:book-create"),
            {
                "title": "New Title",
                "isbn": "",
                "publication_year": 2020,
                "authors": [a.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Book.objects.filter(title="New Title").exists())


class LoanAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("bob", password="pass12345")
        self.member = MemberProfile.objects.get(user=self.user)
        self.book = Book.objects.create(title="API Book")
        self.copy = BookCopy.objects.create(book=self.book, copy_code="API-1")
        self.client = APIClient()

    def test_loan_list_requires_auth(self):
        url = reverse("api-loan-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_sees_only_own_loans(self):
        Loan.objects.create(
            book_copy=self.copy,
            member=self.member,
            due_at=timezone.now() + timedelta(days=5),
        )
        self.client.login(username="bob", password="pass12345")
        res = self.client.get(reverse("api-loan-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)


class LoanStatusTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("carol", password="pass12345")
        self.member = MemberProfile.objects.get(user=self.user)
        self.book = Book.objects.create(title="Status Book")
        self.copy = BookCopy.objects.create(book=self.book, copy_code="ST-1")

    def test_overdue_active_loan_shows_late_status(self):
        Loan.objects.create(
            book_copy=self.copy,
            member=self.member,
            checked_out_at=timezone.now() - timedelta(days=20),
            due_at=timezone.now() - timedelta(days=3),
        )
        self.client.login(username="carol", password="pass12345")
        response = self.client.get(reverse("catalog:loan-list"))
        self.assertContains(response, "LATE")
        self.assertNotContains(response, '<span class="badge text-bg-warning">Active</span>')

    def test_book_detail_shows_late_for_overdue_copy(self):
        Loan.objects.create(
            book_copy=self.copy,
            member=self.member,
            checked_out_at=timezone.now() - timedelta(days=20),
            due_at=timezone.now() - timedelta(days=1),
        )
        response = self.client.get(reverse("catalog:book-detail", kwargs={"pk": self.book.pk}))
        self.assertContains(response, "LATE")
        self.assertNotContains(response, "ACTIVE")
