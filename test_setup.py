#!/usr/bin/env python3
"""
Quick setup verification script.
Run this to check if all dependencies are installed correctly.
"""

import sys


def check_imports():
    """Check if all required packages can be imported."""
    required_packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "chromadb": "ChromaDB",
        "sentence_transformers": "SentenceTransformers",
        "openai": "OpenAI",
        "PyPDF2": "PyPDF2",
        "docx": "python-docx",
    }

    print("🔍 Checking dependencies...\n")

    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - NOT FOUND")
            missing.append(package)

    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("\nInstall them with:")
        print("poetry install")
        return False

    print("\n✅ All dependencies installed!")
    return True


def check_env():
    """Check if .env file exists and has required variables."""
    from pathlib import Path

    print("\n🔍 Checking environment configuration...\n")

    env_path = Path(".env")
    if not env_path.exists():
        print("✗ .env file not found")
        print("\nCreate it with:")
        print("cp .env.example .env")
        return False

    with open(env_path) as f:
        content = f.read()

    if "your_openai_api_key_here" in content:
        print("⚠️  .env file exists but OPENAI_API_KEY needs to be set")
        print("\nEdit .env and add your OpenAI API key")
        return False

    if "OPENAI_API_KEY=" in content:
        print("✓ .env file configured")
        print("\n✅ Environment configuration looks good!")
        return True

    print("✗ .env file missing OPENAI_API_KEY")
    return False


def check_directories():
    """Check if required directories exist."""
    from pathlib import Path

    print("\n🔍 Checking directories...\n")

    dirs = ["uploads", "chroma_db", "example_docs"]

    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✓ {dir_name}/")
        else:
            print(f"✗ {dir_name}/ - creating...")
            dir_path.mkdir(exist_ok=True, parents=True)
            print(f"  Created {dir_name}/")

    print("\n✅ All directories ready!")
    return True


def test_sentence_transformer():
    """Quick test of sentence transformer model."""
    try:
        print("\n🔍 Testing embedding model...\n")
        from sentence_transformers import SentenceTransformer

        print("Loading model (this may take a moment on first run)...")
        model = SentenceTransformer("all-MiniLM-L6-v2")

        test_text = "This is a test sentence."
        embedding = model.encode(test_text)

        print("✓ Model loaded successfully")
        print(f"✓ Embedding dimension: {len(embedding)}")
        print("\n✅ Embedding model working!")
        return True
    except Exception as e:
        print(f"✗ Error testing embedding model: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Knowledge Base API - Setup Verification")
    print("=" * 60)

    checks = [
        check_imports(),
        check_env(),
        check_directories(),
        test_sentence_transformer(),
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("🎉 Everything is set up correctly!")
        print("\nNext steps:")
        print("1. Make sure your OpenAI API key is in .env")
        print("2. Run: uvicorn app.main:app --reload")
        print("3. Visit: http://localhost:8000/docs")
        print("=" * 60)
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
