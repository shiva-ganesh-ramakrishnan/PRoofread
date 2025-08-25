# Proofreader: AI-Powered Code Review Assistant

**Proofreader** is an automated code review tool that integrates with GitHub and OpenAI’s ChatGPT API to analyze pull request diffs and generate intelligent, structured, and severity-aware comments. It helps reviewers focus on impactful changes, improves review quality, and accelerates the review cycle.


## Features

- Parses GitHub pull request diffs in real time via webhooks
- Uses ChatGPT to assess change types, severity, and impact
- Posts structured review comments on PRs
- AST-based method-level context extraction for deeper analysis
- Distinguishes low-importance vs critical changes
- Supports multi-line and method-level comment ranges


## How It Works

Proofreader automates code reviews in the following steps:

1. **Webhook Triggered**  
   A GitHub webhook is configured to hit your server when a pull request is opened or updated.

2. **Fetch Diff URL**  
   From the webhook payload, the diff URL of the PR is extracted and the raw diff data is fetched.

3. **Extract File and Line Changes**  
   The diff is parsed to identify which files were changed and the exact line ranges for each change.

4. **Fetch File Versions**  
   Using commit hashes from the webhook, the tool fetches the base (old) and head (new) versions of the changed files.

5. **AST-Based Method Context Extraction**  
   For each changed line, the enclosing method is identified using an Abstract Syntax Tree (AST) parser. This gives full context about the method's structure.

6. **Send Context to ChatGPT**  
   Instead of sending just the diff, the full method from both base and head versions is sent to ChatGPT, enabling it to reason better with full scope and control flow visibility.

7. **Get Severity from ChatGPT**  
   ChatGPT returns a structured JSON-like response including the type of change, a short explanation, and a severity rating (`LOW`, `MEDIUM`, or `HIGH`).

8. **Generate Comments for Significant Changes**  
   If the severity is not `LOW`, the tool sends the change details to ChatGPT again to generate a reviewer-style comment.

9. **Post to GitHub**  
   The final comment, with proper formatting and line range metadata, is posted directly to the GitHub pull request as a review comment.

Demo Video:
https://drive.google.com/file/d/1YhBRwHnLsaV3OzsdFb-leVcUSxsfCncQ/view?usp=sharing
