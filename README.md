[![Github Actions Status](https://github.com/HDI-Project/ballet-assemble/workflows/Main/badge.svg)](https://github.com/HDI-Project/ballet-assemble/actions)
[![PyPI Shield](https://img.shields.io/pypi/v/ballet-assemble.svg)](https://pypi.org/project/ballet-assemble)
[![npm version](https://img.shields.io/npm/v/ballet-assemble)](https://www.npmjs.com/package/ballet-assemble)

# Assemblé

/alletApp options
-----------------
--AssembleApp.access_token_timeout=<Int>
    Default: 60
    timeout to receive access token from server via polling
--AssembleApp.ballet_yml_path=<Unicode>
    Default: ''
    path to ballet.yml file of Ballet project (if Lab is not run from project
    directory)
--AssembleApp.debug=<Bool>
    Default: False
    enable debug mode (no changes made on GitHub), will read from $ASSEMBLE_DEBUG
    if present
--AssembleApp.github_token=<Unicode>
    Default: ''
    github access token, will read from $GITHUB_TOKEN if present
--AssembleApp.oauth_gateway_url=<Unicode>
    Default: 'https://github-oauth-gateway.herokuapp.com/'
    url to github-oauth-gateway server
```

### Command line arguments

Invoke Jupyter Lab with command line arguments providing config to the ballet
extension, for example:

```
jupyter lab --AssembleApp.debug=True
```

### Config file

1. Determine the path to your jupyter config file (you may have to create it
if it does not exist):

    ```bash
    touch "$(jupyter --config-dir)/jupyter_notebook_config.py"
    ```

2. Append desired config to the end of the file, for example:

    ```python
    c.AssembleApp.debug = True
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
# Move to ballet-assemble directory
# Install server extension
pip install -e .
# Register server extension
jupyter serverextension enable --py ballet_assemble
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
pip uninstall ballet_assemble
jupyter labextension uninstall ballet-assemble
```

### Release process

```
bumpversion <part>
make release
```
