import os
import json
import yaml  # PyYAML
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s') # Simplified format for this script

# --- Copied from fix_mdc_files.py --- #
# (Assuming CustomDumper and parse_mdc_content are in the same directory or accessible)
# For simplicity in this script, we might not need CustomDumper if we are only reading.
# parse_mdc_content is essential.

DEFAULT_FRONTMATTER_KEYS = {
    'type': None, # Using None as placeholder for expected keys, actual defaults not strictly needed for comparison
    'title': None,
    'description': None,
    'globs': None,
    'alwaysApply': None
}

class ComparisonCustomDumper(yaml.SafeDumper):
    """A dumper for consistent YAML output for comparison purposes if needed, though primarily reading."""
    def represent_sequence(self, tag, sequence, flow_style=None):
        if sequence and (any(isinstance(item, (dict, list)) for item in sequence) or len(sequence) > 1):
             flow_style = False # Block style for non-trivial lists
        return super().represent_sequence(tag, sequence, flow_style=flow_style)

    def represent_scalar(self, tag, value, style=None):
        if isinstance(value, str):
            if value.lower() in ['true', 'false', 'yes', 'no', 'on', 'off', 'null', '']:
                style = '\''
            elif value.isdigit() or (value.startswith('0') and not value.startswith('0.')):
                style = '\''
            elif not value:
                style = '\''
        return super().represent_scalar(tag, value, style=style)


def parse_mdc_frontmatter_strictly(content: str, file_path_for_logging: Path) -> tuple[dict | None, str | None]:
    """ Parses the frontmatter strictly assuming a leading '---' and newline.
        Returns (frontmatter_dict, rest_of_content_str) or (None, original_content_if_unparsable)
    """
    normalized_content = content.replace('\r\n', '\n').replace('\r', '\n')

    if not normalized_content.startswith("---\n"):
        logging.warning(f"File {file_path_for_logging} does not start with '---\n'. Attempting less strict parse or failing.")
        # Fallback to a slightly less strict split for files that might not have been perfectly standardized
        parts = normalized_content.split("\n---\n", 2)
        if normalized_content.startswith("---") and len(parts) >= 2:
            # This could be "---\nFM_CONTENT\n---\nBODY" (parts[0]="---", parts[1]=FM_CONTENT, parts[2]=BODY)
            # OR "---FM_CONTENT_NO_NEWLINE_AFTER_FIRST_DELIMITER..."
            # If parts[0] is "---", then parts[1] is likely the intended frontmatter.
            if parts[0] == "---":
                 frontmatter_str = parts[1]
                 body_str = parts[2] if len(parts) > 2 else ""
            else: # Does not start with "---" but contains "\n---\n"
                 logging.error(f"File {file_path_for_logging} does not start with '---' but contains delimiters. Unclear structure.")
                 return None, normalized_content
        else:
            logging.error(f"File {file_path_for_logging} lacks clear '---' delimiters for frontmatter extraction.")
            return None, normalized_content
    else:
        # Starts with "---\n"
        # content_after_first_marker is everything after the initial "---\n"
        content_after_first_marker = normalized_content[4:]
        
        # Find the next "\n---\n" which signifies the end of the frontmatter
        # and the start of the body (or end of file if no body)
        try:
            end_of_fm_idx = content_after_first_marker.index("\n---\n")
            frontmatter_str = content_after_first_marker[:end_of_fm_idx]
            body_str = content_after_first_marker[end_of_fm_idx + len("\n---\n"):]
        except ValueError: # No second "\n---\n" found
            # This means it's either frontmatter only, or the file ends after frontmatter without a trailing delimiter
            logging.debug(f"File {file_path_for_logging} has initial '---' but no clear second '\n---\n' body delimiter. Assuming all remaining content is frontmatter.")
            frontmatter_str = content_after_first_marker
            # Check if the frontmatter_str itself ends with a simple "\n---" (common for frontmatter-only files)
            if frontmatter_str.endswith("\n---"):
                frontmatter_str = frontmatter_str[:-len("\n---")]
            body_str = "" # No body identified by a second delimiter

    if not frontmatter_str.strip():
        logging.debug(f"Extracted empty frontmatter string for {file_path_for_logging}")
        return {}, body_str
        
    try:
        parsed_fm = yaml.safe_load(frontmatter_str)
        if parsed_fm is None: 
            # If yaml.safe_load returns None for an empty but valid YAML string (e.g. just comments, or literally empty)
            # we treat it as an empty dictionary.
            logging.debug(f"Frontmatter for {file_path_for_logging} parsed as None, treating as empty dict. Content: '{frontmatter_str[:100]}'")
            parsed_fm = {}
            
        if not isinstance(parsed_fm, dict):
            logging.warning(f"File {file_path_for_logging}: Frontmatter parsed but not a dict (type: {type(parsed_fm)}). FM content: '{frontmatter_str[:100].strip()}'")
            return None, body_str # Return original body_str in case it's useful
        return parsed_fm, body_str
    except yaml.YAMLError as e:
        logging.error(f"File {file_path_for_logging}: YAML parse error: {e}. Problematic FM content: '{frontmatter_str[:200].strip()}'")
        return None, body_str # Return original body_str

