from typing import Iterable, List, TypeVar, Generator

T = TypeVar("T")


def chunked(iterable: Iterable[T], size: int) -> Generator[List[T], None, None]:
    """Yield successive chunks from an iterable."""
    chunk: List[T] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
