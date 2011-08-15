import requests
import settings
import simplejson
import subprocess

auth = (settings.username, settings.password)
user = 'Miserlou'
repos = 'https://api.github.com/users/' + user + '/repos'
r = requests.get (repos, auth = auth) 

if (r.status_code == 200):
    resp = simplejson.loads (r.content) 
    for repo in resp:
        print "clonged"

def fork_repo(user, repo):
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/forks'
    r = requests.post (url, auth=auth)
    if (r.status_code == 201):
        resp = simplejson.loads(r.content)
        return resp.clone_url
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
    try:
        args =['/usr/bin/git', '--git-dir', repo + '.git', '--work-tree', repo, 'branch', 'clean']
        p = subprocess.Popen(args)
        p.wait()
        args =['/usr/bin/git', '--git-dir', repo + '.git', '--work-tree', repo,
                'checkout', 'clean']
        p = subprocess.Popen(args)
        p.wait()
        return True
    except Exception, e:
        return False

def fix_repo (repo):
    #TODO

def commit_repo(repo):
    try:
        message = "Remove whitespace and format code [Gun.io WhitespaceBot]" 
        args =['/usr/bin/git', '--git-dir', repo + '.git', '--work-tree', repo, 'commit', '-m', message] 
        p = subprocess.Popen(args) 
        p.wait()
        return True 
    except Exception, e:
        return False 

def push_commit(repo):
    try:
        args =['/usr/bin/git', '--git-dir', repo + '.git', '--work-tree',
                'repo', 'push', 'origin', 'clean'] 
        p = subprocess.Popen(args) 
        p.wait ()
        return True
    except Exception, e:
        return False

def submit_pull_request(user, repo):
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/pulls'
    params = {'title': 'Hi! We cleaned up your code for you!', 'body': 'Hi
            there!\n\nThis is WhitespaceBot from Gun.io. I\'m a robot that
            removes white space in your code! Blah blah blah.'}
    r = requests.post(url, auth = auth, params=params)
    if (r.status_code == 201):
        return True
    else:
	return None
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
