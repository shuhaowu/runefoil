from . import network, runelite, price_fetcher, system


def main():
  # NVIDIA GPUs needs special care... Ugh.
  # We need to update NVIDIA drivers if it out of sync with the host.
  # Otherwise OpenGL acceleration will not be available and performance
  # suffers significantly.
  system.ensure_gpu_drivers_are_up_to_date()
  system.ensure_database_is_seeded()

  runelite.stop_all_services()
  runelite.terminate_stray_applications()
  network.enable_internet()
  local_version, remote_version = runelite.check_for_update()
  if remote_version != local_version:
    runelite.update_and_patch_source_code(remote_version)
    runelite.compile()
    runelite.move_compiled_artifact_to_final_positions(remote_version)
    runelite.record_local_version(remote_version)

  price_fetcher.fetch_latest_information_from_internet(remote_version)
  network.disable_internet()

  runelite.start_all_services()
  runelite.run_with_post_stop_hook()
