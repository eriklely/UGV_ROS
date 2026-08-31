#!/bin/bash
set -euo pipefail

DOCKER=/usr/bin/docker
LOG=/home/ws/ugv_ws/ros_docker.log

wait_for_docker() {
    local i
    for i in $(seq 1 60); do
        if $DOCKER info >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    echo "Docker did not become ready" >&2
    return 1
}

pick_name() {
    if $DOCKER ps -a --format '{{.Names}}' | grep -qx 'ugv_jetson_ros_humble'; then
        echo ugv_jetson_ros_humble
    elif $DOCKER ps -a --format '{{.Names}}' | grep -qx 'ugv_rpi_ros_humble'; then
        echo ugv_rpi_ros_humble
    else
        echo ugv_rpi_ros_humble
    fi
}

start_ssh() {
    $DOCKER exec "$NAME" bash -lc '
        service ssh start ||
        /etc/init.d/ssh start ||
        systemctl start ssh ||
        true
    ' || true
}

wait_for_docker
NAME="$(pick_name)"

case "${1:-}" in
    start)
        echo "Starting $NAME..."
        $DOCKER start "$NAME"
        sleep 2
        start_ssh
        echo "Started. SSH service requested inside container."
        ;;
    stop)
        echo "Stopping $NAME..."
        $DOCKER stop "$NAME"
        echo "Stopped."
        ;;
    restart)
        echo "Restarting $NAME..."
        $DOCKER restart "$NAME"
        sleep 2
        start_ssh
        echo "Restarted. SSH service requested inside container."
        ;;
    status)
        $DOCKER ps -a --filter "name=^${NAME}$"
        ;;
    shell)
        $DOCKER start "$NAME" >/dev/null
        $DOCKER exec -it "$NAME" /bin/bash
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|shell}"
        echo "Container: $NAME"
        exit 1
        ;;
esac
