import os
import glob
import yaml  # PyYAML
from pathlib import Path
import logging
import json # Added for available_rules.json

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') # Back to INFO level

DEFAULT_FRONTMATTER = {
    'type': 'restored',        # Corrected structure (ensure no typos like ntype)
    'title': 'Restored File',
    'description': 'This file was automatically restored or completed.',
    'globs': [],
    'alwaysApply': False
}

DEFAULT_MARKDOWN_BODY = (
    "# Restored File Content\n\n" # Use actual newline \n, not literal \\n
    "This file was automatically restored or its frontmatter was completed. "
    "Please review and update its content and frontmatter as necessary."
)

def get_archive_path(original_file_path: Path, project_root: Path) -> Path | None:
    """
    Tries to determine the path to an archived version of the given file.
    Example transformations:
    - .cursor/rules/file.mdc -> archive/cursor_rules/file.mdc
    - scripts/cursor_rules/file.mdc -> archive/scripts/cursor_rules/file.mdc
    """
    try:
        relative_path = original_file_path.relative_to(project_root)
    except ValueError:
        logging.warning(f"File {original_file_path} is not within project root {project_root}")
        return None

    parts = list(relative_path.parts)

    if ".cursor" in parts and "rules" in parts:
        try:
            idx_cursor = parts.index(".cursor")
            if parts[idx_cursor + 1] == "rules":
                # Assumes structure like ".cursor/rules/ACTUAL_RULE_NAME.mdc"
                # And archive is "archive/cursor_rules/ACTUAL_RULE_NAME.mdc"
                archive_parts = ["archive", "cursor_rules"] + parts[idx_cursor + 2:]
                return project_root.joinpath(*archive_parts)
        except (ValueError, IndexError) as e:
            logging.debug(f"Could not apply .cursor/rules archive logic for {original_file_path}: {e}")
            pass  # Fall through to general logic if specific pattern fails

    # General case: prefix with 'archive'
    # e.g. some_dir/file.mdc -> archive/some_dir/file.mdc
    if parts:
        archive_parts = ["archive"] + parts
        return project_root.joinpath(*archive_parts)

    return None


def parse_mdc_content(content: str, file_path_for_logging: Path) -> tuple[dict | None, str | None]:
    """ 
    Parses MDC content string into frontmatter dict and markdown body string.
    Handles potential complexities from previous states. Returns (frontmatter, body).
    """
    # Ensure content is a string
    if not isinstance(content, str):
        logging.error(f"Invalid content type for parsing (expected str, got {type(content)}) in {file_path_for_logging}. Treating as empty.")
        return {}, "" # Default to empty FM and body

    normalized_content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    if not normalized_content.strip(): # Handle empty or whitespace-only files
        logging.warning(f"File {file_path_for_logging} is empty or contains only whitespace.")
        return {}, "" # Return empty dict and empty string

    # Check for standard structure first: "---\nYAML\n---\nBODY"
    if normalized_content.startswith("---\n"):
        # Split after first "---\n", only once. Then from that result, split by "\n---\n"
        # This avoids issues if "---" is in the YAML content itself.
        # parts_after_first_delim = normalized_content.split("\n---\n", 1)
        # frontmatter_str = parts_after_first_delim[0][4:] # Skip initial "---\n"

        end_of_fm_marker = "\n---\n"
        try:
            # Find the first "---"
            if not normalized_content.startswith("---"): # Should be caught by earlier check, but defensive
                 logging.warning(f"Content for {file_path_for_logging} does not start with --- despite earlier check. Treating as body.")
                 return {}, normalized_content

            # Content after the initial "---" (and its newline)
            content_after_initial_delim = normalized_content[4:]
            
            idx_end_of_fm = content_after_initial_delim.find(end_of_fm_marker)

            if idx_end_of_fm == -1: # No closing "---" for frontmatter
                logging.warning(f"File {file_path_for_logging}: No clear closing '---' for frontmatter. Assuming all content after initial '---' is frontmatter, no body.")
                frontmatter_str = content_after_initial_delim
                markdown_body_str = "" # No body
            else:
                frontmatter_str = content_after_initial_delim[:idx_end_of_fm]
                markdown_body_str = content_after_initial_delim[idx_end_of_fm + len(end_of_fm_marker):]
        
        except Exception as e_split: # Should not happen with find
            logging.error(f"Error splitting frontmatter/body for {file_path_for_logging}: {e_split}. Treating as body.")
            return {}, normalized_content # All as body

    else: # Does not start with "---" or "\n---\n"
        logging.warning(f"File {file_path_for_logging} does not start with standard '---\n' or '---'. Treating all as body.")
        return {}, normalized_content # All content is body, no frontmatter

    # Parse the extracted frontmatter string
    parsed_fm = None
    try:
        if not frontmatter_str.strip():
            parsed_fm = {} # Empty frontmatter is an empty dict
        else:
            parsed_fm = yaml.safe_load(frontmatter_str)
        
        if parsed_fm is None: # yaml.safe_load can return None for empty input or comments only
            parsed_fm = {}
        if not isinstance(parsed_fm, dict):
            logging.warning(f"File {file_path_for_logging}: Frontmatter parsed but is not a dictionary (type: {type(parsed_fm)}). FM content: '{frontmatter_str[:100].strip()}'. Treating as invalid.")
            return {}, markdown_body_str # Return original body, but no valid FM
    except yaml.YAMLError as e:
        logging.error(f"File {file_path_for_logging}: Failed to parse YAML frontmatter: {e}. Content: '{frontmatter_str[:200].strip()}'.")
        return {}, markdown_body_str # Return original body, but no valid FM

    return parsed_fm, markdown_body_str.lstrip('\n') # Ensure body doesn't start with extra newlines from delimiter


