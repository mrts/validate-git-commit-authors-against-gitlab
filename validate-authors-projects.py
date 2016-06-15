#!/usr/bin/env python
"""
Script that validates Git commit authors against Gitlab project members.
Copy it to custom_hooks/pre-receive and make executable in a GitLab
server-side Git repository.
When using with SubGit, do the following:
1. Copy the script to custom_hooks/validate-authors-projects.py
2. chmod 755 custom_hooks/validate-authors-projects.py
3. Test by running `./itte.git/custom_hooks/validate-authors-projects.py`
4. Enable it in existing pre-receive hook, which already contains SubGit
script, by adding the following lines to top (before SubGit code):
    set -e
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    $SCRIPT_DIR/validate-authors-projects.py
    set +e

This script can be downloaded from: https://github.com/lauer/validate-git-commit-authors-against-gitlab
"""

from __future__ import print_function
from __future__ import unicode_literals

import sys
import os
import subprocess
import urllib2
import urllib
import json
import contextlib
import codecs
import ssl
from itertools import islice, izip

GITLAB_SERVER = 'http://localhost'
GITLAB_TOKEN = 'SECRET'
# find the ID with curl -X GET -H "PRIVATE-TOKEN: <token>" "http://gitlab.tld/api/v3/projects/search/<projectname>
GITLAB_PROJECT = '24'
EMAIL_DOMAIN = 'example.com'
SKIP_CERT_VALIDATION = True

def main():
    commits = get_commits_from_push()
    authors = get_gitlab_project_members()
    authors.update(get_gitlab_group_members())
    for commit, author, email in commits:
        if author not in authors:
            die('Unknown author', author, commit, authors)
        if email != authors[author]:
            die('Unknown email', email, commit, authors)

def get_commits_from_push():
    old, new, branch = sys.stdin.read().split()
    rev_format = '--pretty=format:%an%n%ae'
    command = ['git', 'rev-list', rev_format, '{0}..{1}'.format(old, new)]
    # branch delete, let it through
    if new == '0000000000000000000000000000000000000000':
        sys.exit(0)
    # new branch
    if old == '0000000000000000000000000000000000000000':
        command = ['git', 'rev-list', rev_format, new, '--not', '--branches=*']
    output = subprocess.check_output(command)
    commits = [line.strip() for line in unicode(output, 'utf-8').split('\n') if line.strip()]
    return izip(islice(commits, 0, None, 3),
            islice(commits, 1, None, 3),
            islice(commits, 2, None, 3))

def get_gitlab_project_members():
    url = '{0}/api/v3/projects/{1}/members'.format(GITLAB_SERVER, GITLAB_PROJECT)
    members = request_api(url)
    return dict((member['name'], '{}@{}'.format(member['username'], EMAIL_DOMAIN))
        for member in members)

def get_gitlab_group_members():
    # first fetch the group id of the project
    url_project = '{0}/api/v3/projects/{1}'.format(GITLAB_SERVER, GITLAB_PROJECT)
    group_id = request_api(url_project)['namespace']['id']
    # use that to get the members
    url_group = '{0}/api/v3/groups/{1}/members'.format(GITLAB_SERVER, group_id)
    members = request_api(url_group)
    return dict((member['name'], '{}@{}'.format(member['username'], EMAIL_DOMAIN))
        for member in members)

def request_api(url):
    headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}
    request = urllib2.Request(url, None, headers)
    with contextlib.closing(urllib2.urlopen(request)) as response:
        result = json.load(response)
    return result

def die(reason, invalid_value, commit, authors):
    message = []
    message.append('*' * 80)
    message.append("ERROR: {0} '{1}' in {2}"
            .format(reason, invalid_value, commit))
    message.append('-' * 80)
    message.append('Allowed authors and emails:')
    print('\n'.join(message), file=sys.stderr)
    for name, email in authors.items():
        print(u"  '{0} <{1}>'".format(name, email), file=sys.stderr)
    sys.exit(1)

def set_locale(stream):
    return codecs.getwriter('utf-8')(stream)

if __name__ == '__main__':
    # Avoid Unicode errors in output
    sys.stdout = set_locale(sys.stdout)
    sys.stderr = set_locale(sys.stderr)
    # Skip certificate validation
    if SKIP_CERT_VALIDATION and hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
    main()
