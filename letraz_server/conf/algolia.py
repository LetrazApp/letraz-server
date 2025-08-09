import asyncio
import logging

from algoliasearch.search.client import SearchClientSync

PROJECT_NAME = 'Letraz'

__module_name = f'{PROJECT_NAME}.{__name__}'
logger = logging.getLogger(__module_name)


class AlgoliaIngestionClient:
    def __init__(self, app_id, api_key):
        self.__app_id = app_id
        self.__api_key = api_key
        self.client = SearchClientSync(app_id, api_key)

    # Add record to an index
    def __add_record(self, index_name: str, record: dict):
        if not record or not isinstance(record, dict):
            raise TypeError('Record must be a dict!')
        try:
            self.client.save_object(index_name=index_name, body=record)
            logger.debug(f'Indexing {index_name}: \n{record}')
        except Exception as e:
            logger.exception(f'ALGOLIA INDEXING FAILED : {e}')

    def add_resume(self, record: dict):
        self.__add_record(index_name='resume', record=record)
