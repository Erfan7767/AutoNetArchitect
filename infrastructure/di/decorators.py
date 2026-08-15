"""Decorators carrying dependency-injection metadata."""
from __future__ import annotations
from typing import Any, Callable
from .scope import Scope
def injectable(scope: Scope = Scope.TRANSIENT) -> Callable[[type[Any]], type[Any]]:
    """Mark a class as injectable."""
    def decorate(cls: type[Any]) -> type[Any]: cls.__di_scope__ = scope; return cls
    return decorate
def inject(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a callable for injection by a container adapter."""
    fn.__di_inject__ = True; return fn
def _metadata(name: str, value: Any) -> Callable[[type[Any]], type[Any]]:
    def decorate(cls: type[Any]) -> type[Any]: setattr(cls, name, value); return cls
    return decorate
def provides(interface: object) -> Callable[[type[Any]], type[Any]]: return _metadata('__di_interface__', interface)
def named(name: str) -> Callable[[type[Any]], type[Any]]: return _metadata('__di_name__', name)
def tagged(*tags: str) -> Callable[[type[Any]], type[Any]]: return _metadata('__di_tags__', tags)
def lazy(cls: type[Any]) -> type[Any]: return _metadata('__di_lazy__', True)(cls)
def optional(cls: type[Any]) -> type[Any]: return _metadata('__di_optional__', True)(cls)
