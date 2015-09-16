from fabric.api import cd, run, sudo


def deploy():
    with cd('who-broke-build-slack'):
        run('git reset --hard HEAD')
        run('git pull origin master')
        run('cp ../settings.py .')
        sudo('service who-broke-build-slack restart')
