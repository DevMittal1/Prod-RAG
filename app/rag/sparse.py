import hashlib
import math
import re
from collections import Counter

from qdrant_client import models

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_:-]+")
SPARSE_HASH_SPACE = 2_147_483_647


def sparse_text_vector(text: str) -> models.SparseVector:
    counts = Counter(_tokens(text))
    if not counts:
        return models.SparseVector(indices=[], values=[])

    weighted: dict[int, float] = {}
    for token, count in counts.items():
        index = _token_index(token)
        weighted[index] = weighted.get(index, 0.0) + 1.0 + math.log(count)

    norm = math.sqrt(sum(value * value for value in weighted.values())) or 1.0
    items = sorted((index, value / norm) for index, value in weighted.items())
    return models.SparseVector(
        indices=[index for index, _ in items],
        values=[value for _, value in items],
    )


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def _token_index(token: str) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % SPARSE_HASH_SPACE

