# Copyright (C) 2013 Linaro Limited
#
# Author: Neil Williams <neil.williams@linaro.org>
#         Senthil Kumaran <senthil.kumaran@linaro.org>
#
# This file is part of LAVA Scheduler.
#
# LAVA Scheduler is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License version 3 as
# published by the Free Software Foundation
#
# LAVA Scheduler is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LAVA Scheduler.  If not, see <http://www.gnu.org/licenses/>.

import copy
import datetime
import errno
import jinja2
import logging
import netifaces
import os
import re
import socket
import subprocess
import urlparse
import yaml

from collections import OrderedDict

from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from lava_scheduler_app.schema import SubmissionException


DEFAULT_IRC_SERVER = "irc.freenode.net"
DEFAULT_IRC_PORT = 6667

SERVICE_UNKNOWN_ERROR = "service not known"
NO_SUCH_NICK_ERROR = "No such nick/channel"


class IRCSendError(Exception):
    """Global IRC error."""


class IRCServerIncorrectError(IRCSendError):
    """Error raised when IRC server name is erroneous."""


class IRCHandleNotFoundError(IRCSendError):
    """Error raised when user handle is not found on specific server."""


def get_fqdn():
    """Returns the fully qualified domain name.
    """
    host = socket.getfqdn()
    try:
        if bool(re.match("[-_a-zA-Z0-9.]+$", host)):
            return host
        else:
            raise ValueError("Your FQDN contains invalid characters")
    except ValueError as exc:
        raise exc


def rewrite_hostname(result_url):
    """If URL has hostname value as localhost/127.0.0.*, change it to the
    actual server FQDN.

    Returns the RESULT_URL (string) re-written with hostname.

    See https://cards.linaro.org/browse/LAVA-611
    """
    domain = get_fqdn()
    try:
        site = Site.objects.get_current()
    except (Site.DoesNotExist, ImproperlyConfigured):
        pass
    else:
        domain = site.domain

    if domain == 'example.com' or domain == 'www.example.com':
        domain = get_ip_address()

    host = urlparse.urlparse(result_url).netloc
    if host == "localhost":
        result_url = result_url.replace("localhost", domain)
    elif host.startswith("127.0.0"):
        ip_pat = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
        result_url = re.sub(ip_pat, domain, result_url)
    return result_url


def split_multi_job(json_jobdata, target_group):  # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    node_json = {}
    node_actions = {}
    node_lmp = {}
    shared_config = get_shared_device_config("/etc/lava-server/shared-device-config.yaml")

    # Check if we are operating on multinode job data. Else return the job
    # data as it is.
    if "device_group" in json_jobdata and target_group:
        pass
    else:
        return json_jobdata

    # get all the roles and create node action list for each role.
    for group in json_jobdata["device_group"]:
        node_actions[group["role"]] = []
        node_lmp[group["role"]] = []

    # Take each action and assign it to proper roles. If roles are not
    # specified for a specific action, then assign it to all the roles.
    all_actions = json_jobdata["actions"]
    for role in node_actions.keys():
        for action in all_actions:
            new_action = copy.deepcopy(action)
            if 'parameters' in new_action \
                    and 'role' in new_action["parameters"]:
                if new_action["parameters"]["role"] == role:
                    new_action["parameters"].pop('role', None)
                    node_actions[role].append(new_action)
            else:
                node_actions[role].append(new_action)

    if "lmp_module" in json_jobdata:
        # For LMP init in multinode case
        all_lmp_modules = json_jobdata["lmp_module"]
        for role in node_lmp.keys():
            for lmp in all_lmp_modules:
                new_lmp = copy.deepcopy(lmp)
                if 'parameters' in new_lmp \
                        and 'role' in new_lmp["parameters"]:
                    if new_lmp["parameters"]["role"] == role:
                        new_lmp["parameters"].pop('role', None)
                        node_lmp[role].append(new_lmp)
                else:
                    node_lmp[role].append(new_lmp)

    group_count = 0
    for clients in json_jobdata["device_group"]:
        group_count += int(clients["count"])
    if group_count <= 1:
        raise ValueError("Only one device requested in a MultiNode job submission.")
    for clients in json_jobdata["device_group"]:
        role = str(clients["role"])
        count = int(clients["count"])
        node_json[role] = []
        for c in range(0, count):
            node_json[role].append({})
            node_json[role][c]["timeout"] = json_jobdata["timeout"]
            if json_jobdata.get("job_name", False):
                node_json[role][c]["job_name"] = json_jobdata["job_name"]
            if clients.get("tags", False):
                node_json[role][c]["tags"] = clients["tags"]
            if "is_slave" in clients:
                node_json[role][c]["is_slave"] = clients["is_slave"]
            node_json[role][c]["group_size"] = group_count
            node_json[role][c]["target_group"] = target_group
            node_json[role][c]["actions"] = node_actions[role]
            if "lmp_module" in json_jobdata:
                node_json[role][c]["lmp_module"] = node_lmp[role]

            node_json[role][c]["role"] = role
            # multinode node stage 2
            if json_jobdata.get("logging_level", False):
                node_json[role][c]["logging_level"] = \
                    json_jobdata["logging_level"]
            if json_jobdata.get("priority", False):
                node_json[role][c]["priority"] = json_jobdata["priority"]
            node_json[role][c]["device_type"] = clients["device_type"]
            if shared_config:
                node_json[role][c]["shared_config"] = shared_config

    return node_json


