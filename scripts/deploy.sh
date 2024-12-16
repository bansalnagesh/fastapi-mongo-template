## scripts/deploy.sh
##!/bin/bash
#
## Colors for output
#RED='\033[0;31m'
#GREEN='\033[0;32m'
#YELLOW='\033[1;33m'
#NC='\033[0m'
#
## Track deployment state
#STACK_CREATED=false
#DEPLOYMENT_COMPLETE=false
#
## Error handling
#set -e  # Exit on any error
#trap cleanup EXIT  # Ensure cleanup runs on script exit
#
## Load environment variables from .env
#if [ -f .env ]; then
#    export $(cat .env | grep -v '^#' | xargs)
#else
#    echo -e "${RED}Error: .env file not found${NC}"
#    exit 1
#fi
#
## Configuration (from .env)
#APP_NAME=${PROJECT_NAME:-"fastapi-template"}
#AWS_REGION=${AWS_REGION:-"ap-south-1"}
#STACK_NAME=${STACK_NAME:-"fastapi-stack"}
#KEY_PAIR_NAME=${AWS_KEY_PAIR_NAME:-""}
#ENV=${1:-production}
#
## Get stack outputs
#get_stack_outputs() {
#    echo -e "${YELLOW}Getting stack outputs...${NC}"
#
#    INSTANCE_1_IP=$(aws cloudformation describe-stacks \
#        --stack-name $STACK_NAME \
#        --query 'Stacks[0].Outputs[?ExportName==`'${STACK_NAME}'-Instance1IP`].OutputValue' \
#        --output text \
#        --region $AWS_REGION)
#
#    INSTANCE_2_IP=$(aws cloudformation describe-stacks \
#        --stack-name $STACK_NAME \
#        --query 'Stacks[0].Outputs[?ExportName==`'${STACK_NAME}'-Instance2IP`].OutputValue' \
#        --output text \
#        --region $AWS_REGION)
#
#    ALB_DNS=$(aws cloudformation describe-stacks \
#        --stack-name $STACK_NAME \
#        --query 'Stacks[0].Outputs[?ExportName==`'${STACK_NAME}'-LoadBalancerDNS`].OutputValue' \
#        --output text \
#        --region $AWS_REGION)
#
#    if [ -z "$INSTANCE_1_IP" ] || [ -z "$INSTANCE_2_IP" ] || [ -z "$ALB_DNS" ]; then
#        echo -e "${RED}Error: Failed to get stack outputs${NC}"
#        exit 1
#    else
#        echo -e "${GREEN}Successfully retrieved stack outputs${NC}"
#        echo -e "Instance 1 IP: ${INSTANCE_1_IP}"
#        echo -e "Instance 2 IP: ${INSTANCE_2_IP}"
#        echo -e "Load Balancer DNS: ${ALB_DNS}"
#    fi
#}
#
## Cleanup function
#cleanup() {
#    local exit_code=$?
#
#    if [ $exit_code -ne 0 ] && [ "$DEPLOYMENT_COMPLETE" = false ]; then
#        echo -e "${YELLOW}Deployment failed. Starting cleanup...${NC}"
#
#        if [ "$STACK_CREATED" = true ]; then
#            echo -e "${YELLOW}Rolling back CloudFormation stack...${NC}"
#            aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION
#
#            echo -e "${YELLOW}Waiting for stack deletion...${NC}"
#            aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $AWS_REGION
#
#            if [ $? -eq 0 ]; then
#                echo -e "${GREEN}Stack deleted successfully${NC}"
#            else
#                echo -e "${RED}Failed to delete stack. Manual cleanup may be required.${NC}"
#                echo -e "${RED}Please check AWS Console and delete stack: $STACK_NAME${NC}"
#            fi
#        fi
#
#        echo -e "${RED}Deployment failed. All resources have been cleaned up.${NC}"
#    elif [ $exit_code -eq 0 ]; then
#        echo -e "${GREEN}Deployment completed successfully!${NC}"
#    fi
#}
#
## Validate required environment variables
#validate_env_vars() {
#    local required_vars=(
#        "AWS_ACCESS_KEY_ID"
#        "AWS_SECRET_ACCESS_KEY"
#        "AWS_REGION"
#        "AWS_KEY_PAIR_NAME"
#        "AWS_SSH_KEY_PATH"
#    )
#
#    local missing_vars=0
#    for var in "${required_vars[@]}"; do
#        if [ -z "${!var}" ]; then
#            echo -e "${RED}Error: $var is not set in .env${NC}"
#            missing_vars=1
#        fi
#    done
#
#    if [ $missing_vars -eq 1 ]; then
#        exit 1
#    fi
#}
#
## Configure AWS CLI
#configure_aws() {
#    mkdir -p ~/.aws
#    cat > ~/.aws/credentials << EOL
#[default]
#aws_access_key_id = ${AWS_ACCESS_KEY_ID}
#aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
#region = ${AWS_REGION}
#EOL
#}
#
## Check if stack exists
#check_stack_exists() {
#    aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION >/dev/null 2>&1
#    return $?
#}
#
## Deploy CloudFormation stack
#deploy_infrastructure() {
#    echo -e "${YELLOW}Deploying infrastructure...${NC}"
#
#    if check_stack_exists; then
#        echo -e "${YELLOW}Updating existing stack...${NC}"
#        update_type="update"
#    else
#        echo -e "${YELLOW}Creating new stack...${NC}"
#        update_type="create"
#    fi
#
#    aws cloudformation deploy \
#        --template-file infrastructure/aws/cloudformation.yml \
#        --stack-name $STACK_NAME \
#        --parameter-overrides \
#            EnvironmentName=$ENV \
#            KeyName=$KEY_PAIR_NAME \
#            SecurityGroupDescription="Security group for $APP_NAME" \
#            EC2TargetGroupName="${APP_NAME}-target-group" \
#        --capabilities CAPABILITY_IAM \
#        --region $AWS_REGION
#
#    if [ $? -eq 0 ]; then
#        STACK_CREATED=true
#        echo -e "${GREEN}Stack deployment successful${NC}"
#    else
#        echo -e "${RED}Stack deployment failed${NC}"
#        exit 1
#    fi
#}
#
## Wait for instances to be ready
#wait_for_instances() {
#    local instance_ip=$1
#    local max_attempts=30
#    local attempt=1
#
#    echo -e "${YELLOW}Waiting for instance ${instance_ip} to be ready...${NC}"
#
#    while [ $attempt -le $max_attempts ]; do
#        if nc -zw 2 ${instance_ip} 22; then
#            echo -e "${GREEN}Instance ${instance_ip} is ready${NC}"
#            return 0
#        fi
#        echo -n "."
#        sleep 10
#        attempt=$((attempt + 1))
#    done
#
#    echo -e "${RED}Timeout waiting for instance ${instance_ip} to be ready${NC}"
#    return 1
#}
#
## Deploy application to EC2 instances
#deploy_application() {
#    local instance_ip=$1
#    echo -e "${YELLOW}Deploying application to ${instance_ip}...${NC}"
#
#    # Wait for instance to be ready
#    wait_for_instances $instance_ip
#
#    # SSH key path from .env
#    local SSH_KEY_PATH=${AWS_SSH_KEY_PATH:-"~/.ssh/id_rsa"}
#
#    # Build and package application
#    echo "Building application..."
#    pip install build
#    python -m build
#
#    # Copy files to EC2
#    echo "Copying files to EC2..."
#    scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -r \
#        dist/* \
#        requirements.txt \
#        .env \
#        ec2-user@$instance_ip:~/app/
#
#    # Install dependencies and start application
#    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$instance_ip '
#        cd ~/app
#        python3 -m venv venv
#        source venv/bin/activate
#        pip install -r requirements.txt
#        sudo systemctl restart nginx
#
#        # Copy systemd service file
#        sudo cp infrastructure/aws/fastapi.service /etc/systemd/system/
#        sudo systemctl daemon-reload
#        sudo systemctl enable fastapi
#        sudo systemctl restart fastapi
#    '
#}
#
## Main deployment process
#main() {
#    echo -e "${YELLOW}Starting deployment process...${NC}"
#
#    # Validate environment variables
#    validate_env_vars
#
#    # Configure AWS if needed
#    if ! aws sts get-caller-identity > /dev/null 2>&1; then
#        echo -e "${YELLOW}Configuring AWS credentials...${NC}"
#        configure_aws
#    fi
#
#    # Deploy infrastructure
#    deploy_infrastructure
#
#    # Get stack outputs
#    get_stack_outputs
#
#    # Deploy to both instances
#    deploy_application $INSTANCE_1_IP
#    deploy_application $INSTANCE_2_IP
#
#    DEPLOYMENT_COMPLETE=true
#    echo -e "${GREEN}Deployment completed successfully!${NC}"
#    echo -e "Application is accessible at: http://${ALB_DNS}"
#    echo -e "Instance 1 IP: ${INSTANCE_1_IP}"
#    echo -e "Instance 2 IP: ${INSTANCE_2_IP}"
#}
#
#main