import os
import sys
import requests

from http.cookies import SimpleCookie
from dataclasses import dataclass
from datetime import date, timedelta, datetime, tzinfo, timezone
from typing import Tuple, List, Dict
from dotenv import load_dotenv

import pandas as pd

load_dotenv()

@dataclass
class JiraTask:
    title: str
    key: str
    id: str


@dataclass
class WorkLogRecord:
    task_id: str
    comment: str
    author: str
    time_started: datetime
    time_spent: timedelta


def get_date():
    if len(sys.argv) == 2:
        return sys.argv[1]
    else:
        now = datetime.now()
        month = ('0' + now.month.__str__())[-2:]
        return f'{now.year}-{month}-01'

def read_jira_info(user) -> dict:
    date = get_date()
    url = os.environ['URL']
    params = {
        'jql': f'assignee in ({user}) and updated > {date} and project in (ME) and timespent > 0',
        'fields': 'summary,worklog'
    }

    print(params['jql'])

    raw_cookie = os.environ['COOKIE']
    simple_cookies = SimpleCookie()
    simple_cookies.load(raw_cookie)
    cookies = {k: v.value for k, v in simple_cookies.items()}

    response = requests.get(url, params=params, cookies=cookies)

    return response.json()


def extract_tasks_and_work_logs(jira_export_dict: dict) -> Tuple[Dict[str, JiraTask], List[WorkLogRecord]]:
    tasks = {}
    work_logs = []
    for issue in jira_export_dict['issues']:
        task = JiraTask(
            title=issue['fields']['summary'],
            key=issue['key'],
            id=issue['id']
        )
        tasks[task.id] = task
        for worklog in issue['fields']['worklog']['worklogs']:
            log = WorkLogRecord(
                task_id=task.id,
                comment=worklog['comment'],
                author=worklog['author']['name'],
                time_started=datetime.fromisoformat(worklog['started'].replace('+0300', '+03:00')).astimezone(
                    timezone(offset=timedelta(hours=8))
                ),
                time_spent=timedelta(seconds=worklog['timeSpentSeconds'])
            )
            work_logs.append(log)

    return tasks, work_logs


def group_work_logs_by_date(work_logs: List[WorkLogRecord]) -> Dict[date, List[WorkLogRecord]]:
    result = {}
    for log in work_logs:
        d = log.time_started.date()
        result[d] = result.setdefault(d, []) + [log]
    return result


def filter_work_logs(work_logs: List[WorkLogRecord], username: str) -> List[WorkLogRecord]:
    return list(filter(lambda l: l.author == username, work_logs))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    user = os.environ['USER']
    jira_info = read_jira_info(user)
    (tasks, work_logs) = extract_tasks_and_work_logs(jira_info)

    work_logs = filter_work_logs(work_logs, user)

    grouped = group_work_logs_by_date(work_logs)
    df = pd.DataFrame(columns=['Результат', 'Задача', 'Дата', 'Время', 'Описание'])

    for date in sorted(grouped.keys(), reverse=True):
        for log in grouped[date]:
            task = tasks[log.task_id]
            df.loc[-1] = [
                task.title,
                task.key,
                str(log.time_started.date()),
                log.time_spent.seconds / 3600,
                log.comment
            ]
            df.index = df.index + 1
            df = df.sort_index()

    print(df)

    df.to_excel('output/report.xlsx', index=False)
