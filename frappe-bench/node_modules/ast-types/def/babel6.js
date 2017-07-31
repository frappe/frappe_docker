module.exports = function (fork) {
  fork.use(require("./babel6-core"));
  fork.use(require("./flow"));
};
