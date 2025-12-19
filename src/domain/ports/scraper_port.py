from abc import ABC, abstractmethod

class ScraperPort(ABC):
    @abstractmethod
    def download_data(self, save_path: str) -> str:
        """
        Downloads data from the external source and saves it to the specified path.
        Returns the absolute path of the saved file.
        """
        pass
