import requests
import settings
import simplejson
import subprocess
import sys
import argparse
import time
from random import choice
import os
from os.path import join
import shutil
import urllib2
import json

#pseudo
#    take name from list
#    scan names for most names most popular repo
#    fork it - POST /repos/:user/:repo/forks
#    clone it
#    switch branch
#    fix it
#    commit it!
#    push it
#    submit pull req
#    remove name from list


def main():
    parser = argparse.ArgumentParser(description='Whitespace annihilating GitHub robot.\nBy Rich Jones - Gun.io - rich@gun.io')
    parser.add_argument('-u', '--users', help='A text file with usernames.', default='users.txt')
    parser.add_argument('-o', '--old-users', help='A text file with usernames.', default='old_users.txt')
    parser.add_argument('-c', '--count', help='The maximum number of total requests to make.', default=999999)
    parser.add_argument('-v', '--verbose', help='Make this sucker loud? (True/False)', default=True)
    args = parser.parse_args()

    auth = (settings.username, settings.password)

    old_users_file = args.old_users
    old_users = load_user_list(old_users_file)

    users = args.users
    new_users = load_user_list(users)
    user = get_user(users)

    #XXX: Potential deal breaker in here!
    count = 0
    while user in old_users:
        print "We've already done that user!"
        user = get_user(users)
    count = count + 1
    if count > len(new_users):
        return

    repos = 'https://api.github.com/users/' + user + '/repos'
    r = requests.get(repos, auth=auth)

    if (r.status_code == 200):
        resp = simplejson.loads(r.content)
        topwatch = 0
        top_repo = ''
        for repo in resp:
            if repo['watchers'] > topwatch:
                top_repo = repo['name']
                topwatch = repo['watchers']
        print dir(repo)

        print user + "'s most watched repo is " + top_repo + " with " + str(topwatch) + " watchers. Forking."

        repo = top_repo
        print "GitHub Forking.."
        clone_url = fork_repo(user, repo)
        print "Waiting.."
        time.sleep(30)
        print "Cloning.."
        cloned = clone_repo(clone_url)
        if not cloned:
            return
        print "Changing branch.."
        branched = change_branch(repo)
        print "Fixing repo.."
        fixed = fix_repo(repo)
        print "Comitting.."
        commited = commit_repo(repo)
        print "Pushing.."
        pushed = push_commit(repo)
        print "Submitting pull request.."
        submitted = submit_pull_request(user, repo)
        print "Delting local repo.."
        deleted = delete_local_repo(repo)
        print "Olding user.."
        old = save_user(old_users_file, user)


def save_user(old_users_file, user):
    with open(old_users_file, "a") as id_file:
        id_file.write(user + '\n')
    return True


def load_user_list(old_users):
    text_file = open(old_users, "r")
    old = text_file.readlines()
    text_file.close()
    x = 0
    for hid in old:
        old[x] = hid.rstrip()
        x = x + 1
    return old


def get_user(users):
    text_file = open(users, "r")
    u = text_file.readlines()
    text_file.close()
    return choice(u).rstrip()


def fork_repo(user, repo):
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/forks'
    auth = (settings.username, settings.password)
    r = requests.post(url, auth=auth)
    if (r.status_code == 201):
        resp = simplejson.loads(r.content)
        return resp['ssh_url']
    else:
        return None


def clone_repo(clone_url):
    try:
        args = ['/usr/bin/git', 'clone', clone_url]
        p = subprocess.Popen(args)
        p.wait()
        return True
    except Exception, e:
        return False


