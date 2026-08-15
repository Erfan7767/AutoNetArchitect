"""Cache decorator helpers."""
from functools import wraps
def cached(cache: object, key_factory: object) -> object:
    """Cache a function result using a key factory."""
    def decorator(function: object) -> object:
        @wraps(function)
        def wrapper(*args: object, **kwargs: object) -> object:
            key = key_factory(*args, **kwargs); value = cache.get(key)
            if value is None: value = function(*args, **kwargs); cache.set(key, value)
            return value
        return wrapper
    return decorator
