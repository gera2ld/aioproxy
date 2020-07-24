__author__ = """Gerald"""

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

try:
    __version__ = metadata.version('aioproxy')
except:
    __version__ = 'DEV'
