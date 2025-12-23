# Choosing a Deployment or Development Method

This repository (`frappe_docker`) supports **multiple ways to run Frappe using Docker**.
Each method is designed for a **specific purpose**, and they are **not interchangeable**.

This document explains:

- All supported ways to use this repository
- Which method to choose depending on your goal
- Common misconceptions, especially around persistence and app installation

Reading this document **before following any setup guide** is strongly recommended.

## Overview

| Goal                         | Recommended Method        | Production Ready |
| ---------------------------- | ------------------------- | ---------------- |
| Quick exploration            | `pwd.yml`                 | ❌               |
| Local development            | VS Code Devcontainers     | ❌               |
| Automated production install | Easy Install Script       | ✅               |
| Manual production deployment | `compose.yml` + overrides | ✅               |

## 1. `pwd.yml` – Quick Test / Exploration Setup

The `pwd.yml` file is a **single, self-contained Docker Compose file** intended for:

- Trying out Frappe and ERPNext
- Demos and short-lived test environments
- Learning the basics without setup overhead

### Characteristics

- One Compose file
- Minimal configuration
- Fast startup
- Disposable by design

### Limitations

- ❌ **Not intended for production**
- ❌ **Not intended for development**
- ❌ **Not suitable as a migration starting point**

If you start with `pwd.yml`, you should expect to **throw the environment away**.

## 2. VS Code Devcontainers – Local Development Setup

The development setup described in [`/docs/05-development`](../05-development)

uses **VS Code Devcontainers** to provide a **local Frappe development environment**.

### Intended Use

- Developing Frappe or custom apps
- Working with source code
- Debugging and testing changes locally

### Key Differences from Other Setups

- Optimized for **interactive development**
- Code is editable live
- Containers are tailored for developer workflows
- Not designed to represent a production environment

### Important Notes

- ❌ **Not a deployment method**
- ❌ **Not intended for production**
- ✔ The **correct way** to do local development with this repository

Using production-oriented setups (`pwd.yml` or `compose.yml`) for development is strongly discouraged.

## 3. Easy Install Script (from `frappe/bench`)

The Easy Install script provided in the [`frappe/bench`](https://github.com/frappe/bench) repository uses `frappe_docker` internally and automates a full deployment process.

It is comparable to what a **deployment pipeline** would perform.

### What It Does

- Installs Docker and prerequisites
- Pulls and configures `frappe_docker`
- Uses production-grade images and services
- Reduces manual configuration

### Intended Use

- Production environments
- Users who want a guided, automated installation
- Server deployments with minimal manual steps

### Production Readiness

✔ **Yes** — suitable for real production systems
✔ Uses the same components as the manual production setup

## 4. `compose.yml` + Overrides – Intended Production Setup

This is the **canonical production deployment method** for `frappe_docker`.

It uses:

- The main `compose.yml`
- Override files from the `overrides/` directory

Detailed instructions are available in [`/docs/02-setup`](../02-setup)

### Characteristics

- Explicit service definitions
- Flexible and configurable
- Designed for long-running production environments
- Suitable for advanced and customized deployments

**This is the preferred approach for teams managing their own infrastructure.**

## Summary

- Each setup serves a **distinct purpose**
- Development, testing, and production are **separate workflows**
- Do not expect to evolve a disposable setup into production
- Apps must be included **at build time**, not installed later ([Docker immutability](02-docker-immutability.md))