def write_mdc_file(file_path: Path, frontmatter: dict, body: str):
    """Writes the MDC file using standard yaml.dump and ensuring structure."""
    try:
        # Use standard dumper
        # default_flow_style=False encourages block style for collections
        fm_yaml = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True, default_flow_style=False, width=120) 
        
        # Basic structure check
        fm_yaml = fm_yaml.strip() # Remove potential leading/trailing whitespace from dump

        # Ensure body starts on a new line after the '---' if body is not empty
        final_body = body if body is not None else ""
        if final_body and not final_body.startswith('\n'):
            final_body = '\n' + final_body
        # Ensure body always ends with a newline for consistency
        if not final_body.endswith('\n'):
             final_body += '\n'
        
        # Construct content string safely
        content_parts = [
            "---",
            fm_yaml, 
            "---",
            final_body
        ]
        content = "\n".join(content_parts)

        # Ensure the final result ends with exactly one newline
        content = content.rstrip('\n') + '\n'

        file_path.write_text(content, encoding='utf-8')
        logging.info(f"Successfully wrote standardized file: {file_path}")
    except Exception as e:
        logging.error(f"Error writing file {file_path}: {e}")

# Rest of the script (fix_mdc_file, main) remains largely the same, 
# but will now use the standard dumper via write_mdc_file and the revised parse_mdc_content.
# Need to ensure fix_mdc_file calls the revised parse_mdc_content.