def split_vm_job(json_jobdata, vm_group):  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    node_json = {}
    node_actions = {}
    vms_list = []

    # Check if we are operating on vm_group job data. Else return the job
    # data as it is.
    if "vm_group" in json_jobdata and vm_group:
        pass
    else:
        raise Exception('Invalid vm_group data')

    # Get the VM host details.
    device_type = json_jobdata['vm_group']['host']['device_type']
    role = json_jobdata['vm_group']['host']['role']
    is_vmhost = True
    auto_start_vms = None
    if 'auto_start_vms' in json_jobdata['vm_group']:
        auto_start_vms = json_jobdata['vm_group']['auto_start_vms']
    vms_list.append((device_type, role, 1, is_vmhost))  # where 1 is the count

    # Get all other constituting VMs.
    for vm in json_jobdata['vm_group']['vms']:
        device_type = vm['device_type']
        count = int(vm.get('count', 1))
        role = vm.get('role', None)
        is_vmhost = False
        vms_list.append((device_type, role, count, is_vmhost))

    # get all the roles and create node action list for each role.
    for vm in vms_list:
        node_actions[vm[1]] = []

    # Take each action and assign it to proper roles. If roles are not
    # specified for a specific action, then assign it to all the roles.
    all_actions = json_jobdata["actions"]
    for role in node_actions.keys():
        for action in all_actions:
            new_action = copy.deepcopy(action)
            if 'parameters' in new_action \
                    and 'role' in new_action["parameters"]:
                if new_action["parameters"]["role"] == role:
                    new_action["parameters"].pop('role', None)
                    node_actions[role].append(new_action)
            else:
                node_actions[role].append(new_action)

    group_count = 0
    for vm in vms_list:
        group_count += int(vm[2])

    group_counter = group_count
    for vm in vms_list:
        role = vm[1]
        count = int(vm[2])
        node_json[role] = []
        is_vmhost = vm[3]
        for c in range(0, count):
            node_json[role].append({})
            node_json[role][c]["timeout"] = json_jobdata["timeout"]
            node_json[role][c]["is_vmhost"] = is_vmhost
            if auto_start_vms is not None:
                node_json[role][c]["auto_start_vms"] = auto_start_vms
            if json_jobdata.get("job_name", False):
                node_json[role][c]["job_name"] = json_jobdata["job_name"]
            if "is_slave" in json_jobdata:
                node_json[role][c]["is_slave"] = json_jobdata["is_slave"]
            node_json[role][c]["group_size"] = group_count
            node_json[role][c]["target_group"] = vm_group
            node_json[role][c]["actions"] = node_actions[role]
            node_json[role][c]["role"] = role
            # vm_group node stage 2
            if json_jobdata.get("logging_level", False):
                node_json[role][c]["logging_level"] = \
                    json_jobdata["logging_level"]
            if json_jobdata.get("priority", False):
                node_json[role][c]["priority"] = json_jobdata["priority"]
            if is_vmhost:
                node_json[role][c]["device_type"] = vm[0]
            else:
                node_json[role][c]["device_type"] = "dynamic-vm"
                node_json[role][c]["config"] = {
                    "device_type": "dynamic-vm",
                    "dynamic_vm_backend_device_type": vm[0],
                }
                node_json[role][c]["target"] = 'vm%d' % group_counter
        group_counter -= 1

    return node_json


