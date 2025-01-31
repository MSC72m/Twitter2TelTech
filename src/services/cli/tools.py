from collections import defaultdict

from rich import print
from rich.progress import track
from rich.table import Table
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Set, Union
from async_property import async_cached_property, async_property

from src.database.models.models import TwitterAccount, Category, Tweet
from src.database.models.pydantic_models import CategoryDbObject
from src.database.repositories.repositories import TwitterAccountRepository, CategoryRepository, TweetRepository
from src.utils.common import get_map_ids_to_categories

class Operation(ABC):
    @abstractmethod
    async def execute(self):
        pass

class DbInfoGetter:
    def __init__(self, categories_repo: CategoryRepository, accounts_repo: TwitterAccountRepository):
        self._categories_repo = categories_repo
        self._accounts_repo = accounts_repo

    @async_property
    async def get_map_ids_to_categories(self):
        return await get_map_ids_to_categories( self._accounts_repo, self._categories_repo)

    @async_cached_property
    async def _category_id_name(self):
        return await self._categories_repo.get_all_category_info()

    async def show_current_categories(self):
        tmp = await self._category_id_name
        print(tmp)
        print(self._category_id_name)