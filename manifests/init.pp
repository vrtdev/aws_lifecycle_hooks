
# Class: aws_lifecyle_hooks
#
# @param base_dir           Directory to deploy lifecycle hook scripts to.
# @param base_requirements  Requirements needed for the base tools. Array of lines to add to requirements.txt
# @param requirements       Array of additional requirements. Array of lines to add to requirements.txt
# @param entry_script       Script that will be triggered at instance boot. Relative to $base_dir.
# @param script_order_index Ordering index in the 'per-boot' dirctory.
# @param script_source      Puppet File resource 'source' param for installing needed files. 
# @param py_version         Python version to install. See python class for details
# @param py_pip             Desired installation state for python-pip.
# @param py_dev             Desired installation state for python-dev
# @param py_virtualenv      Desired installation state for python-virtualenv.
# @param py_gunicorn        Desired installation state for Gunicorn.
#
class aws_lifecycle_hooks (
  String                            $base_dir           = '/opt/aws_lifecycle_hooks',
  Array[String]                     $base_requirements  = ['boto3'],
  Array[String]                     $requirements       = [],
  Optional[String]                  $entry_script       = undef,
  Integer                           $script_order_index = 99,
  Optional[String]                  $script_source      = undef,
  String                            $py_version         = 'system',
  Enum['present','absent','latest'] $py_pip             = 'present',
  Enum['present','absent','latest'] $py_dev             = 'absent',
  Enum['present','absent','latest'] $py_virtualenv      = 'present',
  Enum['present','absent','latest'] $py_gunicorn        = 'absent',
){
  # resources
  if $script_source {
    $recurse = true
    $source = $script_source
  }

  file { $base_dir:
    ensure  => directory,
    mode    => '0755',
    recurse => $recurse,
    source  => $source,
  }

  file { "${base_dir}/set_inservice.py":
    ensure => file,
    mode   => '0755',
    source => 'puppet:///modules/aws_lifecycle_hooks/set_inservice.py',
  }

  $requirements_array = concat($base_requirements, $requirements)
  $requirements_str = join($requirements_array, "\n")
  file { "${base_dir}/requirements.txt":
    ensure  => file,
    mode    => '0444',
    content => $requirements_str,
  }

  if $entry_script {
    exec { 'aws_lifecycle_hooks : Create /var/lib/cloud/scripts/per-boot':
      command => 'mkdir -p /var/lib/cloud/scripts/per-boot',
      creates => '/var/lib/cloud/scripts/per-boot',
    }

    # hook entry point
    $bootstrap_lifecycle_hook_cmd = "${base_dir}/venv/bin/python ${base_dir}/${entry_script}"
    file { "/var/lib/cloud/scripts/per-boot/${script_order_index}_bootstrap_lifecycle_hook.sh":
      ensure  => file,
      mode    => '0755',
      content => $bootstrap_lifecycle_hook_cmd,
      require => Exec['aws_lifecycle_hooks : Create /var/lib/cloud/scripts/per-boot'],
    }
  }

  class { '::python':
    version    => $py_version,
    pip        => $py_pip,
    dev        => $py_dev,
    virtualenv => $py_virtualenv,
    gunicorn   => $py_gunicorn,
  }

  python::virtualenv { $base_dir:
    ensure       => 'present',
    venv_dir     => "${base_dir}/venv",
    version      => '3',
    requirements => "${base_dir}/requirements.txt",
  }
}
