var net = require('net');
var { get_conf } = require('./node_utils');

var conf = get_conf();
var server = ['localhost', conf.socketio_port || 9000];

var sock = new net.Socket();
sock.setTimeout(2500);
sock.on('connect', function() {
    console.info(server[0]+':'+server[1]+' is up.');
    sock.destroy();
    process.exit();
}).on('error', function(e) {
    console.error(server[0]+':'+server[1]+' is down: ' + e.message);
    process.exit(1);
}).on('timeout', function(e) {
    console.error(server[0]+':'+server[1]+' is down: timeout');
    process.exit(1);
}).connect(server[1], server[0]);
