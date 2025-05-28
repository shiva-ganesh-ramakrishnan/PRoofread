import openai
import json
from PRoofread_env import *


client = openai.OpenAI(api_key=CHATGPT_API_KEY)
    
def get_file_name(path: str):
    return path.split('/')[-1]

def merge_duplicate_entries(entries):
    merged_entries = []
    seen = []

    for entry in entries:
        is_duplicate = False
        
        for other in seen:
            if (
                entry['method_changed'] == other['method_changed'] and
                entry['change_type'] == other['change_type'] and
                entry['change_subtype'] == other['change_subtype'] and
                get_file_name(entry['file']) == get_file_name(other['file']) and
                entry['sha'] != other['sha']
            ):
                
                merged_entry = entry.copy()
                merged_entry['merged_from_shas'] = {entry['sha'], other['sha']}
                merged_entries = [e for e in merged_entries if e != other]
                merged_entries.append(merged_entry)
                is_duplicate = True
                break

        if not is_duplicate:
            merged_entries.append(entry)
            seen.append(entry)

    return merged_entries

    

#Just a common interface 
def call_chatgpt_api(chatgpt_conversation, temperature=0, model = 'gpt-4.1-mini'):
    
    response = client.chat.completions.create(    
        model=model,
        messages=chatgpt_conversation,
        temperature=temperature
    )

    return response.choices[0].message.content.strip()


def check_severity_of_change(old_code, new_code, conversation):

    severity_prompt = f'''
    You are a senior engineer performing a code review.

    You are given the base and updated versions of a file, with changes clearly marked between:
    - '---BEGINNING_OF_RESULT FOR <line_range>---'
    - '---END_OF_RESULT---'

    The first two lines of each code block contain:
    - Line 1: file path (e.g., src/controllers/CustomerController.java)
    - Line 2: SHA commit hash (e.g., 87c9c8d7d...abc)

    Each change can be an addition, deletion, or modification. For each change block:
    
    1. Identify the **type of change** (e.g., Logging Addition, Class Renaming, New API Method, Logic Modification).
    2. Write a **brief description** of what was changed and its potential impact.
    3. Assign a **severity level**:
    - LOW: minor edits like logging, renaming, formatting
    - MEDIUM: changes to control flow, error handling, or internal logic
    - HIGH: changes to core business logic, public API behavior, or performance-critical code

    Return a **JSON-like array** of structured objects using the following format:

    [
    {{
        "file": "<file path from line 1>",
        "sha": "<commit hash from line 2>",
        "line_range": "<line range from BEGINNING_OF_RESULT tag>",
        "change_type": LINE_ADDITION (or) LINE_REMOVAL (or) LINE_MODIFICATION,
        "method_changed": Name of method if the line range denotes a method or else None
        "change_subtype": "<short summary>"
        "version": "old" for base branch file, "new" for merging branch file
        "description": "<1-2 sentence explanation of impact>",
        "severity": "<LOW|MEDIUM|HIGH>"
    }},
    ...
    ]

    ### Base branch file:
    {old_code}

    ### Merging branch file:
    {new_code}
    We are looking at changes as each separate method (or) line. So, every method addition, removal should be a separate change. 
    But every method modification doesn't necessarily have to be a separate change. Make it separate only if the modification is huge in size.
    '''
    conversation.append({"role": "user", "content": [{"type": "text", "text": severity_prompt}]})

    
    res = call_chatgpt_api(conversation)
    
    conversation.append({"role": "assistant", "content": [{"type": "text", "text": res}]})
    return json.loads(res)

def get_comments_from_chatgpt(conversation, change_list):
    get_comment_prompt = f'''
    Here are the changes that you mentioned with severity medium or high.
    {change_list}
    Return a **JSON-like array** of structured objects using the following format and stick to this format strictly:
    [
    {{
    "file": "<file field from the change JSON>",
    "sha": "<sha field from the change JSON>",
    "line_range": "<line_range field from the change JSON>",
    "comment_to_add": "<A short comment that says what to do for the change and tags the person who created it?",
    "is_review_required": "True if someone has to check the usage of it in other files (or) else False",
    "version": "<version filed from the change JSON>"
    }},
    ...
    ]    
    '''
    conversation.append({"role": "user", "content": [{"type": "text", "text": get_comment_prompt}]})
    res = call_chatgpt_api(conversation)
    
    return json.loads(res)

def send_diff_data_to_chatgpt(old_code, new_code, numm):
    conversation = []

    changes_data = {'data': check_severity_of_change(old_code, new_code, conversation)}
    with open(f'chatgpt_results/chatgpt_output_{numm}.json', 'w') as cpf:
        json.dump(changes_data, fp=cpf, indent=4)

    with open(f'chatgpt_results/chatgpt_output_{numm}.json', 'r') as cpf:
        changes_data_json = json.load(cpf)
    new_changes = merge_duplicate_entries(changes_data_json['data'])
    with open(f'chatgpt_results/new_chatgpt_output_{numm}.json', 'w') as cpf:
        json.dump({'data': new_changes}, fp=cpf, indent=4)
    with open(f'chatgpt_results/new_chatgpt_output_{numm}.json', 'r') as cpf:
        new_changes_data_json = json.load(cpf)  
    review_needed = False
    change_list_for_comments = []
    for change in new_changes_data_json['data']:
        if change['severity'] == 'LOW':
            continue
        else:
            change_list_for_comments.append(change)
    
    if change_list_for_comments:
        final_comments = get_comments_from_chatgpt(conversation, change_list_for_comments)

        with open(f'final_comments/final_comments_{numm}.json', 'w') as fcp:
            json.dump({'data': final_comments}, fp=fcp, indent=4)