import datetime
import sqlite3


def main() -> None:
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    now = datetime.datetime.utcnow().replace(microsecond=0)

    cur.execute("SELECT COUNT(*) FROM catalog_book")
    has_books = cur.fetchone()[0] > 0
    if has_books:
        print("Catalog already has data. Skipping inserts.")
    else:
        authors = [
            ("George Orwell", "English novelist and essayist."),
            ("J.K. Rowling", "British author of the Harry Potter series."),
            ("Harper Lee", "American novelist known for To Kill a Mockingbird."),
            ("F. Scott Fitzgerald", "American novelist of the Jazz Age."),
        ]
        cur.executemany("INSERT INTO catalog_author(name, bio) VALUES (?, ?)", authors)

        books = [
            ("1984", "9780451524935", 1949),
            ("Animal Farm", "9780451526342", 1945),
            ("Harry Potter and the Sorcerer's Stone", "9780590353427", 1997),
            ("Harry Potter and the Chamber of Secrets", "9780439064873", 1998),
            ("To Kill a Mockingbird", "9780061120084", 1960),
            ("The Great Gatsby", "9780743273565", 1925),
        ]
        cur.executemany(
            "INSERT INTO catalog_book(title, isbn, publication_year) VALUES (?, ?, ?)",
            books,
        )

        cur.execute("SELECT id, name FROM catalog_author")
        author_ids = {name: pk for pk, name in cur.fetchall()}
        cur.execute("SELECT id, title FROM catalog_book")
        book_ids = {title: pk for pk, title in cur.fetchall()}

        links = [
            (book_ids["1984"], author_ids["George Orwell"]),
            (book_ids["Animal Farm"], author_ids["George Orwell"]),
            (book_ids["Harry Potter and the Sorcerer's Stone"], author_ids["J.K. Rowling"]),
            (book_ids["Harry Potter and the Chamber of Secrets"], author_ids["J.K. Rowling"]),
            (book_ids["To Kill a Mockingbird"], author_ids["Harper Lee"]),
            (book_ids["The Great Gatsby"], author_ids["F. Scott Fitzgerald"]),
        ]
        cur.executemany(
            "INSERT INTO catalog_book_authors(book_id, author_id) VALUES (?, ?)",
            links,
        )

        copies = []
        for title, book_id in book_ids.items():
            prefix = "".join(ch for ch in title if ch.isalnum())[:3].upper()
            for i in (1, 2):
                copy_code = f"{prefix}{book_id}-{i:03d}"
                condition = "good" if i == 1 else "new"
                copies.append((copy_code, condition, now.isoformat(" "), book_id))
        cur.executemany(
            "INSERT INTO catalog_bookcopy(copy_code, condition, created_at, book_id) VALUES (?, ?, ?, ?)",
            copies,
        )

        cur.execute("SELECT id FROM catalog_memberprofile ORDER BY id LIMIT 1")
        member = cur.fetchone()
        member_id = member[0] if member else None
        if member_id is None:
            cur.execute("SELECT id FROM auth_user ORDER BY id LIMIT 1")
            user = cur.fetchone()
            if user:
                cur.execute(
                    "INSERT INTO catalog_memberprofile(phone, max_active_loans, user_id) VALUES (?, ?, ?)",
                    ("", 5, user[0]),
                )
                member_id = cur.lastrowid

        if member_id:
            cur.execute("SELECT id FROM catalog_bookcopy ORDER BY id LIMIT 1")
            copy_1 = cur.fetchone()[0]
            cur.execute("SELECT id FROM catalog_bookcopy ORDER BY id LIMIT 1 OFFSET 1")
            copy_2 = cur.fetchone()[0]

            checked_1 = (now - datetime.timedelta(days=3)).isoformat(" ")
            due_1 = (now + datetime.timedelta(days=11)).isoformat(" ")
            checked_2 = (now - datetime.timedelta(days=20)).isoformat(" ")
            due_2 = (now - datetime.timedelta(days=6)).isoformat(" ")
            returned_2 = (now - datetime.timedelta(days=4)).isoformat(" ")

            cur.execute(
                "INSERT INTO catalog_loan(checked_out_at, due_at, returned_at, book_copy_id, member_id) VALUES (?, ?, ?, ?, ?)",
                (checked_1, due_1, None, copy_1, member_id),
            )
            cur.execute(
                "INSERT INTO catalog_loan(checked_out_at, due_at, returned_at, book_copy_id, member_id) VALUES (?, ?, ?, ?, ?)",
                (checked_2, due_2, returned_2, copy_2, member_id),
            )

    conn.commit()
    for table in ("catalog_author", "catalog_book", "catalog_bookcopy", "catalog_loan"):
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(table, cur.fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main()
