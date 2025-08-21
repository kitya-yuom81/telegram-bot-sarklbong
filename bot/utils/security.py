from typing import Iterable
def is_owner(user_id: int, owners: Iterable[int]) -> bool:
    return user_id in owners