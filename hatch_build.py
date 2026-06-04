# flake8: noqa: E402

from pathlib import Path
import sys
from urllib.parse import urljoin

from hatchling.metadata.plugin.interface import MetadataHookInterface  # pylint: disable=E0401

sys.path.insert(0, str(Path(__file__).parent))

from xkits_file.attribute import __authors__  # pylint: disable=wrong-import-position
from xkits_file.attribute import __package_name__  # pylint: disable=wrong-import-position
from xkits_file.attribute import __package_vers__  # pylint: disable=wrong-import-position
from xkits_file.attribute import __project_desc__  # pylint: disable=wrong-import-position
from xkits_file.attribute import __project_home__  # pylint: disable=wrong-import-position


class CustomMetadataHook(MetadataHookInterface):  # pylint: disable=R0903
    def update(self, metadata):
        metadata["name"] = __package_name__
        metadata["version"] = __package_vers__
        metadata["description"] = __project_desc__
        metadata["authors"] = __authors__
        metadata["urls"] = {
            "Homepage": __project_home__,
            "Source Code": __project_home__,
            "Bug Tracker": urljoin(__project_home__, "issues"),
            "Documentation": __project_home__,
        }
