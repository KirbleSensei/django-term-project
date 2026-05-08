from rest_framework import serializers

from .models import Author, Book, Loan, MemberProfile


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ("id", "name", "bio")


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all(),
        write_only=True,
        source="authors",
        required=False,
    )

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "isbn",
            "publication_year",
            "authors",
            "author_ids",
        )


class MemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = MemberProfile
        fields = ("id", "username", "phone", "max_active_loans")


class LoanSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book_copy.book.title", read_only=True)
    copy_code = serializers.CharField(source="book_copy.copy_code", read_only=True)
    member_username = serializers.CharField(source="member.user.username", read_only=True)
    member = serializers.PrimaryKeyRelatedField(
        queryset=MemberProfile.objects.select_related("user").all(),
        required=False,
    )

    class Meta:
        model = Loan
        fields = (
            "id",
            "book_copy",
            "member",
            "book_title",
            "copy_code",
            "member_username",
            "checked_out_at",
            "due_at",
            "returned_at",
        )
        read_only_fields = ("checked_out_at", "returned_at")
