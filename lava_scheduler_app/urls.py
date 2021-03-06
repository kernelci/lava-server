from django.conf.urls import url
from lava_scheduler_app.views import (
    active_device_list, active_jobs, device_derestrict_device, device_detail,
    device_edit_description, device_force_health_check,
    device_health_history_log, device_list, device_looping_mode,
    device_maintenance_mode, device_online, device_reports,
    device_restrict_device, device_type_detail, device_dictionary,
    device_dictionary_plain, device_type_health_history_log,
    device_type_reports, edit_transition, edit_worker_desc,
    expanded_job_definition, failure_report, favorite_jobs,
    get_remote_definition, health_job_list, healthcheck, index,
    job_annotate_failure, job_cancel, job_change_priority, job_complete_log,
    job_definition, job_definition_plain, job_description_yaml, job_detail,
    job_full_log_incremental, job_json, job_list, job_log_file,
    job_log_file_plain, job_log_incremental, job_log_pipeline_incremental,
    job_output, job_pipeline_incremental, job_pipeline_sections,
    job_pipeline_timing, job_resubmit, job_section_log, job_status,
    job_submit, job_submit_wizard, job_toggle_favorite, lab_health, migration,
    longest_jobs, multinode_job_definition, multinode_job_definition_plain,
    mydevice_list, mydevices_health_history_log, myjobs, online_device_list,
    passing_health_checks, pipeline, pipeline_device_list, queue, reports,
    running, transition_detail, username_list_json, vmgroup_job_definition,
    vmgroup_job_definition_plain, worker_detail, workers,
    download_device_type_template, similar_jobs,)


