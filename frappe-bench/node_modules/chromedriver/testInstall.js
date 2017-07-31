#!/usr/bin/env node

"use strict";

const os = require('os');
const path = require('path');
const fs = require('fs');
const spawnSync = require('child_process').spawnSync;

const versions = ['0.12', '4', '6'];
const tmpdir = os.tmpdir();

function directoryExists(file) {
    try {
        var stat = fs.lstatSync(file);
        return stat.isDirectory();
    } catch (err) {
        return false;
    }
}

function fileExists(file) {
    try {
        var stat = fs.lstatSync(file);
        return stat.isFile();
    } catch (err) {
        return false;
    }
}

function removeFolder(dir) {
    if (!fs.existsSync(dir)) return;
    fs.readdirSync(dir).forEach((file) => {
        let curPath = dir + path.sep + file;
        if (fs.lstatSync(curPath).isDirectory())
            removeFolder(curPath);
        else
            fs.unlinkSync(curPath);
    });
    fs.rmdirSync(dir);
}

let tempInstallPath = path.resolve(tmpdir, 'chromedriver-test');
if (directoryExists(tempInstallPath)) {
    console.log(`Deleting directory '${tempInstallPath}'.`);
    removeFolder(tempInstallPath);
}
fs.mkdirSync(tempInstallPath);

function checkSpawn(spawnInfo) {
    if (spawnInfo.stdout) {
        if (typeof (spawnInfo.stdout) !== 'string')
            console.log(spawnInfo.stdout.toString('utf8'));
        else
            console.log(spawnInfo.stdout);
    }
    if (spawnInfo.stderr) {
        if (typeof (spawnInfo.error) !== 'string')
            console.error(spawnInfo.stderr.toString('utf8'));
        else
            console.error(spawnInfo.stderr);
    }
    if (spawnInfo.status !== 0 || spawnInfo.error) {
        console.error('Failed when spawning.');
        process.exit(1);
    }
    if (typeof (spawnInfo.stdout) !== 'string')
        return spawnInfo.stdout.toString('utf8');
    else
        return spawnInfo.stdout;
}

function nvmUse(version) {
    if (os.platform() === 'win32')
        var versionsText = checkSpawn(spawnSync('nvm', ['list']));
    else
        var versionsText = checkSpawn(spawnSync('/bin/bash', ['-c', 'source $HOME/.nvm/nvm.sh && nvm list']));
    const versionsAvailable = versionsText.split('\n').map(v => v.match(/\d+\.\d+\.\d+/)).filter(v => v).map(v => v[0]);
    var largestMatch = versionsAvailable.filter(v => v.match(`^${version}\.`)).map(v => v.match(/\d+\.(\d+)\.\d+/)).reduce(((max, v) => max[1] > v[1] ? max : v), [null, 0]);
    if (largestMatch.length === 0) {
        console.error(`Version '${version}' not found.`);
        process.exit(3);
    }
    var largestMatchingVersion = largestMatch.input;
    console.log(`Found version '${largestMatchingVersion}'.`);
    if (os.platform() === 'win32')
        checkSpawn(spawnSync('nvm', ['use', largestMatchingVersion]));
    else
        checkSpawn(spawnSync('/bin/bash', ['-c', `source $HOME/.nvm/nvm.sh && nvm use ${largestMatchingVersion}`]));
}

function sleep(milliseconds) {
    const inAFewMilliseconds = new Date(new Date().getTime() + 2000);
    while (inAFewMilliseconds > new Date()) { }
}

for (let version of versions) {
    console.log(`Testing version ${version}...`);
    let tempInstallPathForVersion = path.resolve(tmpdir, 'chromedriver-test', version);
    fs.mkdirSync(tempInstallPathForVersion);
    nvmUse(version);
    if (os.platform() === 'win32') {
        sleep(2000); // wait 2 seconds until everything is in place
        checkSpawn(spawnSync('cmd.exe', ['/c', `npm i ${__dirname}`], { cwd: tempInstallPathForVersion }));

    } else {
        checkSpawn(spawnSync('npm', ['i', `${__dirname}`], { cwd: tempInstallPathForVersion }));
    }
    let executable = path.resolve(tempInstallPathForVersion, 'node_modules', 'chromedriver', 'lib', 'chromedriver', `chromedriver${os.platform() === 'win32' ? '.exe' : ''}`);
    if (fileExists(executable)) {
        console.log(`Version ${version} installed fine.`);
    }
    else {
        console.error(`Version ${version} did not install correctly, file '${executable}' was not found.`);
        process.exit(2);
    }
}

try {
    removeFolder(tempInstallPath);
} catch (err) {
    console.error(`Could not delete folder '${tempInstallPath}'.`);
}