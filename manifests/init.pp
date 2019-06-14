
# Class: aws_lifecyle_hooks
#
# @param base_dir          Directory to deploy lifecycle hook scripts to.
# @param base_requirements Requirements needed for the base tools. Array of lines to add to requirements.txt
# @param requirements      Array of additional requirements. Array of lines to add to requirements.txt
#
class aws_lifecyle_hooks (  # For param defaults, see data/common.yaml
  String        $base_dir,
  Array[String] $base_requirements,
  Array[String] $requirements,
  String        $entry_script,
){
  # resources
  file { $base_dir:
    ensure => directory,
    mode   => '0755',
  }

  file { "${base_dir}/set_inservice.py":
    ensure => file,
    mode   => '0750',
    source => 'puppet:///modules/aws_lifecycle_hooks/set_inservice.py',
  }

  $requirements_array = concat($base_requirements, $requirements)
  $requirements_str = join($requirements_array, "\n")
  file { '/opt/vrt-ldap/requirements.txt':
    ensure  => file,
    mode    => '0440',
    content => $requirements_str,
  }

  # problematic cross-class dependency
  class { '::profiles::application::python':
    virtualenv => 'present',
  }

  python::virtualenv { $base_dir:
    ensure       => 'present',
    venv_dir     => "${base_dir}/venv",
    version      => '3',
    requirements => "${base_dir}/requirements.txt",
  }

  # hook entry point
  $bootstrap_lifecycle_hook_cmd = "${base_dir}/venv/bin/python ${base_dir}/${entry_script}"
  file { '/var/lib/cloud/scripts/per-boot/99_bootstrap_lifecycle_hook.sh':
    ensure  => file,
    mode    => '0750',
    content => $bootstrap_lifecycle_hook_cmd,
  }

}
