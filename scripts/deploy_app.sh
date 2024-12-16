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
        # Install required packages
        sudo yum update -y
        sudo yum install -y git gcc openssl-devel bzip2-devel libffi-devel

        # Install Python 3.8
        if ! command -v python3.8 &> /dev/null; then
            echo 'Installing Python 3.8...'
            sudo amazon-linux-extras enable python3.8
            sudo yum install -y python3.8 python3.8-devel

            # Create alternatives group for python3
            sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
            sudo alternatives --set python3 /usr/bin/python3.8

            # Install pip for Python 3.8
            curl -O https://bootstrap.pypa.io/get-pip.py
            python3.8 get-pip.py --user
            rm get-pip.py
        fi

        # Verify Python version
        python3 --version

        # Configure git
        git config --global http.sslVerify false

        # Setup app directory
        cd ~
        if [ -d \"app\" ]; then
            cd app
            git fetch origin $BRANCH
            git reset --hard origin/$BRANCH
        else
            git clone -b $BRANCH $AUTH_REPO_URL app
            cd app
        fi

        # Create virtual environment if it doesn't exist
        if [ ! -d \"venv\" ]; then
            python3 -m venv venv
        fi

        # Copy .env file
        rm -f .env
        cat > .env << 'EOL'
$(cat .env)
EOL

        # Activate virtual environment and install dependencies
        source venv/bin/activate
        python3 -m pip install --upgrade pip
        python3 -m pip install --no-cache-dir -r requirements.txt

        # Setup systemd service
        sudo cp infrastructure/aws/fastapi.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable fastapi
        sudo systemctl restart fastapi
        sudo systemctl restart nginx

        # Clean up git credentials
        git config --global --unset http.sslVerify
        git config --unset-all http.https://github.com/.extraheader

        # Show service status
        echo 'FastAPI Service Status:'
        sudo systemctl status fastapi --no-pager
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