# Lab 1: Introduction to Temporal

Welcome to Lab 1! In this lab, you'll learn how to deploy the Temporal orchestration platform on Amazon Web Services (AWS) using Docker and Docker Compose inside an EC2 instance. This guide is beginner-friendly and walks you through every step, from AWS setup to running Temporal and accessing its Web UI.

---

## Objectives

By the end of this lab, you will be able to:

- **Understand Temporal architecture:** Learn the core components and how they work together
- **Set up Temporal server:** Deploy Temporal using Docker Compose on AWS EC2
- **Explore the Web UI:** Navigate Temporal's dashboard and understand its features
- **Use Temporal CLI:** Execute commands to manage namespaces and server operations
- **Work with namespaces:** Create and manage isolated environments for applications

---

## 📚 Background

### What is Temporal?
Temporal is an open-source workflow orchestration platform designed to build durable, scalable, and fault-tolerant applications. It enables developers to write complex business logic as workflows that can run for days, weeks, or even months, with built-in reliability features.

### Why Use Temporal?
- **Durability:** Workflows survive failures and restarts
- **Reliability:** Automatic retries and error handling
- **Scalability:** Distribute work across multiple workers
- **Visibility:** Rich monitoring and debugging capabilities
- **Simplicity:** Complex distributed logic written as simple code

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

## Deploying Temporal

### 1. Setting Up the Environment
Once connected to your EC2 instance:

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install Docker
sudo apt install docker.io -y

# Add your user to the docker group (so you don't need sudo for docker)
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install docker-compose -y

# Apply group changes without logging out
newgrp docker
```

### 2. Running Docker Compose
1. Create a directory for your Temporal project:
   ```bash
   mkdir temporal-lab && cd temporal-lab
   ```
2. Create a `docker-compose.yml` file:
   ```yaml
   version: '3.8'
   services:
     temporal:
       image: temporalio/admin-tools:latest
       ports:
         - "7233:7233"  # Temporal Server API
         - "8233:8233"  # Web UI Dashboard
       entrypoint: []
       command: ["temporal", "server", "start-dev", "--ui-port", "8233", "--ip", "0.0.0.0"]
   ```
3. Start Temporal:
   ```bash
   docker-compose up -d
   ```
4. Check that it's running:
   ```bash
   docker-compose ps
   docker-compose logs -f temporal
   ```

### 3. Accessing the Temporal Web UI
- In your AWS EC2 dashboard, find your instance's **Public IPv4 address**.
- Open your browser and go to: `http://<your-instance-public-ip>:8233`
- You should see the Temporal Web UI dashboard!

![dashboard](./dashboard.png?raw=true)

#### Dashboard Features

| Section | Purpose | What You'll See |
|---------|---------|-----------------|
| **Workflows** | Monitor workflow executions | Currently empty (no workflows yet) |
| **Task Queues** | View work distribution | Shows available task queues |
| **Namespaces** | Switch between environments | Default namespace pre-configured |
| **Cluster** | Server health monitoring | Server status and metrics |

---

## Using Temporal CLI and Namespaces

The Temporal CLI is included in the Docker container. Let's explore key commands:

#### Server Health Check
```bash
# Check if Temporal server is healthy
docker-compose exec temporal temporal server health

# Get server information
docker-compose exec temporal temporal cluster health
```

#### Namespace Operations

##### View Existing Namespaces
```bash
# List all namespaces
docker-compose exec temporal temporal namespace list

# Describe the default namespace
docker-compose exec temporal temporal namespace describe --namespace default
```

##### Create a New Namespace
```bash
# Register a new namespace for your application
docker-compose exec temporal temporal namespace register --namespace my-lab-app

# Register with retention period and description
docker-compose exec temporal temporal namespace register \
  --namespace production-app \
  --retention 72h \
  --description "Production application namespace"
```

##### Verify Namespace Creation
```bash
# List namespaces again to see your new ones
docker-compose exec temporal temporal namespace list

# Get details of your new namespace
docker-compose exec temporal temporal namespace describe --namespace my-lab-app
```

### Explore Namespaces in Web UI

1. **Refresh Web UI**: Go back to your browser tab
2. **Switch Namespaces**: Use the namespace dropdown at the top
3. **Observe Changes**: Notice how you can now select different namespaces:
   - `default` (pre-existing)
   - `my-lab-app` (created by you)
   - `production-app` (if created)

### Advanced CLI Exploration

#### Task Queue Operations
```bash
# List task queues (will be empty until workflows are running)
docker-compose exec temporal temporal task-queue list --namespace default

# Get task queue information
docker-compose exec temporal temporal task-queue describe \
  --task-queue sample-queue \
  --namespace default
```

#### Server Configuration
```bash
# View server configuration
docker-compose exec temporal temporal server config

# Check server version
docker-compose exec temporal temporal server --version
```

## 🔍 Understanding the System

### What You've Accomplished
1. **Deployed Temporal Server**: Running in development mode with in-memory storage
2. **Configured External Access**: Access via EC2 public IP
3. **Explored Web UI**: Learned about monitoring capabilities
4. **Used CLI Tools**: Managed namespaces and server operations
5. **Created Isolation**: Set up separate namespaces for different applications

### System Architecture in Your Lab

```
┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │  Temporal       │
│  (Your Computer)│<--►│  Server (EC2)   │
└─────────────────┘    └─────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   Namespaces    │
                     │  - default      │
                     │  - my-lab-app   │
                     │  - production.. │
                     └─────────────────┘
```

### Key Concepts Demonstrated

#### Namespaces
- **Purpose**: Provide isolation between different applications or environments
- **Benefits**: Separate development, staging, and production workflows
- **Usage**: Switch between namespaces in Web UI or CLI

#### Development Mode
- **Storage**: In-memory (data lost on restart)
- **Purpose**: Fast setup for learning and development
- **Limitation**: Not suitable for production (use persistent storage)

## 🧪 Experimentation

### Try These Activities

#### 1. Create Multiple Namespaces
```bash
# Create namespaces for different environments
docker-compose exec temporal temporal namespace register --namespace development
docker-compose exec temporal temporal namespace register --namespace staging
docker-compose exec temporal temporal namespace register --namespace testing
```

#### 2. Namespace Management
```bash
# Update namespace retention
docker-compose exec temporal temporal namespace update \
  --namespace my-lab-app \
  --retention 168h

# Add description to existing namespace
docker-compose exec temporal temporal namespace update \
  --namespace development \
  --description "Development environment for testing workflows"
```

#### 3. Explore Different Web UI Sections
- Switch between namespaces and observe how the view changes
- Check the Cluster section for server metrics
- Explore the empty Workflows section (you'll fill this in later labs)

---

## Troubleshooting
- **Can't connect via SSH?**
  - Check your security group allows SSH (port 22) from your IP
  - Make sure you used the correct key pair and permissions
- **Can't access Temporal Web UI?**
  - Check security group allows port 8233 from your IP
  - Make sure Temporal is running (`docker-compose ps`)
- **Docker permission errors?**
  - Run `newgrp docker` or log out and back in
- **Out of memory or disk?**
  - Use a larger EC2 instance or increase storage

---

## Conclusion

Congratulations! 🎉 You've deployed Temporal to AWS using Docker Compose on an EC2 instance. You now have a cloud-based orchestration platform ready for workflow development and experimentation.
