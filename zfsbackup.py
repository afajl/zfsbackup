#!/bin/python2.6

backup_prop = 'afajl:backup'
backup_prefix = 'backup'
bpool = 'backup'
 
import sy
import datetime
import os.path

log_file = os.path.abspath(os.path.dirname(__file__)) + '/log'
today = datetime.datetime.now().strftime('%Y%m%d')

def import_backup_pool(bpool):
    # check if imported
    try:
        sy.cmd.do('zpool list {}', bpool)
    except sy.CommandError:
        sy.cmd.do('zpool import {}', bpool)

    # check health
    health, _ = sy.cmd.do('zpool list -H -o health {}', bpool)
    if health.strip() != 'ONLINE':
        raise RuntimeError('Health of %s is not ONLINE' % bpool)

def export_backup_pool(bpool):
    sy.cmd.do('zpool export {}', bpool)


def fs_to_backup():
    for fsline in sy.cmd.outlines('zfs list -H -o {},name -t fs', backup_prop):
        on, name = fsline.split()
        if on == 'on':
            yield name

def snapshot(fs):
    snap = '%s@%s-%s' % (fs, backup_prefix, today)
    status, _, _ = sy.cmd.run('zfs list ' + snap)
    if status != 0:
        sy.cmd.do('zfs snapshot ' + snap)
    return snap

def escape_fs(fs):
    return fs.replace('/', '_')

def send(fs, snap, bpool):
    fsescaped = escape_fs(fs)
    target = bpool + '/%s-%s-%s' % (fsescaped, backup_prefix, today)

    sy.cmd.do('zfs send {} | zfs recv -o readonly=on -u {}', 
              snap, target, timeout=43200)

def destroy_snapshot(snap):
    sy.cmd.do('zfs destroy {}', snap)

def backup_fs(fs):
    snap = snapshot(fs)
    try:
        send(fs, snap, bpool)
    finally:
        destroy_snapshot(snap)

def set_backup_time(fs):
    sy.cmd.do('zfs set afajl:backed_up={} {}', today, fs)

def get_backup_time(fs):
    out, _ = sy.cmd.do('zfs get -H -o value afajl:backed_up {}', fs)
    return datetime.datetime.strptime(out.strip(), '%Y%m%d')
 
def main():
    import_backup_pool(bpool)
    for fs in fs_to_backup():
        sy.log.info('Backing up ' + fs)
        try:
            backup_fs(fs)
            set_backup_time(fs)
        except Exception, e:
            sy.log.exception('Could not backup ' + fs)
    export_backup_pool(bpool)

    print 'You should maybe run a zfs scrub on', bpool

    
if __name__ == '__main__':
    sy.log.to_screen()
    sy.log.to_file(log_file)

    main()
