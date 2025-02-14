from scraper_manager.application.interfaces.storage_interface import BaseStorage

class LocalStorage(BaseStorage):
    """
    LocalStorage is an implementation of the `BaseStorage` interface that saves data to the local filesystem.

    Methods:
        save(data: str, path: str) -> None:
            Saves the given data to the specified path on the local filesystem.
    """
    def save(self, data, path: str) -> None:
        """
        Save the given data to the specified path on the local filesystem.

        Args:
            data (str): The data to save.
            path (str): The path to save the data to.
        """
        with open(path, 'w') as file:
            file.write(data)