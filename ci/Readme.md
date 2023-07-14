# Steps

- git clone frappe_docker
- cd frappe_docker
- export APPS_JSON_BASE64=$(base64 -w 0 ./ci/apps.json)
- cp ./images/custom/Containerfile ./ci/Dockerfile
- aws / ecr docker login (https://ap-southeast-1.console.aws.amazon.com/ecr/repositories?region=ap-southeast-1)
- run ./build_push_image.sh {TAG} or CI --> set workflow (use github_ci aws iam user)

## AWS Links & Resources

### Users

- root
- selen_user
- github_ci / deployment group (AmazonEC2ContainerRegistryFullAccess)

## Github

### Secrets

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY

- setup Branch protection rule
- checkout new feature branch, merge request, delete branch
