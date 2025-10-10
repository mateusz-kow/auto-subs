import re
import tomllib
from pathlib import Path

import auto_subs


def test_package_is_importable() -> None:
    """Verify that the auto_subs package can be imported."""
    assert auto_subs is not None


def test_version_has_semantic_format() -> None:
    """Verify that the version string conforms to semantic versioning (X.Y.Z)."""
    version = auto_subs.__version__
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Version {version} does not match the X.Y.Z format."


def test_version_is_consistent() -> None:
    """Verify that the version in __init__.py matches the one in pyproject.toml."""
    # Read version from __init__.py
    package_version = auto_subs.__version__

    # Read version from pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found at the project root."

    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)

    pyproject_version = pyproject_data.get("project", {}).get("version")
    assert pyproject_version is not None, "Version not found in pyproject.toml under [project.version]."

    assert (
        package_version == pyproject_version
    ), f"Version mismatch: __init__.py has '{package_version}', pyproject.toml has '{pyproject_version}'."
