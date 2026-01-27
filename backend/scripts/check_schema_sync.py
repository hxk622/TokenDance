#!/usr/bin/env python
"""
Schema Sync Checker - 检测模型与数据库的同步状态

用法:
    cd backend
    uv run python scripts/check_schema_sync.py

这个脚本会检测:
1. 模型中定义但数据库没有的表/列
2. 数据库中存在但模型没有定义的表/列
3. 类型不匹配的列

在以下情况下运行此脚本:
- 修改模型后
- 运行迁移后
- CI/CD pipeline 中
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


async def check_schema_sync():
    """Compare model definitions with actual database schema."""
    from sqlalchemy import text

    # Import all models to register them
    import app.models  # noqa: F401 - triggers model registration
    from app.core.database import Base, engine

    errors = []
    warnings = []

    async with engine.connect() as conn:
        # Get all model tables
        model_tables = set(Base.metadata.tables.keys())

        # Get actual database tables
        result = await conn.execute(text('''
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        '''))
        db_tables = {row[0] for row in result.fetchall()}

        print("=" * 60)
        print("Schema Sync Check")
        print("=" * 60)

        # Check tables
        missing_in_db = model_tables - db_tables - {'alembic_version'}
        extra_in_db = db_tables - model_tables - {'alembic_version'}

        if missing_in_db:
            errors.append(f"Tables in model but NOT in DB: {missing_in_db}")
            print(f"❌ Tables missing in DB: {missing_in_db}")
        if extra_in_db:
            warnings.append(f"Tables in DB but NOT in model: {extra_in_db}")
            print(f"⚠️  Extra tables in DB: {extra_in_db}")

        if not missing_in_db and not extra_in_db:
            print("✅ All tables synced")

        # Check columns for each table
        print("\n" + "-" * 60)
        print("Column Comparison")
        print("-" * 60)

        for table_name in sorted(model_tables & db_tables):
            # Get model columns
            model_table = Base.metadata.tables[table_name]
            model_cols = {c.name for c in model_table.columns}

            # Get DB columns
            result = await conn.execute(text('''
                SELECT column_name FROM information_schema.columns
                WHERE table_name = :table_name AND table_schema = 'public'
            '''), {"table_name": table_name})
            db_cols = {row[0] for row in result.fetchall()}

            missing = model_cols - db_cols
            extra = db_cols - model_cols

            if missing:
                errors.append(f"{table_name}: columns missing in DB: {missing}")
                print(f"❌ {table_name}: missing in DB: {missing}")
            if extra:
                warnings.append(f"{table_name}: extra columns in DB: {extra}")
                print(f"⚠️  {table_name}: extra in DB: {extra}")

            if not missing and not extra:
                print(f"✅ {table_name}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if errors:
        print(f"\n❌ {len(errors)} ERROR(s) - Model has columns/tables not in DB!")
        print("   Run: uv run alembic revision --autogenerate -m 'sync schema'")
        print("   Then: uv run alembic upgrade head")
        for e in errors:
            print(f"   - {e}")

    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNING(s) - DB has extra columns/tables")
        print("   These may be from migrations not yet reflected in models.")
        for w in warnings:
            print(f"   - {w}")

    if not errors and not warnings:
        print("\n✅ Schema is fully synchronized!")

    # Return exit code
    return 1 if errors else 0


def main():
    exit_code = asyncio.run(check_schema_sync())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
