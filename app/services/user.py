"""
User services for the application to interact with the database
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, data: UserCreate) -> User:
        if self.users.get_by_email(data.email):
            raise ConflictError("Email already registered")

        user = User(email=data.email, password_hash=hash_password(data.password))
        try:
            self.db.add(user)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Email already registered") from None

        return user
