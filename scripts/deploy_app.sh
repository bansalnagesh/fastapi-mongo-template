# scripts/deploy_app.sh
#!/bin/bash

# Import utilities
source scripts/utils/deploy_utils.sh

# Validate GitHub configuration
validate_github_config() {
    local required_vars=(
        "GITHUB_TOKEN"
        "GITHUB_REPO_URL"
        "GITHUB_BRANCH"
    )

    local missing_vars=0
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo -e "${RED}Error: $var is not set in .env${NC}"
            missing_vars=1
        fi
    done

    if [ $missing_vars -eq 1 ]; then
        exit 1
    fi
}

# Format GitHub URL with token
get_github_auth_url() {
    local repo_url=$GITHUB_REPO_URL
    repo_url=${repo_url/https:\/\//https:\/\/$GITHUB_TOKEN@}
    echo $repo_url
}

# Deploy application to an instance
deploy_to_instance() {
    local instance_ip=$1
    echo -e "${YELLOW}Deploying application to ${instance_ip}...${NC}"

    # Wait for instance to be ready
    wait_for_instance $instance_ip

    # SSH key path from .env
    local SSH_KEY_PATH=${AWS_SSH_KEY_PATH:-"~/.ssh/id_rsa"}
    local AUTH_REPO_URL=$(get_github_auth_url)
    local BRANCH=${GITHUB_BRANCH:-"main"}

    # Deploy using Git
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$instance_ip "
        echo 'Installing and configuring system packages...'
        # Update system and install base packages
        sudo yum update -y
        sudo yum install -y git gcc openssl-devel bzip2-devel libffi-devel

        # Install Nginx from Amazon Linux Extras
        echo 'Installing Nginx...'
        sudo amazon-linux-extras enable nginx1
        sudo yum clean metadata
        sudo yum install -y nginx

        # Verify Nginx installation
        nginx -v
        if [ $? -ne 0 ]; then
            echo 'Nginx installation failed'
            exit 1
        fi

        # Install Python 3.8
        if ! command -v python3.8 &> /dev/null; then
            echo 'Installing Python 3.8...'
            sudo amazon-linux-extras enable python3.8
            sudo yum install -y python3.8 python3.8-devel

            sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
            sudo alternatives --set python3 /usr/bin/python3.8

            curl -O https://bootstrap.pypa.io/get-pip.py
            python3.8 get-pip.py --user
            rm get-pip.py
        fi

        # Configure git and clone repository
        echo 'Configuring git and cloning repository...'
        git config --global http.sslVerify false
        cd ~
        if [ -d \"app\" ]; then
            cd app
            git fetch origin $BRANCH
            git reset --hard origin/$BRANCH
        else
            git clone -b $BRANCH $AUTH_REPO_URL app
            cd app
        fi

        # Set up Python environment
        echo 'Setting up Python environment...'
        python3 -m venv venv
        source venv/bin/activate
        python3 -m pip install --upgrade pip
        python3 -m pip install --no-cache-dir -r requirements.txt

        # Create and set proper permissions for log directory
        sudo mkdir -p /var/log/fastapi
        sudo chown ec2-user:ec2-user /var/log/fastapi

        # Configure Nginx
        echo 'Configuring Nginx...'
        sudo mkdir -p /etc/nginx/conf.d
        sudo tee /etc/nginx/conf.d/fastapi.conf << 'EOL'
server {
    listen 80;
    server_name _;

    access_log /var/log/nginx/fastapi-access.log;
    error_log /var/log/nginx/fastapi-error.log;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /api/v1/health {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 10;
    }
}
EOL

        # Remove default nginx config if it exists
        sudo rm -f /etc/nginx/conf.d/default.conf

        # Create systemd service file
        echo 'Creating FastAPI service...'
        sudo tee /etc/systemd/system/fastapi.service << 'EOL'
[Unit]
Description=FastAPI application
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/app
Environment=PATH=/home/ec2-user/app/venv/bin
EnvironmentFile=/home/ec2-user/app/.env
ExecStart=/home/ec2-user/app/venv/bin/uvicorn server:app --host 0.0.0.0 --port 3000 --workers 4
Restart=always
RestartSec=10
StandardOutput=append:/var/log/fastapi/access.log
StandardError=append:/var/log/fastapi/error.log

[Install]
WantedBy=multi-user.target
EOL

        # Copy .env file
        echo 'Configuring environment...'
        rm -f .env
        cat > .env << 'EOL'
$(cat .env)
EOL

        # Set proper permissions
        sudo chown -R ec2-user:ec2-user /home/ec2-user/app
        chmod 600 .env

        # Start and enable services
        echo 'Starting services...'
        sudo systemctl daemon-reload

        echo 'Starting Nginx...'
        sudo systemctl enable nginx
        sudo systemctl start nginx

        echo 'Nginx Status:'
        sudo systemctl status nginx --no-pager

        echo 'Starting FastAPI...'
        sudo systemctl enable fastapi
        sudo systemctl start fastapi

        echo 'FastAPI Status:'
        sudo systemctl status fastapi --no-pager

        # Verify services are running
        echo 'Verifying services...'
        if ! sudo systemctl is-active --quiet nginx; then
            echo 'Nginx failed to start. Checking logs...'
            sudo cat /var/log/nginx/error.log
        fi

        if ! sudo systemctl is-active --quiet fastapi; then
            echo 'FastAPI service failed to start. Checking logs...'
            sudo journalctl -u fastapi -n 50 --no-pager
        fi

        # Test if the application is responding
        echo 'Testing application health endpoint...'
        sleep 5  # Give the application time to start
        curl -f http://localhost:3000/api/v1/health || echo 'Health check failed'

        # Clean up git credentials
        git config --global --unset http.sslVerify
        git config --unset-all http.https://github.com/.extraheader
    "

    local deploy_status=$?
    if [ $deploy_status -eq 0 ]; then
        echo -e "${GREEN}Successfully deployed to ${instance_ip}${NC}"
        return 0
    else
        echo -e "${RED}Failed to deploy to ${instance_ip}${NC}"
        return 1
    fi
}

# Verify services are running
verify_services() {
    local instance_ip=$1
    local SSH_KEY_PATH=${AWS_SSH_KEY_PATH:-"~/.ssh/id_rsa"}

    echo -e "${YELLOW}Verifying services on ${instance_ip}...${NC}"

    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$instance_ip "
        echo 'Checking service statuses...'
        echo 'Nginx status:'
        sudo systemctl status nginx --no-pager
        echo 'FastAPI status:'
        sudo systemctl status fastapi --no-pager

        echo 'Testing application health endpoint...'
        curl -f http://localhost:3000/api/v1/health || echo 'Health check failed'

        echo 'Checking logs...'
        echo 'Nginx error log:'
        sudo tail -n 10 /var/log/nginx/error.log
        echo 'FastAPI log:'
        sudo tail -n 10 /var/log/fastapi/error.log
    "
}

# Main function
main() {
    echo -e "${YELLOW}Starting application deployment...${NC}"

    # Load and validate environment
    load_env
    validate_aws_credentials
    validate_github_config
    configure_aws

    # Check if infrastructure exists
    local stack_status=$(check_stack_status)
    if [ "$stack_status" != "CREATE_COMPLETE" ] && [ "$stack_status" != "UPDATE_COMPLETE" ]; then
        echo -e "${RED}Infrastructure is not ready. Please run deploy_infra.sh first${NC}"
        exit 1
    fi

    # Get stack outputs
    get_stack_outputs
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to get stack outputs${NC}"
        exit 1
    fi

    # Deploy to both instances
    deploy_to_instance $INSTANCE_1_IP
    deploy_to_instance $INSTANCE_2_IP

    echo -e "${GREEN}Application deployment completed successfully!${NC}"
    echo -e "Application is accessible at: http://${ALB_DNS}"
}

main