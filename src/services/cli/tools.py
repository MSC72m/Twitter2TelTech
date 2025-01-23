from collections import defaultdict

from rich import print
from rich.progress import track
from rich.table import Table
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Set, Union
from async_property import async_property

from src.database.models.models import TwitterAccount, Category, Tweet
from src.database.repositories.repositories import TwitterAccountRepository, CategoryRepository, TweetRepository
from src.utils.common import get_map_ids_to_categories

class Operation(ABC):
    @abstractmethod
    async def execute(self):
        pass

class CateGoryHandler(Operation):
    def __init__(self, categories_repo: CategoryRepository, accounts_repo: TwitterAccountRepository):
        self._categories_repo = categories_repo
        self._accounts_repo = accounts_repo

    @async_property
    async def get_map_ids_to_categories(self):
        return await get_map_ids_to_categories( self._accounts_repo, self._categories_repo)

    @async_property
    async def category_id_name(self) -> Dict[str, Tuple[int, str]]:
        """First res arg is id, 2nd is desc and 3d last is name"""
        response = await self._categories_repo.get_all_category_info()
        tmp: Dict[str, Tuple[int, str]] = dict(tuple())
        for res in response:
            tmp[str(res[0])] = (res[2], res[1])
        return tmp