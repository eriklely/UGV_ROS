#!/bin/bash
# =============================================================================
# start_ugvrover.sh - Interactive launcher menu for UGV ROS2 workspace
# Repository: https://github.com/waveshareteam/ugv_ws
# =============================================================================
# This script provides a menu-driven interface to launch all available
# ROS2 launch files in the ugv_ws workspace, organized by category.
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Workspace paths
WS_ROOT="/home/ws/ugv_ws"
UGV_MAIN="$WS_ROOT/src/ugv_main"
UGV_ELSE="$WS_ROOT/src/ugv_else"

# Function to print header
print_header() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${BOLD}                    UGV ROVER - LAUNCH MENU                          ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}              ${YELLOW}UGV ROS2 Workspace Launcher${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to print category header
print_category() {
    echo -e "${MAGENTA}┌─ ${BOLD}$1${NC} ${MAGENTA}$(printf '─%.0s' {1..60})${NC}"
    echo -e "${MAGENTA}│${NC}"
}

# Function to print menu item
print_item() {
    local num=$1
    local name=$2
    local desc=$3
    printf "${MAGENTA}│${NC}  ${GREEN}%2s)${NC} ${BOLD}%-35s${NC} %s\n" "$num" "$name" "$desc"
}

# Function to print footer
print_footer() {
    echo -e "${MAGENTA}│${NC}"
    echo -e "${MAGENTA}└─$(printf '─%.0s' {1..75})${NC}"
    echo ""
}

# Function to check if workspace is sourced
check_workspace() {
    if [[ -z "$AMENT_PREFIX_PATH" ]] || [[ "$AMENT_PREFIX_PATH" != *"ugv_ws"* ]]; then
        echo -e "${YELLOW}⚠ Workspace not sourced. Sourcing...${NC}"
        if [[ -f "$WS_ROOT/install/setup.bash" ]]; then
            source "$WS_ROOT/install/setup.bash"
            echo -e "${GREEN}✓ Workspace sourced${NC}"
        else
            echo -e "${RED}✗ Workspace not built! Run: cd $WS_ROOT && colcon build${NC}"
            exit 1
        fi
    fi
}

# Function to run launch file
run_launch() {
    local pkg=$1
    local launch_file=$2
    local args=${3:-""}
    
    echo -e "${CYAN}Launching: ${BOLD}ros2 launch $pkg $launch_file $args${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    ros2 launch "$pkg" "$launch_file" $args
}

# Function to run command
run_command() {
    local cmd=$1
    local desc=$2
    
    echo -e "${CYAN}Running: ${BOLD}$cmd${NC}"
    echo -e "${YELLOW}$desc${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    eval "$cmd"
}

# Function to handle model selection
select_model() {
    echo -e "${CYAN}Select UGV Model:${NC}"
    echo -e "  ${GREEN}1)${NC} rasp_rover"
    echo -e "  ${GREEN}2)${NC} ugv_rover (default)"
    echo -e "  ${GREEN}3)${NC} ugv_beast"
    read -p "Choice [2]: " model_choice
    case $model_choice in
        1) export UGV_MODEL="rasp_rover" ;;
        3) export UGV_MODEL="ugv_beast" ;;
        *) export UGV_MODEL="ugv_rover" ;;
    esac
    echo -e "${GREEN}UGV_MODEL=$UGV_MODEL${NC}"
}

# Function to handle LiDAR model selection
select_lidar() {
    echo -e "${CYAN}Select LiDAR Model:${NC}"
    echo -e "  ${GREEN}1)${NC} ld06"
    echo -e "  ${GREEN}2)${NC} ld19 (default)"
    echo -e "  ${GREEN}3)${NC} stl27l"
    read -p "Choice [2]: " lidar_choice
    case $lidar_choice in
        1) export LDLIDAR_MODEL="ld06" ;;
        3) export LDLIDAR_MODEL="stl27l" ;;
        *) export LDLIDAR_MODEL="ld19" ;;
    esac
    echo -e "${GREEN}LDLIDAR_MODEL=$LDLIDAR_MODEL${NC}"
}

# Function to handle use_rviz
select_rviz() {
    read -p "Launch RViz? (y/N): " rviz_choice
    if [[ "$rviz_choice" =~ ^[Yy]$ ]]; then
        export USE_RVIZ="true"
    else
        export USE_RVIZ="false"
    fi
}

