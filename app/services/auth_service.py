"""
Authentication service for user management and JWT token handling.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.models.schemas import User, UserInDB, TokenData
from app.core.config import get_settings

# Try to import authentication dependencies, fallback to basic implementation
try:
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    JOSE_AVAILABLE = True
    PASSLIB_AVAILABLE = True
    # Password hashing context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    JOSE_AVAILABLE = False
    PASSLIB_AVAILABLE = False
    print("⚠️  Authentication dependencies not installed. Using basic fallback authentication.")
    print("   Install with: pip install python-jose[cryptography] passlib[bcrypt]")

# Get settings
settings = get_settings()

# JWT settings
SECRET_KEY = getattr(settings, 'jwt_secret_key', "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, 'access_token_expire_minutes', 480)  # 8 hours

# Simple fallback password verification (NOT SECURE - for development only)
def simple_hash_password(password: str) -> str:
    """Simple password hashing fallback (NOT SECURE)."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def simple_verify_password(plain_password: str, hashed_password: str) -> bool:
    """Simple password verification fallback (NOT SECURE)."""
    if hashed_password.startswith("$2b$"):  # bcrypt hash
        return PASSLIB_AVAILABLE and pwd_context.verify(plain_password, hashed_password)
    else:  # simple hash
        return simple_hash_password(plain_password) == hashed_password

# In-memory user database (will be initialized after imports)
fake_users_db: Dict[str, UserInDB] = {}


class AuthService:
    """Authentication service for handling user authentication and JWT tokens."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        if PASSLIB_AVAILABLE:
            return pwd_context.verify(plain_password, hashed_password)
        else:
            return simple_verify_password(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        if PASSLIB_AVAILABLE:
            return pwd_context.hash(password)
        else:
            return simple_hash_password(password)

    @staticmethod
    def get_user(username: str) -> Optional[UserInDB]:
        """Get user from database by username."""
        return fake_users_db.get(username)

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password."""
        user = AuthService.get_user(username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        if not JOSE_AVAILABLE:
            # Fallback: create a simple token (NOT SECURE - for development only)
            import json
            import base64
            payload = {
                "sub": data.get("sub"),
                "exp": (datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))).timestamp()
            }
            token_data = json.dumps(payload).encode()
            return base64.b64encode(token_data).decode()

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data."""
        if not JOSE_AVAILABLE:
            # Fallback: decode simple token (NOT SECURE - for development only)
            try:
                import json
                import base64
                token_data = json.loads(base64.b64decode(token.encode()).decode())
                username = token_data.get("sub")
                exp = token_data.get("exp")

                # Check expiration
                if exp and datetime.utcnow().timestamp() > exp:
                    return None

                if username is None:
                    return None
                return TokenData(username=username)
            except Exception:
                return None

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            token_data = TokenData(username=username)
            return token_data
        except JWTError:
            return None

    @staticmethod
    def get_current_user(token: str) -> Optional[User]:
        """Get current user from JWT token."""
        token_data = AuthService.verify_token(token)
        if token_data is None:
            return None

        user = AuthService.get_user(username=token_data.username)
        if user is None:
            return None

        return User(
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            role=getattr(user, 'role', 'user'),
            created_at=getattr(user, 'created_at', None),
            last_login=getattr(user, 'last_login', None)
        )

    @staticmethod
    def add_user(username: str, password: str, full_name: Optional[str] = None,
                 email: Optional[str] = None, role: str = "user") -> UserInDB:
        """Add a new user to the database."""
        if username in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        from datetime import datetime
        hashed_password = AuthService.get_password_hash(password)
        user = UserInDB(
            username=username,
            full_name=full_name or username,
            email=email or f"{username}@company.com",
            hashed_password=hashed_password,
            is_active=True,
            role=role,
            created_at=datetime.now().isoformat(),
            last_login=None
        )
        fake_users_db[username] = user

        # Save to file
        AuthService.save_users_to_file()
        return user

    @staticmethod
    def change_password(username: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        user = AuthService.authenticate_user(username, old_password)
        if not user:
            return False
        
        new_hashed_password = AuthService.get_password_hash(new_password)
        fake_users_db[username].hashed_password = new_hashed_password
        return True

    @staticmethod
    def deactivate_user(username: str) -> bool:
        """Deactivate a user account."""
        if username not in fake_users_db:
            return False
        fake_users_db[username].is_active = False
        return True

    @staticmethod
    def activate_user(username: str) -> bool:
        """Activate a user account."""
        if username not in fake_users_db:
            return False
        fake_users_db[username].is_active = True
        return True

    @staticmethod
    def list_users() -> Dict[str, User]:
        """List all users (without passwords)."""
        return {
            username: User(
                username=user.username,
                full_name=user.full_name,
                email=user.email,
                is_active=user.is_active,
                role=getattr(user, 'role', 'user'),
                created_at=getattr(user, 'created_at', None),
                last_login=getattr(user, 'last_login', None)
            )
            for username, user in fake_users_db.items()
        }

    @staticmethod
    def save_users_to_file():
        """Save users to JSON file."""
        try:
            import json
            from pathlib import Path

            users_data = {
                "users": {},
                "metadata": {
                    "version": "2.0",
                    "last_updated": datetime.now().isoformat()
                }
            }

            for username, user in fake_users_db.items():
                users_data["users"][username] = {
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "hashed_password": user.hashed_password,
                    "is_active": user.is_active,
                    "role": getattr(user, 'role', 'user'),
                    "created_at": getattr(user, 'created_at', None),
                    "last_login": getattr(user, 'last_login', None)
                }

            users_file = Path("users.json")
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Warning: Could not save users to file: {e}")

    @staticmethod
    def load_users_from_file():
        """Load users from JSON file."""
        try:
            import json
            from pathlib import Path

            users_file = Path("users.json")
            if not users_file.exists():
                return {}

            with open(users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            users = {}
            for username, user_data in data.get("users", {}).items():
                users[username] = UserInDB(
                    username=user_data["username"],
                    full_name=user_data["full_name"],
                    email=user_data["email"],
                    hashed_password=user_data["hashed_password"],
                    is_active=user_data["is_active"],
                    role=user_data.get("role", "user"),
                    created_at=user_data.get("created_at"),
                    last_login=user_data.get("last_login")
                )
            return users

        except Exception as e:
            print(f"Warning: Could not load users from file: {e}")
            return {}

    @staticmethod
    def update_last_login(username: str):
        """Update user's last login timestamp."""
        if username in fake_users_db:
            fake_users_db[username].last_login = datetime.now().isoformat()
            AuthService.save_users_to_file()

    @staticmethod
    def update_user(username: str, full_name: Optional[str] = None,
                   email: Optional[str] = None, role: Optional[str] = None,
                   is_active: Optional[bool] = None) -> UserInDB:
        """Update user information."""
        if username not in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user = fake_users_db[username]

        if full_name is not None:
            user.full_name = full_name
        if email is not None:
            user.email = email
        if role is not None and role in ["admin", "chef", "user"]:
            user.role = role
        if is_active is not None:
            user.is_active = is_active

        fake_users_db[username] = user
        AuthService.save_users_to_file()
        return user

    @staticmethod
    def change_password(username: str, new_password: str) -> bool:
        """Change user password."""
        if username not in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user = fake_users_db[username]
        user.hashed_password = AuthService.get_password_hash(new_password)
        fake_users_db[username] = user
        AuthService.save_users_to_file()
        return True

    @staticmethod
    def delete_user(username: str) -> bool:
        """Delete a user."""
        if username not in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prevent deleting the last admin
        if fake_users_db[username].role == "admin":
            admin_count = sum(1 for user in fake_users_db.values() if getattr(user, 'role', 'user') == 'admin')
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin user"
                )

        del fake_users_db[username]
        AuthService.save_users_to_file()
        return True


