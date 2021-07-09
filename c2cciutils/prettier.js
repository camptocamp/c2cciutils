const prettier = require('prettier');

exports.getFileInfo = (file) => {
  return new Promise((resolve) => {
    prettier.resolveConfig(file, { editorconfig: true }).then((config) => {
      prettier.getFileInfo(file, { ignorePath: '.prettierignore' }).then((result) => {
        resolve({
          config: config,
          info: result,
        });
      });
    });
  });
};

exports.format = (code, config) => {
  return prettier.format(code, config);
};

exports.check = (code, config) => {
  return prettier.check(code, config);
};

exports.info = () => prettier.getSupportInfo();