def fix_mdc_file(file_path: Path, project_root: Path, json_rules_data: dict):
    logging.info(f"Processing file: {file_path}")
    
    # --- Revised file reading block ---
    original_content = None
    try:
        # Try UTF-8 first
        logging.debug(f"Attempting to read {file_path} with UTF-8 encoding.")
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        logging.debug(f"Successfully read {file_path} with UTF-8.")
    except UnicodeDecodeError:
        logging.warning(f"UTF-8 decode error for {file_path}. Attempting with latin-1 encoding.")
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                original_content = f.read()
            logging.info(f"Successfully read {file_path} with latin-1 after UTF-8 decode error.")
        except Exception as e_latin1:
            logging.error(f"Failed to read {file_path} with latin-1 encoding after UTF-8 error: {e_latin1}. Skipping file.")
            return False, None # Explicit tuple return
    except Exception as e_utf8_other:
        # Catch any other error during UTF-8 read (e.g., permission denied before decoding)
        logging.error(f"Failed to read {file_path} with UTF-8 (general error): {e_utf8_other}. Skipping file.")
        return False, None # Explicit tuple return

    if original_content is None:
        # This condition implies all read attempts failed or were bypassed,
        # and one of the return statements above should have been hit.
        # This is a fallback/sanity check.
        logging.error(f"Critical: File {file_path} could not be read (original_content is None after all attempts). Skipping file.")
        return False, None # Explicit tuple return
    # --- End of revised file reading block ---

    # Continue with processing if original_content was successfully read
    parsed_fm, parsed_body = parse_mdc_content(original_content, file_path)

    changes_made = False
    current_fm_source = "original"

    if parsed_fm is None:
        logging.warning(f"Frontmatter in {file_path} is unparsable or structure is too malformed.")
        # ... (archive/default logic for final_fm, final_body) ...
        # This part is assumed to set final_fm and final_body correctly
        archive_path = get_archive_path(file_path, project_root)
        archive_fm, archive_body = None, None
        if archive_path and archive_path.exists():
            logging.info(f"Attempting to use archive version: {archive_path}")
            try:
                with open(archive_path, "r", encoding="utf-8") as af: # Assuming archive is utf-8
                    archive_content = af.read()
                archive_fm, archive_body = parse_mdc_content(archive_content, archive_path)
                if archive_fm is not None:
                    current_fm_source = "archive"
                    logging.info(f"Successfully parsed archive frontmatter for {file_path}.")
                else:
                    logging.warning(f"Archive frontmatter for {file_path} also unparsable.")
            except Exception as e_arch:
                logging.error(f"Could not read or parse archive file {archive_path}: {e_arch}")

        if archive_fm is not None:
            final_fm = archive_fm
            final_body = archive_body if archive_body is not None else DEFAULT_MARKDOWN_BODY
        else:
            logging.warning(f"Using default frontmatter and body for {file_path} due to parsing issues.")
            final_fm = DEFAULT_FRONTMATTER.copy()
            final_body = parsed_body if parsed_body is not None else DEFAULT_MARKDOWN_BODY
            current_fm_source = "default"
        changes_made = True # Mark changes if FM was bad
    else:
        final_fm = parsed_fm
        final_body = parsed_body if parsed_body is not None else DEFAULT_MARKDOWN_BODY
        if not final_fm:
            current_fm_source = "default_empty_fm"
            # final_fm = DEFAULT_FRONTMATTER.copy() # Ensure final_fm is a dict
            # changes_made = True

    # Ensure final_fm is a dict if it came from parsing an empty but valid FM (e.g. "--- ---")
    if not isinstance(final_fm, dict):
        logging.warning(f"final_fm for {file_path} is not a dict ({type(final_fm)}), resetting to default. Original source: {current_fm_source}")
        final_fm = DEFAULT_FRONTMATTER.copy()
        changes_made = True
        current_fm_source = "default_type_correction"


    # --- DETAILED LOGGING FOR JSON OVERRIDE ---
    json_entry_for_this_file = None
    # Correctly find the JSON entry using the pre-built map or by iterating `json_rules_data['rules']`
    # For simplicity, assuming direct iteration as in the original implementation attempt:
    if isinstance(json_rules_data, dict) and 'rules' in json_rules_data:
        for rule_in_json in json_rules_data.get('rules', []):
            try:
                json_path_full = project_root.joinpath(rule_in_json.get('path', '')).resolve()
                if file_path.resolve() == json_path_full:
                    json_entry_for_this_file = rule_in_json
                    logging.debug(f"Found JSON entry for {file_path}: Name='{json_entry_for_this_file.get('name')}'")
                    break
            except Exception: pass
    
    if not json_entry_for_this_file:
        logging.debug(f"No JSON entry found for {file_path}.")


    if json_entry_for_this_file:
        mdc_title_before_json = final_fm.get('title')
        mdc_desc_before_json = final_fm.get('description')
        json_name_as_title = json_entry_for_this_file.get('name')
        json_description = json_entry_for_this_file.get('description')

        logging.debug(f"  MDC Title (pre-JSON): '{mdc_title_before_json}', JSON Name (for title): '{json_name_as_title}'")
        logging.debug(f"  MDC Desc (pre-JSON): '{mdc_desc_before_json}', JSON Desc: '{json_description}'")

        if json_name_as_title and mdc_title_before_json != json_name_as_title:
            final_fm['title'] = json_name_as_title
            if not changes_made: changes_made = True # Set if not already true
            logging.info(f"  Updated 'title' for {file_path} from JSON ('{json_name_as_title}'). changes_made={changes_made}")
        
        if json_description and mdc_desc_before_json != json_description:
            final_fm['description'] = json_description
            if not changes_made: changes_made = True # Set if not already true
            logging.info(f"  Updated 'description' for {file_path} from JSON. changes_made={changes_made}")
        
        for key in ['globs', 'alwaysApply']:
            # ... (existing globs/alwaysApply logic, ensure changes_made is updated if they change)
            mdc_val = final_fm.get(key)
            json_val = json_entry_for_this_file.get(key)
            default_val = DEFAULT_FRONTMATTER[key]
            
            valid_mdc = False
            if key == 'globs': valid_mdc = isinstance(mdc_val, list) and all(isinstance(s, str) for s in mdc_val)
            elif key == 'alwaysApply': valid_mdc = isinstance(mdc_val, bool)

            chosen_val = default_val # Start with default
            if valid_mdc: chosen_val = mdc_val
            elif json_val is not None: chosen_val = json_val
            
            if final_fm.get(key) != chosen_val:
                final_fm[key] = chosen_val
                if not changes_made: changes_made = True
                logging.debug(f"  Updated '{key}' for {file_path} to '{chosen_val}'. changes_made={changes_made}")
    # --- END DETAILED LOGGING ---

    # Ensure all default keys exist and have correct types
    candidate_fm_for_completion = DEFAULT_FRONTMATTER.copy()
    candidate_fm_for_completion.update(final_fm)
    
    initial_changes_made_state = changes_made # Preserve state before this loop

    for key, default_value in DEFAULT_FRONTMATTER.items():
        current_value = candidate_fm_for_completion.get(key)
        value_is_correct_type = False
        if key in ['type', 'title', 'description']: value_is_correct_type = isinstance(current_value, str)
        elif key == 'globs': value_is_correct_type = isinstance(current_value, list) and all(isinstance(s, str) for s in current_value)
        elif key == 'alwaysApply': value_is_correct_type = isinstance(current_value, bool)

        if key not in candidate_fm_for_completion or not value_is_correct_type:
            if current_value != default_value: # Avoid logging if it's already default
                logging.debug(f"  Key '{key}' in {file_path} is missing, None, or wrong type (Val: '{current_value}', Type: {type(current_value)}). Setting to default: '{default_value}'.")
                candidate_fm_for_completion[key] = default_value
                if not changes_made: changes_made = True # Set if not already true from JSON or earlier steps
    
    final_fm = candidate_fm_for_completion
    if initial_changes_made_state != changes_made:
        logging.debug(f"  changes_made became True during default key completion for {file_path}")


    temp_fm_yaml = yaml.dump(final_fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=120)
    temp_fm_yaml = temp_fm_yaml.strip()
    
    temp_final_body = final_body if final_body is not None else ""
    if temp_final_body and not temp_final_body.startswith('\\n'): temp_final_body = '\\n' + temp_final_body
    if temp_final_body.strip() == "": temp_final_body = "\\n"
    if not temp_final_body.endswith('\\n'): temp_final_body += '\\n'

    expected_content_parts = ["---", temp_fm_yaml, "---", temp_final_body]
    expected_content = "\\n".join(expected_content_parts)
    if not expected_content.endswith("\\n"): expected_content += "\\n"

    normalized_original_content = original_content.replace('\\r\\n', '\\n').replace('\\r', '\\n') if original_content else ""
    if normalized_original_content and not normalized_original_content.endswith('\\n'):
        normalized_original_content += '\\n'
    
    # --- LOGGING FOR WRITE DECISION ---
    logging.debug(f"File: {file_path}")
    logging.debug(f"  changes_made flag: {changes_made}")
    # For brevity, only log if they differ or if changes_made is true
    # To avoid excessively long logs, compare first, then log if different.
    content_differs = normalized_original_content.strip() != expected_content.strip()
    logging.debug(f"  Content differs (stripped compare): {content_differs}")
    if changes_made or content_differs :
        logging.debug(f"    Normalized Original (first 100 chars, stripped): '{normalized_original_content.strip()[:100]}'")
        logging.debug(f"    Expected Content  (first 100 chars, stripped): '{expected_content.strip()[:100]}'")
    # --- END LOGGING FOR WRITE DECISION ---

    if changes_made or content_differs:
        log_reason = []
        if changes_made: log_reason.append("changes_made_flag_true")
        if content_differs: log_reason.append("content_strings_differ")
        logging.info(f"Standardizing/Updating {file_path} (Reason: {', '.join(log_reason)}, Source: {current_fm_source}).")
        write_mdc_file(file_path, final_fm, final_body)
    else:
        logging.info(f"File {file_path} is already valid and standardized. No changes made.")
        # Return False for changes_made if no write happened, but True for success
        return True, final_fm # Return the final_fm even if no write, for JSON update logic

    return True, final_fm


