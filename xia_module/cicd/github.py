import os
import io
from ruamel.yaml import YAML


class GitHubWorkflow:
    def load_data(self, data):
        buffer = io.StringIO()
        self.yaml.dump(data, buffer)
        buffer.seek(0)
        self.data = self.yaml.load(buffer)

    @classmethod
    def _extract_comments(cls, data):
        """Extract Comments from data objects

        Args:
            data(CommentedBase): data object

        Returns:
            All comments objects
        """
        comments = {}
        for key in data:
            comment = data.ca.items.get(key)
            if comment is not None:
                comments[key] = comment
        return comments

    @classmethod
    def _reapply_comments(cls, data, comments):
        """Reapply comments

        Args:
            data(CommentedBase): data object
            comments: comments dict to be reapplied
        """
        for key, comment in comments.items():
            data.ca.items[key] = comment

    def __init__(self, filename: str = "", workflow_name: str = "", env_name: str = "", env_params: dict = None):
        self.yaml = YAML()
        self.filename = filename
        if os.path.exists(filename):
            with open(filename) as fp:
                self.data = self.yaml.load(fp)
            return
        else:
            env_params = env_params or {}
            default_workflow_name = "Workflow" if not env_name or env_name == "base" else f"Workflow - {env_name}"
            workflow_name = workflow_name if workflow_name else default_workflow_name
            match_event = env_params.get("match_event", "push")
            match_branch = env_params.get("match_branch", ".*")
            runs_on = env_params.get("runs_on", "ubuntu-latest")
            if match_event == "release":
                trigger_event = {"release": None}
            else:
                trigger_cfg = self._regex_to_github_actions(match_branch)
                trigger_event = trigger_cfg.get("on", None)

            self.load_data({"name": workflow_name, "on": trigger_event, "jobs": {}})
            self.data.yaml_set_comment_before_after_key('on', before="\n")
            self.data.yaml_set_comment_before_after_key('jobs', before="\n")

            last_stage = ""
            for stage_name in env_params.get("stages", []):
                stage_header = {
                    "if": True,
                    "environment": env_name,
                    "runs-on": runs_on,
                    "steps": self.yaml.seq([
                        self.yaml.map(id="checkout-code", uses="actions/checkout@v4")
                    ])
                }
                if not env_name or env_name == "base":
                    stage_header.pop("environment")
                self.data["jobs"].update(self.yaml.map(**{stage_name: self.yaml.map(**stage_header)}))
                if last_stage != "":  # Not the first stage
                    self.data["jobs"].yaml_set_comment_before_after_key(stage_name, before="\n")
                    self.data["jobs"][stage_name]["needs"] = last_stage
                last_stage = stage_name
            # Reload the generated file to get better format
            self.dump()
            with open(filename) as fp:
                self.data = self.yaml.load(fp)

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
            else:
                actions_config['on']['push']['branches'] = [branch_pattern]
        return actions_config

    def dump(self):
        """Dump final workflow to files

        """
        for stage_name, stage_config in self.data["jobs"].items():
            self.data["jobs"][stage_name]["if"] = False if len(stage_config.get("steps", [])) <= 1 else True
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, "w") as fp:
            self.yaml.dump(self.data, fp)

    def get_stage_job(self, stage_name: str):
        return self.data.mlget(["jobs", stage_name], self.yaml.map(), list_ok=True)

    def merge_stage(self, stage_name: str, workflow):
        """Merge steps of a stage from another workflow

        Args:
            stage_name(str): stage_name to merge
            workflow: workflow
        """
        current_stage_job = self.get_stage_job(stage_name)
        existed_keys = list(current_stage_job)
        existed_step_ids = [step["id"] for step in current_stage_job.get("steps", []) if "id" in step]
        to_merge_stage_job = workflow.get_stage_job(stage_name)
        to_merge_steps = to_merge_stage_job.pop("steps", self.yaml.seq())
        for existed_key in existed_keys:
            to_merge_stage_job.pop(existed_key, None)
        current_steps = current_stage_job.pop("steps", self.yaml.seq())
        to_merge_steps = self.yaml.seq([step for step in to_merge_steps if step.get("id", "") not in existed_step_ids])
        current_steps.extend(to_merge_steps)
        self.data["jobs"][stage_name].update(to_merge_stage_job)
        self.data["jobs"][stage_name]["steps"] = current_steps
        # Add an empty line
        if to_merge_steps:
            stage_names = list(self.data["jobs"])
            current_stage_index = stage_names.index(stage_name)
            if stage_name != stage_names[-1]:
                next_stage_name = stage_names[current_stage_index + 1]
                self.data["jobs"].yaml_set_comment_before_after_key(next_stage_name, before="\n")
