# Contribution Guidelines
## Branches

* *master*:  images on the master branch are built monthly.
* *develop*: images on this branch are built daily.

# Pull Requests

Please **send all pull request exclusively to the *develop*** branch. 
When the PR are merged, the merge will trigger the image build automatically.

Please test all PR as extensively as you can, considering that the software can be run in different modes:
* with docker-compose for production
* with or without Nginx proxy
* with VScode for testing environments

Every once in a while (or before monthly release) develop will be merged into master.

## Reducing the number of branching and builds :evergreen_tree: :evergreen_tree: :evergreen_tree: 
Please be considerate when pushing commits and opening PR for multiple branches, as the process of building images (triggered on push and PR branch push) uses energy and contributes to global warming.

# Documentation

You should place README.md(s) in the relevant directories, explaining what the software in that particular directory does.