urlpatterns = [
    url(r'^$', index, name='lava.scheduler'),
    url(r'^reports$', reports, name='lava.scheduler.reports'),
    url(r'^reports/failures$', failure_report, name='lava.scheduler.failure_report'),
    url(r'^edit_worker_desc', edit_worker_desc, name='lava.scheduler.edit_worker_desc'),
    url(r'^activejobs$', active_jobs, name='lava.scheduler.job.active'),
    url(r'^alljobs$', job_list, name='lava.scheduler.job.list'),
    url(r'^jobsubmit$', job_submit, name='lava.scheduler.job.submit'),
    url(r'^jobsubmitwizard$', job_submit_wizard, name='lava.scheduler.job.submit_wizard'),
    url(r'^device_type/(?P<pk>[-_a-zA-Z0-9]+)$', device_type_detail,
        name='lava.scheduler.device_type.detail'),
    url(r'^alldevices$', device_list, name='lava.scheduler.alldevices'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)$', device_detail,
        name='lava.scheduler.device.detail'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/devicedict$', device_dictionary,
        name='lava.scheduler.device.dictionary'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/devicedict/plain$',
        device_dictionary_plain,
        name='lava.scheduler.device.dictionary.plain'),
    url(r'^allworkers$', workers, name='lava.scheduler.workers'),
    url(r'^worker/(?P<pk>[-_a-zA-Z0-9.]+)$', worker_detail,
        name='lava.scheduler.worker.detail'),
    url(r'^edit-transition', edit_transition,
        name='lava.scheduler.edit_transition'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/maintenance$', device_maintenance_mode,
        name='lava.scheduler.device.maintenance'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/forcehealthcheck$',
        device_force_health_check,
        name='lava.scheduler.device.forcehealthcheck'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/looping$', device_looping_mode,
        name='lava.scheduler.device.looping'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/online$', device_online,
        name='lava.scheduler.device.online'),
    url(r'^labhealth/$', lab_health, name='lava.scheduler.labhealth'),
    url(r'^labhealth/device/(?P<pk>[-_a-zA-Z0-9.]+)$', health_job_list,
        name='lava.scheduler.labhealth.detail'),
    url(r'^longestjobs$', longest_jobs, name='lava.scheduler.longest_jobs'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)$', job_detail,
        name='lava.scheduler.job.detail'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/definition$', job_definition,
        name='lava.scheduler.job.definition'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/definition/plain$', job_definition_plain,
        name='lava.scheduler.job.definition.plain'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/description$', job_description_yaml,
        name='lava.scheduler.job.description.yaml'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/multinode_definition$',
        multinode_job_definition,
        name='lava.scheduler.job.multinode_definition'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/multinode_definition/plain$',
        multinode_job_definition_plain,
        name='lava.scheduler.job.multinode_definition.plain'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/vmgroup_definition$',
        vmgroup_job_definition,
        name='lava.scheduler.job.vmgroup_definition'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/vmgroup_definition/plain$',
        vmgroup_job_definition_plain,
        name='lava.scheduler.job.vmgroup_definition.plain'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/expanded_definition$',
        expanded_job_definition,
        name='lava.scheduler.job.expanded_definition'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/expanded_definition/plain$',
        vmgroup_job_definition_plain,
        name='lava.scheduler.job.expanded_definition.plain'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/log_file$', job_log_file,
        name='lava.scheduler.job.log_file'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/log_file/plain$', job_log_file_plain,
        name='lava.scheduler.job.log_file.plain'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/pipeline_incremental$',
        job_pipeline_incremental,
        name='lava.scheduler.job_pipeline_incremental'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/pipeline_sections$',
        job_pipeline_sections,
        name='lava.scheduler.job_pipeline_sections'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/timing$',
        job_pipeline_timing,
        name='lava.scheduler.job_pipeline_timing'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/job_status$', job_status,
        name='lava.scheduler.job_status'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/complete_log$', job_complete_log,
        name='lava.scheduler.job.complete_log'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)(/download/)(?P<log_name>[-_a-zA-Z0-9.]+)$',
        job_section_log,
        name='lava.scheduler.job.section_log'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/cancel$', job_cancel,
        name='lava.scheduler.job.cancel'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/resubmit$', job_resubmit,
        name='lava.scheduler.job.resubmit'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/annotate_failure$',
        job_annotate_failure,
        name='lava.scheduler.job.annotate_failure'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/toggle_favorite$',
        job_toggle_favorite,
        name='lava.scheduler.job.toggle_favorite'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/json$', job_json, name='lava.scheduler.job.json'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/output$', job_output,
        name='lava.scheduler.job.output'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/log_incremental$',
        job_log_incremental,
        name='lava.scheduler.job.log_incremental'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/log_pipeline_incremental$',
        job_log_pipeline_incremental,
        name='lava.scheduler.job.log_pipeline_incremental'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/full_log_incremental$',
        job_full_log_incremental,
        name='lava.scheduler.job.full_log_incremental'),
    url(r'^get-remote-definition', get_remote_definition,
        name='lava.scheduler.get_remote_definition'),
    url(r'^myjobs$', myjobs, name='lava.scheduler.myjobs'),
    url(r'^favorite-jobs$', favorite_jobs, name='lava.scheduler.favorite_jobs'),
    url(r'^favorite-jobs/~(?P<username>[^/]+)$', favorite_jobs,
        name='lava.scheduler.favorite_jobs'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+\.[0-9]+)/priority$', job_change_priority,
        name='lava.scheduler.job.priority'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/restrict$', device_restrict_device,
        name='lava.scheduler.device.restrict_device'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/derestrict$', device_derestrict_device,
        name='lava.scheduler.device.derestrict_device'),
    url(r'^device/(?P<pk>[-_a-zA-Z0-9.]+)/description$',
        device_edit_description,
        name='lava.scheduler.device.edit_description'),
    url(r'^transition/(?P<pk>[0-9]+)$', transition_detail,
        name='lava.scheduler.transition_detail'),
    url(r'^alldevices/pipeline$', pipeline_device_list,
        name='lava.scheduler.pipeline_devices'),
    url(r'^alldevices/active$', active_device_list,
        name='lava.scheduler.active_devices'),
    url(r'^alldevices/online$', online_device_list,
        name='lava.scheduler.online_devices'),
    url(r'^alldevices/passinghealthchecks$', passing_health_checks,
        name='lava.scheduler.passing_health_checks'),
    url(r'^reports/device/(?P<pk>[-_a-zA-Z0-9.]+)', device_reports,
        name='lava.scheduler.device_report'),
    url(r'^reports/device_type/(?P<pk>[-_a-zA-Z0-9]+)', device_type_reports,
        name='lava.scheduler.device_type_report'),
    url(r'^mydevices$', mydevice_list, name='lava.scheduler.mydevice_list'),
    url(r'^username-list-json$', username_list_json,
        name='lava.scheduler.username_list_json'),
    url(r'^queue$', queue, name='lava.scheduler.queue'),
    url(r'^pipeline$', pipeline, name='lava.scheduler.pipeline'),
    url(r'^healthcheck$', healthcheck, name='lava.scheduler.healthcheck'),
    url(r'^running$', running, name='lava.scheduler.running'),
    url(r'^devicehealthhistory/device/(?P<pk>[-_a-zA-Z0-9.]+)',
        device_health_history_log,
        name='lava.scheduler.device_health_history_log'),
    url(r'^dthealthhistory/device_type/(?P<pk>[-_a-zA-Z0-9.]+)',
        device_type_health_history_log,
        name='lava.scheduler.device_type_health_history_log'),
    url(r'^mydevicetypehealthhistory$',
        mydevices_health_history_log,
        name='lava.scheduler.mydevices_health_history_log'),
    url(r'^devicetypeyaml/(?P<pk>[-_a-zA-Z0-9]+)', download_device_type_template,
        name='lava_scheduler_download_device_type_yaml'),
    url(r'^job/(?P<pk>[0-9]+|[0-9]+.[0-9]+)/similarjobs$', similar_jobs,
        name='lava.scheduler.job.similar_jobs'),
    url(r'^migration$', migration, name='lava.scheduler.migration'),
]