def is_master():
    """Checks if the current machine is the master.
    """
    worker_config_path = '/etc/lava-server/worker.conf'
    if "VIRTUAL_ENV" in os.environ:
        worker_config_path = os.path.join(os.environ["VIRTUAL_ENV"],
                                          worker_config_path[1:])

    return not os.path.exists(worker_config_path)


def get_uptime():
    """Return the system uptime string.
    """
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = int(float(f.readline().split()[0]))
        uptime = str(datetime.timedelta(seconds=uptime_seconds))
        return uptime


# pylint gets confused with netifaces
def get_ip_address():  # pylint: disable=no-member
    """Returns the IP address of the default interface, if found.
    """
    ip = '0.0.0.0'
    gateways = netifaces.gateways()
    if gateways:
        default_gateway = gateways.get('default')
        if default_gateway:
            default_interface = default_gateway.get(netifaces.AF_INET)[1]
            if default_interface:
                default_interface_values = netifaces.ifaddresses(
                    default_interface)
                if default_interface_values:
                    ip = default_interface_values.get(
                        netifaces.AF_INET)[0].get('addr')
    return ip


def get_heartbeat_timeout():
    """Returns the HEARTBEAT_TIMEOUT value specified in worker.conf

    If there is no value found, we return a default timeout value 300.
    """
    return 300


# Private variable to record scheduler tick, which shouldn't be accessed from
# other modules, except via the following APIs.
__last_scheduler_tick = timezone.now()


def record_scheduler_tick():
    """Records the scheduler tick timestamp in the global variable
    __last_scheduler_tick
    """
    global __last_scheduler_tick
    __last_scheduler_tick = timezone.now()


def last_scheduler_tick():
    """Returns django.utils.timezone object of last scheduler tick timestamp.
    """
    return __last_scheduler_tick


def process_repeat_parameter(json_jobdata):  # pylint: disable=too-many-branches
    new_json = {}
    new_actions = []
    allowed_actions = ["delpoy_linaro_image", "deploy_image",
                       "boot_linaro_image", "boot_linaro_android_image",
                       "lava_test_shell", "lava_android_test_run",
                       "lava_android_test_run_custom", "lava_android_test_run_monkeyrunner"]

    # Take each action and expand it if repeat parameter is specified.
    all_actions = json_jobdata["actions"]
    for action in all_actions:
        new_action = copy.deepcopy(action)
        if 'parameters' in new_action \
           and 'repeat' in new_action["parameters"]:
            if new_action["command"] not in allowed_actions:
                raise ValueError("Action '%s' can't be repeated" % new_action["command"])
            repeat = new_action["parameters"]["repeat"]
            new_action["parameters"].pop('repeat', None)
            if repeat > 1:
                for i in range(repeat):
                    new_action["parameters"]["repeat_count"] = i
                    new_actions.append(copy.deepcopy(new_action))
            else:
                new_actions.append(copy.deepcopy(new_action))
        else:
            new_actions.append(new_action)

    new_json["timeout"] = json_jobdata["timeout"]
    if json_jobdata.get("device_type", False):
        new_json["device_type"] = json_jobdata["device_type"]
    if json_jobdata.get("target", False):
        new_json["target"] = json_jobdata["target"]
    if json_jobdata.get("job_name", False):
        new_json["job_name"] = json_jobdata["job_name"]
    if json_jobdata.get("logging_level", False):
        new_json["logging_level"] = json_jobdata["logging_level"]
    if json_jobdata.get("priority", False):
        new_json["priority"] = json_jobdata["priority"]
    if json_jobdata.get("tags", False):
        new_json["tags"] = json_jobdata["tags"]
    if "health_check" in json_jobdata:
        new_json["health_check"] = json_jobdata.get("health_check")
    if "device_group" in json_jobdata:
        new_json["device_group"] = json_jobdata.get("device_group")
    if "vm_group" in json_jobdata:
        new_json["vm_group"] = json_jobdata.get("vm_group")
    new_json["actions"] = new_actions

    return new_json


def is_member(user, group):
    return user.groups.filter(name='%s' % group).exists()


def _read_log(log_path):
    logger = logging.getLogger('lava_scheduler_app')
    if not os.path.exists(log_path):
        return {}
    logs = {}
    for logfile in os.listdir(log_path):
        filepath = os.path.join(log_path, logfile)
        with open(filepath, 'r') as log_files:
            try:
                logs.update({logfile: yaml.load(log_files)})
            except yaml.YAMLError as exc:
                logger.warning(exc)
                logs.update({logfile: [{'warning': "YAML error in %s" % os.path.basename(logfile)}]})
    return logs


