# AutoDoc-Ansible-Playbook

Generate a README.md for Ansible playbook YAML files.

The generated README files include information about the playbook's description, hosts, variables, tasks, and roles.

## Features

- Extracting playbook description.
- Finding hosts and hosts variables.
- Extracting playbook variables and their values.
- Extracting playbook tasks.
- Extracting playbook roles.
- Finding mandatory variables using the `assert` module.

- Extracts role metadata from meta/main.yml, including role_name, description, author, dependencies, and platforms.
- Parses defaults/main.yml to gather default variables and their descriptions based on associated comments.
- Parses vars/main.yml to find other variables and their descriptions from associated comments.
- Analyzes assert statements in task files to determine actual required variables (when using "is defined").
- If present, uses content from example.yml for the example playbook; otherwise, constructs an example based on the identified required variables.
- If present, uses content from KNOWN-BUGS.md to fill the "Known problems and limitations" section.
- If present, uses data from dependecies.yml to add more dependencies to collections and roles (not listed in the meta\main.yml file).
- Provides usage instructions using the clone-url parameter to indicate the URL to be used in the requirements.yml file.

## Usage

The script can be used via the command line by providing the following arguments:

- `-p, --playbook-path`: Required. Path to the Ansible playbook YAML file.
- `-o, --output-path`: Optional. Path to the output README.md file. If not provided, the default output filename will be used.

## Example

Generate a README.md file for an Ansible playbook:

```bash
python autodoc-playbook.py -p path/to/your/playbook.yml -o README.md
```

## Requirements

- Python 3.6 or higher
- PyYAML
- Jinja2
- Tabulate

## Installation

```bash
pip install pyyaml jinja2 tabulate
```

## Limitations

- The script currently supports extracting information from tasks that use the include_role or ansible.builtin.include_role module.
- The script assumes that tasks using the assert module follow the pattern of checking if a variable is defined.
- The script does not handle all possible variations of playbook structures or module usages.

## License

This script is released under the [MIT License](https://opensource.org/licenses/MIT).

## Author

Fabio Ambrosanio <fabio.ambrosanio@staff.aruba.it>
