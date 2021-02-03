# Manage the entry_script of aws_lifecycle_hooks
# 
# @param base_dir Directory to deploy lifecycle hook scripts to.
# @param script_name Name of the lifecycle hook script.
# @param index Index number of the script, used for execution ordering.
# @param use_python_venv Boolean to use a python virtual env or not.
# @param parameters Array of additional parameters to give to the script.
# @param ensure Whether the file should exist.
# @param pass_state_dir_param Boolean to pass the state dir as a param or not.
#
define aws_lifecycle_hooks::entry_script (
  String                            $base_dir,
  String                            $script_name,
  Integer[1]                        $index,
  Boolean                           $use_python_venv      = false,
  Array[String]                     $parameters           = [],
  Enum['file','present','absent']   $ensure               = 'file',
  Boolean                           $pass_state_dir_param = false,
) {
  # hook entry point
  if $use_python_venv {
    $cmd_init = "${base_dir}/venv/bin/python"
  } else {
    $cmd_init = undef
  }

  if $pass_state_dir_param {
    $_parameters = concat(['--state-dir', $aws_lifecycle_hooks::state_dir], $parameters)
  } else {
    $_parameters = $parameters
  }

  $cmd = join(['exec', $cmd_init, "${base_dir}/${script_name}", $_parameters, "\n"], ' ')

  $entry_script = join(['#!/bin/bash', $cmd], "\n")

  $index_str = sprintf('%02d', $index)
  file { "/var/lib/cloud/scripts/per-boot/${index_str}_${script_name}.sh":
    ensure  => $ensure,
    mode    => '0755',
    content => $entry_script,
    require => Exec['aws_lifecycle_hooks : Create /var/lib/cloud/scripts/per-boot'],
  }
}
