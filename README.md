[![Github Actions Status](https://github.com/HDI-Project/ballet-submit-labextension/workflows/Build/badge.svg)](https://github.com/HDI-Project/ballet-submit-labextension/actions)
[![PyPI Shield](https://img.shields.io/pypi/v/ballet-submit-labextension.svg)](https://pypi.org/project/ballet-submit-labextension)
[![npm version](https://img.shields.io/npm/v/ballet-submit-labextension)](https://www.npmjs.com/package/ballet-submit-labextension)

# ballet-submit-labextension

Submit ballet modules from within JupyterLab

This extension is composed of a Python package named `ballet-submit-labextension`
for the server extension and a NPM package also named `ballet-submit-labextension`
for the frontend extension.

## Requirements

- JupyterLab >= 2.0

## Install

Installation can be done completely using `pip`, which installs both the 
server and the frontend extensions. The frontend extension only can be 
installed using `jupyter labextension install` but will not function properly
without the corresponding server extension.

```bash
pip install ballet-submit-labextension
jupyter lab build
```

Note: You will need NodeJS to install the extension; the installation process
will complain if it is not found.

## Authenticate with GitHub

The extension provides an in-lab experience for authenticating
with GitHub. When you open a notebook, you should see the GitHub icon to the
right on the Notebook toolbar. The icon should be grey at first, indicating
you are not authenticated. Click the icon to open a login window, in which
you can enter your GitHub username and password. These will be exchanged by
the extension for an OAuth token and will be used to propose changes to the
upstream Ballet project on your behalf (if you attempt to submit features).

Alternately, you can provide a personal access token directly using the
configuration approaches below.

## Configure

The extension ties into the same configuration system as Jupyter [Lab] itself.
You can configure the extension with command line arguments or via the
config file, just like you configure Jupyter Notebook or Jupyter Lab.

### All configuration options
    
The following configuration options are available:

```
$ python -c 'from ballet_submit_labextension.app import print_help;print_help()'

BalletApp options
-----------------
--BalletApp.access_token_timeout=<Int>
    Default: 60
    timeout to receive access token from server via polling
--BalletApp.ballet_yml_path=<Unicode>
    Default: ''
    path to ballet.yml file of Ballet project (if Lab is not run from project
    directory)
--BalletApp.debug=<Bool>
    Default: False
    enable debug mode (no changes made on GitHub), will read from $BALLET_DEBUG
    if present
--BalletApp.github_token=<Unicode>
    Default: ''
    github access token, will read from $GITHUB_TOKEN if present
--BalletApp.oauth_gateway_url=<Unicode>
    Default: 'https://github-oauth-gateway.herokuapp.com/'
    url to github-oauth-gateway server
```

### Command line arguments

Invoke Jupyter Lab with command line arguments providing config to the ballet
extension, for example:

```
jupyter lab --BalletApp.debug=True
```

### Config file

1. Determine the path to your jupyter config file (you may have to create it 
if it does not exist):

    ```bash
    touch "$(jupyter --config-dir)/jupyter_notebook_config.py"
    ```

2. Append desired config to the end of the file, for example:

    ```python
    c.BalletApp.debug = True
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
jupyter labextension uninstall ballet-submit-labextension
```

### Release process

```
bumpversion <part>
make release
```
