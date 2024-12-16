# setup_project.py
from pathlib import Path
import os


def create_file(path: Path, content: str = ""):
    """Create a file with given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def setup_project():
    # Root directory
    root = Path("fastapi-template")

    # Create main project structure
    directories = [
        # App structure
        "app/api/v1",
        "app/core",
        "app/db/repositories",
        "app/models",
        "app/schemas",
        "app/services",
        "app/utils",
        # Infrastructure
        "infrastructure/aws",
        # Tests
        "tests/api/v1",
        "tests/unit",
        # GitHub Actions
        ".github/workflows",
        # Scripts
        "scripts",
    ]

    # Create directories
    for dir_path in directories:
        (root / dir_path).mkdir(parents=True, exist_ok=True)

    # Create __init__.py files in all Python directories
    python_dirs = [d for d in directories if not any(x in d for x in ['.github', 'infrastructure', 'scripts'])]
    for dir_path in python_dirs:
        create_file(root / dir_path / "__init__.py", "")

    # Core files
    core_files = {
        "app/core/config.py": "from pydantic_settings import BaseSettings\n\nclass Settings(BaseSettings):\n    pass\n",
        "app/core/security.py": "# JWT and security related functions\n",
        "app/core/logging.py": "# Logging configuration\n",
        "app/core/oauth.py": "# OAuth implementation\n",
        "app/core/scheduler.py": "# APScheduler configuration\n"
    }

    # Database files
    db_files = {
        "app/db/mongodb.py": "# MongoDB connection and initialization\n",
        "app/db/repositories/base.py": "# Base repository with common CRUD operations\n",
        "app/db/repositories/user.py": "# User specific database operations\n"
    }

    # API files
    api_files = {
        "app/api/v1/auth.py": "# Authentication endpoints\n",
        "app/api/v1/users.py": "# User management endpoints\n",
        "app/api/v1/health.py": "# Health check endpoints\n",
        "app/api/deps.py": "# Dependency injection\n"
    }

    # Models and schemas
    model_schema_files = {
        "app/models/user.py": "# User MongoDB model\n",
        "app/schemas/user.py": "# User Pydantic schemas\n",
        "app/schemas/token.py": "# JWT token schemas\n"
    }

    # Service and utility files
    service_util_files = {
        "app/services/auth.py": "# Authentication service\n",
        "app/services/user.py": "# User service\n",
        "app/utils/constants.py": "# Constants and enums\n",
        "app/utils/helpers.py": "# Helper functions\n"
    }

    # Infrastructure files
    infra_files = {
        "infrastructure/aws/cloudformation.yml": "# AWS CloudFormation template\n",
        "infrastructure/aws/userdata.sh": "# EC2 user data script\n"
    }

    # Configuration and setup files
    config_files = {
        ".env.example": "# Environment variables\n",
        ".gitignore": """
# Python
__pycache__/
*.py[cod]
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.venv
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
""",
        "requirements.txt": """
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.4.2
pydantic-settings>=2.0.3
motor>=3.3.1
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
APScheduler>=3.10.4
watchtower>=3.0.1
boto3>=1.28.44
python-dotenv>=1.0.0
google-auth>=2.23.3
google-auth-oauthlib>=1.1.0
""",
        "README.md": """# FastAPI Template

A production-ready FastAPI template with MongoDB, JWT authentication, Google OAuth, APScheduler, and AWS deployment support.

## Features
- FastAPI with async support
- MongoDB integration using motor
- JWT authentication
- Google OAuth integration
- APScheduler for background tasks
- AWS deployment with Load Balancer
- Cloudwatch logging
- CI/CD using GitHub Actions

## Getting Started
1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your values
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `uvicorn main:app --reload`

## Project Structure
[Project structure description]

## Development
[Development guidelines]

## Deployment
[Deployment instructions]

## License
MIT
""",
        "main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.mongodb import db

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Set up logging
    setup_logging()

    return application

app = create_application()

@app.on_event("startup")
async def startup_db_client():
    await db.connect_to_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    await db.close_database_connection()
"""
    }

    # Create all files
    all_files = {
        **core_files,
        **db_files,
        **api_files,
        **model_schema_files,
        **service_util_files,
        **infra_files,
        **config_files
    }

    for file_path, content in all_files.items():
        create_file(root / file_path, content)

    # Create test files
    test_files = {
        "tests/conftest.py": "# pytest fixtures\n",
        "tests/api/v1/test_auth.py": "# Authentication tests\n",
        "tests/api/v1/test_users.py": "# User endpoints tests\n",
        "tests/unit/test_services.py": "# Service layer tests\n"
    }

    for file_path, content in test_files.items():
        create_file(root / file_path, content)

    print("Project structure created successfully!")


if __name__ == "__main__":
    setup_project()