# Initialize default users
def init_default_users():
    """Initialize default users if they don't exist."""
    global fake_users_db

    # Try to load users from file first
    loaded_users = AuthService.load_users_from_file()
    if loaded_users:
        fake_users_db = loaded_users
        print(f"✅ Loaded {len(loaded_users)} users from users.json")
        return

    # If no file exists or loading failed, create default users
    if not fake_users_db:  # Only initialize if empty
        fake_users_db = {
            "admin": UserInDB(
                username="admin",
                full_name="Aziz Boufath",
                email="admin@company.com",
                hashed_password="$2b$12$wybryr2T18eRKoC5Flo11uVPK0EMrobnPA3zy9B8uSOzjgRJUU.a6" if PASSLIB_AVAILABLE else simple_hash_password("admin123"),  # "admin123"
                is_active=True,
                role="admin",
                created_at=datetime.now().isoformat(),
                last_login=None
            ),
            "chef": UserInDB(
                username="chef",
                full_name="Chef de Production",
                email="chef@company.com",
                hashed_password="$2b$12$yJ63G3zI43jR686rfL37qeFvZLywAyh23jwRlSOihdPl3fzgDhkLC" if PASSLIB_AVAILABLE else simple_hash_password("chef123"),  # "chef123"
                is_active=True,
                role="chef",
                created_at=datetime.now().isoformat(),
                last_login=None
            ),
            "user": UserInDB(
                username="user",
                full_name="Utilisateur Standard",
                email="user@company.com",
                hashed_password="$2b$12$yJ63G3zI43jR686rfL37qeFvZLywAyh23jwRlSOihdPl3fzgDhkLC" if PASSLIB_AVAILABLE else simple_hash_password("user123"),  # "user123"
                is_active=True,
                role="user",
                created_at=datetime.now().isoformat(),
                last_login=None
            ),
        }

        # Save the default users to file
        AuthService.save_users_to_file()
        print("✅ Created default users and saved to users.json")

# Initialize users when module is imported
init_default_users()


# Export the service instance
auth_service = AuthService()
