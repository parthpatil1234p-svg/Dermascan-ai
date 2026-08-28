import argparse
import asyncio
import json
from pathlib import Path

from app.core.config import get_settings
from app.database.mongodb import mongo_connection
from app.services.product_import_service import import_product_file


async def run(path: Path, dry_run: bool) -> None:
    if not path.is_file():
        raise SystemExit(f"Import file not found: {path}")
    database = await mongo_connection.connect(get_settings())
    try:
        result = await import_product_file(
            path, database["products"], database["product_import_jobs"], dry_run=dry_run
        )
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    finally:
        await mongo_connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and import skincare catalogue products.")
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.file, args.dry_run))


if __name__ == "__main__":
    main()
