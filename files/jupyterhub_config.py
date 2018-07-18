# flake8: noqa
import json
import os
from kubespawner.spawner import KubeSpawner
from jhub_remote_user_authenticator.remote_user_auth import RemoteUserAuthenticator
from oauthenticator.github import GitHubOAuthenticator

class KubeFormSpawner(KubeSpawner):

  # relies on HTML5 for image datalist
  def _options_form_default(self):
    return '''
    <label for='image'>Image</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <input list="image" name="image" placeholder='repo/image:tag'>
    <datalist id="image">
      <option value="gcr.io/kubeflow-images-public/tensorflow-1.4.1-notebook-cpu:v20180419-0ad94c4e">
      <option value="gcr.io/kubeflow-images-public/tensorflow-1.4.1-notebook-gpu:v20180419-0ad94c4e">
      <option value="gcr.io/kubeflow-images-public/tensorflow-1.5.1-notebook-cpu:v20180419-0ad94c4e">
      <option value="gcr.io/kubeflow-images-public/tensorflow-1.5.1-notebook-gpu:v20180419-0ad94c4e">
      <option value="gcr.io/kubeflow-images-public/tensorflow-1.6.0-notebook-cpu:v20180419-0ad94c4e">
      <option value="gcr.io/kubeflow-images-public/tensorflow-1.6.0-notebook-gpu:v20180419-0ad94c4e">
      <option value="gcr.io/kubeflow-images-public/tensorflow-1.7.0-notebook-cpu:v20180419-0ad94c4e">
      <option value="gcr.io/kubeflow-images-public/tensorflow-1.7.0-notebook-gpu:v20180419-0ad94c4e">
    </datalist>
    <br/><br/>

    <label for='cpu_guarantee'>CPU</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <input name='cpu_guarantee' placeholder='200m, 1.0, 2.5, etc'></input>
    <br/><br/>

    <label for='mem_guarantee'>Memory</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <input name='mem_guarantee' placeholder='100Mi, 1.5Gi'></input>
    <br/><br/>

    <label for='extra_resource_limits'>Extra Resource Limits</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <input name='extra_resource_limits' placeholder='{&apos;nvidia.com/gpu&apos;: &apos;3&apos;}'></input>
    <br/><br/>
    '''

  def options_from_form(self, formdata):
    options = {}
    options['image'] = formdata.get('image', [''])[0].strip()
    options['cpu_guarantee'] = formdata.get('cpu_guarantee', [''])[0].strip()
    options['mem_guarantee'] = formdata.get('mem_guarantee', [''])[0].strip()
    options['extra_resource_limits'] = formdata.get('extra_resource_limits', [''])[0].strip()
    return options

  @property
  def singleuser_image_spec(self):
    image = 'gcr.io/kubeflow/tensorflow-notebook-cpu'
    if self.user_options.get('image'):
      image = self.user_options['image']
    return image

  @property
  def cpu_guarantee(self):
    cpu = '500m'
    if self.user_options.get('cpu_guarantee'):
      cpu = self.user_options['cpu_guarantee']
    return cpu

  @property
  def mem_guarantee(self):
    mem = '1Gi'
    if self.user_options.get('mem_guarantee'):
      mem = self.user_options['mem_guarantee']
    return mem

  @property
  def extra_resource_limits(self):
    extra = ''
    if self.user_options.get('extra_resource_limits'):
      extra = json.loads(self.user_options['extra_resource_limits'])
    return extra

###################################################
### JupyterHub Options
###################################################
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.hub_ip = '0.0.0.0'
# Don't try to cleanup servers on exit - since in general for k8s, we want
# the hub to be able to restart without losing user containers
c.JupyterHub.cleanup_servers = False
###################################################

###################################################
### Spawner Options
###################################################
c.JupyterHub.spawner_class = KubeFormSpawner
c.KubeSpawner.singleuser_image_spec = 'gcr.io/kubeflow/tensorflow-notebook'
c.KubeSpawner.cmd = 'start-singleuser.sh'
c.KubeSpawner.args = ['--allow-root']
# gpu images are very large ~15GB. need a large timeout.
c.KubeSpawner.start_timeout = 60 * 30
# Increase timeout to 5 minutes to avoid HTTP 500 errors on JupyterHub
c.KubeSpawner.http_timeout = 60 * 5
# override API hostname since it doesn't match the pod name
c.KubeSpawner.hub_connect_ip = '{{k8s_service_name}}'  # not actually honored :(
c.KubeSpawner.args.append('--hub-api-url=http://{{k8s_service_name}}:8081/hub/api')

{% if config['persistent-storage'] -%}
###################################################
### Persistent volume options
###################################################
c.KubeSpawner.user_storage_pvc_ensure = True
c.KubeSpawner.user_storage_capacity = '{{config['persistent-storage']}}'
{% if config['storage-class'] -%}
c.KubeSpawner.storage_class = '{{config['storage-class']}}'
{%- endif %}
c.KubeSpawner.pvc_name_template = 'claim-{username}{servername}'
c.KubeSpawner.volumes = [
  {
    'name': 'volume-{username}{servername}',
    'persistentVolumeClaim': {
      'claimName': 'claim-{username}{servername}'
    }
  }
]
c.KubeSpawner.volume_mounts = [
  {
    'mountPath': '/home/jovyan/work',
    'name': 'volume-{username}{servername}'
  }
]
# set the group to "users" ("jovyan" doesn't exist)
c.KubeSpawner.singleuser_fs_gid = 100
{%- endif %}

######## Authenticator ######
c.JupyterHub.authenticator_class = 'dummyauthenticator.DummyAuthenticator'
