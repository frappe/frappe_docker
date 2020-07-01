#!/bin/bash

function nodeCleanUp() {
    rm -fr node_modules
    yarn install --production=true
}

cd /home/frappe/frappe-bench/apps/frappe
yarn
yarn run production
yarn add nunjucks -D

if [[ "$GIT_BRANCH" =~ ^(version-12|version-11)$ ]]; then
    nodeCleanUp
else
    node generate_standard_style_css.js \
            frappe/website/doctype/website_theme/website_theme_template.scss > \
            /home/frappe/standard_templates_string
    node generate_bootstrap_theme.js \
            /home/frappe/frappe-bench/sites/assets/css/standard_style.css \
            "$(cat /home/frappe/standard_templates_string)"
    nodeCleanUp
fi
