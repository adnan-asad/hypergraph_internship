"""OS peak RSS in KiB; unavailable counters are explicitly missing."""
import sys


def peak_memory_kb():
    try:
        import resource
    except ImportError:
        return None
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / 1024 if sys.platform == 'darwin' else value
