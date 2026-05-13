import tkinter


def safe_focus(widget) -> None:
    """Focus ``widget`` if it still exists. Used by deferred ``after``
    callbacks (titlebar withdraw+deiconify focus restore, input dialog
    focus delay) where the saved widget may have been destroyed before
    the callback fires — e.g. inline editors that commit + destroy on
    ``<FocusOut>`` when the spawning dialog steals focus.
    """
    try:
        if widget.winfo_exists():
            widget.focus()
    except tkinter.TclError:
        pass


def pop_from_dict_by_set(dictionary: dict, valid_keys: set) -> dict:
    """ remove and create new dict with key value pairs of dictionary, where key is in valid_keys """
    new_dictionary = {}

    for key in list(dictionary.keys()):
        if key in valid_keys:
            new_dictionary[key] = dictionary.pop(key)

    return new_dictionary


def check_kwargs_empty(kwargs_dict, raise_error=False) -> bool:
    """ returns True if kwargs are empty, False otherwise, raises error if not empty """

    if len(kwargs_dict) > 0:
        if raise_error:
            raise ValueError(f"{list(kwargs_dict.keys())} are not supported arguments. Look at the documentation for supported arguments.")
        else:
            return True
    else:
        return False
