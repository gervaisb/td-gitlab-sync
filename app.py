#!/usr/bin/python
# -*- coding: UTF-8 -*-

import configparser
import subprocess
import gitlab
import re
import os


class LocalTodo:
    _details = None
    def __init__(self, id, name, completed):
        self.completed = completed
        self.name = name
        self.id = id

    def __repr__(self):
        return "LocalTodo(#{}, {}, completed:{})".format(self.id, self.name, self.completed)

    def _get_details(self):
        if not self._details:
            self._load_details()
        return self._details

    def _load_details(self):
        # td print the group and one empty line before the details.
        # after the details, it print one empty line and the task
        output = subprocess.check_output(['td', self.id])   
        lines = output.splitlines()                         
        self._details = ''
        for index, line in enumerate(lines, start=1):
            if index>2 and index<(len(lines)-1):
                self._details = self._details + str(line)

    def refer_to(self, gitlab_todo):
        # a local task refer to a remote when the remote url is the last line
        # of the details
        details = self._get_details()
        last_line = details.splitlines()[-1]
        reference = 'Ref: '+gitlab_todo.url
        return reference in last_line

    def sync_with(self, gitlab_todo):
        copy = LocalTodo(self.id, gitlab_todo.title, gitlab_todo.completed)
        copy._details = '{}\n\nRef: {}'.format(gitlab_todo.description, gitlab_todo.url)
        return copy


class LocalTodoRepository:
    def __init__(self, group):
        self.group = group
        if not self.group_exists():
            self.create_group(group)

    def group_exists(self):
        pattern = re.compile('.*'+self.group+'.*')
        output = subprocess.check_output(['td', 'list-groups'])
        for line in output.splitlines():
            if pattern.match(str(line)):
                return True
        return False

    def create_group(self):
        output = subprocess.check_output(['td', 'add-group', self.group])

    def list_todos(self):
        pattern = re.compile('(?P<state>x|✓)\s.\[\dm(?P<id>\d+).*:\s(?P<name>.+)')
        output = subprocess.check_output(['td', 'list', '--group', self.group])
        tasks = []
        for line in output.splitlines():
            match = pattern.search(str(line, encoding='UTF8'))
            if match:
                completed = match.group('state')=='✓'
                task = LocalTodo(match.group('id'), match.group('name'), completed)
                tasks.append(task)
        return tasks

    def find_referer(self, gitlab_todo):
        print('Find Referer in {} local todos'.format(len(self.list_todos())))
        for local in self.list_todos():
            if local.refer_to(gitlab_todo):
                return local
        return None

    def save(self, todo):
        subprocess.check_output(['td', todo.id, 'edit', '--name', todo.name, '--details', todo._details])
        if todo.completed:
            subprocess.check_output(['td', todo.id, 'complete'])

    def create(self, gitlab_todo):
        details = '{}\n\nRef: {}'.format(gitlab_todo.description, gitlab_todo.url)
        subprocess.check_output(['td', 'add', gitlab_todo.title, '--uncomplete', '--group', self.group, '--details', details])            

class GitlabTodo:
    def __init__(self, url, title, description, completed, remote):
        self.description = description
        self.completed = completed
        self.remote = remote
        self.title = title
        self.url = url

    def __repr__(self):
        return "GitlabTodo({}, {}, completed:{})".format(self.url, self.title, self.completed) 

    def set_completed(self, completed):
        if completed and not self.completed:
            self.remote.mark_as_done()


class GitlabTodoRepository:
    def __init__(self, host, token):
        self.gl = gitlab.Gitlab(host, private_token=token)

    def list_remote_todos(self):
        remotes = self.gl.todos.list()
        todos = []
        for remote in remotes:
            completed = remote.state=='done'
            todo = GitlabTodo(remote.target['web_url'], remote.target['title'], remote.target['description'], completed, remote)
            todos.append(todo)
        return todos


# ~ ---------------------------------------------------------------------- ~ //

# Expecting a Toml config file with the following content:
# > [local]
# > group = any_group_name # Usually Gitlab host name
# >
# > [gitlab]
# > url = gitlab_url
# > token = gitalb_personal_access_token # (Gitalb > Settings > Access Tokens; with API scope)
config = configparser.ConfigParser()
config.read(os.getenv('HOME')+'/.config/td-gitlab-sync.toml')

td = LocalTodoRepository(config['local']['group'])
gitlab = GitlabTodoRepository(config['gitlab']['url'], config['gitlab']['token'])

for remote in gitlab.list_remote_todos():
    referer = td.find_referer(remote)
    if referer:
        print('Remote: {}\n\t Synching to: {}\n\t Completing: {}', remote, referer, referer.completed)
        td.save(referer.sync_with(remote))
        remote.set_completed(referer.completed)
    else:
        print('Creating local task refering to {}'.format(remote))
        td.create(remote)