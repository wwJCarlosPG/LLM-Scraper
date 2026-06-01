from abc import ABC, abstractmethod


class ScorerPort(ABC):
    """
    Port for ranking chunks by relevance to a query.
    Implementations may use embedding similarity, HyDE, or other strategies.
    """

    @abstractmethod
    def rank(
        self,
        query: str,
        chunks: list[str],
        top_k: int,
        compute_scores: bool = False,
    ) -> tuple[list[str], list[float]]:
        """
        Rank chunks by relevance to the query and return top-k.

        Args:
            query: the user extraction query.
            chunks: list of text chunks to rank.
            top_k: number of chunks to return.
            compute_scores: if True, return real similarity scores
                            even when len(chunks) <= top_k.

        Returns:
            tuple of (top-k chunks sorted by relevance, their scores).
        """
        ...
