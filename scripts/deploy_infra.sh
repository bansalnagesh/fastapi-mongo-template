# scripts/deploy_infra.sh
#!/bin/bash

# Import utilities
source scripts/utils/deploy_utils.sh

# Track deployment state
STACK_MODIFIED=false
DEPLOYMENT_COMPLETE=false

# Cleanup function
cleanup() {
    local exit_code=$?

    if [ $exit_code -ne 0 ] && [ "$DEPLOYMENT_COMPLETE" = false ]; then
        echo -e "${YELLOW}Deployment failed. Starting cleanup...${NC}"

        # Only cleanup if we modified the stack in this run
        if [ "$STACK_MODIFIED" = true ]; then
            local stack_status=$(check_stack_status)

            # If stack exists and is in a failed state, delete it
            if [[ $stack_status == *"FAILED"* ]] || [[ $stack_status == *"ROLLBACK"* ]]; then
                echo -e "${YELLOW}Rolling back CloudFormation stack...${NC}"
                aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION

                echo -e "${YELLOW}Waiting for stack deletion...${NC}"
                aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $AWS_REGION

                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}Stack deleted successfully${NC}"
                else
                    echo -e "${RED}Failed to delete stack. Manual cleanup may be required.${NC}"
                    echo -e "${RED}Please check AWS Console and delete stack: $STACK_NAME${NC}"
                    echo -e "${RED}Resources to check:${NC}"
                    echo -e "  - EC2 Instances"
                    echo -e "  - Load Balancer"
                    echo -e "  - Target Groups"
                    echo -e "  - Security Groups"
                    echo -e "  - VPC and associated resources"
                fi
            else
                echo -e "${YELLOW}Stack is in ${stack_status} state. No cleanup needed.${NC}"
            fi
        else
            echo -e "${YELLOW}No resources were modified. Cleanup not needed.${NC}"
        fi

        echo -e "${RED}Infrastructure deployment failed.${NC}"
        exit 1
    elif [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}Infrastructure deployment completed successfully!${NC}"
    fi
}

# Set up cleanup trap
trap cleanup EXIT

# Deploy CloudFormation stack
deploy_infrastructure() {
    local stack_status=$(check_stack_status)

    case $stack_status in
        "CREATE_COMPLETE"|"UPDATE_COMPLETE")
            echo -e "${GREEN}Stack already exists and is in a good state${NC}"
            return 0
            ;;
        "UPDATE_IN_PROGRESS"|"CREATE_IN_PROGRESS")
            echo -e "${YELLOW}Stack deployment is in progress. Please wait...${NC}"
            return 1
            ;;
        "STACK_NOT_FOUND")
            echo -e "${YELLOW}Creating new stack...${NC}"
            STACK_MODIFIED=true
            ;;
        *)
            echo -e "${YELLOW}Stack exists but needs update...${NC}"
            STACK_MODIFIED=true
            ;;
    esac

    # Check if template is valid
    echo -e "${YELLOW}Validating CloudFormation template...${NC}"
    if ! aws cloudformation validate-template \
        --template-body file://infrastructure/aws/cloudformation.yml \
        --region $AWS_REGION; then
        echo -e "${RED}Template validation failed${NC}"
        return 1
    fi

    # Deploy stack
    aws cloudformation deploy \
        --template-file infrastructure/aws/cloudformation.yml \
        --stack-name $STACK_NAME \
        --parameter-overrides \
            EnvironmentName=$ENV \
            KeyName=$KEY_PAIR_NAME \
            SecurityGroupDescription="Security group for $APP_NAME" \
            EC2TargetGroupName="${APP_NAME}-target-group" \
        --capabilities CAPABILITY_IAM \
        --region $AWS_REGION

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Stack deployment successful${NC}"
        DEPLOYMENT_COMPLETE=true
        return 0
    else
        echo -e "${RED}Stack deployment failed${NC}"
        return 1
    fi
}

# Wait for stack to stabilize
wait_for_stack_completion() {
    local stack_name=$1
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        local status=$(check_stack_status)

        case $status in
            *COMPLETE*)
                echo -e "${GREEN}Stack deployment completed successfully${NC}"
                return 0
                ;;
            *FAILED*|*ROLLBACK*)
                echo -e "${RED}Stack deployment failed${NC}"
                return 1
                ;;
            *)
                echo -e "${YELLOW}Stack status: $status. Waiting...${NC}"
                sleep 30
                ;;
        esac

        attempt=$((attempt + 1))
    done

    echo -e "${RED}Timeout waiting for stack completion${NC}"
    return 1
}

# Main function
main() {
    echo -e "${YELLOW}Starting infrastructure deployment...${NC}"

    # Load and validate environment
    load_env
    validate_aws_credentials
    configure_aws

    # Deploy infrastructure
    deploy_infrastructure
    if [ $? -eq 0 ]; then
        # Wait for stack to stabilize
        wait_for_stack_completion $STACK_NAME
        if [ $? -eq 0 ]; then
            get_stack_outputs
        else
            echo -e "${RED}Stack did not stabilize${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Infrastructure deployment failed${NC}"
        exit 1
    fi
}

main