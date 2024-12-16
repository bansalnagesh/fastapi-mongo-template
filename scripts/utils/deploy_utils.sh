# scripts/utils/deploy_utils.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment variables
load_env() {
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo -e "${RED}Error: .env file not found${NC}"
        exit 1
    fi

    # Set default values
    APP_NAME=${PROJECT_NAME:-"fastapi-template"}
    AWS_REGION=${AWS_REGION:-"ap-south-1"}
    STACK_NAME=${STACK_NAME:-"fastapi-stack"}
    KEY_PAIR_NAME=${AWS_KEY_PAIR_NAME:-""}
    ENV=${1:-production}
}

# Validate AWS credentials
validate_aws_credentials() {
    local required_vars=(
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "AWS_REGION"
        "AWS_KEY_PAIR_NAME"
        "AWS_SSH_KEY_PATH"
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

# Configure AWS CLI
configure_aws() {
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${YELLOW}Configuring AWS credentials...${NC}"
        mkdir -p ~/.aws
        cat > ~/.aws/credentials << EOL
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
region = ${AWS_REGION}
EOL
    fi
}

# Check if stack exists and is in a good state
check_stack_status() {
    local stack_status
    stack_status=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].StackStatus' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "STACK_NOT_FOUND")

    echo $stack_status
}

# Get stack outputs
get_stack_outputs() {
    echo -e "${YELLOW}Getting stack outputs...${NC}"

    INSTANCE_1_IP=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?ExportName==`'${STACK_NAME}'-Instance1IP`].OutputValue' \
        --output text \
        --region $AWS_REGION)

    INSTANCE_2_IP=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?ExportName==`'${STACK_NAME}'-Instance2IP`].OutputValue' \
        --output text \
        --region $AWS_REGION)

    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?ExportName==`'${STACK_NAME}'-LoadBalancerDNS`].OutputValue' \
        --output text \
        --region $AWS_REGION)

    if [ -z "$INSTANCE_1_IP" ] || [ -z "$INSTANCE_2_IP" ] || [ -z "$ALB_DNS" ]; then
        echo -e "${RED}Error: Failed to get stack outputs${NC}"
        return 1
    fi

    echo -e "${GREEN}Successfully retrieved stack outputs${NC}"
    echo -e "Instance 1 IP: ${INSTANCE_1_IP}"
    echo -e "Instance 2 IP: ${INSTANCE_2_IP}"
    echo -e "Load Balancer DNS: ${ALB_DNS}"
    return 0
}

# Wait for instance to be ready
wait_for_instance() {
    local instance_ip=$1
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}Waiting for instance ${instance_ip} to be ready...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if nc -zw 2 ${instance_ip} 22; then
            echo -e "${GREEN}Instance ${instance_ip} is ready${NC}"
            return 0
        fi
        echo -n "."
        sleep 10
        attempt=$((attempt + 1))
    done

    echo -e "${RED}Timeout waiting for instance ${instance_ip} to be ready${NC}"
    return 1
}