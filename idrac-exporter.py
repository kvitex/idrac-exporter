#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from flask import Flask
from flask import request
from flask import Response


load_dotenv()
user             = os.environ['IDRAC_USER']
password         = os.environ['IDRAC_PASSWORD']
ssl_verify       = os.environ.get('SSL_VERIFY','True').lower() == 'true'
metrics_name_prefix = os.environ.get('METRICS_NAME_PREFIX', '')

status_value = lambda x: 'NaN' if x is None else int(x.lower() == 'ok')
system_metrics = (
    (('MemorySummary', 'Status', 'Health'), 'MemorySummary_Health', status_value),
    (('MemorySummary', 'Status', 'TotalSystemMemoryGiB'), 'MemorySummary_TotalSystemMemoryGiB', float),
    (('Oem', 'Dell', 'DellSystem', 'BatteryRollupStatus'), 'BatteryRollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'CPURollupStatus'), 'CPURollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'FanRollupStatus'), 'FanRollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'IntrusionRollupStatus'), 'IntrusionRollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'LicensingRollupStatus'), 'LicensingRollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'MaxCPUSockets'), 'MaxCPUSockets', float),
    (('Oem', 'Dell', 'DellSystem', 'MaxDIMMSlots'), 'MaxDIMMSlots', float),
    (('Oem', 'Dell', 'DellSystem', 'MaxPCIeSlots'), 'MaxPCIeSlots', float),
    (('Oem', 'Dell', 'DellSystem', 'PopulatedDIMMSlots'), 'PopulatedDIMMSlots', float),
    (('Oem', 'Dell', 'DellSystem', 'PopulatedPCIeSlots'), 'PopulatedPCIeSlots', float),
    (('Oem', 'Dell', 'DellSystem', 'SDCardRollupStatus'), 'SDCardRollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'ServerAllocationWatts'), 'ServerAllocationWatts', status_value),
    (('Oem', 'Dell', 'DellSystem', 'StorageRollupStatus'), 'StorageRollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'SysMemPrimaryStatus'), 'SysMemPrimaryStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'TempRollupStatus'), 'TempRollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'TempStatisticsRollupStatus'), 'TempStatisticsRollupStatus', status_value),
    (('Oem', 'Dell', 'DellSystem', 'VoltRollupStatus'), 'VoltRollupStatus', status_value),
    (('ProcessorSummary','Count'), 'ProcessorSummary_Count', float),
    (('ProcessorSummary', 'Status', 'Health'), 'ProcessorSummary_Health', status_value),
    (('ProcessorSummary', 'Status', 'HealthRollup'), 'ProcessorSummary_HealthRollup', status_value),
    (('Status', 'Health'), 'Health', status_value),
    (('Status', 'Health'), 'HealthRollup', status_value),
)
system_labels = (
    (('Model',), 'Model'),
    (('Name',), 'Name'),
    (('SerialNumber',), 'SerialNumber'),
)

def extract_label_value(data, label_path):
    label_value = data.get(label_path[0], '')
    if (type(label_value) == dict) and (len(label_path) > 1):
        label_value = extract_label_value(label_value, label_path[1:])
    elif (type(label_value) != dict) and (len(label_path) > 1):
        label_value = ''
    elif (type(label_value) == dict):
        label_value = ''
    return label_value

def extract_metric_value(data, metric_path):
    metric_value = data.get(metric_path[0], '')
    if (type(metric_value) == dict) and (len(metric_path) > 1):
        metric_value = extract_metric_value(metric_value, metric_path[1:])
    elif (type(metric_value) != dict) and (len(metric_path) > 1):
        metric_value = ''
    elif (type(metric_value) == dict):
        metric_value = ''
    return metric_value

def get_system_metrics(host, user, password, ssl_verify, system_labels, system_metrics, **kwargs):
    metrics_name_prefix = kwargs.get('metrics_name_prefix','system')
    response = requests.get(f'https://{host}/redfish/v1/Systems/System.Embedded.1/', 
                              verify=ssl_verify, auth=(user, password))
    data = response.json()
    # x[1] is designated label name, x[0] is a tuple with data path to label value
    labels = list(map(lambda x: (x[1], extract_label_value(data, x[0])), system_labels))
    metrics = []
    for metric_def in system_metrics:
        if (metric_value := extract_metric_value(data, metric_def[0])) != '':
            metrics.append(
                {
                    'name': f'{metrics_name_prefix}_{metric_def[1]}',
                    'value': metric_def[2](metric_value),
                    'labels': labels
                }
            )
    return metrics

app = Flask(__name__)
@app.route('/metrics', methods=['GET', 'POST'])
def main():
    global ssl_verify
    if request.method == 'POST':
        params = request.form
    else:
        params = request.args
    hostname = params.get('hostname')
    # Set ssl_verify var from request parameter, if no such parameter leave curret state
    ssl_verify = str(request.form.get('ssl_verify', ssl_verify)).lower == 'true'
    if not hostname:
        return('Missing parameter: hostname')
    metrics = get_system_metrics(hostname, user, password, ssl_verify, system_labels, system_metrics)
    output_list = []
    for metric in metrics:
        metric_name = metric['name']
        metric_value = metric['value']
        labels_string = ','.join(list(map(lambda st: f'{st[0]}="{st[1]}"', metric['labels'])))
        output_list.append(f'{metrics_name_prefix}{metric_name} {{{labels_string}}} {metric_value}')
    return Response('\n'.join(output_list), mimetype='text/plain')
