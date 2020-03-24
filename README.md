![Github Actions Status](https://github.com/HDI-Project/ballet-submit-labextension/workflows/Build/badge.svg)
![npm version](https://img.shields.io/npm/v/ballet-submit-labextension)
![PyPI Shield](https://img.shields.io/pypi/v/ballet-submit-labextension.svg)

# ballet-submit-labextension

Submit ballet modules from within JupyterLab

This extension is composed of a Python package named `ballet-submit-labextension`
for the server extension and a NPM package also named `ballet-submit-labextension`
for the frontend extension.

## Requirements

- JupyterLab >= 2.0

## Install

Note: You will need NodeJS to install the extension.

```bash
pip install ballet-submit-labextension
jupyter lab build
```

## Troubleshoot

If you are see the frontend extension but it is not working, check
that the server extension is enabled:

```bash
jupyter serverextension list
```

If the server extension is installed and enabled but your not seeing
the frontend, check the frontend is installed:

```bash
jupyter labextension list
```

If it is installed, try:

```bash
jupyter lab clean
jupyter lab build
```

## Contributing

### Development Install

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Move to ballet-submit-labextension directory
# Install server extension
pip install -e .
# Register server extension
jupyter serverextension enable --py ballet-submit-labextension
# Install dependencies
jlpm
# Build Typescript source
jlpm build
# Link your development version of the extension with JupyterLab
jupyter labextension link .

# Rebuild Typescript source after making changes
jlpm build
# Rebuild JupyterLab after making any changes
jupyter lab build
```

You can watch the source directory and run JupyterLab in watch mode to watch for changes in the extension's source and automatically rebuild the extension and application.

```bash
# Watch the source directory in another terminal tab
jlpm watch
# Run jupyterlab in watch mode in one terminal tab
jupyter lab --watch
```

### Uninstall

```bash
pip uninstall ballet-submit-labextension
jupyter labextension uninstall jupyterlab_ballet-submit-labextension
```
