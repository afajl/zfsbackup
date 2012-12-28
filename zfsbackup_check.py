import sy

warn_time = 90

import zfsbackup
import datetime


def main():
    today = datetime.datetime.today()
    for fs in zfsbackup.fs_to_backup():
        try:
            backed_up = zfsbackup.get_backup_time(fs)
        except CommandError:
            sy.log.warn('Filesystem %s has never been backed up', fs)
            continue

        delta = today - backed_up
        if delta.days >= warn_time:
            sy.net.sendmail(
                to=['p@afajl.com'],
                subject='%s needs to be backed up' % fs,
                message='%d days since last backup, run zfsbackup' % delta.days)


if __name__ == '__main__':
    sy.log.to_file(zfsbackup.log_file)
    try:
        main()
    except:
        sy.log.exception('Problem checking zfsbackup time')