def change_branch(repo):
    #XXX fuck this
    gitdir = os.path.join(settings.pwd, repo, ".git")
    repo = os.path.join(settings.pwd, repo)

    try:
        args = ['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'branch', 'clean']
        p = subprocess.Popen(args)
        p.wait()
        args = ['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'checkout', 'clean']
        p = subprocess.Popen(args)
        p.wait()
        return True
    except Exception, e:
        return False


def fix_repo(repo):
    gitdir = os.path.join(settings.pwd, repo, ".git")
    repo = os.path.join(settings.pwd, repo)
    for root, dirs, files in os.walk(repo):
        for f in files:
            path = os.path.join(root, f)

            # gotta be a way more pythonic way of doing this
            banned = ['.git', '.py', '.yaml', '.patch', '.hs', '.occ', '.md']
            cont = False
            for b in banned:
                if b in path:
                    cont = True
            if cont:
                continue

            p = subprocess.Popen(['file', '-bi', path], stdout=subprocess.PIPE)

            while True:
                o = p.stdout.readline()
                if o == '':
                    break
                #XXX: Motherfucking OSX is a super shitty and not real operating system
                #XXX: and doesn't do file -bi properly
                if 'text' in o:
                    q = subprocess.Popen(['sed', '-i', 's/[ \\t]*$//', path])
                    q.wait()
                    args = ['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'add', path]
                    pee = subprocess.Popen(args)
                    pee.wait()
                if o == '' and p.poll() != None: break

    git_ignore = os.path.join(repo, '.gitignore')
    if not os.path.exists(git_ignore):
        ignorefile = open(git_ignore, 'w')
        ignore = '# Compiled source #\n' + \
            '###################\n' + \
            '*.com\n' + \
            '*.class\n' + \
            '*.dll\n' + \
            '*.exe\n' + \
            '*.o\n' + \
            '*.so\n' + \
            '*.pyc\n\n' + \
            '# Logs and databases #\n' + \
            '######################\n' + \
            '*.log\n\n' + \
            '# OS generated files #\n' + \
            '######################\n' + \
            '.DS_Store*\n' + \
            'ehthumbs.db\n' + \
            'Icon?\n' + \
            'Thumbs.db\n'
        ignorefile.write(ignore)
        ignorefile.close()
        try:
            args = ['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'add', git_ignore]
            p = subprocess.Popen(args)
            p.wait()
            return True
        except Exception, e:
            return False

    return True


def commit_repo(repo):
    gitdir = os.path.join(settings.pwd, repo, ".git")
    repo = os.path.join(settings.pwd, repo)

    try:
        message = "Remove whitespace [Gun.io WhitespaceBot]"
        args = ['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'commit', '-m', message]
        p = subprocess.Popen(args)
        p.wait()
        return True
    except Exception, e:
        print e
        return False


def push_commit(repo):
    gitdir = os.path.join(settings.pwd, repo, ".git")
    repo = os.path.join(settings.pwd, repo)
    try:
        args = ['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'push', 'origin', 'clean']
        p = subprocess.Popen(args)
        p.wait()
        return True
    except Exception, e:
        print e
    return False


def basic_authorization(user, password):
    s = user + ":" + password
    return "Basic " + s.encode("base64").rstrip()


def submit_pull_request(user, repo):
    auth = (settings.username, settings.password)
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/pulls'
    params = {'title': 'Hi! I cleaned up your code for you!', 'body': 'Hi'
            + ' there!\n\nThis is WhitespaceBot. I\'m an [open-source](https://github.com/Gunio/LightWrite) robot that'
            + ' removes trailing white space in your code, and gives you a gitignore file if you didn\'t have one! ' +
            ' \n\nWhy whitespace? Whitespace is an eyesore for developers who use text editors with dark themes. It\'s not ' +
            ' a huge deal, but it\'s a bit annoying if you use Vim in a terminal. Really, I\'m just a proof of ' +
            ' concept - GitHub\'s V3 API allows robots to automatically improve open source projects, and that\'s really' +
            ' cool. Hopefully, somebody, maybe you!, will fork me and make me even more useful. My owner is ' +
            '[funding a bounty](http://gun.io/open/12/add-security-flaw-fixing-features-to-whitespacebot) to anybody ' +
            'who can add security fixing features to me. ' +
            '\n\nI\'ve only cleaned your most popular project, and I\'ve added you to a list of users not to contact ' +
            'again, so you won\'t get any more pull requests from me unless you ask. If I\'m misbehaving, please email my ' +
            'owner and tell him to turn me off! If this is pull request is of no use to you, please just ignore it.\n\n' +
            'Thanks!\nWhiteSpacebot from [Gun.io](http://gun.io).',
            'base': 'master', 'head': 'GunioRobot:clean'}

    req = urllib2.Request(url,
                          headers={
                              "Authorization": basic_authorization(settings.username, settings.password),
                              "Content-Type": "application/json",
                              "Accept": "*/*",
                              "User-Agent": "WhitespaceRobot/Gunio",
                          },
                          data=json.dumps(params))
    f = urllib2.urlopen(req)
    return True


def delete_local_repo(repo):
    repo = os.path.join(settings.pwd, repo)
    try:
        shutil.rmtree(repo)
        return True
    except Exception, e:
        return False


if __name__ == '__main__':
        sys.exit(main())
