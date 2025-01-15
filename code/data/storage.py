from abc import ABC, abstractmethod
class Storage(ABC):

    @abstractmethod
    def save(key: str, data: str):
        """Save data using unique key

        Args:
            key (str): The unique key for database
            data (str): Data to save
        """
        pass

    @abstractmethod
    def load(key: str):
        """Load data using unique key

        Args:
            key (str): Unique data identifier
        """
        pass
        
    
