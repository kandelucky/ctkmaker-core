import os


def get_hook_dirs():
    """Return the path to the PyInstaller hooks directory for customtkinter."""
    return [os.path.dirname(__file__)]
