# flake8: noqa: E402

from pathlib import Path
import sys
from urllib.parse import urljoin

from hatchling.metadata.plugin.interface import MetadataHookInterface

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "xpip-upload"))

from xkits_file.attribute import __author_mail__
from xkits_file.attribute import __author_name__
from xkits_file.attribute import __package_name__
from xkits_file.attribute import __package_vers__
from xkits_file.attribute import __project_desc__
from xkits_file.attribute import __project_home__


class CustomMetadataHook(MetadataHookInterface):
    def update(self, metadata):
        metadata["name"] = __package_name__
        metadata["version"] = __package_vers__
        metadata["description"] = __project_desc__
        metadata["authors"] = [
            {"name": __author_name__, "email": __author_mail__},
        ]
        metadata["urls"] = {
            "Homepage": __project_home__,
            "Source Code": __project_home__,
            "Bug Tracker": urljoin(__project_home__, "issues"),
            "Documentation": __project_home__,
        }
