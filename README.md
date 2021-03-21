
# Td - Gitlab sync

> A simple script synchronize `td` with _Gitlab_ todo's. 

A `td` todo is created for all _Gitlab_ todo and each task completed in `td` 
is marked as done in _Gitlab_.

## Usage

### Configuration

This script read his cconfiguration from `/home/$USER/.config/td-gitlab-sync.toml`.
Create this file and add the following content:

    # local refer to your 'td' installation
    # "group" is any group that you want to use to create synched tasks
    [local]
    group = your_group

    # your gitlab instance configuration
    # "url" is an absolute url to your gitlab instance
    # "token" is a Gitlab access token with the "api" scope
    [gitlab]
    url = your_gitlab_url
    token = gitlab_access_token

### Execution

`pipenv` is required to setup and run the project. Once available, start the 
script with:

    $ pipenv run python app.py