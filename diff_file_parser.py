import re
import json
import base64
from PRoofread_env import *
import requests
from tree_sitter import Language, Parser
from chatgpt_api_service import send_diff_data_to_chatgpt


'''
Fully functional diff parser that takes in the diff file and then returns the line numbers that have the changes associated with them.
THe next step would be to go through the whole document and find those code blocks(methods/classes in which this change has been made.
'''
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

def get_file_from_sha_hash(path, blob):
    url = GITHUB_REPO_URL+f'contents/{path}?ref={blob}'
    print(f'Fetching whole file contents: {path}')
    # print(url)
    
    headers = {
        "Authorization": f"token {GITHUB_API_KEY}",
        "Accept": "application/vnd.github.v3+json" #TODO - need to try out different accept formats
    }

    blob_response = requests.get(url=url, headers=headers)
    
    # print(blob_response.status_code)
    jsonn = blob_response.json()

    if str(blob_response.status_code) == '200':
        content = base64.b64decode(jsonn['content']).decode('utf-8')
        with open('files/parsing_diff/content_from_blob.txt', 'w') as content_file:
            content_file.write(content)
        # print('Done writing content to file')
        return content

    # print('Done writing into blob_file')
    return None



def find_enclosing_method_or_class(tree, line):    
    cursor = tree.walk()
    stack = [cursor.node]
    method_node = None
    class_node = None
    some_other_node = None
    while stack:
        node = stack.pop()
        if node.start_point[0] <= line - 1 <= node.end_point[0]:
            if node.type == "method_declaration":
                method_node = node
            elif node.type == "class_declaration":
                class_node = node
            else:
                some_other_node = node
            stack.extend(reversed(node.children))

    if method_node:
        return method_node.start_byte, method_node.end_byte, "method", method_node.start_point[0], method_node.end_point[0]
    elif class_node:
        return class_node.start_byte, class_node.end_byte, "class"
    else:
        print(f'SOmething wrong with this line - {line}')
        print(some_other_node.type if some_other_node else 'No node found for that line')
        return (-1, -1, 'program')
    
def is_empty(string):
    for ch in string:
        if ch not in ['', ' ']:
            return False
    return True

def is_comment(string):
    return string.lstrip().startswith('//')


def get_relevant_method_block_for_lines(data, lines_list, numm, file_name, sha):
    print(f'Getting relevant method blocks for file: {file_name}')
    data_lines = data.splitlines()
    JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    tree = parser.parse(bytes(data, encoding="utf8"))

    if tree.root_node.has_error:
        print('Java file has syntax errors')
    if is_trivial_change(data_lines, lines_list):
        print('Change is trivial, no need of checking')
        res = f'File Name: {file_name}\nSHA: {sha}\n'
        with open(f'files/relevant_data_from_ast_/tree_output_{numm}.txt', 'w') as tof:
            tof.write(res)
            
        return res
    
    res_list = []
    res_dic = {}
    
    for line_no in lines_list:
        if line_no != -1:
            start_end_type = find_enclosing_method_or_class(tree, line_no)
            if start_end_type[2] not in ['method', 'class']:
                # print(start_end_type)
                # print(data_lines[max(0, line_no-10):line_no])
                continue
            elif start_end_type[2] == 'method':
                # print(f'Method found for line number: {line_no}')
                
                if start_end_type not in res_dic:
                    res_dic[start_end_type] = [line_no-1]
                    res_list.append(start_end_type)
                else:
                    res_dic[start_end_type].append(line_no-1)
            else:
                # print(f'The enclosing node is not a method - {start_end_type[2]}')
                if (line_no, data_lines[line_no-1], 'class') not in res_list:
                    key = (line_no, data_lines[line_no-1], 'class')
                    res_dic[key] = [line_no]
                    res_list.append((line_no, data_lines[line_no-1], 'class'))
        else:
            res_list.append((-1, '\n', 'blank'))
    if res_list:
        with open(f'files/relevant_data_from_ast_/tree_output_{numm}.txt', 'w') as tof:
            tof.write(f'File Name: {file_name}\n')
            tof.write(f'SHA: {sha}\n')
            for (i, res) in enumerate(res_list):
                if res[0] == -1:
                    continue
                _range = str(res_dic[res][0]) if len(res_dic[res]) == 1 else str(res_dic[res][0])+'-'+str(res_dic[res][-1])
                tof.write(f'------CHANGE_BLOCK INFO---\n')
                if len(res) == 5:
                    tof.write(f'Whole method lines range: {res[3]}-{res[4]}\n')
                tof.write(f'Changed Lines range: {_range}\n')
                tof.write(f'------CHANGE_BLOCK START---\n')
                if res[2] in ['class', 'blank']:
                    tof.write(res[1]+'\n')
                else:
                    tof.write(data[res[0]:res[1]]+'\n')
                tof.write(f'------CHANGE_BLOCK END---\n')
        
        print('Successfully written the enclosing blocks to a new file')
        with open(f'files/relevant_data_from_ast_/tree_output_{numm}.txt', 'r') as tof:
            dat = tof.read()
        return dat
    return f'File Name: {file_name}\nSHA: {sha}\n'
    



