import os
import yaml
import inspect


def get_prompt_yaml(tag, path=None):

    if path is None:
        caller_file = inspect.stack()[1].filename
        caller_dir = os.path.dirname(caller_file)
        path = os.path.join(caller_dir, "prompt.yaml")
    else:
        caller_file = inspect.stack()[1].filename
        caller_dir = os.path.dirname(caller_file)
        path = os.path.join(caller_dir, path)
        path = os.path.abspath(path)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    keys = tag.split(".")
    current = config
    for key in keys:
        current = current.get(key, {})
    return current