def folded_logs(job, section_name, sections, summary=False, increment=False):
    log_data = None
    if increment:
        latest = 0
        section_name = ''
        for item in sections:
            current = int(item.values()[0])
            log_path = os.path.join(job.output_dir, 'pipeline', item.values()[0])
            if os.path.isdir(log_path):
                latest = current if current > latest else latest
                section_name = item.keys()[0] if latest == current else section_name
        if not section_name:
            return log_data
    logs = {}
    initialise_log = os.path.join(job.output_dir, 'pipeline', '0')
    if os.path.exists(initialise_log) and section_name == 'deploy':
        logs.update(_read_log(initialise_log))
    for item in sections:
        if section_name in item:
            log_path = os.path.join(job.output_dir, 'pipeline', item[section_name])
            logs.update(_read_log(log_path))
            log_keys = sorted(logs)
            log_data = OrderedDict()
            for key in log_keys:
                summary_items = [item for item in logs[key] if 'ts' in item or 'warning' in item or 'exception' in item]
                if summary_items and summary:
                    log_data[key] = summary_items
                else:
                    log_data[key] = logs[key]
    return log_data


def _split_multinode_vland(submission, jobs):

    for role, _ in jobs.iteritems():
        # populate the lava-vland protocol metadata
        if len(jobs[role]) != 1:
            raise SubmissionException("vland protocol only supports one device per role.")
        jobs[role][0]['protocols'].update({'lava-vland': submission['protocols']['lava-vland'][role]})
    return jobs


def split_multinode_yaml(submission, target_group):  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    """
    Handles the lava-multinode protocol requirements.
    Uses the multinode protocol requirements to generate as many YAML
    snippets as are required to create TestJobs for the multinode submission.
    Each multinode YAML submission is only split once for all roles and all sub jobs.
    parameters:
      submission - the dictionary of the submission YAML.
      device_dict - the dictionary mapping device hostnames to roles
      target_group - the uuid of the multinode group
    return:
      None on error or a dictionary of job roles.
      key: role
      value: list of jobs to be created for that role.
     """
    # the list of devices cannot be definite here, only after devices have been reserved

    # FIXME: needs a Protocol base class in the server and protocol-specific split handlers

    copies = [
        'job_name',
        'timeouts',
        'priority',
        'visibility',
        'notify',
        'metadata',
    ]
    skip = ['role', 'roles']
    scheduling = ['device_type', 'connection', 'host_role', 'context']  # top level values to be preserved
    maps = ['count']  # elements to be matched but not listed at top level.

    roles = {}
    actions = {}
    subid = 0

    # FIXME: check structure using a schema

    role_data = submission['protocols']['lava-multinode']['roles']
    group_size = sum(
        [role_data[count]['count'] for count in role_data if 'count' in role_data[count]]
    )

    # populate the lava-multinode protocol metadata
    for role, value in submission['protocols']['lava-multinode']['roles'].iteritems():
        roles[role] = {}
        for item in copies:
            if item in submission:
                roles[role][item] = submission[item]
        for name in maps:
            if name in value:
                roles[role][name] = value[name]
        for name in scheduling:
            if name in value:
                roles[role][name] = value[name]
        tags = set(value) - set(maps) - set(scheduling)
        params = {
            'target_group': target_group,
            'role': role,
            'group_size': group_size,
            'sub_id': subid,
        }
        if 'essential' in value:
            params['essential'] = value
        for tag in tags:
            params[tag] = value[tag]
        roles[role].update({'protocols': {'lava-multinode': params}})
        subid += 1

    # split the submission based on the roles specified for the actions, retaining order.
    for role in roles:
        for action in submission['actions']:
            for key, value in action.items():
                try:
                    value['role']
                except (KeyError, TypeError):
                    raise SubmissionException("Invalid YAML - check for consistent use of whitespace indents.")
                if role in value['role']:
                    actions.setdefault(role, {'actions': []})
                    actions[role]['actions'].append({copy.deepcopy(key): copy.deepcopy(value)})

    # add other parameters from the lava-multinode protocol
    for key, value in submission['protocols']['lava-multinode'].iteritems():
        if key in skip:
            continue
        for role in roles:
            roles[role]['protocols']['lava-multinode'][key] = value

    # set the role for each action to the role of the job instead of the original list..
    for role in actions:
        for action in actions[role]['actions']:
            for key, value in action.items():
                value['role'] = role

    # jobs dictionary lists the jobs per role,
    jobs = {}
    # check the count of the host_roles
    check_count = None
    for role in roles:
        if 'host_role' in roles[role]:
            check_count = roles[role]['host_role']
    for role in roles:
        if role == check_count:
            if roles[role]['count'] != 1:
                raise SubmissionException('The count for a role designated as a host_role must be 1.')
    sub_id_count = 0
    for role in roles:
        jobs[role] = []
        for sub in range(0, roles[role]['count']):
            job = {}
            job.update(actions[role])
            job.update(roles[role])
            # only here do multiple jobs for the same role differ
            params = job['protocols']['lava-multinode']
            params.update({'sub_id': sub_id_count})
            job['protocols']['lava-multinode'].update(params)
            del params
            for item in maps:
                if item in job:
                    del job[item]
            jobs[role].append(copy.deepcopy(job))
            sub_id_count += 1

    # populate the lava-vland protocol metadata
    if 'lava-vland' in submission['protocols']:
        _split_multinode_vland(submission, jobs)

    # populate the lava-lxc protocol data
    if 'lava-lxc' in submission['protocols']:
        for role, _ in jobs.iteritems():
            if role not in submission['protocols']['lava-lxc']:
                continue
            # populate the lava-lxc protocol metadata
            jobs[role][0]['protocols'].update({'lava-lxc': submission['protocols']['lava-lxc'][role]})

    return jobs


