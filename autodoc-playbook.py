import os
import yaml
import re
import argparse
import os
import sys
from tabulate import tabulate
from jinja2 import Environment, FileSystemLoader
from jinja2 import Template

TEMPLATE = """
# {{ playbook_name }}

{% for play in playbook_plays %}
# Description
{{ play.description }}

## Hosts
{{ play.hosts }}
{% if play.hosts_variable %}
Note: hosts depends from variable `{{ play.hosts_variable }}`.
{% endif %}

## Mandatory variables
{% if play.mandatory_variables %}
The following variables are necessary for this play:

{% for variable in play.mandatory_variables %}
- {{ variable }}
{% endfor %}
{% else %}
No mandatory variables found.
{% endif %}

## Default variables
{% if play.variables_table | length > 0 %}
The following table lists the variables used in this play, along with their value.

{{ tabulate(play.variables_table, headers='keys', tablefmt='pipe', showindex=False) }}

{% else %}
No variables found.
{% endif %}

## Tasks
{% if play.tasks %}
The following tasks are defined in this play:
{% for task in play.tasks %}
- {{ task }}
{% endfor %}
{% else %}
No tasks found.
{% endif %}

## Roles
{% if play.roles %}
The following roles are used in this play:
{% for role in play.roles %}
- {{ role }}
{% endfor %}
{% else %}
No roles found.
{% endif %}

{% endfor %}

"""

# Define a custom YAML constructor to handle '!vault' tags.
# When encountering a '!vault' tag in a YAML file, replace its content with the string "ENCRYPTED".
def construct_vault_encrypted_unicode(loader, node):
    return "ENCRYPTED"

# Load and return the content of a YAML file.
def load_yaml_file(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def extract_hosts_variable(play):
    variable = None

    hosts = play["hosts"]
    if isinstance(hosts, str) and "{{" in hosts and "}}" in hosts:
        variable_match = re.findall(r"{{(.*?)}}", hosts)
        variable = variable_match[0].strip()

    return variable

def find_mandatory_variables(tasks):
    mandatory_vars = set()

    def extract_vars_from_assert(assert_task):
        if "that" in assert_task:
            for condition in assert_task["that"]:
                for each_match in re.finditer(r'(\w+)\s+is\s+defined', condition):
                    var_name = each_match.group(1)
                    mandatory_vars.add(var_name)

    for task in tasks:
        if "block" in task:
            for block_task in task["block"]:
                if "ansible.builtin.assert" in block_task:
                    extract_vars_from_assert(block_task["ansible.builtin.assert"])
                elif "assert" in block_task:
                    extract_vars_from_assert(block_task["assert"])
        elif "ansible.builtin.assert" in task:
            extract_vars_from_assert(task["ansible.builtin.assert"])
        elif "assert" in task:
            extract_vars_from_assert(task["assert"])

    return mandatory_vars


def extract_playbook_variables(play):
    variables = []

    if "vars" in play and isinstance(play["vars"], dict):
        for var_name, var_value in play["vars"].items():
            variables.append({"name": var_name, "value": var_value})

    return variables

def extract_playbook_tasks(play):
    tasks = []

    if "tasks" in play and isinstance(play["tasks"], list):
        for task in play["tasks"]:
            if isinstance(task, dict) and "name" in task:
                task_name = task["name"]
                tasks.append(task_name)

    return tasks

def extract_playbook_roles(play):
    roles = []

    if "roles" in play:
        if isinstance(play["roles"], list):
            roles.extend(play["roles"])
        elif isinstance(play["roles"], dict):
            roles.append(play["roles"].get("name", play["roles"].get("role")))

    # Check for roles used with 'include_role' in tasks
    if "tasks" in play and isinstance(play["tasks"], list):
        for task in play["tasks"]:
            if isinstance(task, dict) and ("include_role" in task or "ansible.builtin.include_role" in task):
                role = task.get("include_role", task.get("ansible.builtin.include_role"))
                if isinstance(role, dict):
                    roles.append(role.get("name"))
                else:
                    roles.append(role)

    return roles

def extract_and_process_plays(playbook_content):
    plays = []

    for play in playbook_content:
        if isinstance(play, dict) and "hosts" in play:
            description = play.get("name", "No description found")
            hosts = play["hosts"]
            hosts_variable = extract_hosts_variable(play)
            variables = extract_playbook_variables(play)
            tasks = extract_playbook_tasks(play)
            roles = extract_playbook_roles(play)

            variables_table = get_variables_table(variables)
            mandatory_variables = find_mandatory_variables(play.get("tasks", []))

            plays.append({
                "description": description,
                "hosts": hosts,
                "hosts_variable": hosts_variable,
                "mandatory_variables": mandatory_variables,
                "variables_table": variables_table,
                "tasks": tasks,
                "roles": roles
            })

    return plays

def get_variables_table(variables):
    variables_table = []

    for var in variables:
        variables_table.append({
            "Name": var['name'],
            "Value": var["value"],
        })

    return variables_table

def generate_playbook_readme(playbook_path, playbook_plays, output_path=None):
    playbook_name = os.path.basename(playbook_path)
    playbook_name_without_extension = os.path.splitext(playbook_name)[0]

    template = Template(TEMPLATE)

    if not output_path:
            output_path = f"README_{playbook_name_without_extension}_.md"

    with open(output_path, 'w') as f:
        f.write(template.render(
            playbook_name=playbook_name,
            playbook_plays=playbook_plays,
            tabulate=tabulate
        ))

def parse_args():
    parser = argparse.ArgumentParser(description="Generate a README.md file for an Ansible playbook.")
    parser.add_argument('--playbook-path', '-p', required=True, help="The path to the Ansible playbook file.")
    parser.add_argument('--output-path', '-o', dest='output_path', help='Path to the output README.md file', default=None)
    return parser.parse_args()

# Add the custom constructor to the SafeLoader of the PyYAML library.
yaml.SafeLoader.add_constructor(u'!vault', construct_vault_encrypted_unicode)

if __name__ == "__main__":
    args = parse_args()

    playbook_content = load_yaml_file(args.playbook_path)
    playbook_plays = extract_and_process_plays(playbook_content)

    generate_playbook_readme(args.playbook_path, playbook_plays, args.output_path)
