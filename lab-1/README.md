# Lab 1: Introduction to Temporal

Welcome to Lab 1! In this lab, you'll learn how to deploy the Temporal orchestration platform on Amazon Web Services (AWS) using Docker and Docker Compose inside an EC2 instance. This guide is beginner-friendly and walks you through every step, from AWS setup to running Temporal and accessing its Web UI.

By the end of this lab, you will be able to:
- **Understand Temporal architecture**: Learn the core components and how they work together
- **Set up Temporal server**: Deploy Temporal using Docker Compose on AWS EC2
- **Explore the Web UI**: Navigate Temporal's dashboard and understand its features
- **Use Temporal CLI**: Execute commands to manage namespaces and server operations
- **Work with namespaces**: Create and manage isolated environments for applications

## 📚 Background

### What is Temporal?
Temporal is an **open-source workflow orchestration platform** designed to build durable, scalable, and fault-tolerant applications. It enables developers to write complex business logic as workflows that can run for days, weeks, or even months, with built-in reliability features.

### Why Use Temporal?
- **Durability**: Workflows survive failures and restarts
- **Reliability**: Automatic retries and error handling
- **Scalability**: Distribute work across multiple workers
- **Visibility**: Rich monitoring and debugging capabilities
- **Simplicity**: Complex distributed logic written as simple code

In this lab, you'll deploy Temporal to AWS so it can be accessed from anywhere. You'll set up the necessary AWS networking, launch an EC2 instance, install Docker and Docker Compose, and then run Temporal using Docker Compose. This is a great way to learn both Temporal and basic AWS cloud deployment!

---

## Prerequisites

Before you begin, make sure you have:
- An AWS Account
- AWS Console access (browser)
- SSH client (Terminal on macOS/Linux, PuTTY or WSL on Windows)
- Basic familiarity with AWS EC2 and networking (helpful, but not required)

---

## Setting Up AWS Resources

### 1. Creating a VPC
1. Log in to the [AWS Console](https://console.aws.amazon.com/).
2. Change the region to **Singapore (ap-southeast-1)** (top right corner).
3. Navigate to **VPC Dashboard**.
4. Click **Create VPC**.
5. Enter:
   - Name tag: `temporal-vpc-1`
   - IPv4 CIDR block: `10.0.0.0/16`
   - IPv6 CIDR block: No IPv6 CIDR block
   - Tenancy: Default
6. Click **Create VPC**.

### 2. Creating Subnets
1. In the VPC Dashboard, go to **Subnets** > **Create subnet**.
2. Enter:
   - VPC ID: Select your `temporal-vpc-1`
   - Subnet name: `temporal-subnet-1`
   - Availability Zone: e.g., `ap-southeast-1a`
   - IPv4 subnet CIDR block: `10.0.1.0/24`
3. Click **Create subnet**.
4. Go to **Action > Edit Subnet Setting** and enable **auto-assign public IPv4 address**.

### 3. Setting Up Internet Gateway
1. Go to **Internet Gateways** > **Create internet gateway**.
2. Name tag: `temporal-igw-1` > **Create internet gateway**.
3. Select the new gateway > **Actions > Attach to VPC** > select `temporal-vpc-1` > **Attach**.

### 4. Configuring Route Tables
1. Go to **Route Tables** > **Create route table**.
2. Name tag: `temporal-rt-1`, VPC: `temporal-vpc-1` > **Create**.
3. Select your new route table > **Routes** tab > **Edit routes** > **Add route**:
   - Destination: `0.0.0.0/0`
   - Target: Select **Internet Gateway** and choose `temporal-igw-1`
   - **Save changes**
4. Go to **Subnet associations** > **Edit subnet associations** > select `temporal-subnet-1` > **Save**.

### 5. Creating Security Groups
1. Go to **Security Groups** > **Create security group**.
2. Enter:
   - Name: `temporal-sg-1`
   - Description: Security group for Temporal
   - VPC: `temporal-vpc-1`
3. Configure **inbound rules**:
   - Type: SSH, Port: 22, Source: Your IP
   - Type: Custom TCP, Port: 7233, Source: 0.0.0.0/0 (Temporal API)
   - Type: Custom TCP, Port: 8233, Source: 0.0.0.0/0 (Temporal Web UI)
4. Configure **outbound rules**:
   - Type: All traffic, Destination: 0.0.0.0/0
5. Click **Create security group**.

### 6. Launching an EC2 Instance
1. Go to **EC2 Dashboard** > **Launch instances**.
2. Name: `temporal-ec2-instance-1`
3. AMI: **Ubuntu Server 22.04 LTS** (or latest)
4. Instance type: `t2.micro` (Free tier eligible)
5. Key pair: Create new or use existing (download and keep safe!)
6. Network settings:
   - Network: `temporal-vpc-1`
   - Subnet: `temporal-subnet-1`
   - Auto-assign Public IP: Enable
   - Firewall: Select **existing security group** > `temporal-sg-1`
7. Storage: Default (8GB SSD)
8. Click **Launch Instance**.

### 7. Connecting to the EC2 Instance
1. Once running, select your instance and copy the **Public IPv4 address**.
2. In your terminal, set permissions and connect:
   ```bash
   chmod 400 temporal-key-pair.pem
   ssh -i "temporal-key-pair.pem" ubuntu@<your-instance-public-ip>
   ```

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
