from typing import Optional, List, Dict, Any

import pulumi
import pulumi_gcp as gcp


@pulumi.input_type
class MyInstanceArgs:
    region: pulumi.Input[str]
    zone: pulumi.Input[str]

    tags: pulumi.Input[List[str]]

    machine_type: pulumi.Input[str] = "n2-standard-4"
    ubuntu_version: pulumi.Input[str] = "2204"

    disk_size: Optional[pulumi.Input[int]] = 50

    network_id: Optional[pulumi.Input[str]] = None
    subnet_id: Optional[pulumi.Input[str]] = None

    gpu_type: Optional[pulumi.Input[str]] = None
    gpu_count: Optional[pulumi.Input[int]] = None


class MyInstance(pulumi.ComponentResource):
    instance: gcp.compute.Instance

    instance_name: pulumi.Output[str]
    public_ipv4: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        args: MyInstanceArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("my-components:compute:MyInstance", name, {}, opts)

        def get_image(version: str) -> str:
            v = str(version).lower()
            base = "projects/ubuntu-os-cloud/global/images/"
            if v in ["2404", "24.04"]:
                return base + "ubuntu-2404-noble-amd64-v20260117"
            return base + "ubuntu-2204-jammy-v20260114"

        _image = pulumi.Output.from_input(args.ubuntu_version).apply(get_image)

        _zone = pulumi.Output.concat(args.region, "-", args.zone)

        def get_network_interfaces(args_list: List[Any]) -> List[Dict[str, Any]]:
            net_id, subnet_id = args_list
            if net_id:
                interface = {
                    "network": net_id,
                    "access_configs": [{"network_tier": "PREMIUM"}],
                }
                if subnet_id:
                    interface["subnetwork"] = subnet_id
                return [interface]

            return [
                {"network": "default", "access_configs": [{"network_tier": "PREMIUM"}]}
            ]

        _network_interfaces = pulumi.Output.all(
            pulumi.Output.from_input(args.network_id),
            pulumi.Output.from_input(args.subnet_id),
        ).apply(get_network_interfaces)

        def get_accelerators(args_list: List[Any]) -> List[Dict[str, Any]]:
            gpu_type, gpu_count = args_list
            if gpu_type:
                return [{"type": gpu_type, "count": gpu_count or 1}]
            return []

        def get_scheduling(gpu_type: Optional[str]) -> Dict[str, Any]:
            if gpu_type:
                return {
                    "automatic_restart": False,
                    "on_host_maintenance": "TERMINATE",
                    "preemptible": False,
                    "provisioning_model": "STANDARD",
                }
            return {"automatic_restart": True, "on_host_maintenance": "MIGRATE"}

        _guest_accelerators = pulumi.Output.all(
            pulumi.Output.from_input(args.gpu_type),
            pulumi.Output.from_input(args.gpu_count),
        ).apply(get_accelerators)

        _scheduling = pulumi.Output.from_input(args.gpu_type).apply(get_scheduling)

        self.instance = gcp.compute.Instance(
            resource_name=name,
            name=name,
            zone=_zone,
            machine_type=args.machine_type,
            guest_accelerators=_guest_accelerators,
            boot_disk={
                "initialize_params": {
                    "image": _image,
                    "size": args.disk_size,
                    "type": "pd-balanced",
                }
            },
            network_interfaces=_network_interfaces,
            scheduling=_scheduling,
            tags=args.tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.instance_name = self.instance.name
        self.public_ipv4 = self.instance.network_interfaces[0].access_configs[0].nat_ip

        self.register_outputs(
            {
                "instance_name": self.instance.name,
                "public_ipv4": self.instance.network_interfaces[0]
                .access_configs[0]
                .nat_ip,
            }
        )