# Main menu
main_menu() {
    while true; do
        print_header
        
        # Check workspace
        check_workspace
        
        echo -e "${BOLD}Main Categories:${NC}"
        echo ""
        
        print_category "�  LAPTOP/DESKTOP (External Device)"
        print_item "1" "description_display" "Robot description + RViz (slam_2d config)"
        print_footer
        
        print_category "🚗  BRINGUP & DRIVERS (Real Robot)"
        print_item "2" "bringup_lidar" "Start LiDAR + robot description + RViz"
        print_item "3" "bringup_imu_ekf" "IMU + EKF sensor fusion (odom + imu)"
        print_item "4" "bringup_imu_origin" "IMU origin (no EKF)"
        print_item "5" "gps" "GPS driver + navsat_transform + EKF fusion"
        print_item "6" "keyboard_ctrl" "Keyboard teleop control"
        print_item "7" "joy_ctrl" "Joystick teleop control"
        print_item "8" "behavior_ctrl" "Behavior/command control"
        print_footer
        
        print_category "🌍  GAZEBO SIMULATION"
        print_item "9" "gazebo_display" "Display robot model in Gazebo (select model)"
        print_item "10" "gazebo_bringup" "Full Gazebo simulation with house world"
        print_item "11" "gazebo_bringup_test" "Gazebo empty world for testing"
        print_footer
        
        print_category "🗺️  SLAM (Mapping)"
        print_item "12" "slam_gmapping" "Gmapping 2D SLAM (laser only)"
        print_item "13" "slam_cartographer" "Cartographer 2D SLAM"
        print_item "14" "slam_rtabmap_rgbd" "RTAB-Map 3D SLAM (RGB-D camera)"
        print_footer
        
        print_category "🧭  NAVIGATION (Requires Map)"
        print_item "15" "nav_amcl" "Nav2 with AMCL localization (DWA/TEB)"
        print_item "16" "nav_emcl" "Nav2 with EMCL localization"
        print_item "17" "nav_cartographer" "Nav2 with Cartographer localization"
        print_item "18" "nav_rtabmap" "Nav2 with RTAB-Map localization"
        print_footer
        
        print_category "🔄  SLAM + NAVIGATION COMBINED"
        print_item "19" "gazebo_slam_nav" "Gazebo: SLAM + Nav combined"
        print_item "20" "slam_nav" "Real robot: SLAM + Nav combined"
        print_footer
        
        print_category "👁️  VISION & PERCEPTION"
        print_item "21" "camera_usb" "USB camera driver"
        print_item "22" "camera_oak_d_lite" "OAK-D Lite depth camera"
        print_item "23" "camera_stereo" "Stereo camera (OAK-D)"
        print_item "24" "apriltag_track" "AprilTag detection + tracking"
        print_footer
        
        print_category "🌐  WEB INTERFACE & VISUALIZATION"
        print_item "25" "web_app" "Vizanti web interface (port 5000)"
        print_item "26" "vizanti_server" "Vizanti ROS2 server"
        print_item "27" "vizanti_rws" "Vizanti RWS backend"
        print_footer
        
        print_category "📡  LIDAR DRIVERS (Standalone)"
        print_item "28" "ldlidar_auto" "Auto-detect LiDAR model"
        print_item "29" "ldlidar_ld06" "LD06 LiDAR"
        print_item "30" "ldlidar_ld19" "LD19 LiDAR"
        print_item "31" "ldlidar_stl27l" "STL-27L LiDAR"
        print_item "32" "ldlidar_viewer" "LiDAR RViz viewer"
        print_footer
        
        print_category "🔧  UTILITIES & TOOLS"
        print_item "33" "explore_lite" "Autonomous exploration"
        print_item "34" "emcl2_localization" "EMCL2 Monte Carlo localization"
        print_item "35" "robot_pose_publisher" "Robot pose publisher"
        print_footer
        
        print_category "⚙️  SETTINGS"
        print_item "M" "Change UGV Model" "Current: ${UGV_MODEL:-ugv_rover}"
        print_item "L" "Change LiDAR Model" "Current: ${LDLIDAR_MODEL:-ld19}"
        print_item "R" "Toggle RViz" "Current: ${USE_RVIZ:-false}"
        print_item "S" "Source Workspace" "Re-source install/setup.bash"
        print_item "Q" "Quit" "Exit launcher"
        print_footer
        
        read -p "Select option: " choice
        echo ""
        
        case $choice in
            # Laptop/Desktop
            1) 
                select_rviz
                run_launch "ugv_description" "display.launch.py" "use_rviz:=$USE_RVIZ rviz_config:=slam_2d"
                ;;
            
            # Bringup & Drivers
            2) 
                select_rviz
                run_launch "ugv_bringup" "bringup_lidar.launch.py" "use_rviz:=$USE_RVIZ"
                ;;
            3) 
                select_rviz
                run_launch "ugv_bringup" "bringup_imu_ekf.launch.py" "use_rviz:=$USE_RVIZ"
                ;;
            4) 
                select_rviz
                run_launch "ugv_bringup" "bringup_imu_origin.launch.py" "use_rviz:=$USE_RVIZ"
                ;;
            5) 
                run_launch "ugv_bringup" "gps.launch.py"
                ;;
            6) run_command "ros2 run ugv_tools keyboard_ctrl" "Keyboard teleop control" ;;
            7) run_command "ros2 run ugv_tools joy_ctrl" "Joystick teleop control" ;;
            8) run_command "ros2 run ugv_tools behavior_ctrl" "Behavior/command control" ;;
            
            # Gazebo Simulation
            9) 
                select_model
                run_launch "ugv_gazebo" "display.launch.py"
                ;;
            10) 
                select_model
                run_launch "ugv_gazebo" "bringup.launch.py"
                ;;
            11) 
                select_model
                run_launch "ugv_gazebo" "bringup_test.launch.py"
                ;;
            
            # SLAM
            12) 
                select_rviz
                run_launch "ugv_slam" "gmapping.launch.py" "use_rviz:=$USE_RVIZ"
                ;;
            13) 
                select_rviz
                run_launch "ugv_slam" "cartographer.launch.py" "use_rviz:=$USE_RVIZ"
                ;;
            14) 
                select_rviz
                run_launch "ugv_slam" "rtabmap_rgbd.launch.py" "use_rviz:=$USE_RVIZ"
                ;;
            
            # Navigation
            15) 
                select_rviz
                run_launch "ugv_nav" "nav.launch.py" "use_rviz:=$USE_RVIZ use_localplan:=teb use_localization:=amcl"
                ;;
            16) 
                select_rviz
                run_launch "ugv_nav" "nav.launch.py" "use_rviz:=$USE_RVIZ use_localplan:=teb use_localization:=emcl"
                ;;
            17) 
                select_rviz
                run_launch "ugv_nav" "nav.launch.py" "use_rviz:=$USE_RVIZ use_localplan:=teb use_localization:=cartographer"
                ;;
            18) 
                select_rviz
                run_launch "ugv_nav" "nav_rtabmap.launch.py" "use_rviz:=$USE_RVIZ use_localplan:=teb"
                ;;
            
            # SLAM + Nav Combined
            19) 
                select_model
                run_launch "ugv_gazebo" "slam_nav/slam_nav.launch.py"
                ;;
            20) 
                select_rviz
                run_launch "ugv_nav" "slam_nav.launch.py" "use_rviz:=$USE_RVIZ"
                ;;
            
            # Vision
            21) run_launch "ugv_vision" "camera.launch.py" ;;
            22) run_launch "ugv_vision" "oak_d_lite.launch.py" ;;
            23) run_launch "ugv_vision" "stereo.launch.py" ;;
            24) run_launch "ugv_vision" "apriltag_track.launch.py" ;;
            
            # Web Interface
            25) 
                read -p "Host IP [0.0.0.0]: " host_ip
                host_ip=${host_ip:-0.0.0.0}
                run_launch "ugv_web_app" "bringup.launch.py" "host:=$host_ip"
                ;;
            26) run_launch "vizanti_server" "vizanti_server.launch.py" ;;
            27) run_launch "vizanti_server" "vizanti_rws.launch.py" ;;
            
            # LiDAR Drivers
            28) 
                select_lidar
                run_launch "ldlidar" "ldlidar.launch.py"
                ;;
            29) 
                export LDLIDAR_MODEL="ld06"
                run_launch "ldlidar" "ld06.launch.py"
                ;;
            30) 
                export LDLIDAR_MODEL="ld19"
                run_launch "ldlidar" "ld19.launch.py"
                ;;
            31) 
                export LDLIDAR_MODEL="stl27l"
                run_launch "ldlidar" "stl27l.launch.py"
                ;;
            32) 
                select_lidar
                run_launch "ldlidar" "viewer_ldlidar.launch.py"
                ;;
            
            # Utilities
            33) run_launch "explore_lite" "explore.launch.py" ;;
            34) run_launch "emcl2" "emcl2.launch.py" ;;
            35) run_launch "robot_pose_publisher" "robot_pose_publisher_launch.py" ;;
            36) 
                select_rviz
                run_launch "ugv_description" "display.launch.py" "use_rviz:=$USE_RVIZ"
                ;;
            
            # Settings
            M|m) select_model ;;
            L|l) select_lidar ;;
            R|r) 
                if [[ "$USE_RVIZ" == "true" ]]; then
                    export USE_RVIZ="false"
                else
                    export USE_RVIZ="true"
                fi
                echo -e "${GREEN}USE_RVIZ=$USE_RVIZ${NC}"
                sleep 1
                ;;
            S|s) 
                source "$WS_ROOT/install/setup.bash"
                echo -e "${GREEN}✓ Workspace re-sourced${NC}"
                sleep 1
                ;;
            Q|q) 
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *) 
                echo -e "${RED}Invalid option. Press Enter to continue...${NC}"
                read
                ;;
        esac
    done
}

# Check if running in correct directory
if [[ ! -f "$WS_ROOT/install/setup.bash" ]] && [[ ! -f "/opt/ros/humble/setup.bash" ]]; then
    echo -e "${RED}Error: ROS2 Humble not found or workspace not built${NC}"
    echo "Please ensure:"
    echo "  1. ROS2 Humble is installed"
    echo "  2. Workspace is built: cd $WS_ROOT && colcon build"
    exit 1
fi

# Source ROS2
source /opt/ros/humble/setup.bash

# Run main menu
main_menu