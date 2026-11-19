# Keep this file lightweight to prevent circular imports and Streamlit
# context errors during test collection. Import app components explicitly
# where needed (e.g. in app entrypoints), not at package init time.

__all__ = ["main"]


def main():
    """Deferred entry point — imports app only when actually called."""
    from omnix.ui.app import main as _main  # noqa: PLC0415
    _main()