# --- End of copied/adapted code --- #

def compare_rules(project_root: Path):
    json_rules_path = project_root / ".cursor/rules/available_rules.json"
    if not json_rules_path.exists():
        logging.error(f"JSON rules file not found at: {json_rules_path}")
        return

    try:
        with open(json_rules_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        json_rules_list = json_data.get("rules", [])
    except Exception as e:
        logging.error(f"Error reading or parsing {json_rules_path}: {e}")
        return

    logging.info(f"Comparing {len(json_rules_list)} rules from {json_rules_path} with their .mdc files.\n")

    json_paths_processed = set()

    for json_rule in json_rules_list:
        rule_name_json = json_rule.get("name")
        rule_desc_json = json_rule.get("description", "")
        rule_path_str = json_rule.get("path")

        if not rule_name_json or not rule_path_str:
            logging.warning(f"Skipping incomplete rule entry in JSON: {json_rule}")
            continue
        
        mdc_file_path = project_root / rule_path_str
        json_paths_processed.add(mdc_file_path.resolve())

        logging.info(f"--- Checking Rule: '{rule_name_json}' (Path: {mdc_file_path}) ---")

        if not mdc_file_path.exists():
            logging.warning(f"  MDC File MISSING: {mdc_file_path}")
            print("\n")
            continue
        
        try:
            mdc_content = mdc_file_path.read_text(encoding='utf-8')
        except Exception as e:
            logging.error(f"  Could not read MDC file {mdc_file_path}: {e}")
            if "invalid start byte" in str(e).lower():
                 logging.error(f"    HINT: This looks like a UTF-16LE (often from Windows PowerShell > out-file) or other non-UTF-8 encoding issue.")
            print("\n")
            continue

        frontmatter, _ = parse_mdc_frontmatter_strictly(mdc_content, mdc_file_path)

        if frontmatter is None:
            logging.warning(f"  MDC File PARSE ERROR: Could not parse frontmatter for {mdc_file_path}. It might be malformed or empty.")
        else:
            mdc_title = frontmatter.get("title", "[MDC title missing]")
            mdc_desc = frontmatter.get("description", "[MDC description missing]")
            
            # Comparison: JSON name vs MDC title
            if rule_name_json != mdc_title:
                logging.warning(f"  Name/Title MISMATCH:")
                logging.warning(f"    JSON 'name':         {rule_name_json}")
                logging.warning(f"    MDC frontmatter 'title': {mdc_title}")
            else:
                logging.info(f"  Name/Title MATCH: '{rule_name_json}'")

            # Comparison: JSON description vs MDC description
            if rule_desc_json != mdc_desc:
                logging.warning(f"  Description MISMATCH:")
                logging.warning(f"    JSON 'description':          {rule_desc_json}")
                logging.warning(f"    MDC frontmatter 'description': {mdc_desc}")
            else:
                logging.info(f"  Description MATCH: '{rule_desc_json}'")
            
            # Check for other standard keys in MDC frontmatter
            missing_keys = [k for k in DEFAULT_FRONTMATTER_KEYS if k not in frontmatter]
            if missing_keys:
                logging.info(f"  MDC Frontmatter: Missing standard keys: {missing_keys}")
            # superfluous_keys = [k for k in frontmatter if k not in DEFAULT_FRONTMATTER_KEYS]
            # if superfluous_keys:
            #     logging.info(f"  MDC Frontmatter: Contains non-standard keys: {superfluous_keys}")
        print("\n")

    # Check for MDC files in .cursor/rules that are NOT in the JSON file
    logging.info("--- Checking for MDC files not listed in JSON ---")
    rules_dir = project_root / ".cursor/rules"
    if rules_dir.is_dir():
        all_mdc_in_rules_dir = set(rules_dir.rglob("*.mdc"))
        unlisted_mdc_files = all_mdc_in_rules_dir - json_paths_processed
        if unlisted_mdc_files:
            logging.warning(f"Found {len(unlisted_mdc_files)} .mdc files in '{rules_dir}' (and subdirectories) not listed in {json_rules_path}:")
            for mdc_path in sorted(list(unlisted_mdc_files)):
                logging.warning(f"  - {mdc_path.relative_to(project_root)}")
        else:
            logging.info(f"All .mdc files found in '{rules_dir}' are listed in {json_rules_path}.")
    else:
        logging.warning(f"Rules directory '{rules_dir}' not found for unlisted check.")
    print("\n")



def main():
    project_root_abs = Path(os.getcwd()).resolve()
    logging.info(f"Starting rule comparison in project root: {project_root_abs}")
    compare_rules(project_root_abs)
    logging.info("Rule comparison complete.")

if __name__ == "__main__":
    main() 