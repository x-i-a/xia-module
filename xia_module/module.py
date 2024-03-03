import copy
import os
import sys
import shutil
from jinja2 import Environment, FileSystemLoader


class Module:
    module_name = "xia-module"  # Module Names
    activate_depends = []  # Those modules must be activated before this module

    def __init__(self, source_dir: str = "", **kwargs):
        package_dir = os.path.dirname(os.path.abspath(sys.modules[self.__class__.__module__].__file__))
        self.source_dir = source_dir
        self.module_dir = os.path.join(package_dir, "templates", self.module_name, "module")
        self.activate_dir = os.path.join(package_dir, "templates", self.module_name, "activate")
        self.base_dir = os.path.join(package_dir, "templates", self.module_name, "base")
        self.base_file = os.path.join(self.base_dir, "main.tf")
        self.activate_file = os.path.join(self.base_dir, "activate.tf")
        self.init_dir = os.path.join(package_dir, "templates", self.module_name, "init")
        self.template_dir = os.path.join(package_dir, "templates", self.module_name, "template")
        self.env = Environment(
            loader=FileSystemLoader(searchpath=self.template_dir),
            trim_blocks=True,
            keep_trailing_newline=True
        )

    def enable(self, module_dir: str = os.path.sep.join(["iac", "modules"]),
               base_dir: str = os.path.sep.join(["iac", "environments", "base"]), **kwargs):
        """Enable a module

        Args:
            module_dir (str): Target Terraform Module Directory
            base_dir (str): Target Terraform Base Directory
        """
        target_module_dir = os.path.sep.join([module_dir, self.module_name])
        if os.path.exists(target_module_dir):
            print(f"Found local module {self.module_name}")
        elif not os.path.exists(self.module_dir):
            print(f"No module directory defined-{self.module_name}, skip")
        else:
            shutil.copytree(self.module_dir, target_module_dir)
            print(f"Global module {self.module_name} loaded")
        target_base_file = os.path.sep.join([base_dir, self.module_name.replace("-", "_") + ".tf"])
        if os.path.exists(target_base_file):
            print(f"Found local base file {target_base_file}")
        elif not os.path.exists(self.base_file):
            print(f"No base file defined-{self.module_name}, skip")
        else:
            shutil.copy(self.base_file, target_base_file)
            print(f"Global base file {target_base_file} loaded")

    def activate(self, module_dir: str = os.path.sep.join(["iac", "modules"]),
                 base_dir: str = os.path.sep.join(["iac", "environments", "base"]), **kwargs):
        """Activate a module in a foundation

        Args:
            module_dir (str): Target Terraform Module Directory
            base_dir (str): Target Terraform Base Directory
        """
        target_module_dir = os.path.sep.join([module_dir, "activate-" + self.module_name])
        if os.path.exists(target_module_dir):
            print(f"Found local module activate-{self.module_name}")
        elif not os.path.exists(self.activate_dir):
            print(f"No activate module directory defined-{self.module_name}, skip")
        else:
            shutil.copytree(self.activate_dir, target_module_dir)
            print(f"Global module activate-{self.module_name} loaded")
        target_file = os.path.sep.join([base_dir, "activate_" + self.module_name.replace("-", "_") + ".tf"])
        if os.path.exists(target_file):
            print(f"Found local activate file {target_file}")
        elif not os.path.exists(self.activate_file):
            print(f"No activate file defined-{self.module_name}, skip")
        else:
            shutil.copy(self.activate_file, target_file)
            print(f"Global activate file {target_file} loaded")

    @classmethod
    def copy_dir(cls, source_dir, target_dir, overwrite: bool = False):
        if not os.path.exists(source_dir):
            print("Source directory not found, skip")
        for root, dirs, files in os.walk(source_dir):
            # Create corresponding subdirectories in the destination directory
            for dir_name in dirs:
                source_subdir = os.path.join(root, dir_name)
                target_subdir = os.path.join(target_dir, os.path.relpath(source_subdir, source_dir))
                os.makedirs(target_subdir, exist_ok=True)
            # Copy files to the destination directory
            for file_name in files:
                source_file = os.path.join(root, file_name)
                target_file = os.path.join(target_dir, os.path.relpath(source_file, source_dir))
                if overwrite or not os.path.exists(target_file):
                    shutil.copy2(source_file, target_file)
                    print(f"Copied: {source_file} -> {target_file}")
                else:
                    print(f"Skip existed file: {target_file}")

    def _build_template(self, **kwargs):
        """Build From template directory

        Args:
            **kwargs:
        """

    def _build_cicd(self, **kwargs):
        """Build Pipeline files

        Args:
            **kwargs:
        """
        # Step 1: Need build environments
        if "github" in kwargs:
            github_config = kwargs["github"]



    def initialize(self, **kwargs):
        """Initialize a module in an application
        """
        self.copy_dir(self.init_dir, ".", False)
        template_params = copy.deepcopy(kwargs)
        cicd_params = template_params.pop("cicd", {})
        self._build_template(**template_params)
        self._build_cicd(**cicd_params)

    def compile(self):
        """Compile a module to prepare terraform apply
        """

    def clean(self):
        """Clean Task after terraform apply
        """

