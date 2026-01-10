#!/bin/bash
# Dev Orchestrator - Combined launcher script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/.dev-orchestrator/logs"
PID_DIR="$HOME/.dev-orchestrator/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[dev-orch]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[dev-orch]${NC} $1"
}

error() {
    echo -e "${RED}[dev-orch]${NC} $1"
}

start_websocket() {
    log "Starting WebSocket server..."
    cd "$SCRIPT_DIR"
    python -m src.websocket_server > "$LOG_DIR/websocket.log" 2>&1 &
    echo $! > "$PID_DIR/websocket.pid"
    log "WebSocket server started (PID: $(cat $PID_DIR/websocket.pid))"
}

start_dashboard() {
    log "Starting dashboard..."
    cd "$SCRIPT_DIR/dashboard"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        warn "Installing dashboard dependencies..."
        npm install
    fi
    
    npm run dev > "$LOG_DIR/dashboard.log" 2>&1 &
    echo $! > "$PID_DIR/dashboard.pid"
    log "Dashboard started (PID: $(cat $PID_DIR/dashboard.pid)) - http://127.0.0.1:3333"
}

start_menubar() {
    log "Starting menubar app..."
    cd "$SCRIPT_DIR"
    python -m src.menubar_app > "$LOG_DIR/menubar.log" 2>&1 &
    echo $! > "$PID_DIR/menubar.pid"
    log "Menubar app started (PID: $(cat $PID_DIR/menubar.pid))"
}

start_all() {
    log "Starting all Dev Orchestrator services..."
    start_websocket
    sleep 1
    start_dashboard
    sleep 1
    start_menubar
    log "All services started!"
    echo ""
    log "Dashboard: http://127.0.0.1:3333"
    log "WebSocket: ws://127.0.0.1:8766"
    echo ""
    log "Logs: $LOG_DIR"
    log "To tail logs: tail -f $LOG_DIR/*.log"
}

stop_all() {
    log "Stopping all Dev Orchestrator services..."
    
    for pidfile in "$PID_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            name=$(basename "$pidfile" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
                log "Stopped $name (PID: $pid)"
            fi
            rm "$pidfile"
        fi
    done
    
    log "All services stopped."
}

status() {
    echo "Dev Orchestrator Status"
    echo "========================"
    
    for pidfile in "$PID_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            name=$(basename "$pidfile" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "  ${GREEN}●${NC} $name (PID: $pid)"
            else
                echo -e "  ${RED}○${NC} $name (dead)"
            fi
        fi
    done
    
    if [ ! "$(ls -A $PID_DIR 2>/dev/null)" ]; then
        echo "  No services running."
    fi
}

tail_logs() {
    exec tail -f "$LOG_DIR"/*.log
}

case "${1:-}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    status)
        status
        ;;
    logs)
        tail_logs
        ;;
    websocket)
        start_websocket
        ;;
    dashboard)
        start_dashboard
        ;;
    menubar)
        start_menubar
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|websocket|dashboard|menubar}"
        echo ""
        echo "Commands:"
        echo "  start     - Start all services (WebSocket, Dashboard, Menubar)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status"
        echo "  logs      - Tail all log files"
        echo "  websocket - Start only WebSocket server"
        echo "  dashboard - Start only Dashboard"
        echo "  menubar   - Start only Menubar app"
        exit 1
        ;;
esac
