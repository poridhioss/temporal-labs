# Lab 2: Hello World Workflow with Temporal

## 🎯 Learning Objectives

By the end of this lab, you will be able to:
- **Understand Temporal fundamentals**: Learn the core concepts of workflows and activities
- **Create workflow components**: Implement activities, workflows, and workers in Python
- **Deploy with Docker**: Use Docker Compose to run Temporal server and workers
- **Execute workflows**: Start workflows using CLI and monitor execution
- **Observe in Web UI**: Use Temporal's dashboard to monitor workflow execution
- **Configure load balancers**: Set up external access in Poridhi Lab environment

In this lab, you'll deploy Temporal to AWS so it can be accessed from anywhere. You'll set up the necessary AWS networking, launch an EC2 instance, install Docker and Docker Compose, and then run Temporal using Docker Compose. This is a great way to learn both Temporal and basic AWS cloud deployment!

---

## Prerequisites

Before you begin, make sure you have:

- An AWS Account with configured credentials
- Pulumi CLI installed ([installation guide](https://www.pulumi.com/docs/get-started/install/))
- Python 3.7+ installed
- SSH client (Terminal on macOS/Linux, PuTTY or WSL on Windows)
- AWS CLI installed
- An AWS key pair created in the Singapore region (`ap-southeast-1`)

---

## Setting Up AWS Resources with Pulumi

### 1. Install Pulumi (if not already installed)

```bash
curl -fsSL https://get.pulumi.com | sh
```

### 2. Configure AWS CLI

Configure AWS CLI with the necessary credentials. Run the following command and follow the prompts:

```bash
aws configure
```

You will be prompted for:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (e.g., `ap-southeast-1`)
- Default output format (e.g., `json`)

Fill in the details using the generated credentials in Poridhi Labs.

### 3. Set Up a Pulumi Project

**Install Python virtual environment:**

```bash
sudo apt update
sudo apt install python3.8-venv
```

**Create a new directory and initialize a Pulumi project:**

```bash
mkdir ssh-lab-pulumi && cd ssh-lab-pulumi
pulumi new aws-python
```

This command creates a new directory with the basic structure for a Pulumi project. Follow the prompts to set up your project:
- Project name: `temporal-lab`
- Project description: `Temporal Lab Infrastructure`
- Stack name: `dev`
- AWS region: `ap-southeast-1`

### 4. Create AWS Key Pair

Create a new key pair for your instances using the following command:

```bash
aws ec2 create-key-pair --key-name MyKeyPair --query 'KeyMaterial' --output text > MyKeyPair.pem
```

Set file permissions of the key file:

```bash
chmod 400 MyKeyPair.pem
```

### 5. Configure Your Infrastructure

Replace the contents of `__main__.py` with the following code:

```python
import pulumi
import pulumi_aws as aws

# Create a VPC
vpc = aws.ec2.Vpc("my-vpc",
   cidr_block="10.0.0.0/16",
   enable_dns_hostnames=True,
   enable_dns_support=True,
   tags={
      "Name": "my-vpc",
   })

# Create a public subnet
public_subnet = aws.ec2.Subnet("my-subnet",
   vpc_id=vpc.id,
   cidr_block="10.0.1.0/24",
   availability_zone="ap-southeast-1a",
   map_public_ip_on_launch=True,
   tags={
      "Name": "my-subnet",
   })

# Create an Internet Gateway
internet_gateway = aws.ec2.InternetGateway("my-igw",
   vpc_id=vpc.id,
   tags={
      "Name": "my-igw",
   })

# Create a Route Table
public_route_table = aws.ec2.RouteTable("my-rt",
   vpc_id=vpc.id,
   tags={
      "Name": "my-rt",
   })

# Create a route in the Route Table for the Internet Gateway
route = aws.ec2.Route("igw-route",
   route_table_id=public_route_table.id,
   destination_cidr_block="0.0.0.0/0",
   gateway_id=internet_gateway.id)

# Associate Route Table with Public Subnet
rt_association = aws.ec2.RouteTableAssociation("rt-association",
   subnet_id=public_subnet.id,
   route_table_id=public_route_table.id)

# Create a Security Group for the SSH Lab Instance
my_security_group = aws.ec2.SecurityGroup("my-secgrp",
   vpc_id=vpc.id,
   description="Allow SSH access",
   ingress=[
    # SSH access from anywhere
    {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
    # Temporal API
    {"protocol": "tcp", "from_port": 7233, "to_port": 7233, "cidr_blocks": ["0.0.0.0/0"]},
    # Temporal Web UI
    {"protocol": "tcp", "from_port": 8233, "to_port": 8233, "cidr_blocks": ["0.0.0.0/0"]}
],
   egress=[
      # Allow all outbound traffic
      {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}
   ],
   tags={
      "Name": "my-secgrp",
   })

# Define an AMI for the EC2 instance (Ubuntu 24.04 LTS)
ami_id = "ami-01811d4912b4ccb26"  # Ubuntu 24.04 LTS, update if needed for your region

# Create the SSH Lab EC2 Instance
ssh_lab_instance = aws.ec2.Instance("my-instance",
   instance_type="t2.micro",
   vpc_security_group_ids=[my_security_group.id],
   ami=ami_id,
   subnet_id=public_subnet.id,
   key_name="MyKeyPair",
   associate_public_ip_address=True,
   tags={
      "Name": "my-instance",
      "Environment": "Lab",
      "Project": "Temporal-Lab"
   })

# Export the relevant outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("subnet_id", public_subnet.id)
pulumi.export("security_group_id", my_security_group.id)
pulumi.export("instance_id", ssh_lab_instance.id)
pulumi.export("public_ip", ssh_lab_instance.public_ip)
```

### 6. Deploy the Infrastructure

Deploy the infrastructure:

```bash
pulumi up
```

This will create the necessary resources in AWS. When prompted, select **yes** to confirm the deployment.

**Note:** Remember the public IP address of the instance for later use. You can view it anytime by running:

```bash
pulumi stack output public_ip
```

### 7. Connect to the EC2 Instance

Connect to the EC2 instance using SSH:

```bash
ssh -i MyKeyPair.pem ubuntu@<public_ip>
```

Replace `<public_ip>` with the actual public IP address from the Pulumi output.

---
Now that your AWS infrastructure is up and running, you're ready to shift your focus to Temporal itself. In the next sections, you'll learn how to build, deploy, and interact with Temporal workflows using the environment you've just provisioned. This is where you'll get hands-on experience with Temporal's core concepts and see how everything comes together in practice.


## Architectural Point of View
![arch](./lab2.png?raw=true)

## 📚 Background

### What is Temporal?
Temporal is a **durable workflow orchestration platform** that helps you build reliable, scalable applications by managing the execution of long-running business processes.

### Key Concepts
- **Workflow**: A durable function that orchestrates activities and manages state
- **Activity**: A regular function that performs a single task (e.g., API call, database query)
- **Worker**: A service that executes workflows and activities
- **Task Queue**: A mechanism for distributing work to workers

### Why Use Temporal?
- **Reliability**: Automatic retries and failure handling
- **Scalability**: Distribute work across multiple workers
- **Visibility**: Built-in monitoring and debugging tools
- **Durability**: Workflows survive process restarts and failures

## 🛠 Prerequisites

### Poridhi Lab Environment:
- Access to Poridhi Lab with VS Code interface
- **Docker & Docker Compose**: ✅ Pre-installed in Poridhi Lab
- **Web Browser**: For accessing the Temporal Web UI through load balancer
- **Terminal Access**: Available through VS Code integrated terminal

### Verify Prerequisites
```bash
# Open VS Code terminal and verify Docker installation
docker --version
docker-compose --version
docker ps
```

## 📁 Project Structure

You'll create the following structure in your lab-2 directory:

```
lab-2/
├── docker-compose.yml      # Docker services configuration
├── hello_world_workflow/   # Workflow implementation
│   ├── Dockerfile          # Worker container setup
│   ├── hello_activity.py   # Activity definition
|   ├── requriements.txt    
│   ├── hello_workflow.py   # Workflow definition
│   ├── worker.py          # Worker service
│   └── start_workflow.py  # Workflow starter script
└── README.md              # This documentation
```

## 🚀 Lab Implementation

### Step 1: Set Up Project Structure

Open VS Code terminal in Poridhi Lab and navigate to your lab-2 directory:

```bash
# Navigate to lab-2 directory
cd lab-2

# Create workflow directory
mkdir hello_world_workflow
```

### Step 2: Create Docker Compose Configuration

Create `docker-compose.yml` in the lab-2 directory:

```yaml
version: '3.8'

services:
  temporal:
    image: temporalio/admin-tools:latest
    ports:
      - "7233:7233"
      - "8233:8233"
    entrypoint: []
    command: ["temporal", "server", "start-dev", "--ui-port", "8233", "--ip", "0.0.0.0"]

  worker:
    build: ./hello_world_workflow
    volumes:
      - ./hello_world_workflow:/app
    depends_on:
      - temporal
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
    command: ["python", "worker.py"]
```

### Step 3: Create Worker Container Setup

Create `hello_world_workflow/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Copy the workflow code
COPY . .

# Install Temporal Python SDK and dependencies
RUN pip install -r requirements.txt

# Keep container running for development
# CMD ["tail", "-f", "/dev/null"]
CMD ["python", "-u", "worker.py"] 
```

### Step 4: Implement Workflow Components

#### Create Activity (`hello_world_workflow/hello_activity.py`)
```python
from temporalio import activity

@activity.defn
async def say_hello(name: str) -> str:
    """
    Activity that generates a greeting message.
    Activities are where you put your business logic.
    """
    return f"Hello, {name}!"
```

#### Create Workflow (`hello_world_workflow/hello_workflow.py`)
```python
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

# Import the activity
with workflow.unsafe.imports_passed_through():
    from hello_activity import say_hello

@workflow.defn
class HelloWorkflow:
    """
    Workflow that orchestrates the hello activity.
    Workflows are durable and can survive failures.
    """
    
    @workflow.run
    async def run(self, name: str) -> str:
        # Execute activity with timeout and retry policy
        return await workflow.execute_activity(
            say_hello,
            name,
            start_to_close_timeout=timedelta(seconds=5),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
```

#### Create Worker (`hello_world_workflow/worker.py`)
```python
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from hello_workflow import HelloWorkflow
from hello_activity import say_hello

async def main():
    """
    Worker connects to Temporal server and processes workflows/activities.
    """
    # Connect to Temporal server
    client = await Client.connect("temporal:7233", namespace="default")
    
    # Create worker that listens to task queue
    worker = Worker(
        client,
        task_queue="hello-task-queue",
        workflows=[HelloWorkflow],  # Register workflow
        activities=[say_hello],     # Register activity
    )
    
    print("🚀 Worker started! Listening for workflows...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Create Workflow Starter (`hello_world_workflow/start_workflow.py`)
```python
import asyncio
from temporalio.client import Client
from hello_workflow import HelloWorkflow

async def main():
    """
    Script to start a workflow programmatically.
    """
    # Connect to Temporal server
    client = await Client.connect("temporal:7233", namespace="default")
    
    # Execute workflow and wait for result
    result = await client.execute_workflow(
        HelloWorkflow.run,
        "World",
        id="hello-workflow-id",
        task_queue="hello-task-queue",
    )
    
    print(f"✅ Workflow result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 5: Deploy Services in Poridhi Lab

```bash
# Build and start Temporal server and worker
docker-compose up --build -d

# Verify containers are running
docker-compose ps

# Check worker logs
docker-compose logs -f worker
```

## Run `make up` to start the Temporal server and worker
![arch](./make-up-test.png?raw=true)

### Step 6: Configure Load Balancer for Web UI Access

#### Get Network Information
```bash
# Get your lab instance IP address for load balancer configuration
ifconfig eth0

# Note the IP address (e.g., 192.168.1.100)
```

#### Set Up Load Balancer
1. **Access Load Balancer Configuration** in Poridhi Lab interface
2. **Create New Load Balancer**:
   - **Enter IP**: Your lab instance eth0 IP address
   - **Enter Port**: `8233`
3. **Click Create**

You'll receive a load balancer URL like:
```
https://[your-instance-id]-lb-[port].bm-southeast.lab.poridhi.io/
```

### Step 7: Execute Your First Workflow

#### Option A: Using CLI in Terminal
```bash
# Start workflow using Temporal CLI
docker-compose exec temporal temporal workflow start \
  --task-queue hello-task-queue \
  --type HelloWorkflow \
  --input '"World"' \
  --workflow-id hello-workflow-cli \
  --namespace default
```

#### Option B: Using Python Script
```bash
# Run the workflow starter script
docker-compose exec worker python start_workflow.py
```

### Step 8: Monitor in Web UI

1. **Open Temporal Web UI**: Use your load balancer URL in a web browser
2. **Navigate to Workflows**: Click on "Workflows" in the sidebar
3. **Select Namespace**: Choose "default" from the dropdown
4. **Find Your Workflow**: Look for `hello-workflow-id` or `hello-workflow-cli`
5. **Inspect Execution**: Click on the workflow to see:
   - Input: `"World"`
   - Output: `"Hello, World!"`
   - Execution history and timeline

## Expected dashboard view
![arch](./dashboard.png?raw=true)

## 🔍 Understanding Your Workflow

### Workflow Execution Flow
1. **Client** submits workflow to task queue
2. **Worker** picks up workflow task
3. **Workflow** executes and schedules activity
4. **Worker** picks up activity task
5. **Activity** executes and returns result
6. **Workflow** completes with final result

### Key Components Analysis

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **HelloWorkflow** | Orchestrates the greeting process | Durable, retry policies, timeouts |
| **say_hello Activity** | Performs the actual greeting logic | Stateless, can be retried |
| **Worker** | Executes workflows and activities | Scalable, polls task queue |
| **Task Queue** | Distributes work to workers | Load balancing, fault tolerance |

## 🧪 Experimentation

### Try These Variations

#### 1. Modify the Greeting
```python
# In hello_activity.py, try different messages
return f"¡Hola, {name}! Welcome to Temporal!"
```

#### 2. Add Error Handling
```python
# In hello_activity.py, simulate failures
import random
if random.random() < 0.3:  # 30% chance of failure
    raise Exception("Simulated failure!")
return f"Hello, {name}!"
```

#### 3. Add Multiple Activities
```python
# Create additional activities and chain them in your workflow
@workflow.run
async def run(self, name: str) -> str:
    greeting = await workflow.execute_activity(say_hello, name, ...)
    farewell = await workflow.execute_activity(say_goodbye, name, ...)
    return f"{greeting} ... {farewell}"
```

## 🔧 Troubleshooting

### Common Issues

#### Container Not Starting
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs temporal
docker-compose logs worker
```

#### Web UI Not Accessible
```bash
# Verify port binding
docker-compose port temporal 8233

# Test local access
curl http://localhost:8233
```

#### Worker Not Processing
```bash
# Check worker logs
docker-compose logs -f worker

# Restart worker
docker-compose restart worker
```

### Load Balancer Issues

#### Load Balancer Not Working
```bash
# Verify port 8233 is bound
netstat -tlnp | grep :8233

# Check Temporal service health
curl http://localhost:8233
```

## 🧹 Cleanup

### Stop Services
```bash
# Stop all containers
docker-compose down

# Remove volumes and networks
docker-compose down -v

# Clean up Docker images
docker system prune -a
```

**Remove Load Balancer**: Delete the load balancer configuration in Poridhi Lab interface.

## 🎓 Key Takeaways

- **Workflows** orchestrate business logic and are durable
- **Activities** contain your actual business logic and can be retried
- **Workers** execute both workflows and activities
- **Task Queues** enable scalable work distribution
- **Temporal Web UI** provides powerful monitoring and debugging capabilities
- **Docker Compose** simplifies development and deployment
- **Load Balancers** enable external access to services in cloud environments

## 🚀 Next Steps

- **Lab 3**: Learn about retry policies and timeout handling
- **Lab 4**: Implement long-running workflows with signals
- **Lab 5**: Explore parent-child workflow relationships
- **Advanced**: Add queries, signals, and child workflows to this example

## 📚 Additional Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Python SDK Reference](https://python.temporal.io/)
- [Temporal Samples](https://github.com/temporalio/samples-python)
- [Community Forum](https://community.temporal.io/)

