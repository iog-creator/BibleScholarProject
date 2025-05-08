import yaml

DEFAULT_FRONTMATTER = {
    'type': 'restored',
    'title': 'Restored File',
    'description': 'This file was automatically restored or completed.',
    'globs': [],
    'alwaysApply': False
}

class CustomDumper(yaml.SafeDumper):
    def represent_sequence(self, tag, sequence, flow_style=None):
        if sequence and (any(isinstance(item, (dict, list)) for item in sequence) or len(sequence) > 2):
            flow_style = False
        return super().represent_sequence(tag, sequence, flow_style=flow_style)

    def represent_scalar(self, tag, value, style=None):
        if isinstance(value, str):
            if value.lower() in ['true', 'false', 'yes', 'no', 'on', 'off', 'null', '']:
                style = "'"  # PyYAML style character for single quotes
            elif value.isdigit() or (value.startswith('0') and not value.startswith('0.')):
                style = "'" # PyYAML style character for single quotes
            elif not value: # Empty string
                style = "'" # PyYAML style character for single quotes
        return super().represent_scalar(tag, value, style=style)

def main():
    print(f"Using PyYAML version: {yaml.__version__}")

    fm_yaml_output = yaml.dump(DEFAULT_FRONTMATTER, Dumper=CustomDumper, sort_keys=False, allow_unicode=True, default_flow_style=None, width=120)
    print("---- Dumped YAML ----")
    print(fm_yaml_output)

    try:
        parsed_result = yaml.safe_load(fm_yaml_output)
        print("---- Parsed Result ----")
        print(parsed_result)
        if parsed_result == DEFAULT_FRONTMATTER:
            print("SUCCESS: Dumped YAML is parsable and matches original.")
        else:
            print("ERROR: Parsed result does not match original.")
            print(f"Original: {DEFAULT_FRONTMATTER}")
            print(f"Parsed:   {parsed_result}")

    except yaml.YAMLError as e:
        print(f"ERROR during safe_load: {e}")
        # Print more detailed error if available
        if hasattr(e, 'problem_mark'):
            print(f"Error location: Line {e.problem_mark.line+1}, Column {e.problem_mark.column+1}")
        if hasattr(e, 'problem'):
            print(f"Problem: {e.problem}")
        if hasattr(e, 'context'):
            print(f"Context: {e.context}")


if __name__ == "__main__":
    main() 