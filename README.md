# My Cloud Infrastructure and Configuration as Code Library

This repo contains a combination of Infrastructure as Code (Pulumi) and Configuration as Code (Ansible) to deploy standardized cloud resources.

## Cloud IaC Components

Reusable Pulumi Python components for deploying standardized resources.

### How to Use?

#### Installation

Add the library to your Pulumi Python project using `uv`. Replace `@v0.1.0` with the desired version tag.

```bash
uv add "git+https://github.com/pablordoricaw/my-cloud-lib.git@v0.1.0#subdirectory=pulumi"
```

#### Usage Example

Deploy a standard Ubuntu development VM with optional GPU support and default network/subnet configuration.

```python
import pulumi
from my_components.compute import MyInstance, MyInstanceArgs

# Deploy a standard student VM
vm = MyInstance("dev-box", MyInstanceArgs(
    region="us-east1",
    zone="b",
    tags=["dev-env"],
    ubuntu_version="24.04",       # Options: "2204", "24.04"
    machine_type="n2-standard-4",
    gpu_type="nvidia-t4",         # Optional: Attaches GPU & sets Spot scheduling
    gpu_count=1
))

pulumi.export("vm_ip", vm.public_ipv4)
```

### Available Components

| Component | Description | Key Features |
| --- | --- | --- |
| `MyInstance` | Ubuntu GCP Compute Instance | <ul><li>GPU support</li><li>Deploy in default or in specified network/subnet</li></ul> |


## Cloud Configuration

The cloud configuration is a set of Ansible playbooks.
