#!/usr/bin/env -S python3 -B

import sys
import logging
import re
import urllib.request
import urllib.parse
import json
from urllib.parse import quote

DEV_API_URL = "dev.api.uclusion.com/v1"
STAGE_API_URL = "stage.api.uclusion.com/v1"
PRODUCTION_API_URL = "production.api.uclusion.com/v1"
DEV_SECRET_KEY_ID = "942a8a2a-2b72-4def-b4ae-68c020cce326_1a0e71d8-16f9-4984-8cc3-3bbeca8df29a"
STAGE_SECRET_KEY_ID = "24a08ec1-70c0-47d7-9a4f-b7cc3acb3776_8755dc22-ab53-422c-8188-7198d2104d30"


def send(data, method, my_api_url, auth=None):
    headers = {'Content-Type': 'application/json'}
    if auth is not None:
        headers['Authorization'] = auth
    if data is not None:
        req = urllib.request.Request(
            my_api_url,
            data=json.dumps(data).encode('utf-8'),  # Convert to bytes
            headers=headers,
            method=method
        )
    else:
        req = urllib.request.Request(
            my_api_url,
            headers=headers,
            method=method
        )

    with urllib.request.urlopen(req) as response:
        # Check the HTTP status code
        if response.status == 200 or response.status == 201:
            # Read and decode the response body
            response_body = response.read().decode('utf-8')
            # If the response is JSON, you can parse it
            response_json = json.loads(response_body)
            return response_json
        else:
           raise Exception(response.status)


def login(api_url, market_id, secret, secret_id):
    login_api_url = 'https://sso.' + api_url + '/cli'
    data = {
        'market_id': market_id,
        'client_secret': secret,
        'client_id': secret_id
    }
    return send(data, 'POST', login_api_url)


def get_completed_stage(stages):
    for stage in stages:
        if not stage.get('allows_tasks', True):
            return stage
    raise Exception('No stage found')


def mark_job_complete(short_code, completed_stage, capability, domain):
    complete_job_api_url = 'https://investibles.' + domain + '/cli/' + quote(short_code)
    data = {
        'stage_id': completed_stage['id']
    }
    return send(data, 'PATCH', complete_job_api_url, capability)


def label_jobs(short_codes, capability, domain, label_to_apply):
    label_api_url = 'https://investibles.' + domain + '/add_labels'
    data = {'ticket_codes': short_codes, 'label': label_to_apply}
    return send(data, 'PATCH', label_api_url, capability)


def get_job_report(short_code, capability, domain):
    report_api_url = 'https://investibles.' + domain + '/cli_report/' + quote(short_code)
    return send(None, 'GET', report_api_url, capability)


def job_has_open_tasks(report):
    # Open tasks render as '#### Task T-...'; resolved tasks render as '#### Resolved Task ...' (no match).
    return report is not None and '\n#### Task ' in report


def get_enclosing_job_code(report):
    if not report:
        return None
    match = re.search(r'##\s*Job\s+(J-[A-Za-z\s]+-\d+)', report)
    return match.group(1).strip() if match else None


def add_note(short_code, body, capability, domain):
    note_api_url = 'https://investibles.' + domain + '/cli/' + quote(short_code)
    return send({'body': body, 'tz': 'UTC'}, 'POST', note_api_url, capability)


if __name__ == "__main__" :
    secret_key_id = sys.argv[1]
    secret_key = sys.argv[2]
    workspace_id = sys.argv[3]
    commit_message = sys.argv[4]
    pending_label = sys.argv[5] if len(sys.argv) > 5 else 'Awaiting deploy'

    logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s: %(message)s')

    # Match any short code (J-/T-/B-/C-...), not just jobs, so task commits are handled too.
    regex = r'([A-Z]+-[A-Za-z\s]+-\d+)'
    extracted = None

    # extract from 'something https://stage.uclusion.com/dd56682c-9920-417b-be46-7a30d41bc905/T-Marketing-9 else'
    # or 'some T-Marketing-9 other'
    match = re.search(regex, commit_message)
    if match:
        extracted = match.group(1).strip()

    if extracted is not None:
        logger.info('extracted %s', extracted)
        api_url = PRODUCTION_API_URL
        if secret_key_id == DEV_SECRET_KEY_ID:
            api_url = DEV_API_URL
        elif secret_key_id == STAGE_SECRET_KEY_ID:
            api_url = STAGE_API_URL
        response = login(api_url, workspace_id, secret_key, secret_key_id)
        if response is None or 'uclusion_token' not in response:
            raise Exception(response)
        api_token = response['uclusion_token']
        stages = response['stages']
        job_code = None
        if extracted.startswith('J-'):
            # By convention a J- code is only committed when the job has no tasks left, so it is done -
            # move it to the completed stage. Guard against completion resolving open tasks: only mark
            # complete when the report confirms none are open; if the report cannot be fetched, skip
            # marking complete (T-all-2243).
            try:
                if job_has_open_tasks(get_job_report(extracted, api_token, api_url)):
                    logger.info('%s has open tasks - not marking complete', extracted)
                else:
                    completed_stage = get_completed_stage(stages)
                    mark_job_complete(extracted, completed_stage, api_token, api_url)
            except Exception as e:
                logger.info('could not verify open tasks for %s - not marking complete: %s', extracted, e)
            job_code = extracted
        else:
            # A task/bug commit - resolve its enclosing job.
            try:
                job_code = get_enclosing_job_code(get_job_report(extracted, api_token, api_url))
            except Exception as e:
                logger.info('could not resolve job for %s: %s', extracted, e)
        if job_code is not None:
            # A new commit means the job has work not yet on any environment. Append a dated
            # 'Awaiting deploy' label (newest label wins in the UI, superseding a stale 'Deployed to ...')
            # plus a note, so the job stops falsely showing as deployed (J-all-329).
            try:
                label_jobs([job_code], api_token, api_url, pending_label)
                add_note(job_code, extracted + ' committed - awaiting deploy.', api_token, api_url)
            except Exception as e:
                logger.info('could not mark %s awaiting deploy: %s', job_code, e)
