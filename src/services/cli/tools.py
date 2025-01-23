from rich import print
from rich.progress import track
from rich.table import Table
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Set

from src.database.models.models import TwitterAccount, Category, Tweet
from src.database.repositories.repositories import TwitterAccountRepository, CategoryRepository, TweetRepository
from src.utils.common import get_map_ids_to_categories

class Operation(ABC):
    @abstractmethod
    async def execute(self):
        pass

class CateGoryHandler(Operation):
    def __init__(self, categories_repo: CategoryRepository):
        self._categories_repo = categories_repo
