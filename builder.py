#!/usr/bin/env python3

import argparse
import subprocess
import os


def parse_args():
    parser = argparse.ArgumentParser(
        description="frappe_docker common CI elements", add_help=True
    )

    parser.add_argument(
        "service",
        action="store",
        type=str,
        help='Name of the service to build: "erpnext" or "frappe"',
    )
    parser.add_argument(
        "-o",
        "--tag-only",
        required=False,
        action="store_true",
        dest="tag_only",
        help="Only tag an image and push it.",
    )
    parser.add_argument(
        "-b",
        "--is-beta",
        required=False,
        default=False,
        action="store_true",
        dest="is_beta",
        help="Specify if tag is beta",
    )

    image_type = parser.add_mutually_exclusive_group(required=True)
    image_type.add_argument(
        "-a",
        "--nginx",
        action="store_const",
        dest="image_type",
        const="nginx",
        help="Build the nginx + static assets image",
    )
    image_type.add_argument(
        "-s",
        "--socketio",
        action="store_const",
        dest="image_type",
        const="socketio",
        help="Build the frappe-socketio image",
    )
    image_type.add_argument(
        "-w",
        "--worker",
        action="store_const",
        dest="image_type",
        const="worker",
        help="Build the python environment image",
    )

    tag_type = parser.add_mutually_exclusive_group(required=True)
    tag_type.add_argument(
        "-g",
        "--git-version",
        action="store",
        type=str,
        dest="version",
        help='The version number of service (i.e. "11", "12", etc.)',
    )
    tag_type.add_argument(
        "-t",
        "--tag",
        action="store",
        type=str,
        dest="tag",
        help="The image tag (i.e. erpnext-worker:$TAG )",
    )

    args = parser.parse_args()
    return args


def git_version(service, version, branch, is_beta=False):
    print(f"Pulling {service} v{version}")
    subprocess.run(
        f"git clone https://github.com/frappe/{service} --branch {branch}", shell=True
    )
    cd = os.getcwd()
    os.chdir(os.getcwd() + f"/{service}")
    subprocess.run("git fetch --tags", shell=True)

    # XX-beta becomes XX for tags search
    version = version.split("-")[0]

    version_tag = (
        subprocess.check_output(
            f"git tag --list --sort=-version:refname \"v{version}*\" | sed -n 1p | sed -e 's#.*@\(\)#\\1#'",
            shell=True,
        )
        .strip()
        .decode("ascii")
    )

    if not is_beta:
        version_tag = version_tag.split("-")[0]

    os.chdir(cd)
    return version_tag


def build(service, tag, image, branch):
    build_args = f"--build-arg GIT_BRANCH={branch}"
    if service == "erpnext":
        build_args += f" --build-arg IMAGE_TAG={branch}"
    if image == "nginx" and branch == "version-11":
        build_args += f" --build-arg NODE_IMAGE_TAG=10-prod"

    print(f"Building {service} {image} image")
    subprocess.run(
        f"docker build {build_args} -t {service}-{image} -f build/{service}-{image}/Dockerfile .",
        shell=True,
    )
    tag_and_push(f"{service}-{image}", tag)


def tag_and_push(image_name, tag):
    print(f'Tagging {image_name} as "{tag}" and pushing')
    subprocess.run(f"docker tag {image_name} frappe/{image_name}:{tag}", shell=True)
    subprocess.run(f"docker push frappe/{image_name}:{tag}", shell=True)


def main():
    args = parse_args()
    tag = args.tag
    branch = "develop"

    if args.version:
        branch = "version-" + args.version
        tag = git_version(args.service, args.version, branch, args.is_beta)

    if args.tag_only:
        tag_and_push(f"{args.service}-{args.image_type}", tag)
    else:
        build(args.service, tag, args.image_type, branch)


if __name__ == "__main__":
    main()
