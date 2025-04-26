import importlib.resources as res
from functools import cache
from pathlib import Path
from types import ModuleType

from jinja2 import BaseLoader, Environment, PackageLoader, Template


@cache
def load_template_env(module: ModuleType | None = None) -> Environment:
    if not module:
        return Environment(loader=BaseLoader())

    loader = PackageLoader(module.__name__)
    return Environment(
        loader=loader,
        trim_blocks=True,
    )


def load_template(module: ModuleType, name: str, **kwargs) -> Template:
    """Load template from a module.

    Example:

    ```python
    import chisellm_utils.dataset as dataset_module
    # load a template named `template.j2` from `chisellm_utils.dataset.templates` directory
    template = load_template(dataset_module, "template")
    ```

    Args:
        module (ModuleType): A module contains a subdirectory named `templates`.
        name (str): Template name without extension. e.g. `template.j2` -> `template`

    Returns:
        Template: A jinja2 template object.
    """
    return load_template_env(module).get_template(f"{name}.j2")


def load_text(module: ModuleType, path: Path) -> str:
    with res.as_file(res.files(module)) as module_path:
        return (module_path / path).read_text(encoding="utf-8")


def load_template_text(module: ModuleType, name: str) -> str:
    if not (file_path := Path(name)).suffix:
        file_path = file_path.with_suffix(".j2")

    return load_text(module, Path("templates") / file_path)


@cache
def create_template(template: str) -> Template:
    return load_template_env().from_string(template)
