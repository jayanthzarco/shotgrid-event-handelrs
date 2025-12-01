import subprocess
import sys
import threading

import ayon_api
import shotgun_api3

import os, json

sg = shotgun_api3.Shotgun()

running = True


def get_supported_projects():
    projects = sg.find('Project', filters=[['sg_ayon_auto_sync', 'is', True]])  # [{'type': 'Project', 'id': 536}]
    return projects



def start_monitor(evnt_id, evnt_data):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_file = f"{base_dir}/process_tasks.py"
    cmd = [sys.executable, script_file, str(evnt_id), json.dumps(evnt_data)]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    def read_output():
        for line in process.stdout:
            print(f"[WORKER 1] {line.rstrip()}")

    threading.Thread(target=read_output, daemon=True).start()


def get_task_details(task_id, project_id):
    return sg.find("Task", [['project', 'is', {'type': 'Project', 'id': project_id}], ['id', 'is', task_id]],
                   ['task_assignees', 'content', 'id', 'start_date', 'end_date'])


old_events = [30651234]

while running:
    old = old_events[-1]
    live_projects = get_supported_projects()
    events = sg.find("EventLogEntry",
                     [["project", "in", live_projects], ["event_type", "is", ["Shotgun_Task_New"]],
                      ['id', 'greater_than', old]], ['id', 'meta', 'project', 'description'])
    if events:
        for evnt in events:
            if evnt['id'] not in old_events:
                old_events.append(evnt['id'])
                meta = evnt['meta']
                print(f"new task has been created {evnt['id']} -- {evnt['description']}")
                threading.Thread(target=start_monitor, args=(evnt['id'], evnt), daemon=True).start()

        print("----loop-end-----\n  \n  ---- ")
