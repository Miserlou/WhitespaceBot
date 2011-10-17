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
    user = get_user(users)

    #XXX: Potential deal breaker in here!
    while user in old_users:
        print "We've already done that user!"
        user = get_user(users)

    repos = 'https://api.github.com/users/' + user + '/repos'
    r = requests.get (repos, auth = auth) 

    if (r.status_code == 200):
        resp = simplejson.loads (r.content) 
        topwatch = 0
        top_repo = None
        top_repo = None
        for repo in resp:
            if repo['watchers'] > topwatch:
                top_repo = repo['name']
                topwatch = repo['watchers']

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

def load_user_list(old_users):
    text_file = open(old_users, "r")
    old = text_file.readlines()
    text_file.close()
    x=0
    for hid in old:
        old[x] = hid.rstrip()
        x=x+1
    return old

def get_user(users):
    text_file = open(users, "r")
    u = text_file.readlines()
    text_file.close()
    return choice(u).rstrip() 

def fork_repo(user, repo):
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/forks'
    auth = (settings.username, settings.password)
    r = requests.post (url, auth=auth)
    if (r.status_code == 201):
        resp = simplejson.loads(r.content)
        return resp['clone_url']
    else:
        return None

def clone_repo(clone_url):
    try:
        args =['/usr/bin/git', 'clone', clone_url] 
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
        args =['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'branch', 'clean']
        p = subprocess.Popen(args)
        p.wait()
        args =['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'checkout', 'clean']
        p = subprocess.Popen(args)
        p.wait()
        return True
    except Exception, e:
        return False

def fix_repo (repo):

    gitdir = os.path.join(settings.pwd, repo, ".git")
    repo = os.path.join(settings.pwd, repo)
    for root, dirs, files in os.walk(repo):
       for f in files:
        path = os.path.join(root, f)
        p = subprocess.Popen(['file','-bi',path],stdout=subprocess.PIPE)

        while True:
            o = p.stdout.readline()
            if o == '':
                break
            #XXX: Motherfucking OSX is a super shitty and not real operating system
            #XXX: and doesn't do file -bi properly
            if 'text' in o:
                q = subprocess.Popen(['sed','-i','s/[ \\t]*$//', path])
                q.wait()
                args =['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'add', path]
                p = subprocess.Popen(args) 
                p.wait()
                print "True"
            else:
                print "False"
            if o == '' and p.poll() != None: break

    git_ignore = os.path.join(repo, '.gitignore') 
    if not os.path.exists(git_ignore):
        ignorefile = open(git_ignore, 'w')
        ignore = '# Compiled source #\n' + \
            '###################\n' + \
            '*.com\n' + \
            '*.class\n'+ \
            '*.dll\n'+\
            '*.exe\n'+\
            '*.o\n'+\
            '*.so\n'+\
            '*.pyc\n\n'+\
            '# Logs and databases #\n'+\
            '######################\n'+\
            '*.log\n\n'+\
            '# OS generated files #\n'+\
            '######################\n'+\
            '.DS_Store*\n'+\
            'ehthumbs.db\n'+\
            'Icon?\n'+\
            'Thumbs.db\n'+\
            'ignorefile.close()'
        ignorefile.write(ignore)
        ignorefile.close()
        try:
            args =['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'add', git_ignore] 
            p = subprocess.Popen(args) 
            p.wait ()
            return True
        except Exception, e:
            return False

    return True
    #TODO
    # sed '/^$/d' Remove blank lines
    # sed 's/[ \t]*$//' Remove trailing whitespace

def commit_repo(repo):
    gitdir = os.path.join(settings.pwd, repo, ".git")
    repo = os.path.join(settings.pwd, repo)

    try:
        message = "Remove whitespace [Gun.io WhitespaceBot]" 
        args =['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'commit', '-m', message] 
        p = subprocess.Popen(args) 
        p.wait()
        return True 
    except Exception, e:
        return False 

def push_commit(repo):
    gitdir = os.path.join(settings.pwd, repo, ".git")
    repo = os.path.join(settings.pwd, repo)
    try:
        args =['/usr/bin/git', '--git-dir', gitdir, '--work-tree', repo, 'push', 'origin', 'clean'] 
        p = subprocess.Popen(args) 
        p.wait ()
        return True
    except Exception, e:
        return False

def submit_pull_request(user, repo):
    auth = (settings.username, settings.password)
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/pulls'
    params = {'title': 'Hi! We cleaned up your code for you!', 'body': 'Hi'
            + 'there!\n\nThis is WhitespaceBot from Gun.io. I\'m a robot that'
            + 'removes white space in your code! [Gun.io](http://gun.io).'}
    r = requests.post(url, auth = auth, params=params)
    if (r.status_code == 201):
        return True
    else:
	return None

if __name__ == '__main__':
        sys.exit(main())