def main():
    project_root = Path(os.getcwd()).resolve()
    logging.info(f"Starting MDC file check in project root: {project_root}")

    # Load available_rules.json
    available_rules_path = project_root.joinpath(".cursor/rules/available_rules.json")
    json_rules_data = {"rules": []} # Default empty structure
    if available_rules_path.exists():
        try:
            with open(available_rules_path, "r", encoding="utf-8") as f:
                json_rules_data = json.load(f)
                if not isinstance(json_rules_data.get('rules'), list):
                    logging.warning(f"{available_rules_path} does not have a 'rules' list. Initializing as empty.")
                    json_rules_data = {"rules": []}
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding {available_rules_path}: {e}. Starting with empty rules list.")
            json_rules_data = {"rules": []}
        except Exception as e:
            logging.error(f"Could not load {available_rules_path}: {e}. Starting with empty rules list.")
            json_rules_data = {"rules": []}
    else:
        logging.warning(f"{available_rules_path} not found. Starting with empty rules list.")

    # Create a quick lookup map from resolved file path string to rule object in JSON
    json_path_to_rule_map = {}
    for rule_obj in json_rules_data.get('rules', []):
        try:
            path_str = rule_obj.get('path')
            if path_str:
                full_path = project_root.joinpath(path_str).resolve()
                json_path_to_rule_map[str(full_path)] = rule_obj
        except Exception as e:
            logging.warning(f"Could not resolve path for rule {rule_obj.get('name')} from JSON: {e}")


    mdc_files = []
    for ext in ("*.mdc", "*.MDC"): 
        mdc_files.extend(project_root.rglob(ext))
    
    mdc_files = sorted(list(set(mdc_files)))

    if not mdc_files:
        logging.info("No .mdc files found.")
        return

    logging.info(f"Found {len(mdc_files)} .mdc files to check.")

    processed_mdc_file_paths_abs = set()
    for mdc_file_str in mdc_files:
        mdc_file_path = Path(mdc_file_str)
        # Ensure we only process files, not directories if glob returns them
        if not mdc_file_path.is_file():
            logging.debug(f"Skipping non-file path: {mdc_file_path}")
            continue
            
        # Skip ignored directories (add this check here if needed)
        ignored_dirs = {'.git', 'node_modules', '__pycache__', '.vscode', '.idea', 'build', 'dist', 'env', 'venv'}
        if any(ignored_dir in mdc_file_path.parts for ignored_dir in ignored_dirs):
            logging.debug(f"Skipping {mdc_file_path} (in an ignored directory).")
            continue
            
        success, final_fm = fix_mdc_file(mdc_file_path, project_root, json_rules_data)
        if success:
            processed_mdc_file_paths_abs.add(str(mdc_file_path.resolve()))
            # If fix_mdc_file updated based on JSON, json_rules_data is implicitly aligned for that file's FM.
            rule_in_json = json_path_to_rule_map.get(str(mdc_file_path.resolve()))
            if rule_in_json and final_fm:
                # ... (update description, globs, alwaysApply in rule_in_json) ...
                # Example update:
                if final_fm.get('description') is not None: rule_in_json['description'] = final_fm['description']
                if final_fm.get('globs') is not None: rule_in_json['globs'] = final_fm['globs']
                if final_fm.get('alwaysApply') is not None: rule_in_json['alwaysApply'] = final_fm['alwaysApply']

    # --- LOGGING BEFORE ADDING MISSING RULES ---
    logging.debug("--- Checking for rules to add to JSON ---")
    existing_json_paths_abs = set(json_path_to_rule_map.keys())
    logging.debug(f"Total paths processed successfully: {len(processed_mdc_file_paths_abs)}")
    logging.debug(f"Total paths found in original JSON: {len(existing_json_paths_abs)}")
    # Log first few paths from each set for comparison (if sets are large)
    if len(processed_mdc_file_paths_abs) > 0:
        logging.debug(f" Example processed paths: {list(processed_mdc_file_paths_abs)[:5]}")
    if len(existing_json_paths_abs) > 0:
        logging.debug(f" Example JSON paths: {list(existing_json_paths_abs)[:5]}")
    # --- END LOGGING ---

    # Identify MDC files not in available_rules.json and add them
    mdc_rules_dir_abs_str = str(project_root.joinpath(".cursor/rules").resolve())

    rules_added_count = 0
    for mdc_abs_path_str in processed_mdc_file_paths_abs:
        if mdc_abs_path_str not in existing_json_paths_abs:
            if not mdc_abs_path_str.startswith(mdc_rules_dir_abs_str):
                logging.debug(f"Skipping adding {mdc_abs_path_str} to JSON as it's not under .cursor/rules.")
                continue

            mdc_file_path = Path(mdc_abs_path_str)
            logging.debug(f"File {mdc_file_path} not found in {available_rules_path}. Attempting to generate JSON entry.")
            
            current_content = ""
            try:
                with open(mdc_file_path, "r", encoding="utf-8") as f:
                    current_content = f.read()
            except Exception as e:
                logging.error(f"Could not re-read {mdc_file_path} to add to JSON: {e}")
                continue
            
            fm_for_json, _ = parse_mdc_content(current_content, mdc_file_path)

            if fm_for_json:
                try:
                    json_entry_path = str(mdc_file_path.relative_to(project_root)).replace("\\\\", "/")
                except ValueError:
                    logging.warning(f"Cannot make {mdc_file_path} relative to {project_root}. Skipping add to JSON.")
                    continue

                json_entry_name = fm_for_json.get('title', Path(json_entry_path).stem)
                if json_entry_name == "Restored File" or not json_entry_name:
                    try:
                         relative_to_rules_dir = mdc_file_path.relative_to(project_root.joinpath(".cursor/rules"))
                         json_entry_name = str(relative_to_rules_dir.with_suffix('')).replace("\\\\", "/")
                    except ValueError:
                         # Fallback if it's not under .cursor/rules (though outer check should prevent this)
                         json_entry_name = Path(json_entry_path).stem 
                
                # --- ADDED: Construct the new_rule_entry dictionary --- 
                new_rule_entry = {
                    "name": json_entry_name,
                    "path": json_entry_path,
                    "description": fm_for_json.get('description', DEFAULT_FRONTMATTER['description']),
                    "globs": fm_for_json.get('globs', DEFAULT_FRONTMATTER['globs']),
                    "alwaysApply": fm_for_json.get('alwaysApply', DEFAULT_FRONTMATTER['alwaysApply']),
                }
                # --- END ADDED --- 

                rules_added_count += 1
                json_rules_data.setdefault('rules', []).append(new_rule_entry)
                logging.info(f"Prepared new entry for {json_entry_name} ({json_entry_path}) to be added to JSON data.")
                json_path_to_rule_map[str(mdc_file_path.resolve())] = new_rule_entry
            else:
                logging.warning(f"Could not parse frontmatter from {mdc_file_path} even after fixing. Cannot add to JSON.")
    
    logging.info(f"Identified {rules_added_count} new rules under .cursor/rules to add to available_rules.json.")

    # Write back the possibly modified json_rules_data
    final_rule_count = len(json_rules_data.get('rules', []))
    logging.info(f"Attempting to write {final_rule_count} rules back to {available_rules_path}.")
    
    try:
        with open(available_rules_path, "w", encoding="utf-8") as f:
            json.dump(json_rules_data, f, indent=4, ensure_ascii=False) # Added ensure_ascii=False
        logging.info(f"Successfully updated {available_rules_path} with {final_rule_count} rules.")
    except Exception as e_write:
        # Log the exception with traceback
        logging.error(f"CRITICAL: Failed to write updated rules to {available_rules_path}: {e_write}", exc_info=True)

    logging.info(f"MDC file processing complete.")

if __name__ == "__main__":
    main() 