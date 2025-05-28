import re


def is_trivial_change(file_lines, changed_lines):
    """
    Check if changed lines are trivial ie. comments, blank lines, or logging-only statements
    Might need enhancements later
    """
    log_pattern = re.compile(r'\blogger\.(debug|info|warn|error|trace|fatal)\s*\(')
    var_decl_pattern = re.compile(r'^\s*(final\s+)?(int|String|boolean|long|float|double|char|var)\s+\w+(\s*=\s*[^;]+)?;')    
    
    for line_no in changed_lines:
        if line_no == -1 or line_no > len(file_lines):
            continue

        line = file_lines[line_no - 1].strip()
        if not line or log_pattern.search(line) or var_decl_pattern.match(line):
            continue
        
        return False

    return True
