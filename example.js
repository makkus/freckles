var hosts = ["dev.cutecode.co"]
tasks = []

for (i in hosts) {

    task = { "target": "root@"+hosts[i],
             "frecklet": "basic-hardening",
             "vars": {
                 "fail2ban": true,
                 "ufw": true,
                 "ufw_open_tcp": [80, 443] }}
    tasks.push(task)
}

task_desc = JSON.stringify(tasks)
const { spawn } = require('child_process');
const freckles_run = spawn("freckles", [task_desc]);

freckles_run.stdout.on("data", function(data) {
    console.log("stdout: " + data);
});

freckles_run.stderr.on("data", function(data) {
    console.log("stderr: " + data);
});

freckles_run.on("close", function(code) {
    console.log(`child process exited with code ${code}`);
});
