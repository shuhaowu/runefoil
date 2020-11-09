import os
import contextlib
import subprocess
import logging


@contextlib.contextmanager
def chdir(p):
  cwd = os.getcwd()
  try:
    os.chdir(p)
    yield
  finally:
    os.chdir(cwd)


def system(cmd):
  logging.info(cmd)
  subprocess.check_call(cmd, shell=True)
