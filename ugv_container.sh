#!/bin/bash
set -euo pipefail

pick_name() {
    if docker ps -a --format '{{.Names}}' | grep -qx 'ugv_jetson_ros_humble'; then
        echo ugv_jetson_ros_humble
    elif docker ps -a --format '{{.Names}}' | grep -qx 'ugv_rpi_ros_humble'; then
        echo ugv_rpi_ros_humble
    elif find / -name 'ugv_jetson' 2>/dev/null | grep -q 'ugv_jetson'; then
        echo ugv_jetson_ros_humble
    else
        echo ugv_rpi_ros_humble
    fi
}

NAME="$(pick_name)"

start_ssh() {
    docker exec "$NAME" service ssh start >/dev/null 2>&1 || \
    docker exec "$NAME" bash -lc 'service ssh start || /etc/init.d/ssh start || systemctl start ssh || true'
}

case "${1:-}" in
    start)
        echo "Starting $NAME..."
        docker start "$NAME"
        start_ssh
        echo "Started. SSH service requested inside container."
        ;;
    stop)
        echo "Stopping $NAME..."
        docker stop "$NAME"
        echo "Stopped."
        ;;
    restart)
        echo "Restarting $NAME..."
        docker restart "$NAME"
        start_ssh
        echo "Restarted. SSH service requested inside container."
        ;;
    status)
        docker ps -a --filter "name=^${NAME}$"
        ;;
    shell)
        docker start "$NAME" >/dev/null
        docker exec -it "$NAME" /bin/bash
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|shell}"
        echo "Container: $NAME"
        exit 1
        ;;
esac
