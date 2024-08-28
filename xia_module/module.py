import copy
import os
import sys
import shutil
import subprocess
import yaml
from jinja2 import Environment, FileSystemLoader
from xia_module.cicd.github import GitHubWorkflow


class Module:
    module_name = "xia-module"  # Module Names
    cicd_stages = ["test-local", "build", "deploy", "test-remote", "publish"]
    activate_depends = []  # Those modules must be activated before this module
    deploy_depends = []  # Those modules must be deployed before this module

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
        self.cicd_dir = os.path.join(package_dir, "templates", self.module_name, "cicd")
        self.config_dir = os.path.join(package_dir, "templates", self.module_name, "config")
        self.env = Environment(
            loader=FileSystemLoader(searchpath=self.template_dir),
            trim_blocks=True,
            keep_trailing_newline=True
        )

    @classmethod
    def git_add(cls, filename: str):
        if os.path.exists(filename):
            subprocess.run(['git', 'add', filename], check=True)
        else:
            raise ValueError(f"{filename} doesn't exist, cannot add to Git")

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
        target_base_file = os.path.sep.join([base_dir, self.module_name + ".tf"])
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
        target_file = os.path.sep.join([base_dir, "activate_" + self.module_name + ".tf"])
        if os.path.exists(target_file):
            print(f"Found local activate file {target_file}")
        elif not os.path.exists(self.activate_file):
            print(f"No activate file defined-{self.module_name}, skip")
        else:
            shutil.copy(self.activate_file, target_file)
            print(f"Global activate file {target_file} loaded")

    @classmethod
    def copy_dir(cls, source_dir, target_dir, overwrite: bool = False, git_add: bool = False):
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
                    if git_add:
                        cls.git_add(target_file)
                    print(f"Copied: {source_file} -> {target_file}")
                else:
                    print(f"Skip existed file: {target_file}")

    def _build_template(self, **kwargs):
        """Build From template directory

        Args:
            **kwargs:
        """

    def _build_config(self, **kwargs):
        """Build From config directory

        Args:
            **kwargs:
        """
        self.copy_dir(self.config_dir, "./config", overwrite=False, git_add=True)

    @classmethod
    def _regex_to_github_actions(cls, pattern: str):
        tag_dict = {".*": ["*"]}
        actions_config = {'on': {'push': {}}}

        if pattern == ".*":
            return {'on': {'push': {"branches": "**", "tags": "*"}}}

        if pattern.startswith("refs/tags/"):
            tag_pattern = pattern.replace("refs/tags/", "")
            actions_config['on']['push']['tags'] = tag_dict[tag_pattern]
        elif pattern.startswith("refs/heads/"):
            branch_pattern = pattern.replace("refs/heads/", "")
            if branch_pattern == ".*":
                actions_config['on']['push']['branches'] = ["**"]
            elif branch_pattern.startswith("(") and branch_pattern.endswith(")"):
                branch_pattern = branch_pattern[1:-1]
                actions_config['on']['push']['branches'] = branch_pattern.split("|")
        return actions_config

    def _upsert_cicd_github_global(self, env_name: str, **kwargs) -> dict:
        """Generate CICD

        Args:
            env_name:
            **kwargs:

        Returns:
            workflow yaml in dict
        """
        workflow_yaml = os.path.join(".", ".github", "workflows", f"workflows-{env_name}.yml")
        if os.path.exists(workflow_yaml):
            # Case 1: If exists, return the existed one
            with open(workflow_yaml, 'r') as file:
                return yaml.safe_load(file) or {}
        else:
            # Case 2: If not exists, create a new one
            os.makedirs(os.path.join(".", ".github", "workflows"), exist_ok=True)
            match_branch = kwargs.get("match_branch", "push")
            match_event = kwargs.get("match_event", "push")
            if match_event == "release":
                trigger_event = {"release": None}
            elif match_event == "push":
                trigger_cfg = self._regex_to_github_actions(match_branch)
                trigger_event = trigger_cfg.get("on", None)
            else:
                raise ValueError(f"{match_event} doesn't exist")
            workflow_config = {
                "name": f"Workflow - {env_name}",
                "on": trigger_event
            }

            with open(workflow_yaml, 'w') as file:
                yaml.dump(workflow_config, file, default_flow_style=False, sort_keys=False)

    def _build_cicd(self, **kwargs):
        """Build Pipeline files

        Args:
            **kwargs:
        """
        # Step 1: Get information
        landscape_yaml = os.path.join(".", "config", "landscape.yaml")
        with open(landscape_yaml, 'r') as file:
            landscape_config = yaml.safe_load(file) or {}
        cicd_engine = landscape_config.get("cicd", landscape_config.get("git", "github"))
        # Step 2: Copy Action Files
        source_action_dir = os.path.join(self.cicd_dir, "github", "actions")
        target_action_dir = f".github/actions/{self.module_name}"
        self.copy_dir(source_action_dir, target_action_dir, git_add=True)
        # Step 3: Need build environments
        default_env_config = {"base": {"match_branch": "refs/tags/.*"}, "stages": self.cicd_stages}
        for env_name, env_config in landscape_config.get("environments", default_env_config).items():
            if cicd_engine == "github":
                gh_action_filename = f".github/workflows/workflow-{env_name}.yml"
                gh_action = GitHubWorkflow(gh_action_filename, workflow_name="",
                                           env_name=env_name, env_params=env_config)
                module_gh_action_fn = os.path.join(self.cicd_dir, "github", "workflow.yml")
                if os.path.exists(module_gh_action_fn):
                    module_action = GitHubWorkflow(module_gh_action_fn)
                    for stage_name in env_config.get("stages", []):
                        gh_action.merge_stage(stage_name=stage_name, workflow=module_action)
                    gh_action.dump()
                    self.git_add(gh_action_filename)

    def initialize(self, **kwargs):
        """Initialize a module in an application
        """
        self.copy_dir(self.init_dir, ".", overwrite=False, git_add=True)
        template_params = copy.deepcopy(kwargs)
        cicd_params = template_params.pop("cicd", {})
        config_params = template_params.pop("config", {})
        self._build_template(**template_params)
        self._build_cicd(**cicd_params)
        self._build_config(**config_params)

    def compile(self):
        """Compile a module to prepare terraform apply
        """

    def clean(self):
        """Clean Task after terraform apply
        """