def parse_diff(diff_file):
    print('Parsing diff file')
    old_new_file_mappings = {}
    with open(diff_file, 'r') as df:
        lines = df.read().splitlines()
        pr_number = lines[0].strip()
        base_sha, head_sha = lines[1].split(' ')
        base_sha, head_sha = base_sha.strip(), head_sha.strip()

    changed_lines_for_a_file = {'before': {}, 'after': {}}

    before_file, after_file = None, None
    before_changes, after_changes = None, None
    change_line_number = None
    curr_line_counter = 0
    neg_lines = 0
    pos_lines = 0

    index_line_pattern = r"^index\s+([a-f0-9]+)\.\.([a-f0-9]+)\s+(\d+)$"
    changed_lines_pattern = r"^@@\s+(\-\d+,\d+)\s(\+\d+,\d+)\s@@.*"
    for line in lines[2:]:

        if line.startswith('diff --git'):    
            
            before_file, after_file = line.split()[2:]
            before_file = before_file[2:]
            after_file = after_file[2:]

            old_new_file_mappings[before_file] = after_file
            changed_lines_for_a_file['before'][before_file] = []
            changed_lines_for_a_file['after'][after_file] = []

    

        elif re.match(index_line_pattern, line):
            
            continue
            
        elif line.startswith('---') or line.startswith('+++'):
            
            continue

        elif match:=re.match(changed_lines_pattern, line):
            # print(line)
            curr_line_counter = 0
            before_changes = match.group(1)
            print(before_changes)
            neg_lines = 0
            pos_lines = 0
            
            after_changes = match.group(2)
            print(after_changes)
            before_changes = abs(int(before_changes.split(',')[0]))
            print(before_changes)
            after_changes = int(after_changes.split(',')[0])
            print(after_changes)
            
        
        elif line.startswith('-'):
            if is_empty(line[1:]) or is_comment(line[1:]):
                changed_lines_for_a_file['before'][before_file].append(-1)
            else:
                changed_lines_for_a_file['before'][before_file].append(before_changes+curr_line_counter+neg_lines)
                
            neg_lines += 1
        
        elif line.startswith('+'):
            if is_empty(line[1:]) or is_comment(line[1:]):
                changed_lines_for_a_file['after'][after_file].append(-1)
            else:
                changed_lines_for_a_file['after'][after_file].append(after_changes+curr_line_counter+pos_lines)
                
            pos_lines += 1
        else:
            curr_line_counter += 1
    
    new_json = { 'pr_number': pr_number , 'shas': [base_sha, head_sha], 'old_to_new_file_mappings': old_new_file_mappings, 'diff_lines_to_parse': changed_lines_for_a_file}

    with open('files/parsing_diff/new_diff_file_parser_output.json', 'w') as ndf:
        json.dump(new_json, ndf, indent=4)


'''
Given the SHAs for the base branch and the head branch, along with the lines changed before and after,
1. Need to download the file
2. Construct the AST for the file (treesitter)
3. Parse through the tree and find the block(method or class or the whole block for that line)
4. Return the code for that block
'''
def get_context_from_all_data(parsed_diff_file):
    
    # with open(sha_file, 'r') as sf:
    #     before_sha, after_sha = sf.read().split()
    with open(parsed_diff_file, 'r') as pdf:
        parsed_diff_data = json.load(pdf)
    
    before_sha, after_sha = parsed_diff_data['shas'][0], parsed_diff_data['shas'][1]
    old_files = [key for key in parsed_diff_data['old_to_new_file_mappings']]
    new_files = [parsed_diff_data['old_to_new_file_mappings'][key] for key in old_files]

    file_to_method_mappings = {}

    #For a given pair of files, need to get all the related changes.
    #1. Fetch the whole files using the API
    #2. Get the lines to be fetched from those files
    #3. Send both to the AST parser and get the method enclosing both
    #4. Store them as diff pairs
    #5. Check if the change makes sense

        
    files_counter = 0
    for (old_file, new_file) in zip(old_files, new_files):
        #Step 1: Fetching the whole files using the API
        old_file_content = get_file_from_sha_hash(old_file, before_sha)
        new_file_content = get_file_from_sha_hash(new_file, after_sha)

        #Step 2: Get the lines to be fetched from those files
        file_to_method_mappings[old_file] = files_counter
        file_to_method_mappings[new_file] = files_counter+1

        old_file_diff_lines = parsed_diff_data['diff_lines_to_parse']['before'][old_file]
        new_file_diff_lines = parsed_diff_data['diff_lines_to_parse']['after'][new_file]


        #Step 3: Send them both to the AST Parser

        
        old_diff_data = get_relevant_method_block_for_lines(old_file_content, old_file_diff_lines, files_counter, old_file, before_sha)
        new_diff_data = get_relevant_method_block_for_lines(new_file_content, new_file_diff_lines, files_counter+1, new_file, after_sha)
        files_counter += 2

        if old_diff_data.count('\n') == 2 and new_diff_data.count('\n') == 2:
            print(old_diff_data)
            print(new_diff_data)
            print('Nothing to compare. Changes are very simple')
        else:
            print('Calling chatgpt API for getting comments')
            send_diff_data_to_chatgpt(old_diff_data, new_diff_data, files_counter//2)
            print('Done getting comments for current file data\n\n')
            

        


    







# parse_diff('diff_data_3.txt')
# get_context_from_all_data('files/parsing_diff/new_diff_file_parser_output.json')

    
        
