"""Infrastructure adapters; import concrete modules directly.

The initializer intentionally avoids eager imports, circular dependencies,
cloud client creation, and application startup side effects.
"""
