import os

import pytest
from xia_module.cicd.github import GitHubWorkflow


def test_existed():
    action = GitHubWorkflow("data/workflow-1.yml")
    # print(action.data)


def test_create():
    filename_1 = "./data/workflow-action-1.yml"
    if os.path.exists(filename_1):
        os.remove(filename_1)
    action_1 = GitHubWorkflow(filename_1, "", "dev",
                              {"match_branch": "refs/heads/(develop|main)",
                               "stages": ["local-test", "deploy"]})

    workflow_1 = GitHubWorkflow("./data/workflow-1.yml")
    workflow_2 = GitHubWorkflow("./data/workflow-2.yml")

    action_1.merge_stage("deploy", workflow_1)
    action_1.merge_stage("deploy", workflow_2)
    # print(action_1.data)
    action_1.dump()
