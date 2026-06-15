#!/bin/bash
docker compose -p ranch exec backend bench ${@:1}
