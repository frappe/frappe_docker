def update(pull=False, patch=False, build=False, update_bench=False, auto=False, restart_supervisor=False,
		restart_systemd=False, requirements=False, no_backup=False, bench_path='.', force=False, reset=False):
	conf = get_config(bench_path=bench_path)
	version_upgrade = is_version_upgrade(bench_path=bench_path)

	if version_upgrade[0] or (not version_upgrade[0] and force):
		validate_upgrade(version_upgrade[1], version_upgrade[2], bench_path=bench_path)

	before_update(bench_path=bench_path, requirements=requirements)

	conf.update({ "maintenance_mode": 1, "pause_scheduler": 1 })
	update_config(conf, bench_path=bench_path)

	if not no_backup:
		print('Backing up sites...')
		backup_all_sites(bench_path=bench_path)

	if pull:
		pull_all_apps(bench_path=bench_path, reset=reset)

	if requirements:
		update_requirements(bench_path=bench_path)
		update_node_packages(bench_path=bench_path)

	if version_upgrade[0] or (not version_upgrade[0] and force):
		pre_upgrade(version_upgrade[1], version_upgrade[2], bench_path=bench_path)
		import bench.utils, bench.app
		print('Reloading bench...')
		if sys.version_info >= (3, 4):
			import importlib
			importlib.reload(bench.utils)
			importlib.reload(bench.app)
		else:
			reload(bench.utils)
			reload(bench.app)

	if patch:
		print('Patching sites...')
		patch_sites(bench_path=bench_path)
	if build:
		build_assets(bench_path=bench_path)
	if version_upgrade[0] or (not version_upgrade[0] and force):
		post_upgrade(version_upgrade[1], version_upgrade[2], bench_path=bench_path)
	if restart_supervisor or conf.get('restart_supervisor_on_update'):
		restart_supervisor_processes(bench_path=bench_path)
	if restart_systemd or conf.get('restart_systemd_on_update'):
		restart_systemd_processes(bench_path=bench_path)

	conf.update({ "maintenance_mode": 0, "pause_scheduler": 0 })
	update_config(conf, bench_path=bench_path)

	print("_"*80)
	print("Bench: Deployment tool for Frappe and ERPNext (https://erpnext.org).")
	print("Open source depends on your contributions, so please contribute bug reports, patches, fixes or cash and be a part of the community")
	print()