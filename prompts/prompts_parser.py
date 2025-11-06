import os
import yaml
from jinja2 import Template
from typing import List, Dict, Optional, Union


def load_yaml_prompt(path: str) -> Dict:
    """
    YAMLテンプレを読み込む（辞書で返す）。
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def render_yaml_prompt(yaml_prompt: Dict, variables: Dict[str, str]) -> tuple[str, str]:
    """
    YAML内の system と task を Jinja2 でレンダリングして返す（system, user_task_text）。
    """
    system_template = yaml_prompt.get("system", "")
    task_template = yaml_prompt.get("task", "")

    # system もテンプレ化されている可能性があるので一応 render をかける
    system_text = Template(system_template).render(**variables)
    task_text = Template(task_template).render(**variables)
    return system_text, task_text