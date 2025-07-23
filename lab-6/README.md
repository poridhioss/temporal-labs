# 🛰️ Lab 6: Cron Scheduling & External Triggers

**Goal:** Build external integration systems with automated scheduling.

- Define cron-scheduled workflows for automated execution
- Create HTTP endpoints for external system integration
- Use signals for real-time communication with running workflows
- Implement multi-trigger workflow architectures
- Handle external events and webhook integrations

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
With your environment set up, you’re now ready to explore even more powerful features of Temporal. In this lab, you’ll work with cron workflows to automate recurring tasks and see how Temporal handles scheduled executions. This will deepen your understanding of Temporal’s scheduling capabilities and how to build robust, time-based automation.

# Lab 6: Cron Scheduling & External Triggers

**Goal:** Build sophisticated external integration systems using cron scheduling, HTTP triggers, and real-time signal communication.

## Features
- Define cron-scheduled workflows for automated execution
- Create HTTP endpoints for external system integration
- Use signals for real-time communication with running workflows
- Implement multi-trigger workflow architectures
- Handle external events and webhook integrations
- Manage schedule lifecycle programmatically

## Quick Start

1. **Start Services:**
   ```bash
   docker-compose up --build
   ```

2. **Access Services:**
   - **Temporal Web UI**: [http://localhost:8233](http://localhost:8233)
   - **FastAPI Interface**: [http://localhost:8000](http://localhost:8000)

3. **Test HTTP Trigger:**
   ```bash
   curl -X POST "http://localhost:8000/trigger-workflow/test-001?name=Quick%20Start"
   ```

4. **Create Cron Schedule:**
   ```bash
   curl -X POST "http://localhost:8000/schedule-workflow/test-schedule?cron=*/1%20*%20*%20*%20*"
   ```

## How it Works
- FastAPI service provides HTTP endpoints for external integration
- Workflows can be triggered via HTTP requests, cron schedules, or CLI commands
- Running workflows receive real-time signals from external systems
- Schedule management enables automated recurring workflow execution
- Multiple trigger types allow flexible integration patterns

## 🎯 Learning Objectives

By the end of this lab, you will be able to:
- **Master cron scheduling**: Create and manage automated recurring workflows with precise timing control
- **Build HTTP integrations**: Design REST APIs that bridge external systems with Temporal workflows
- **Implement real-time signals**: Enable external systems to communicate with running workflows asynchronously
- **Design multi-trigger architectures**: Create workflows that can be started through multiple different mechanisms
- **Handle external events**: Process webhooks, API calls, and other external triggers in workflow systems
- **Manage schedule lifecycles**: Programmatically create, modify, pause, and delete workflow schedules

## 📚 Background

### Why External Integration Matters

Modern applications exist in **complex ecosystems** where workflows must interact with multiple external systems, respond to real-time events, and execute on predetermined schedules. External integration capabilities are essential for building production-ready workflow systems.

### Workflow Integration Benefits

#### Multi-Modal Triggering
- **Flexibility**: Workflows can be started via HTTP, schedules, CLI, or other workflows
- **External Coupling**: External systems can initiate workflows without direct temporal knowledge
- **Event-Driven Architecture**: Respond to external events as they occur
- **Hybrid Patterns**: Combine scheduled and event-driven execution in single workflows

#### Real-Time Communication
- **Asynchronous Signals**: External systems send data without blocking workflow execution
- **Dynamic Behavior**: Workflows adapt based on incoming external events
- **Bidirectional Flow**: Workflows can query external systems and receive updates
- **Event Aggregation**: Collect multiple external events before processing

#### Automated Scheduling
- **Cron Precision**: Execute workflows at specific times using familiar cron syntax
- **Reliable Execution**: Built-in retry mechanisms for failed scheduled executions
- **Schedule Management**: Create, modify, and delete schedules programmatically
- **Timezone Handling**: Proper handling of timezone-aware scheduling

#### Production Integration
- **API Endpoints**: RESTful interfaces for external system communication
- **Webhook Support**: Handle incoming webhooks from external services
- **Authentication**: Secure integration with proper access control
- **Monitoring**: Track external triggers and schedule execution

### Real-World Applications

#### E-commerce Order Processing
```
External Event: Customer places order via web app
├── HTTP Trigger: Start order fulfillment workflow
├── Signal: Inventory system sends stock updates
├── Signal: Payment gateway sends transaction status
└── Cron Schedule: Daily order summary reports
```

#### DevOps Pipeline Automation
```
External Event: Code push to repository
├── Webhook: GitHub triggers deployment workflow
├── Signal: Build system sends compilation results
├── Signal: Testing framework sends test outcomes
└── Cron Schedule: Nightly backup and cleanup workflows
```

#### Financial Data Processing
```
External Event: Market data feed updates
├── HTTP Trigger: Portfolio rebalancing workflow
├── Signal: Risk system sends threshold alerts
├── Signal: Compliance system sends audit requirements
└── Cron Schedule: End-of-day reconciliation reports
```

#### IoT Device Management
```
External Event: Sensor threshold exceeded
├── HTTP Trigger: Alert processing workflow
├── Signal: Device management system sends status updates
├── Signal: Maintenance system sends service schedules
└── Cron Schedule: Hourly device health monitoring
```

### Architecture Patterns
#### Pattern 1: HTTP Trigger (On-Demand)
```
User/System → HTTP Request → FastAPI → Starts Workflow
  "Process this order"        ↓
                        Temporal Workflow
                        "Order processing..."
```

#### Pattern 2: Cron Schedule (Time-Based)
```
Clock → Every 5 minutes → Temporal Scheduler → Starts Workflow
     "It's time!"                     ↓
                               Temporal Workflow
                               "Daily report..."
```

#### Pattern 3: Signal Communication (Real-Time)
```
External System → HTTP Request → FastAPI → Sends Signal → Running Workflow
  "Update status"              ↓                    ↓
                        "Signal sent"      "Got the update!"
```

#### Pattern 4: Multi-Trigger (Flexible)
```
Same Workflow Can Be Started By:
├── HTTP Request (immediate)
├── Cron Schedule (automatic)
├── Signal Input (while running)
└── Manual CLI (testing)
```

## 🛠 Prerequisites

### Poridhi Lab Environment:
- Completion of **Lab 5** (Parent-Child Workflows)
- Access to Poridhi Lab with VS Code interface
- **Docker & Docker Compose**: ✅ Pre-installed in Poridhi Lab
- **Web Browser**: For accessing Temporal Web UI and FastAPI interface through load balancer
- **Understanding**: Knowledge of workflows, signals, and HTTP APIs

### Verify Prerequisites
```bash
# Open VS Code terminal and verify setup
cd lab-6
docker --version
docker-compose --version
curl --version
```

## 📁 Project Structure

You'll work with the following structure in your lab-6 directory:

```
lab-6/
├── docker-compose.yml          # Multi-service configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                 # Container configuration
└── app/
    ├── __init__.py            # Package initialization
    ├── cronWorkflow.py        # Signal-enabled workflow with cron support
    ├── main.py               # FastAPI endpoints for external integration
    ├── worker.py             # Worker service
    ├── activity.py           # Activity definitions
    └── Dockerfile            # App-specific container config
```

## 🚀 Lab Implementation

### Step 1: Set Up Project Structure

Open VS Code terminal in Poridhi Lab and navigate to your lab-6 directory:

```bash
# Navigate to lab-6 directory
cd lab-6

# Verify the app directory exists
ls -la app/
```

### Step 2: Understand the Docker Configuration

The `docker-compose.yml` configures a multi-service architecture:

```yaml
version: '3.8'

services:
  temporal:
    image: temporalio/admin-tools:latest
    ports:
      - "7233:7233"  # Temporal Server gRPC
      - "8233:8233"  # Web UI
    entrypoint: []
    command: ["temporal", "server", "start-dev", "--ui-port", "8233", "--ip", "0.0.0.0"]
    networks:
      - temporal-net     # attach to the shared network

  worker:
    build: .
    command: ["python", "-u", "worker.py"]
    volumes:
      - ./app:/app/
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - TASK_QUEUE=cron-task-queue
    depends_on:
      - temporal
    networks:
      - temporal-net     # attach to the shared network

  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    volumes:
      - ./app:/app/
    ports:
      - "8000:8000"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
    depends_on:
      - temporal
    networks:
      - temporal-net     # attach to the shared network

networks:
  temporal-net:          # declares the network so Docker Compose creates it
    driver: bridge       # default driver (could omit—bridge is the default)
```

### Step 3: Examine the Signal-Enabled Workflow Implementation

The `app/cronWorkflow.py` demonstrates multi-trigger workflow architecture:

```python
# shared/workflow.py
from datetime import timedelta
from temporalio import workflow

@workflow.defn
class CronWorkflow:  # Better name - describes what it does
    def __init__(self):
        self.messages = []        # Collect signals from external systems
        self.should_stop = False  # External stop control
    
    @workflow.signal
    async def add_message(self, message: str):
        """External services can send data via this signal"""
        self.messages.append(message)
    
    @workflow.signal  
    async def stop_processing(self):
        """External services can stop the workflow"""
        self.should_stop = True
    
    @workflow.run
    async def run(self, task_name: str) -> dict:
        """
        This workflow can be:
        1. Scheduled with cron (e.g., daily at 9am)
        2. Triggered manually via HTTP
        3. Receive signals while running
        """
        workflow.logger.info(f"Processing task: {task_name}")
        
        # Wait for signals or timeout
        await workflow.wait_condition(
            lambda: self.should_stop or len(self.messages) >= 5,
            timeout=timedelta(seconds=30)
        )   
        
        # Process collected messages
        processed_count = len(self.messages)
        
        return {
            "task": task_name,
            "messages_processed": processed_count,
            "messages": self.messages,
            "completed_at": str(workflow.now())
        }
```

#### Key Concepts Demonstrated

| Component | Purpose | Code Pattern |
|-----------|---------|--------------|
| **Signal Handlers** | External system communication | `@workflow.signal` for `add_message` and `stop_processing` |
| **Event Aggregation** | Collect multiple external events | `wait_condition()` with threshold (`>= 5`) or timeout (`30s`) |
| **Graceful Termination** | External stop control | `should_stop` flag controlled by signal |
| **Multi-Trigger Support** | Various initiation methods | HTTP, cron, CLI triggers for same workflow |
| **Simple Message Storage** | Collect signals from external systems | `self.messages.append(message)` |
| **Conditional Processing** | Wait for events or timeout | `lambda: self.should_stop or len(self.messages) >= 5` |

### Step 4: Examine the FastAPI Integration Service

The `app/main.py` provides HTTP endpoints for external integration:

```python
# api/main.py
from fastapi import FastAPI, HTTPException
from temporalio.client import Client
from cronWorkflow import CronWorkflow
from datetime import datetime

app = FastAPI()
client = None

@app.on_event("startup")
async def startup():
    import os
    global client
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")
    client = await Client.connect(temporal_address)

# 1. Regular HTTP trigger
@app.post("/trigger-workflow/{workflow_id}")
async def trigger_workflow(workflow_id: str, name: str = "HTTP Triggered"):
    """Trigger workflow from HTTP endpoint"""
    try:
        handle = await client.start_workflow(
            CronWorkflow.run,
            name,
            id=workflow_id,  
            task_queue="lab6-queue",
        )
        return {"workflow_id": handle.id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 2. Create cron schedule
@app.post("/schedule-workflow/{schedule_id}")
async def schedule_workflow(schedule_id: str, cron: str = "* * * * *"):
    """Schedule workflow with cron expression"""
    
    try:
        from datetime import datetime
        from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec

        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    CronWorkflow.run,
                    "Cron Triggered",
                    id=f"cron-{datetime.now().timestamp()}",
                    task_queue="lab6-queue",
                ),
                spec=ScheduleSpec(
                    cron_expressions=[cron],
                ),
            ),
        )
        return {"schedule_id": schedule_id, "cron": cron, "status": "scheduled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/schedule-workflow/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete (stop) a cron schedule"""
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()
        return {"schedule_id": schedule_id, "status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# 3. Signal workflow from external service
@app.post("/signal-workflow/{workflow_id}")
async def signal_workflow(workflow_id: str, message: str):
    """Send signal to running workflow"""
    try:
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(CronWorkflow.add_message, message)
        return {"workflow_id": workflow_id, "signal": "sent", "message": message}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/stop-workflow/{workflow_id}")
async def stop_workflow(workflow_id: str):
    """Send stop signal to workflow"""
    try:
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(CronWorkflow.stop_processing)
        return {"workflow_id": workflow_id, "signal": "stop sent"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/workflow-result/{workflow_id}")
async def get_result(workflow_id: str):
    """Get workflow result"""
    try:
        handle = client.get_workflow_handle(workflow_id)
        result = await handle.result()
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Step 5: Deploy and Configure Load Balancer

```bash
# Build and start all services
docker-compose up --build -d

# Verify all containers are running
docker-compose ps

# Check service logs
docker-compose logs -f api
docker-compose logs -f worker
```

#### Configure Load Balancer
1. Get your lab instance IP: `ifconfig eth0`
2. **Create Load Balancer for Temporal Web UI**:
   - **Enter IP**: Your lab instance eth0 IP address
   - **Enter Port**: `8233`
   - **Click Create**
3. **Create Load Balancer for FastAPI**:
   - **Enter IP**: Your lab instance eth0 IP address
   - **Enter Port**: `8000`
   - **Click Create**

### Step 6: Test HTTP Workflow Triggers

Test direct workflow triggering via HTTP endpoints:

```bash
# Trigger a workflow with custom parameters
curl -X POST "http://localhost:8000/trigger-workflow/http-test-001?name=HTTP%20Integration%20Test"

# Verify response contains workflow details
# Expected: {"workflow_id": "http-test-001", "status": "started"}
```

**Important**: Note the **Workflow ID** for monitoring in the Web UI!

### Step 7: Implement Cron Scheduling

Create automated recurring workflows:

```bash
# Create a schedule that runs every minute
curl -X POST "http://localhost:8000/schedule-workflow/every-minute?cron=*%20*%20*%20*%20*"

# Create a schedule that runs every 5 minutes
curl -X POST "http://localhost:8000/schedule-workflow/every-5-min?cron=*/5%20*%20*%20*%20*"

# Create a schedule for business hours (9 AM - 5 PM, weekdays)
curl -X POST "http://localhost:8000/schedule-workflow/business-hours?cron=0%209-17%20*%20*%201-5"

# Expected response: {"schedule_id": "every-minute", "cron": "* * * * *", "status": "scheduled"}
```

### Step 8: Test Real-Time Signal Communication

Test dynamic signal sending to running workflows:

```bash
# Start a long-running workflow
curl -X POST "http://localhost:8000/trigger-workflow/signal-test-001?name=Signal%20Communication%20Test"

# Send multiple messages to the running workflow
curl -X POST "http://localhost:8000/signal-workflow/signal-test-001?message=First%20external%20event%20from%20API"

curl -X POST "http://localhost:8000/signal-workflow/signal-test-001?message=Second%20external%20event%20from%20API"

curl -X POST "http://localhost:8000/signal-workflow/signal-test-001?message=Third%20external%20event%20from%20API"

# Check workflow status
curl -X GET "http://localhost:8000/workflow-result/signal-test-001"

# Expected signal response: {"workflow_id": "signal-test-001", "signal": "sent", "message": "First external event from API"}
```

### Step 9: Monitor in Web UI

1. **Open Temporal Web UI**: Use your load balancer URL (port 8233)
2. **Navigate to Workflows**: Click "Workflows" in sidebar
3. **Find HTTP-Triggered Workflows**: Look for workflows with your custom IDs
4. **Navigate to Schedules**: Click "Schedules" in sidebar
5. **Monitor Schedule Execution**: View schedule triggers and executions

#### What to Look For in Web UI

##### Workflow Execution View
- **Trigger Type**: HTTP-triggered vs Cron-triggered workflows
- **Signal Events**: SignalReceived events in workflow history
- **Query Events**: External status checks
- **Execution Duration**: Time from start to completion

##### Schedule Management View
- **Schedule Status**: Active, paused, or deleted schedules
- **Next Execution**: Upcoming schedule triggers
- **Execution History**: Past schedule-triggered workflows
- **Cron Expression**: Configured scheduling patterns

### Step 10: Test Schedule Lifecycle Management

Test complete schedule management:

```bash
# Create a test schedule
curl -X POST "http://localhost:8000/schedule-workflow/lifecycle-test?cron=*/2%20*%20*%20*%20*"

# Wait for schedule to trigger (2 minutes)
sleep 130

# Check for triggered workflows in Web UI
# Look for workflows with name "Cron Triggered"

# Delete the schedule
curl -X DELETE "http://localhost:8000/schedule-workflow/lifecycle-test"

# Verify schedule is deleted
docker-compose exec temporal temporal schedule list | grep lifecycle-test || echo "Schedule successfully deleted"
```

## 🔍 Understanding External Integration Patterns

### Multi-Trigger Architecture Analysis

#### Integration Benefits
- **Flexible Initiation**: Multiple ways to start the same workflow logic
- **External Decoupling**: External systems don't need Temporal knowledge
- **Event Aggregation**: Collect and process multiple external events
- **Real-Time Response**: Immediate reaction to external triggers

#### Trigger Type Comparison
```
HTTP Trigger     ├─ Immediate execution
                 ├─ External system initiated
                 ├─ Request-response pattern
                 └─ On-demand processing

Cron Schedule    ├─ Time-based execution
                 ├─ System initiated
                 ├─ Recurring pattern
                 └─ Automated processing

Signal Input     ├─ Real-time communication
                 ├─ External event driven
                 ├─ Asynchronous pattern
                 └─ Dynamic behavior
```

### Signal Communication Strategies

#### Event Aggregation Techniques

| Technique | Implementation | Use Case |
|-----------|----------------|----------|
| **Threshold-Based** | `len(messages) >= 5` | Batch processing |
| **Time-Based** | `timeout=timedelta(seconds=30)` | Maximum wait time |
| **Signal-Based** | `should_stop` flag | External control |
| **Condition-Based** | `wait_condition()` | Complex logic |

#### Communication Patterns
- **Fire-and-Forget**: Send signal without waiting for response
- **Request-Response**: Send signal and wait for workflow completion
- **Publish-Subscribe**: Multiple workflows receive same signal
- **Event Sourcing**: Signals become part of workflow history

## 🧪 Experimentation

### Try These Variations

#### 1. Complex Cron Schedules
Test advanced scheduling patterns:
```bash
# Every weekday at 9 AM
curl -X POST "http://localhost:8000/schedule-workflow/weekday-morning?cron=0%209%20*%20*%201-5"

# Every 15 minutes during business hours
curl -X POST "http://localhost:8000/schedule-workflow/business-frequent?cron=*/15%209-17%20*%20*%201-5"

# First day of every month at midnight
curl -X POST "http://localhost:8000/schedule-workflow/monthly-report?cron=0%200%201%20*%20*"
```

#### 2. Batch Signal Processing
Modify workflow to process signals in batches:
```python
@workflow.run
async def run(self, task_name: str) -> dict:
    while not self.should_stop:
        # Wait for batch of messages
        await workflow.wait_condition(
            lambda: len(self.messages) >= 10 or self.should_stop,
            timeout=timedelta(minutes=5)
        )
        
        # Process batch
        if self.messages:
            batch = self.messages[:10]
            self.messages = self.messages[10:]
            await workflow.execute_activity("process_batch", batch)
```

#### 3. Multi-Workflow Coordination
Create workflows that signal other workflows:
```python
@workflow.run
async def coordinator_workflow(self, child_workflow_ids: list) -> dict:
    # Start child workflows
    for workflow_id in child_workflow_ids:
        await client.start_workflow(
            CronWorkflow.run,
            f"Child {workflow_id}",
            id=workflow_id,
            task_queue="lab6-queue"
        )
    
    # Signal all children
    for workflow_id in child_workflow_ids:
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(CronWorkflow.add_message, "Coordinator message")
```

#### 4. Webhook Integration
Add webhook endpoints to FastAPI service:
```python
@app.post("/webhook/github")
async def github_webhook(payload: dict):
    """Handle GitHub webhook"""
    if payload.get("action") == "push":
        workflow_id = f"deploy-{payload['repository']['name']}"
        await client.start_workflow(
            CronWorkflow.run,
            f"Deploy {payload['repository']['name']}",
            id=workflow_id,
            task_queue="lab6-queue"
        )
    return {"status": "processed"}
```

### Performance Testing

#### Load Testing HTTP Triggers
```bash
# Test concurrent HTTP triggers
for i in {1..10}; do
  curl -X POST "http://localhost:8000/trigger-workflow/load-test-$i?name=Load%20Test%20$i" &
done
wait
```

#### High-Frequency Scheduling
```bash
# Test frequent schedule (every 30 seconds)
curl -X POST "http://localhost:8000/schedule-workflow/high-freq?cron=*/30%20*%20*%20*%20*"

# Monitor worker performance
docker-compose logs -f worker
```

## 🔧 Troubleshooting

### Common Issues

#### HTTP Endpoints Not Responding
```bash
# Check FastAPI service status
docker-compose logs api

# Verify service is running
curl http://localhost:8000/

# Check port binding
docker-compose ps api
```

#### Schedules Not Triggering
```bash
# List all schedules
docker-compose exec temporal temporal schedule list

# Check specific schedule
docker-compose exec temporal temporal schedule describe --schedule-id <schedule-id>

# Verify cron expression
echo "*/5 * * * *" | curl -X POST "http://localhost:8000/schedule-workflow/test-cron?cron=$(cat)"
```

#### Signals Not Reaching Workflows
```bash
# Check if workflow is running
curl http://localhost:8000/workflow-result/<workflow-id>

# Verify signal in Web UI
# Navigate to workflow → History → Look for SignalReceived events

# Check worker logs
docker-compose logs worker | grep signal
```

#### Worker Overload
```bash
# Monitor worker performance
docker-compose exec worker top

# Check concurrent workflow count
docker-compose exec temporal temporal workflow list --namespace default | wc -l
```

## 🧹 Cleanup

```bash
# Stop all running workflows
docker-compose exec temporal temporal workflow terminate \
  --workflow-id signal-test-001 \
  --reason "Lab completed" \
  --namespace default

# Delete all schedules
curl -X DELETE "http://localhost:8000/schedule-workflow/every-minute"
curl -X DELETE "http://localhost:8000/schedule-workflow/every-5-min"
curl -X DELETE "http://localhost:8000/schedule-workflow/business-hours"

# Stop all services
docker-compose down

# Clean up resources
docker-compose down -v
docker system prune -a
```

**Remove Load Balancers**: Delete both load balancer configurations (ports 8233 and 8000) in Poridhi Lab interface.

## 🎓 Key Takeaways

- **Multi-Modal Integration** enables workflows to be triggered through HTTP, schedules, signals, and other mechanisms
- **Real-Time Communication** through signals allows external systems to dynamically influence running workflows
- **Cron Scheduling** provides reliable, timezone-aware automated workflow execution
- **HTTP APIs** create bridges between external systems and Temporal workflows
- **Event Aggregation** patterns enable workflows to collect and process multiple external events
- **Schedule Lifecycle Management** allows programmatic control of automated workflow execution
- **External System Decoupling** enables integration without requiring Temporal knowledge in external systems

## 🚀 Next Steps

- **Advanced Scheduling**: Implement complex scheduling patterns with timezone handling
- **Webhook Integration**: Build comprehensive webhook handlers for external services
- **Authentication & Security**: Add proper authentication and authorization to HTTP endpoints
- **Monitoring & Observability**: Implement comprehensive monitoring for external integrations
- **Error Handling**: Add sophisticated error handling and retry mechanisms
- **Performance Optimization**: Optimize for high-throughput external integration scenarios

## 📚 Additional Resources

- [Temporal Cron Scheduling](https://docs.temporal.io/concepts/what-is-a-schedule)
- [Temporal Signals](https://docs.temporal.io/concepts/what-is-a-signal)
- [External Integration Patterns](https://docs.temporal.io/application-development/foundations#external-systems)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Cron Expression Guide](https://crontab.guru/)