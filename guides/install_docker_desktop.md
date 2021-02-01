# Install

## Step

Download Docker Desktop [here](https://www.docker.com/products/docker-desktop).

Execute and Install it.

In Setting->General **Not** enable "Use the WSL 2 based engine"

## Minimal Resources

In Setting->Resources->Advanced

Give to your Docker at least this resources
* 2 CPUs
* 4Gb of RAM
* 1Gb of Swap memory
* Dick image size 64Gb

## Share your Docker Directory

**Remember to share your docker directory** or your docker installation will fail.
Operating System should and you to share folder automatically but sometimes no.

In Setting->Resources->File Sharing click on add button and past your docker root directory.

ex for me is:
 
```shell
C:\Users\Utente\frappe_docker
```
