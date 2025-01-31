from collections import defaultdict

from rich import print
from rich.progress import track
from rich.table import Table
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Set, Union
from async_property import async_cached_property

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
        self._cached_mapped_category_ids = None
        self._cached_category_id_name = None

    @async_cached_property
    async def mapped_category_ids(self):
        if self._cached_mapped_category_ids is None:
            self._cached_mapped_category_ids = await get_map_ids_to_categories(
                self._accounts_repo,
                self._categories_repo
            )
        return self._cached_mapped_category_ids

    @async_cached_property
    async def category_id_name(self):
        if self._cached_category_id_name is None:
            self._cached_category_id_name = await self._categories_repo.get_all_category_info()
        return self._cached_category_id_name

    async def show_current_categories(self):
        print(await self.category_id_name)
        print(self._cached_category_id_name)

