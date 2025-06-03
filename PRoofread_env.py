import os
GITHUB_REPO_URL = 'https://api.github.com/repos/shiva-ganesh-ramakrishnan/Testing_Repo_PRoofread/'

GET_ISSUE_COMMENTS_URL = GITHUB_REPO_URL + 'issues/{request_no}/comments'
GET_DIFF_DATA_URL = GITHUB_REPO_URL + 'pulls/{request_no}'
GET_FILE_FROM_HASH_URL = GITHUB_REPO_URL + 'contents/{path}?ref={blob}'
GET_COMMIT_DATA_URL = GITHUB_REPO_URL + 'pulls/{request_no}/commits'
POST_COMMENTS_ON_PR_URL = GITHUB_REPO_URL + 'pulls/{request_no}/comments'

GET_DIFF_DATA_ACCEPT_HEADER_VALUE = 'application/vnd.github.v3.diff'
GET_FILE_FROM_HASH_ACCEPT_HEADER_VALUE = 'application/vnd.github.v3+json'
GET_ISSUE_COMMENTS_ACCEPT_HEADER_VALUE = 'application/vnd.github-commitcomment.text+json'
POST_COMMENTS_ON_PR_ACCEPT_HEADER_VALUE = 'application/vnd.github+json'

GITHUB_API_KEY = os.environ["GITHUB_API_KEY"]
CHATGPT_API_KEY = os.environ["CHATGPT_API_KEY"]