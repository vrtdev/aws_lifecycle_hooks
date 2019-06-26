# Define: aws_lifecycle_hooks::entry_script
# Parameters:
# arguments
#
define aws_lifecycle_hooks::entry_script (
  String                            $base_dir,
  String                            $script_name,
  Integer[1]                        $index,
  Enum['file','present','absent']   $ensure          = 'file',
) {
  # hook entry point
  $bootstrap_lifecycle_hook_cmd = "#!/bin/bash\n${base_dir}/venv/bin/python ${base_dir}/${script_name}\n"

  file { "/var/lib/cloud/scripts/per-boot/${index}_${script_name}.sh":
    ensure  => $ensure,
    mode    => '0755',
    content => $bootstrap_lifecycle_hook_cmd,
    require => Exec['aws_lifecycle_hooks : Create /var/lib/cloud/scripts/per-boot'],
  }
}
