# Define: aws_lifecycle_hooks::entry_script
# Parameters:
# arguments
#
define aws_lifecycle_hooks::entry_script (
  String                            $base_dir,
  String                            $script_name,
  Integer[1]                        $index,
  Boolean                           $use_python_venv = true,
  Array[String]                     $parameters      = [],
  Enum['file','present','absent']   $ensure          = 'file',
) {
  # hook entry point
  if $use_python_venv {
    $cmd_init = "${base_dir}/venv/bin/python"
  } else {
    $cmd_init = undef
  }

  $cmd = join([$cmd_init, "${base_dir}/${script_name}", $parameters, "\n"], ' ')

  $entry_script = join(['#!/bin/bash', $cmd], "\n")

  file { "/var/lib/cloud/scripts/per-boot/${index}_${script_name}.sh":
    ensure  => $ensure,
    mode    => '0755',
    content => $entry_script,
    require => Exec['aws_lifecycle_hooks : Create /var/lib/cloud/scripts/per-boot'],
  }
}
