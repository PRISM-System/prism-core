import abc
from typing import Any, Dict, List, Optional

class BaseDataStore(abc.ABC):
    """
    The base class for all data store implementations.

    This abstract class defines the standard interface for interacting with
    different types of data storage, such as SQL databases, vector databases, etc.
    """

    @abc.abstractmethod
    def add(self, data: Dict[str, Any], **kwargs) -> Any:
        """
        Adds a new data entry to the store.

        Args:
            data: A dictionary representing the data to be added.

        Returns:
            The ID or a representation of the newly added data.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, id: Any, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieves a data entry by its ID.

        Args:
            id: The unique identifier of the data entry.

        Returns:
            A dictionary representing the data entry, or None if not found.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, id: Any, data: Dict[str, Any], **kwargs) -> bool:
        """
        Updates an existing data entry.

        Args:
            id: The ID of the data entry to update.
            data: A dictionary containing the fields to update.

        Returns:
            True if the update was successful, False otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, id: Any, **kwargs) -> bool:
        """
        Deletes a data entry.

        Args:
            id: The ID of the data entry to delete.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def query(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """

        Searches the data store based on a query.

        Args:
            query: The search query string.

        Returns:
            A list of dictionaries, where each dictionary is a search result.
        """
        raise NotImplementedError 