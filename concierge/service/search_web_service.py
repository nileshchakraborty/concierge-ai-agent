
from ..client.search_web_client import SearchWebClient


class SearchWebService:

    _search_web_client: SearchWebClient
    def search_web(self, query: str) -> dict:
        # Implementation of web search using Serper API
        self._search_web_client.search_web(query)