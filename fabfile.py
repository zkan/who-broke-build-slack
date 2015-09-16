from fabric.api import cd, run


def deploy():
    with cd('who-broke-build-slack'):
        run('git reset --hard HEAD')
        run('git pull origin master')
        run('cp ../settings.py .')
        try:
            run("kill $(ps -ef | grep [w]ho_broke_build | awk '{print $2}')")
        except:
            pass
        run('bash run.sh')
