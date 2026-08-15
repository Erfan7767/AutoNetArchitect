"""Dependency injection infrastructure."""
from .scope import Scope, ScopeManager
from .container import Container
from .provider import Provider, ValueProvider, FactoryProvider, ServiceProvider
