#!/bin/bash
# ============================================================================
# SmartRisk EC2 Initial Setup Script
# ============================================================================
# This script automates the installation of all required software on a
# fresh Ubuntu EC2 instance.
#
# Usage:
#   1. Upload this script to new EC2 instance:
#      scp -i smartrisk-key.pem setup_new_ec2.sh ubuntu@<NEW_IP>:~/
#
#   2. SSH into server and run:
#      chmod +x setup_new_ec2.sh
#      ./setup_new_ec2.sh
#
# Or run remotely in one command:
#   ssh -i smartrisk-key.pem ubuntu@<NEW_IP> 'bash -s' < setup_new_ec2.sh
# ============================================================================

set -e  # Exit on any error

echo "============================================================================"
echo "SmartRisk EC2 Setup Script"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

check_root() {
    if [ "$EUID" -eq 0 ]; then
        error "Please run as ubuntu user, not root. The script will use sudo when needed."
    fi
}

# ============================================================================
# Step 1: System Update
# ============================================================================

step1_system_update() {
    info "Step 1: Updating system packages..."
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y curl wget git vim unzip jq dnsutils htop
    info "✅ System updated"
}

# ============================================================================
# Step 2: Install Docker
# ============================================================================

step2_install_docker() {
    info "Step 2: Installing Docker..."
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        warn "Docker is already installed: $DOCKER_VERSION"
        read -p "Do you want to reinstall? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Skipping Docker installation"
            return
        fi
        sudo apt remove -y docker docker-engine docker.io containerd runc || true
    fi
    
    # Install Docker prerequisites
    sudo apt install -y ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Add Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add ubuntu user to docker group
    sudo usermod -aG docker ubuntu
    
    # Verify installation
    DOCKER_VERSION=$(docker --version)
    info "✅ Docker installed: $DOCKER_VERSION"
    
    warn "You may need to re-login for docker group changes to take effect"
    warn "Run: newgrp docker"
}

# ============================================================================
# Step 3: Install Docker Compose (Standalone)
# ============================================================================

step3_install_docker_compose() {
    info "Step 3: Installing Docker Compose standalone..."
    
    # Check if docker-compose is already installed
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        warn "Docker Compose is already installed: $COMPOSE_VERSION"
        return
    fi
    
    # Download Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    
    # Make executable
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    # Verify installation
    COMPOSE_VERSION=$(docker-compose --version)
    info "✅ Docker Compose installed: $COMPOSE_VERSION"
}

# ============================================================================
# Step 4: Install Certbot
# ============================================================================

step4_install_certbot() {
    info "Step 4: Installing Certbot for SSL certificates..."
    
    # Check if certbot is already installed
    if command -v certbot &> /dev/null; then
        CERTBOT_VERSION=$(certbot --version)
        warn "Certbot is already installed: $CERTBOT_VERSION"
        return
    fi
    
    # Install Certbot via snap
    sudo snap install core
    sudo snap refresh core
    sudo snap install --classic certbot
    
    # Create symlink
    sudo ln -sf /snap/bin/certbot /usr/bin/certbot
    
    # Verify installation
    CERTBOT_VERSION=$(certbot --version)
    info "✅ Certbot installed: $CERTBOT_VERSION"
}

# ============================================================================
# Step 5: Install Database and Redis Tools
# ============================================================================

step5_install_tools() {
    info "Step 5: Installing PostgreSQL and Redis tools..."
    
    sudo apt install -y postgresql-client redis-tools
    
    info "✅ Database and Redis tools installed"
}

# ============================================================================
# Step 6: Configure Firewall
# ============================================================================

step6_configure_firewall() {
    info "Step 6: Configuring UFW firewall..."
    
    # Check if UFW is active
    if sudo ufw status | grep -q "Status: active"; then
        warn "UFW is already active"
    else
        sudo ufw --force reset
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow 22/tcp comment 'SSH'
        sudo ufw allow 80/tcp comment 'HTTP'
        sudo ufw allow 443/tcp comment 'HTTPS'
        sudo ufw allow 8000/tcp comment 'Django (optional)'
        sudo ufw --force enable
    fi
    
    info "✅ Firewall configured"
    sudo ufw status numbered
}

# ============================================================================
# Step 7: Create Project Directory
# ============================================================================

step7_create_directories() {
    info "Step 7: Creating project directories..."
    
    mkdir -p ~/smartrisk
    cd ~/smartrisk
    mkdir -p nginx/certbot nginx/ssl
    
    info "✅ Project directories created at ~/smartrisk"
}

# ============================================================================
# Step 8: System Configuration
# ============================================================================

step8_system_config() {
    info "Step 8: Applying system optimizations..."
    
    # Increase file descriptor limits
    sudo bash -c 'cat >> /etc/security/limits.conf' << 'EOF'

# SmartRisk application limits
ubuntu soft nofile 65536
ubuntu hard nofile 65536
EOF
    
    # Sysctl optimizations
    sudo bash -c 'cat >> /etc/sysctl.conf' << 'EOF'

# SmartRisk network optimizations
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
EOF
    
    sudo sysctl -p
    
    info "✅ System configuration applied"
}

# ============================================================================
# Step 9: Summary
# ============================================================================

step9_summary() {
    echo ""
    echo "============================================================================"
    echo "✅ SmartRisk EC2 Setup Complete!"
    echo "============================================================================"
    echo ""
    info "Installed Software:"
    echo "  - Docker: $(docker --version 2>/dev/null || echo 'Not found')"
    echo "  - Docker Compose: $(docker-compose --version 2>/dev/null || echo 'Not found')"
    echo "  - Certbot: $(certbot --version 2>/dev/null || echo 'Not found')"
    echo "  - PostgreSQL Client: $(psql --version 2>/dev/null || echo 'Not found')"
    echo "  - Redis CLI: $(redis-cli --version 2>/dev/null || echo 'Not found')"
    echo ""
    info "Project Directory: ~/smartrisk"
    echo ""
    info "Next Steps:"
    echo "  1. Update GitHub Secrets:"
    echo "     - EC2_SSH_KEY: Your new PEM key content"
    echo "     - EC2_HOST: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo '<YOUR_SERVER_IP>')"
    echo ""
    echo "  2. Update DNS records to point to this server IP"
    echo ""
    echo "  3. Trigger GitHub Actions deployment:"
    echo "     - Push to main branch, OR"
    echo "     - Manually trigger workflow from GitHub Actions tab"
    echo ""
    echo "  4. Re-login to apply docker group changes:"
    echo "     - exit"
    echo "     - ssh ubuntu@<SERVER_IP>"
    echo "     - Or run: newgrp docker"
    echo ""
    warn "Important: Make sure to update EC2_HOST secret in GitHub before deploying!"
    echo ""
    echo "============================================================================"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    check_root
    
    echo "This script will install:"
    echo "  - Docker & Docker Compose"
    echo "  - Certbot (for SSL)"
    echo "  - PostgreSQL & Redis tools"
    echo "  - Configure firewall"
    echo "  - Create project directories"
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Setup cancelled by user"
    fi
    
    step1_system_update
    step2_install_docker
    step3_install_docker_compose
    step4_install_certbot
    step5_install_tools
    step6_configure_firewall
    step7_create_directories
    step8_system_config
    step9_summary
}

# Run main function
main "$@"