def get_shared_device_config(filename):
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as f:
                config_dict = yaml.load(f.read())
        except (yaml.YAMLError, IOError):
            return None
    else:
        return None
    return config_dict


def mkdir(path):
    try:
        os.makedirs(path, mode=0o755)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def send_irc_notification(nick, recipient, message,
                          server=DEFAULT_IRC_SERVER, port=DEFAULT_IRC_PORT):
    """
    Sends private IRC msg with netcat.
    parameters:
      server - the IRC server where the recipient is.
      port - server port used for the communication.
      nick - nick that sends the message.
      recipient - recipient handle.
      message - message content.
    raise:
      If there is an error, raise an exception and pass stderr message.
    """

    netcat_cmd = "echo -e 'NICK %s\nUSER %s 8 * %s\nPRIVMSG %s :%s\nQUIT\n' | nc -i 5 -q 15 %s %s" % (
        nick, nick, nick, recipient, message,
        server, port)

    proc = subprocess.Popen(['/bin/bash', '-c', netcat_cmd],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.stderr:
        with proc.stderr:
            for line in iter(proc.stderr.readline, b''):
                if SERVICE_UNKNOWN_ERROR in line:
                    raise IRCServerIncorrectError(line)
                else:
                    raise IRCSendError(line)

    with proc.stdout:
        for line in iter(proc.stdout.readline, b''):
            if NO_SUCH_NICK_ERROR in line:
                raise IRCHandleNotFoundError(line)
    proc.wait()


def _dump_value(node):
    if isinstance(node, jinja2.nodes.Const):
        return node.as_const()

    elif isinstance(node, jinja2.nodes.Dict):
        ret = {}
        for n in node.iter_child_nodes():
            ret[n.key.as_const()] = _dump_value(n.value)
        return ret

    elif isinstance(node, (jinja2.nodes.List, jinja2.nodes.Tuple)):
        ret = []
        for n in node.iter_child_nodes():
            ret.append(_dump_value(n))
        return ret if isinstance(node, jinja2.nodes.List) else tuple(ret)


def device_dictionary_to_dict(ast):
    ret = {}

    for node in ast.find_all(jinja2.nodes.Assign):
        ret[node.target.name] = _dump_value(node.node)

    return ret


def device_dictionary_sequence():
    return [
        'connection_command',
        'power_on_command',
        'power_off_command',
        'soft_reset_command',
        'hard_reset_command',
        'pre_power_command',
        'pre_os_command',
        'adb_serial_number',
        'fastboot_options',
        'fastboot_serial_number',
        'device_info',
    ]


def device_dictionary_vlan():
    return [
        'interfaces',
        'tags',
        'map',
        'mac_addr',
        'sysfs',
    ]
