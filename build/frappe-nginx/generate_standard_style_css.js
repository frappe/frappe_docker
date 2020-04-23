const nunjucks = require("nunjucks");

const templatePath = process.argv[2];
const pathArray = templatePath.split("/");
const templateFile = pathArray.pop();
const templateDir = pathArray.join("/");

nunjucks.configure(templateDir);
const rendered = nunjucks.render(templateFile, {
    button_rounded_corners: true,
    font_properties: "300,600",
});

console.log(rendered.replace(/\n/gm, "\\n"));
