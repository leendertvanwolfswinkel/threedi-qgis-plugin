from pathlib import Path
from ThreeDiToolbox import dependencies

import mock
import os
import pytest


available_dependency = dependencies.Dependency("numpy", "numpy", "")
dependency_with_wrong_version = dependencies.Dependency("numpy", "numpy", "==1972")
missing_dependency = dependencies.Dependency("reinout", "reinout", "")


def test_check_importability():
    # Everything should just be importable.
    dependencies.check_importability()


def test_check_presence_1():
    dependencys_that_are_present = [available_dependency]
    dependencies._check_presence(dependencys_that_are_present)


def test_check_presence_2():
    dependencies_some_missing = [available_dependency, missing_dependency]
    missing = dependencies._check_presence(dependencies_some_missing)
    assert missing == [
        missing_dependency
    ], "reinout is not installed, so it should be missing"


def test_check_presence_3():
    missing = dependencies._check_presence([dependency_with_wrong_version])
    assert missing == [
        dependency_with_wrong_version
    ], "numpy is installed, but not with the requested version"


def test_ensure_everything_installed_smoke():
    # Should just run without errors as we have a correct test setup.
    dependencies.ensure_everything_installed()


def test_install_dependencies(tmpdir):
    small_dependencies = [
        dependency
        for dependency in dependencies.DEPENDENCIES
        if dependency.name == "lizard-connector"
    ]
    dependencies._install_dependencies(small_dependencies, target_dir=tmpdir)
    installed_directory = Path(tmpdir) / "lizard_connector"
    assert installed_directory.exists()


def test_generate_constraints_txt(tmpdir):
    target_dir = Path(tmpdir)
    dependencies.generate_constraints_txt(target_dir=target_dir)
    generated_file = target_dir / "constraints.txt"
    assert "lizard-connector" in generated_file.read_text()


def test_dependencies_target_dir_smoke():
    assert "python" in str(dependencies._dependencies_target_dir())


def test_dependencies_target_dir_somewhere_else(tmpdir):
    # The tmpdir is not a regular your_profile/python/plugins/ThreeDiToolbox dir.
    # So _dependencies_target_dir() will ask qgis for your profile's settings path.
    # We mock that and check that it is used.
    with mock.patch("qgis.core.QgsApplication.qgisSettingsDirPath") as patched:
        patched.return_value = "/some/profile/dir"
        result = str(dependencies._dependencies_target_dir(tmpdir))
        assert "/some/profile/dir/python" == result


def test_get_python_interpreter_linux():
    python_interpreter = dependencies._get_python_interpreter()
    directory, filename = os.path.split(python_interpreter)
    assert "python3" in filename


def test_get_python_interpreter_windows():
    with mock.patch(
        "sys.executable", "C:/Program Files/QGIS 3.4/bin/qgis-ltr-bin.exe"
    ), mock.patch("os.path.exists", return_value=True):
        python_interpreter = dependencies._get_python_interpreter()
        directory, filename = os.path.split(python_interpreter)
        assert filename == "python3.exe"


def test_get_python_interpreter_unknown():
    with mock.patch("sys.executable", "/usr/bin/beer"):
        with pytest.raises(EnvironmentError):
            dependencies._get_python_interpreter()