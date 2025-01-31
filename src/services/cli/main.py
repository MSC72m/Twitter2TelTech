import argparse
import asyncio
from unicodedata import category
from rich.console import  Console

from src.database.db import get_session
from src.services.cli.tools import PrintTable, DbInfoGetter
from src.database.repositories.repositories import TwitterAccountRepository, CategoryRepository
from src.database.models.models import TwitterAccount, Category


async def main():
    async with get_session() as session:
        account_repo = TwitterAccountRepository(TwitterAccount, session)
        category_repo = CategoryRepository(Category, session)
        db_info_getter = DbInfoGetter(accounts_repo=account_repo, categories_repo=category_repo)
        category_names = await db_info_getter.show_current_categories()
        printter = PrintTable(title="Category Printter", columns=category_names)
        printter.add_row("ids 3242345425")
        console = Console()
        console.print(printter)


        return None


if __name__=="__main__":
    asyncio.run(main())
