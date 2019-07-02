
# Class: aws_lifecyle_hooks
#
# @param base_dir           Directory to deploy lifecycle hook scripts to.
# @param base_requirements  Requirements needed for the base tools. Array of lines to add to requirements.txt
# @param requirements       Array of additional requirements. Array of lines to add to requirements.txt
# @param entry_scripts      Scripts that will be triggered at instance boot.
# @param script_sources     Array of Puppet File resource 'source' param for installing needed files. 
#
class aws_lifecycle_hooks (
  String                            $base_dir           = '/opt/aws_lifecycle_hooks',
  Array[String]                     $base_requirements  = ['boto3'],
  Array[String]                     $requirements       = [],
  Hash                              $entry_scripts      = {},
  Array[String]                     $script_sources     = [],
){
  # resources
  if ! empty($script_sources) {
    $recurse = true
    $source = $script_sources
    $sourceselect = 'all'
  } else {
    $recurse = undef
    $source = undef
    $sourceselect = undef
  }

  $_source = concat( $source, 'puppet:///modules/aws_lifecycle_hooks/aws_lifecycle_hooks/')

  file { $base_dir:
    ensure       => directory,
    mode         => '0755',
    recurse      => $recurse,
    source       => $_source,
    sourceselect => $sourceselect,
  }

  $requirements_array = concat($base_requirements, $requirements)
  $requirements_str = join($requirements_array, "\n")
  file { "${base_dir}/requirements.txt":
    ensure  => file,
    mode    => '0444',
    content => $requirements_str,
  }

  exec { 'aws_lifecycle_hooks : Create /var/lib/cloud/scripts/per-boot':
    command => 'mkdir -p /var/lib/cloud/scripts/per-boot',
    creates => '/var/lib/cloud/scripts/per-boot',
  }

  if $entry_scripts {
    $entry_scripts.each |String $name, Hash $settings| {
      aws_lifecycle_hooks::entry_script {$name:
        base_dir => $base_dir,
        *        => $settings,
      }
    }
  }

  python::virtualenv { $base_dir:
    ensure       => 'present',
    venv_dir     => "${base_dir}/venv",
    version      => '3',
    requirements => "${base_dir}/requirements.txt",
    require      => Class['python']
  }
}
