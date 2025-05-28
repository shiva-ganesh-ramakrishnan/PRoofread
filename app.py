'''
Main controller file with all the endpoints
'''

from flask import Flask, request, Response
import json
import requests
from PRoofread_env import *
from diff_file_parser import parse_diff, get_context_from_all_data
import os

app = Flask(__name__)

def post_comment_on_pr(pr_number, comment_json):
    if '-' in comment_json["line_range"]:
        start_line, end_line = map(int, comment_json["line_range"].split('-'))
    else:
        start_line = end_line = int(comment_json["line_range"])
    
    version = "RIGHT" if comment_json["version"] == "new" else "LEFT"

    body = {
    "body": comment_json["comment_to_add"],
    "commit_id": comment_json["sha"],
    "path": comment_json["file"],
    "start_line": start_line,
    "start_side": version,
    "line": end_line,
    "side": version
    }

    url = POST_COMMENTS_ON_PR_URL.format(request_no = pr_number)
    headers = {
        "Authorization": f"token {GITHUB_API_KEY}",
        "Accept": POST_COMMENTS_ON_PR_ACCEPT_HEADER_VALUE
    }
    print(url)
    try:
        resp = requests.post(url=url, json=body, headers=headers)
        if resp.status_code == 201:
            print('Comment created successfully')
        else:
            print(resp.json())
    
    except Exception as e:
        print(f'Error occurred while sending post request: {e}')

#Main endpoint that gets called when github webhook is triggered
@app.route('/get-pr-data', methods=['POST'])
def get_pr_data_from_github():
    print('Webhook triggered')
    data = request.json
    if 'pull_request' in data:
        try:
            request_no = data['pull_request']['number']
            head_sha = data['pull_request']['head']['sha']
            base_sha = data['pull_request']['base']['sha']
            print('Pull request data is legit!')

            with open(f'pull_request_{request_no}_webhook_response.json', 'w') as file:
                json.dump(data, file, indent=4)      
            print(f'Done writing the webhook data into pull_request_{request_no}_webhook_response.json')
        
        except Exception as e:
            print(f'Failed to write webhook data into file: {e}')
            return Response(), 500
        
        try:
            url = data['pull_request']['url']
            print('Found diff url: ', url)

        except Exception as e:
            print(f'Unable to fetch PR diff url from the response body: {e}')
            return Response(), 500
        
        try:
            diff_data, status_code, status_phrase = get_diff_data_from_url(url)
            if status_code != 200:
                print("Couldn't fetch diff data from the provided URL")
                raise Exception(f'{status_code} {status_phrase}, when tried getting diff data from {url}')
            print('Got diff data from Github APIs')            
                
            with open(f'diff_data_{request_no}.txt', 'w') as file2:
                #Writing the PR number and base_sha and head_sha
                file2.write(f'{request_no}\n{base_sha} {head_sha}\n'+diff_data.text)
            
            with open(f'pr_{request_no}_file_hashes.txt', 'w') as file3:
                file3.write(base_sha + ' ' + head_sha)
            print(f'Done writing data into diff_data_{request_no}.txt')
        except Exception as e:
            print(f"Couldn't fetch data from diff url: {e}")            
            return Response(), 500
        
        #Parse and get comments from ChatGPT
        try:
            parse_diff(f'diff_data_{request_no}.txt')
            get_context_from_all_data('files/parsing_diff/new_diff_file_parser_output.json')
        except Exception as e:
            print(f"Couldn't process the diff data: {e}")
            return Response(), 500
        
        #Post comments on github
        try:            
            
            folder_path = 'final_comments'

            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

            for fil in files:
                with open(fil, 'r') as fp:
                    final_comments_data = json.load(fp)
                for final_comment in final_comments_data['data']:
                    post_comment_on_pr(request_no, final_comment)

            

            # print(files)

        except Exception as e:
            print(f"Couldn't post the comments to Github : {e}")

    else:
        print(data)
        print("This doesn't seem to be from a github webhook")
    return Response(), 200


def get_diff_data_from_url(url):
    headers = {
        "Authorization": f"token {GITHUB_API_KEY}",
        "Accept": "application/vnd.github.v3.diff" #TODO - need to try out different accept formats
    }
    
    diff_data = requests.get(url=url, headers=headers)
    print('Fetched diff_data successfully')
    return diff_data, diff_data.status_code, diff_data.reason
    


@app.route('/', methods=['GET'])
def get_status_of_app():
    return Response('App is running on port 5001'), 200

if __name__ == '__main__':
    app.run(port=5001, debug=True)