"""
Setup Module to setup Python Handlers for the ballet-submit-labextension extension.
"""
import os

from setupbase import (
    create_cmdclass, install_npm, ensure_targets,
    combine_commands, ensure_python, get_version,
)
import setuptools

HERE = os.path.abspath(os.path.dirname(__file__))

# The name of the project
name="ballet-submit-labextension"

# Ensure a valid python version
ensure_python(">=3.6")

# Get our version
version = '0.4.0'

lab_path = os.path.join(HERE, "server", name, "labextension")

# Representative files that should exist after a successful build
jstargets = [
    os.path.join(HERE, "lib", "serverextension.js"),
]

package_data_spec = {
    name: [
        "*"
    ]
}

data_files_spec = [
    ("share/jupyter/lab/extensions", lab_path, "*.tgz"),
    ("etc/jupyter/jupyter_notebook_config.d", "server/jupyter-config", "ballet-submit-labextension.json"),
]

cmdclass = create_cmdclass("jsdeps", 
    package_data_spec=package_data_spec,
    data_files_spec=data_files_spec
)

cmdclass["jsdeps"] = combine_commands(
    install_npm(HERE, build_cmd="build:all", npm=["jlpm"]),
    ensure_targets(jstargets),
)

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "jupyterlab >= 2.0",
]

setup_args = dict(
    name=name,
    version=version,
    url="https://github.com/HDI-Project/ballet-submit-labextension",
    author="Micah Smith",
    description="Submit ballet modules from within JupyterLab",
    long_description=long_description,
    long_description_content_type="text/markdown",
    cmdclass=cmdclass,
    packages=setuptools.find_packages(where='server',
                                      include=['ballet_submit_labextension',
                                               'ballet_submit_labextension.*']),
    install_requires=install_requires,
    zip_safe=False,
    include_package_data=True,
    license="MIT",
    platforms="Linux, Mac OS X, Windows",
    keywords=["Jupyter", "JupyterLab"],
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Framework :: Jupyter",
    ],
)


if __name__ == '__main__':
    setuptools.setup(**setup_args)
