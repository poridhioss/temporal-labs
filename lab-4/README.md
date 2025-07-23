# 📦 Lab 4: Signals and Queries

**Goal:** Interact with running workflows.

- Create a long-running counter workflow
- Send signals to increment count
- Query current count at any time
- Practice sending signal/query via CLI

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
With your cloud environment prepared, you’re now ready to explore more advanced Temporal concepts. In this lab, you’ll work with long-running workflows and learn how to use signals and queries to interact with them in real time. This is where you’ll see Temporal’s power in handling dynamic, stateful processes that respond to external input.

# Long Running Counter Workflow

A Temporal workflow example that demonstrates a long-running counter with signal and query capabilities.

## Architectural Point of View
![arch](./lab4_archi-diagram.svg?raw=true)


## Quick Start

1. **Navigate to the workflow directory:**
   ```bash
   cd longRunningCounterWorkflow
   ```

2. **Start the services:**
   ```bash
   docker-compose up --build
   ```

## Expected Terminal View
![arch](./make-up.png?raw=true)

3. **Run the workflow:**
   ```bash
   docker-compose exec worker python start_workflow.py
   ```

4. **Access Temporal Web UI:**
   Open [http://localhost:8233](http://localhost:8233) and note the workflow ID.

### Note the workflow ID
![id](./running-workflow.png?raw=true)


## Workflow Operations

### Send Signal (Increment Counter)
```bash
docker-compose exec temporal tctl --namespace default workflow signal \
  --workflow_id <workflow-id> --name increment
```

## Send the signal and get the cli output
![signal](./signal.png?raw=true)

### Query Counter Value
```bash
docker-compose exec temporal temporal workflow query \
  --workflow-id <workflow-id> --type get_count
```

## Try with query and get the cli output
![signal](./query.png?raw=true)

## Notes
- The workflow runs indefinitely and prints the counter every 10 seconds
- Use signals to increment the counter
- Use queries to check the current count value


# Lab 4: Signals and Queries

## 🎯 Learning Objectives

By the end of this lab, you will be able to:
- **Understand workflow communication**: Learn how to interact with running workflows in real-time
- **Implement signals**: Send data and commands to workflows while they're executing
- **Use queries**: Retrieve current state and data from running workflows
- **Create long-running workflows**: Build workflows that run indefinitely and maintain state
- **Master CLI interactions**: Use Temporal CLI to send signals and execute queries
- **Design interactive systems**: Build workflows that respond to external events and user interactions


## Sequence Diagram:
![arch](./seq-diagram.png?raw=true)

## 📚 Background

### Why Signals and Queries Matter

Traditional batch workflows run to completion without external interaction. However, many real-world scenarios require **dynamic interaction** with running workflows - updating parameters, checking status, or triggering actions based on external events.

### Temporal's Interactive Features

#### Signals
**Signals** allow you to send data to a running workflow, enabling dynamic updates and external control.

| Signal Characteristic | Description | Use Cases |
|----------------------|-------------|-----------|
| **Asynchronous** | Fire-and-forget, doesn't wait for response | User actions, external events |
| **Durable** | Persisted and replayed during recovery | Critical state updates |
| **Ordered** | Processed in the order they're received | Sequential operations |
| **Type-Safe** | Strongly typed parameters | Data integrity |

#### Queries
**Queries** allow you to retrieve current state from a running workflow without affecting its execution.

| Query Characteristic | Description | Use Cases |
|---------------------|-------------|-----------|
| **Synchronous** | Returns immediate response | Status checks, dashboards |
| **Read-Only** | Cannot modify workflow state | Safe data access |
| **Consistent** | Returns current workflow state | Real-time monitoring |
| **Fast** | Low latency operations | User interfaces |

### Real-World Applications

#### E-commerce Order Processing
- **Signals**: Cancel order, update shipping address, apply discount
- **Queries**: Check order status, get tracking info, view current total

#### IoT Device Management
- **Signals**: Change configuration, trigger maintenance, update firmware
- **Queries**: Get sensor readings, check device status, view metrics

#### Financial Trading Systems
- **Signals**: Modify trading parameters, stop trading, update limits
- **Queries**: Get current positions, check P&L, view trade history

#### Game Servers
- **Signals**: Player actions, game events, admin commands
- **Queries**: Player stats, game state, leaderboards

### Communication Patterns

```
┌─────────────┐    Signals     ┌─────────────────┐
│   External  │──────────────► │   Running       │
│   Systems   │                │   Workflow      │
│             │◄─────────────  │                 │
└─────────────┘    Queries     └─────────────────┘
```

## 🛠 Prerequisites

### Poridhi Lab Environment:
- Completion of **Lab 3** (Retry and Timeout Handling)
- Access to Poridhi Lab with VS Code interface
- **Docker & Docker Compose**: ✅ Pre-installed in Poridhi Lab
- **Web Browser**: For accessing Temporal Web UI through load balancer
- **Understanding**: Knowledge of workflows, activities, and fault tolerance

### Verify Prerequisites
```bash
# Open VS Code terminal and verify setup
cd lab-4
docker --version
docker-compose --version
```

## 📁 Project Structure

You'll work with the following structure in your lab-4 directory:

```
lab-4/
├── docker-compose.yml                # Temporal server configuration
├── longRunningCounterWorkflow/       # Interactive workflow implementation
│   ├── Dockerfile                    # Worker container setup
│   ├── counter_workflow.py          # Long-running workflow with signals/queries
│   ├── worker.py                    # Worker service
│   ├── start_workflow.py            # Workflow starter
│   └── requirements.py             # Python dependencies
└── README.md                        # This documentation
```

## 🚀 Lab Implementation

### Step 1: Set Up Project Structure

Open VS Code terminal in Poridhi Lab and navigate to your lab-4 directory:

```bash
# Navigate to lab-4 directory
cd lab-4

# Verify the longRunningCounterWorkflow directory exists
ls -la longRunningCounterWorkflow/
```

### Step 2: Understand the Docker Configuration

The `docker-compose.yml` should already be configured:

```yaml
version: "3.9"

networks:
  temporal-net:

services:
  # ───────── Postgres (backing store) ─────────
  postgres:
    image: postgres:12-alpine
    container_name: temporal-postgres
    environment:
      - POSTGRES_USER=temporal
      - POSTGRES_PASSWORD=temporal
      - POSTGRES_DB=temporal
    networks: [temporal-net]
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "temporal"]
      interval: 5s
      timeout: 3s
      retries: 10

  # ───────── Temporal Server (auto-setup) ─────
  temporal:
    image: temporalio/auto-setup:1.28.0          # any 1.24+ is fine
    container_name: temporal
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DB=postgres12
      - DB_PORT=5432
      - POSTGRES_SEEDS=postgres                 # host of DB container :contentReference[oaicite:0]{index=0}
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - TEMPORAL_CLI_ADDRESS=temporal:7233
    ports:
      - "7233:7233"                              # gRPC / SDK
    networks: [temporal-net]
    healthcheck:
      test: ["CMD-SHELL", "tctl --address temporal:7233 --ns default namespace list >/dev/null 2>&1 || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 10


  # ───────── Temporal Web UI (stand-alone) ────
  temporal-ui:
    image: temporalio/ui:2.39.0                  # latest at time of writing :contentReference[oaicite:1]{index=1}
    container_name: temporal-ui
    depends_on:
      temporal:
        condition: service_healthy
    environment:
      - TEMPORAL_ADDRESS=temporal:7233           # tell UI where the server lives
    ports:
      - "8080:8080"                              # http://localhost:8080
    networks: [temporal-net]

    # ───────── Worker (Python) ───────────────────
  worker:
    build: ./longRunningCounterWorkflow
    volumes:
      - ./longRunningCounterWorkflow:/app
    depends_on:
      temporal:
        condition: service_healthy
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
    # command: ["python", "-u", "worker.py"]
    networks: [temporal-net]
```

### Step 3: Examine the Counter Workflow

The existing `longRunningCounterWorkflow/counter_workflow.py` demonstrates signals and queries:

```python
from temporalio import workflow
from datetime import timedelta

@workflow.defn(name="CounterWorkflow")
class CounterWorkflow:
    def __init__(self):
        self.count = 0

    @workflow.run
    async def run(self) -> int:
        """
        Long-running workflow that maintains state and responds to signals.
        This workflow runs indefinitely, demonstrating persistent state management.
        """
        while True:
            # Sleep for 10 seconds between status updates
            await workflow.sleep(timedelta(seconds=10))
            
            # Print current status (only when not replaying)
            if not workflow.unsafe.is_replaying():
                print(f"Current count: {self.count}")

    @workflow.signal
    async def increment(self) -> None:
        """
        Signal handler to increment the counter.
        Signals allow external systems to send data to running workflows.
        """
        self.count += 1
        if not workflow.unsafe.is_replaying():
            print(f"🔔 Signal received! Count incremented to: {self.count}")

    @workflow.query
    def get_count(self) -> int:
        """
        Query handler to retrieve current counter value.
        Queries allow external systems to read workflow state without modification.
        """
        return self.count
```

#### Key Concepts Demonstrated

| Component | Purpose | Code Pattern |
|-----------|---------|--------------|
| **Long-running Loop** | Keeps workflow alive indefinitely | `while True:` with `workflow.sleep()` |
| **Signal Handler** | Receives external commands | `@workflow.signal` decorator |
| **Query Handler** | Provides state access | `@workflow.query` decorator |
| **State Management** | Maintains workflow state | Instance variable `self.count` |
| **Replay Safety** | Prevents duplicate logging | `workflow.unsafe.is_replaying()` check |

### Step 4: Examine the Worker Service

The `longRunningCounterWorkflow/worker.py` registers the workflow:

```python
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

# Import the workflow
from counter_workflow import CounterWorkflow

async def main():
    """Worker that processes long-running counter workflows."""
    
    # Connect to Temporal server
    client = await Client.connect("temporal:7233", namespace="default")
    
    # Create worker with counter workflow
    worker = Worker(
        client,
        task_queue="long-running-counter-task-queue",
        workflows=[CounterWorkflow],
    )
    
    print("🔄 Long-running Counter Worker started!")
    print("📋 Listening on task queue: long-running-counter-task-queue")
    print("🎯 Ready to process counter workflows...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 5: Deploy and Configure Load Balancer

```bash
# Build and start services
docker-compose up --build -d

# Verify containers are running
docker-compose ps

# Check worker logs
docker-compose logs -f worker
```

#### Configure Load Balancer
1. Get your lab instance IP: `ifconfig eth0`
2. **Create Load Balancer** in Poridhi Lab interface:
   - **Enter IP**: Your lab instance eth0 IP address
   - **Enter Port**: `8233`
3. **Click Create**

### Step 6: Start the Counter Workflow

```bash
# Start the counter workflow
docker-compose exec worker python start_workflow.py
```

The workflow will start and you should see output like:
```
🚀 Starting CounterWorkflow...
📋 Workflow ID: counter-workflow-1703845200
✅ Workflow started successfully!
Current count: 0
Current count: 0
...
```

**Important**: Note the **Workflow ID** from the output - you'll need it for sending signals and queries!

### Step 7: Access Web UI and Monitor Workflow

1. **Open Temporal Web UI**: Use your load balancer URL
2. **Navigate to Workflows**: Click "Workflows" in sidebar
3. **Find Your Workflow**: Look for the CounterWorkflow
4. **Observe the Running State**: The workflow should show as "Running"

#### What to Look For in Web UI
- **Status**: Running (green)
- **Run ID**: Unique execution identifier
- **Task Queue**: `long-running-counter-task-queue`
- **History**: Shows workflow started event

### Step 8: Send Signals to the Workflow

#### Using Temporal CLI
```bash
# Replace <workflow-id> with your actual workflow ID
export WORKFLOW_ID="counter-workflow-1703845200"

# Send increment signal
docker-compose exec temporal temporal workflow signal \
  --workflow-id $WORKFLOW_ID \
  --name increment \
  --namespace default

# Send multiple signals
docker-compose exec temporal temporal workflow signal \
  --workflow-id $WORKFLOW_ID \
  --name increment \
  --namespace default

docker-compose exec temporal temporal workflow signal \
  --workflow-id $WORKFLOW_ID \
  --name increment \
  --namespace default
```

#### Observe Signal Effects
After sending signals, check the worker logs:
```bash
docker-compose logs -f worker
```

You should see:
```
🔔 Signal received! Count incremented to: 1
🔔 Signal received! Count incremented to: 2
🔔 Signal received! Count incremented to: 3
Current count: 3
```

### Step 9: Query Workflow State

#### Get Current Counter Value
```bash
# Query the current count
docker-compose exec temporal temporal workflow query \
  --workflow-id $WORKFLOW_ID \
  --type get_count \
  --namespace default
```

Expected output:
```
Query result: 3
```

#### Multiple Queries
```bash
# Send more signals
docker-compose exec temporal temporal workflow signal \
  --workflow-id $WORKFLOW_ID \
  --name increment \
  --namespace default

# Query again to see updated count
docker-compose exec temporal temporal workflow query \
  --workflow-id $WORKFLOW_ID \
  --type get_count \
  --namespace default
```

### Step 10: Observe in Web UI

#### Signal and Query Events
1. **Refresh the Web UI**
2. **Click on your workflow**
3. **Examine the Timeline**: You should see:
   - **WorkflowTaskScheduled** events
   - **WorkflowTaskCompleted** events
   - **Signal** events for each increment
   - **Query** events for each state request

## Event History
![signal](./event-history.png?raw=true)


#### Workflow Details
- **Input and Results**: Shows workflow parameters
- **Timeline**: Complete history of events
- **Query Results**: Shows latest query responses
- **Signals Sent**: List of all signals received

## 🔍 Understanding Signals and Queries

### Signal Behavior Analysis

#### What You Should Observe
- **Immediate Processing**: Signals are processed as soon as the workflow task runs
- **Durable State**: Counter value persists even if containers restart
- **Ordered Processing**: Signals are processed in the order they're sent
- **Event History**: All signals appear in the workflow timeline

#### Signal Flow
```
CLI Command → Temporal Server → Workflow Task → Signal Handler → State Update
```

### Query Behavior Analysis

#### Query Characteristics
- **Immediate Response**: Queries return current state without delay
- **No State Change**: Queries don't modify workflow state
- **Consistent Reads**: Always returns current workflow state
- **No History Impact**: Queries don't appear in workflow execution history

#### Query vs Signal Comparison

| Aspect | Signals | Queries |
|--------|---------|---------|
| **Purpose** | Modify state | Read state |
| **Response** | Asynchronous (fire-and-forget) | Synchronous (immediate response) |
| **Durability** | Persisted in history | Not persisted |
| **Side Effects** | Can change workflow state | Read-only |
| **Performance** | Queued with workflow tasks | Immediate execution |

## 🧪 Experimentation

### Try These Variations

#### 1. Send Rapid Signals
```bash
# Send many signals quickly
for i in {1..10}; do
  docker-compose exec temporal temporal workflow signal \
    --workflow-id $WORKFLOW_ID \
    --name increment \
    --namespace default
  echo "Sent signal #$i"
done

# Query the result
docker-compose exec temporal temporal workflow query \
  --workflow-id $WORKFLOW_ID \
  --type get_count \
  --namespace default
```

#### 2. Create Additional Signal Handlers
Add to `counter_workflow.py`:
```python
@workflow.signal
async def decrement(self) -> None:
    """Signal to decrement the counter."""
    self.count = max(0, self.count - 1)  # Don't go below 0
    if not workflow.unsafe.is_replaying():
        print(f"🔔 Count decremented to: {self.count}")

@workflow.signal  
async def reset(self) -> None:
    """Signal to reset the counter."""
    self.count = 0
    if not workflow.unsafe.is_replaying():
        print(f"🔔 Counter reset to: {self.count}")
```

#### 3. Add More Query Types
```python
@workflow.query
def get_status(self) -> str:
    """Query to get workflow status information."""
    return f"Counter at {self.count}, workflow running for {self.get_runtime()}"

@workflow.query
def is_even(self) -> bool:
    """Query to check if counter is even."""
    return self.count % 2 == 0
```

#### 4. Test Signal Parameters
```python
@workflow.signal
async def add_value(self, value: int) -> None:
    """Signal to add a specific value to the counter."""
    self.count += value
    if not workflow.unsafe.is_replaying():
        print(f"🔔 Added {value}, count now: {self.count}")
```

Send with parameters:
```bash
# Send signal with parameter (requires JSON input)
docker-compose exec temporal temporal workflow signal \
  --workflow-id $WORKFLOW_ID \
  --name add_value \
  --input '5' \
  --namespace default
```

## 🔧 Troubleshooting

### Common Issues

#### Workflow Not Receiving Signals
```bash
# Check if workflow is running
docker-compose exec temporal temporal workflow describe \
  --workflow-id $WORKFLOW_ID \
  --namespace default

# Verify signal name spelling
docker-compose exec temporal temporal workflow signal \
  --workflow-id $WORKFLOW_ID \
  --name increment \
  --namespace default
```

#### Query Not Returning Data
```bash
# Check query type name
docker-compose exec temporal temporal workflow query \
  --workflow-id $WORKFLOW_ID \
  --type get_count \
  --namespace default

# List available queries
docker-compose exec temporal temporal workflow describe \
  --workflow-id $WORKFLOW_ID \
  --namespace default
```

#### Worker Not Processing
```bash
# Check worker logs
docker-compose logs worker

# Restart worker if needed
docker-compose restart worker
```

## 🧹 Cleanup

### Stop the Long-Running Workflow
```bash
# Terminate the workflow
docker-compose exec temporal temporal workflow terminate \
  --workflow-id $WORKFLOW_ID \
  --reason "Lab completed" \
  --namespace default

# Stop all services
docker-compose down

# Clean up resources
docker-compose down -v
docker system prune -a
```

**Remove Load Balancer**: Delete the load balancer configuration in Poridhi Lab interface.

## 🎓 Key Takeaways

- **Signals** enable real-time communication with running workflows without interrupting execution
- **Queries** provide immediate access to workflow state for monitoring and dashboards
- **Long-running workflows** can maintain state indefinitely and respond to external events
- **Temporal CLI** provides powerful tools for interacting with workflows in development and production
- **Durable state** ensures workflow data persists across restarts and failures
- **Event sourcing** means all signals and state changes are recorded in workflow history
- **Interactive patterns** enable building responsive, event-driven applications

## 🚀 Next Steps

- **Lab 5**: Explore parent-child workflow relationships and workflow composition
- **Advanced**: Implement workflow cancellation and timeout patterns
- **Production**: Add monitoring and alerting for workflow signals and queries
- **Integration**: Connect workflows to external APIs and user interfaces

## 📚 Additional Resources

- [Temporal Signals Documentation](https://docs.temporal.io/concepts/what-is-a-signal)
- [Temporal Queries Documentation](https://docs.temporal.io/concepts/what-is-a-query)
- [Long-Running Workflow Patterns](https://docs.temporal.io/application-development/foundations#long-running-workflows)
- [CLI Reference Guide](https://docs.temporal.io/cli/workflow)