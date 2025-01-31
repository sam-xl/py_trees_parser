# Copyright 2025 SAM XL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test for linting of all python files."""

import subprocess
from pathlib import Path

"""The path of the Python linting script used by the CI/CD pipeline."""
SCRIPT_FILEPATH = Path(".ci/python/lint.sh")


class FormattingError(Exception):
    """
    A custom exception raised for formatting-related errors.

    This exception is intended to signal formatting errors using the same
    script as the CI/CD pipeline uses.
    """

    pass


def test_python_format_check(request):
    """Test if the Python code is formatted correctly."""
    rootdir = request.config.rootdir
    # Run the same linting script as the CI/CD pipeline uses to check the formatting
    result = subprocess.run(
        ["bash", rootdir / SCRIPT_FILEPATH],
        capture_output=True,
        text=True,
    )
    try:
        result.check_returncode()
    except subprocess.CalledProcessError as ex:
        raise FormattingError(result.stdout + result.stderr) from ex
