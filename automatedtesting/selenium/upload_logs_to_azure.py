#!/usr/bin/env python3
"""
Azure Log Analytics Log Ingestion Script
Uploads Selenium test logs to Azure Log Analytics Workspace
"""

import json
import requests
import datetime
import hashlib
import hmac
import base64
import os
import sys
import re


def build_signature(customer_id, shared_key, date, content_length, method, content_type, resource):
    """
    Build the authorization signature for Azure Log Analytics
    
    Args:
        customer_id: Log Analytics Workspace ID
        shared_key: Primary or Secondary shared key
        date: RFC1123 formatted date string
        content_length: Length of the JSON payload
        method: HTTP method (POST)
        content_type: Content type header
        resource: Resource path
    
    Returns:
        Authorization header value
    """
    x_headers = f'x-ms-date:{date}'
    string_to_hash = f'{method}\n{str(content_length)}\n{content_type}\n{x_headers}\n{resource}'
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = base64.b64decode(shared_key)
    encoded_hash = base64.b64encode(
        hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
    ).decode()
    authorization = f"SharedKey {customer_id}:{encoded_hash}"
    return authorization


def post_data(customer_id, shared_key, body, log_type):
    """
    Send log data to Azure Log Analytics
    
    Args:
        customer_id: Log Analytics Workspace ID
        shared_key: Primary or Secondary shared key
        body: JSON payload
        log_type: Custom log table name (will be suffixed with _CL)
    
    Returns:
        HTTP response status code
    """
    method = 'POST'
    content_type = 'application/json'
    resource = '/api/logs'
    rfc1123date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    # Use byte length for content-length to match Azure signature requirements
    content_length = len(body.encode('utf-8'))
    
    signature = build_signature(
        customer_id, shared_key, rfc1123date, 
        content_length, method, content_type, resource
    )
    
    uri = f'https://{customer_id}.ods.opinsights.azure.com{resource}?api-version=2016-04-01'
    
    # Ensure Log-Type contains only allowed characters (letters, numbers, underscore)
    safe_log_type = re.sub(r'[^0-9A-Za-z_]', '_', log_type)

    headers = {
        'content-type': content_type,
        'Accept': 'application/json',
        'Authorization': signature,
        'Log-Type': safe_log_type,
        'x-ms-date': rfc1123date,
        'Content-Length': str(content_length)
    }
    
    # Debug output: payload size
    print(f'DEBUG: Uploading payload bytes={content_length} to {uri} with Log-Type={safe_log_type}_CL')
    response = requests.post(uri, data=body.encode('utf-8'), headers=headers)
    
    if response.status_code >= 200 and response.status_code <= 299:
        print(f'✓ Successfully uploaded logs to Azure Log Analytics')
        print(f'  Status: {response.status_code}')
        print(f'  Log Type: {log_type}_CL')
    else:
        print(f'✗ Error uploading logs to Azure Log Analytics')
        print(f'  Status: {response.status_code}')
        print(f'  Response: {response.text}')
    
    return response.status_code


def parse_log_file(log_file_path):
    """
    Parse Selenium log file and convert to JSON format
    
    Args:
        log_file_path: Path to the log file
    
    Returns:
        List of log entries as dictionaries
    """
    log_entries = []
    
    # Pattern to match log entries: YYYY-MM-DD HH:MM:SS[,mmm] - LEVEL - MESSAGE
    # Python logging %(asctime)s produces "2026-03-05 10:23:45,123" (comma + ms)
    log_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d+)?) - (\w+) - (.+)$')
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                match = log_pattern.match(line)
                if match:
                    timestamp, level, message = match.groups()
                    log_entry = {
                        'TimeGenerated': timestamp,
                        'Level': level,
                        'Message': message,
                        'TestSuite': 'Selenium',
                        'Source': 'FunctionalUITests'
                    }
                    log_entries.append(log_entry)
                else:
                    # If line doesn't match pattern, append to previous message
                    if log_entries:
                        log_entries[-1]['Message'] += f'\n{line}'
    except FileNotFoundError:
        print(f'✗ Error: Log file not found: {log_file_path}')
        sys.exit(1)
    except Exception as e:
        print(f'✗ Error reading log file: {str(e)}')
        sys.exit(1)
    
    return log_entries


def get_latest_log_file(log_dir='log'):
    """
    Get the most recent log file from the log directory
    
    Args:
        log_dir: Directory containing log files
    
    Returns:
        Path to the latest log file
    """
    try:
        log_files = [
            os.path.join(log_dir, f) 
            for f in os.listdir(log_dir) 
            if f.startswith('selenium-test-') and f.endswith('.log')
        ]
        
        if not log_files:
            print(f'✗ No log files found in {log_dir}')
            sys.exit(1)
        
        # Get the most recent file
        latest_log = max(log_files, key=os.path.getctime)
        return latest_log
    except Exception as e:
        print(f'✗ Error finding log files: {str(e)}')
        sys.exit(1)


def main():
    """
    Main function to upload Selenium logs to Azure Log Analytics
    """
    print('=' * 80)
    print('Azure Log Analytics - Selenium Log Upload')
    print('=' * 80)
    
    # Get Log Analytics configuration from environment variables
    customer_id = os.getenv('LOG_ANALYTICS_WORKSPACE_ID')
    shared_key = os.getenv('LOG_ANALYTICS_SHARED_KEY')
    log_type = os.getenv('LOG_TYPE', 'SeleniumTest')
    
    if not customer_id:
        print('✗ Error: LOG_ANALYTICS_WORKSPACE_ID environment variable not set')
        print('  Set it with: export LOG_ANALYTICS_WORKSPACE_ID=<workspace-id>')
        sys.exit(1)
    
    if not shared_key:
        print('✗ Error: LOG_ANALYTICS_SHARED_KEY environment variable not set')
        print('  Set it with: export LOG_ANALYTICS_SHARED_KEY=<shared-key>')
        sys.exit(1)
    
    print(f'Workspace ID: {customer_id}')
    print(f'Log Type: {log_type}_CL')
    
    # Get log file path from argument or find latest
    if len(sys.argv) > 1:
        log_file_path = sys.argv[1]
    else:
        print('\nFinding latest log file...')
        log_file_path = get_latest_log_file()
    
    print(f'Log File: {log_file_path}')
    
    # Parse log file
    print('\nParsing log file...')
    log_entries = parse_log_file(log_file_path)
    print(f'✓ Parsed {len(log_entries)} log entries')
    
    if not log_entries:
        print('✗ No log entries found to upload')
        sys.exit(1)
    
    # Convert to JSON
    json_payload = json.dumps(log_entries)
    
    # Upload to Log Analytics
    print('\nUploading to Azure Log Analytics...')
    status_code = post_data(customer_id, shared_key, json_payload, log_type)
    
    if status_code >= 200 and status_code <= 299:
        print('\n✓ Log upload completed successfully')
        print(f'\nQuery your logs in Azure Portal with:')
        print(f'  {log_type}_CL')
        print(f'  | where TimeGenerated > ago(1h)')
        print(f'  | order by TimeGenerated desc')
        sys.exit(0)
    else:
        print('\n✗ Log upload failed')
        sys.exit(1)


if __name__ == '__main__':
    main()
