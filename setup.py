#!/usr/bin/env python3

import os

from setuptools import setup, find_packages
from setuptools.command.install import install as _install


class install(_install):
  def run(self):
    cwd = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), "runefoil", "files"))
    try:
      print("compiling JarVerifier...")
      os.system("make")
    finally:
      os.chdir(cwd)
    super().run()


setup(
  name="runefoil",
  version="1.0",
  description="Paranoid runelite",
  packages=find_packages(),
  package_data={"": ["files/*"]},
  cmdclass={"install": install},
  entry_points={"console_scripts": [
    "runefoil-update = runefoil.updater:main",
    "runefoil-network = runefoil.network_sentry:main",
    "runefoil = runefoil.runelite:main"
  ]},
  zip_safe=False
)
