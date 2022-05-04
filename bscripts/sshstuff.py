from bscripts.tricks import tech as t
import paramiko, time

def ssh_command(command, sleep=1):
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.load_system_host_keys()
    s.connect(
        t.config('nas_ssh', curious=True),
        '22',
        t.config('nas_login', curious=True),
        t.config('nas_pwd', curious=True)
    )
    s.exec_command(command)
    time.sleep(sleep)
    s.close()