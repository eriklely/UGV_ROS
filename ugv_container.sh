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

start_ds() {
    for i in 1 2 3 4 5 6 7 8 9 10; do
        docker exec "$NAME" true >/dev/null 2>&1 && break
        sleep 1
    done
    if docker exec "$NAME" bash -lc 'pgrep -f "[f]astdds discovery" >/dev/null' 2>/dev/null; then
        return 0
    fi
    docker exec -d "$NAME" bash -lc \
      'source /opt/ros/humble/setup.bash && exec fastdds discovery --server-id 0 -l 0.0.0.0 -p 11888'
}

case "${1:-}" in
    start)
        echo "Starting $NAME..."
        pkill -f "ugv_rpi/app.py" || true
        fuser -k 5000/tcp >/dev/null 2>&1 || true
        fuser -k 11123/tcp >/dev/null 2>&1 || true
        pkill -f "start_jupyter.sh" || true
        pkill -f jupyter || true
        docker start "$NAME"
        sleep 2
        start_ssh
        start_ds
        echo "Started. SSH + discovery server requested inside container."
        ;;
    stop)
        echo "Stopping $NAME..."
        docker stop "$NAME"
        echo "Stopped."
        ;;
    restart)
        echo "Restarting $NAME..."
        docker restart "$NAME"
        sleep 2
        start_ssh
        start_ds
        echo "Restarted. SSH + discovery server requested inside container."
        ;;
    status)
        docker ps -a --filter "name=^${NAME}$"
        ;;
    shell)
        docker start "$NAME" >/dev/null
        sleep 2
        start_ssh
        start_ds
        docker exec -it "$NAME" /bin/bash
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|shell}"
        echo "Container: $NAME"
        exit 1
        ;;
esac
