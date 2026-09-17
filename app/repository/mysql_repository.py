from __future__ import annotations

from app.domain.enums import UserStatus
from app.domain.models import PasswordResetToken, SocialAccount, User, UserProfile
from app.infrastructure.db.database import Database
from app.repository.interfaces import (
    PasswordResetRepository,
    SocialAccountRepository,
    UserProfileRepository,
    UserRepository,
)


def _row_to_user(row: dict) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        password_hash=row["password_hash"],
        status=UserStatus(row["status"]),
        failed_login_attempts=row["failed_login_attempts"],
        last_login_at=row["last_login_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class MySQLUserRepository(UserRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    def save(self, user: User) -> None:
        query = """
            INSERT INTO users (id, email, password_hash, status, failed_login_attempts,
                                last_login_at, created_at, updated_at)
            VALUES (%(id)s, %(email)s, %(password_hash)s, %(status)s, %(failed_login_attempts)s,
                    %(last_login_at)s, %(created_at)s, %(updated_at)s)
            ON DUPLICATE KEY UPDATE
                password_hash = VALUES(password_hash),
                status = VALUES(status),
                failed_login_attempts = VALUES(failed_login_attempts),
                last_login_at = VALUES(last_login_at),
                updated_at = VALUES(updated_at)
        """
        params = {
            "id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
            "status": user.status.value,
            "failed_login_attempts": user.failed_login_attempts,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            cursor.close()

    def find_by_id(self, user_id: str) -> User | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            cursor.close()
        return _row_to_user(row) if row else None

    def find_by_email(self, email: str) -> User | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
            cursor.close()
        return _row_to_user(row) if row else None

    def exists_by_email(self, email: str) -> bool:
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE email = %s LIMIT 1", (email,))
            found = cursor.fetchone() is not None
            cursor.close()
        return found


class MySQLUserProfileRepository(UserProfileRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    def save(self, profile: UserProfile) -> None:
        query = """
            INSERT INTO user_profiles (user_id, first_name, last_name, avatar_url,
                                        date_of_birth, address_line1, address_line2,
                                        city, state, postal_code, country)
            VALUES (%(user_id)s, %(first_name)s, %(last_name)s, %(avatar_url)s,
                    %(date_of_birth)s, %(address_line1)s, %(address_line2)s,
                    %(city)s, %(state)s, %(postal_code)s, %(country)s)
            ON DUPLICATE KEY UPDATE
                first_name = VALUES(first_name), last_name = VALUES(last_name),
                avatar_url = VALUES(avatar_url), date_of_birth = VALUES(date_of_birth),
                address_line1 = VALUES(address_line1), address_line2 = VALUES(address_line2),
                city = VALUES(city), state = VALUES(state),
                postal_code = VALUES(postal_code), country = VALUES(country)
        """
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, vars(profile))
            cursor.close()

    def find_by_user_id(self, user_id: str) -> UserProfile | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            cursor.close()
        return UserProfile(**row) if row else None


class MySQLSocialAccountRepository(SocialAccountRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    def save(self, account: SocialAccount) -> None:
        query = """
            INSERT INTO social_accounts (id, user_id, provider, provider_user_id, linked_at)
            VALUES (%(id)s, %(user_id)s, %(provider)s, %(provider_user_id)s, %(linked_at)s)
        """
        params = {**vars(account), "provider": account.provider.value}
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            cursor.close()

    def find_by_provider_id(self, provider: str, provider_user_id: str) -> SocialAccount | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM social_accounts WHERE provider = %s AND provider_user_id = %s",
                (provider, provider_user_id),
            )
            row = cursor.fetchone()
            cursor.close()
        return SocialAccount(**row) if row else None


class MySQLPasswordResetRepository(PasswordResetRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    def save(self, token: PasswordResetToken) -> None:
        query = """
            INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at, used, created_at)
            VALUES (%(id)s, %(user_id)s, %(token_hash)s, %(expires_at)s, %(used)s, %(created_at)s)
        """
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, vars(token))
            cursor.close()

    def find_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        query = """
            SELECT * FROM password_reset_tokens
            WHERE token_hash = %s AND used = FALSE AND expires_at > UTC_TIMESTAMP()
        """
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (token_hash,))
            row = cursor.fetchone()
            cursor.close()
        return PasswordResetToken(**row) if row else None

    def mark_used(self, token_id: str) -> None:
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE password_reset_tokens SET used = TRUE WHERE id = %s", (token_id,))
            cursor.close()
