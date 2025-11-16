
from ..client.browse_website_client import BrowseWebsiteClient

class BrowseWebsiteService:

    _browse_website_service_instance = BrowseWebsiteClient()

    def browse_website(self, url: str) -> str:
        # Implementation of browsing a website and returning its content
        self._browse_website_service_instance.browse_website(url)