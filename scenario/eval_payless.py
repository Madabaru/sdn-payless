import sys
import time
import yaml
import subprocess

tasks = None
procs = {}
if len(sys.argv) == 2:
    scene_file = sys.argv[1]
    try:
        with open(scene_file, "r") as file:
            parsed = yaml.safe_load(file.read())
            tasks = parsed.get("root")
    except Exception as e:
        print str(e)
        sys.exit(1)
else:
    print "usage: sudo python %s SCENEFILE" % sys.argv[0]
    sys.exit(1)

reft = time.time()
# extract each task from parsed yaml file
# and execute every task in a separate process
# delay is important here to make sure all the tasks start at the same time
for task_name in tasks:
    t = tasks.get(task_name)
    task = dict(
        name      = task_name,
        host      = t['host'],
        interface = t['interface'],
        start     = t['start'],
        stop      = t['stop'],
        step      = t['step'],
        number    = t['number'],
        packet    = t['packet'],
        delay     = 3,
        reft      = reft
    )
    cmd = ("m %(host)s sudo python send_raw.py"
           " --name %(name)s --interface %(interface)s"
           " --start %(start)f --stop %(stop)f --step %(step)f"
           " --number %(number)d --packet %(packet)s"
           " --delay %(delay)f --reftime %(reft)f") % task
    print cmd
    p = subprocess.Popen([cmd], shell=True)
    procs[task_name] = p

for name, p in procs.items():
    pid = p.pid
    ret = p.wait()
    print "[{}] {} exited with {}".format(pid, name, ret)

