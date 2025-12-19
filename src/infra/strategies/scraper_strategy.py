from abc import ABC, abstractmethod
from playwright.sync_api import Page

class ScraperStrategy(ABC):
    @abstractmethod
    def execute(self, page: Page, save_path_dir: str, strategy_config: dict = None) -> str:
        """
        Executes the scraping strategy.
        
        Args:
            page: The Playwright Page object (already logged in).
            save_path_dir: Directory to save the downloaded file.
            strategy_config: Dictionary containing strategy configuration (e.g., HS Code).
            
        Returns:
            The full path to the downloaded/processed file.
        """
        pass
