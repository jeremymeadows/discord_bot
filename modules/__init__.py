from os import listdir

__all__ = [mod.rstrip(".py") for mod in listdir("modules") if mod.endswith(".py") and not mod.startswith("__")]