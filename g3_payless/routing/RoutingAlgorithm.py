import yaml
from netaddr import IPAddress, IPNetwork


class RoutingAlgorithm(object):
    """
    Class that defines a framework for routing algorithms
    """

    def __init__(self, topology_file):
        """
        Initializes the routing algorithm
        :param topology_file: The path to the topology file for which to create
                              routing decisions
        :type topology_file: str
        """
        with open(topology_file, "r") as f:
            self.config = yaml.safe_load(f.read())["root"]["topology"]
        self.host_subnets, self.switch_names, self.topology = \
            self.generate_topology()
        self.routing_table = self.calculate_routing_table()

    def calculate_routing_table(self):
        """
        This method should be overwritten by child classes.
        It defines a static routing table with which to fell routing decisions
        :return: The routing table in the following format:
                    {switch_id: {(src_ip, dst_ip): port}}
        :rtype: dict
        """
        raise NotImplementedError()

    def generate_topology(self):
        """
        Generates the topology based on the data in the YAML config file
        :return: A tuple consisting of:
                    * A dictionary mapping host names to their IP subnets
                    * A dictionary mapping switch IDs to the switch names
                    * The topology that contains information about the links
                      between the switches and hosts in the following format:
                        {src_name: {dst_name: (port, link_speed)}}
        :rtype: tuple
        """
        host_subnets = {
            host["name"]: host["ip"]
            for host in self.config["hosts"]
        }
        switch_names = {
            switch["dpid"]: switch["name"]
            for switch in self.config["switches"]
        }
        topology = {}

        for src, dst, link_speed in self.config["links"]:
            if src not in topology:
                topology[src] = {}
            if dst not in topology:
                topology[dst] = {}
            src_port = len(topology[src]) + 1
            dst_port = len(topology[dst]) + 1
            topology[src][dst] = (src_port, link_speed)
            topology[dst][src] = (dst_port, link_speed)
        return host_subnets, switch_names, topology

    def calculate_routing_decision(self, switch_id, _src_ip, _dst_ip):
        """
        Calculates the port on which to forward a packet based on
        the source and destination IP address and the static routing table
        :param switch_id: The ID of the switch for which to decide the port
        :type switch_id: int
        :param _src_ip: The source IP address
        :type _src_ip: str
        :param _dst_ip: The destination IP address
        :type _dst_ip: str
        :return: A tuple consisting of:
                    * The port on which to forward
                    * The source subnet
                    * The destination subnet
        :rtype: tuple
        """
        switch_name = self.switch_names[switch_id]
        switch_routing_table = self.routing_table[switch_name]
        src_ip = IPAddress(_src_ip)
        dst_ip = IPAddress(_dst_ip)

        for (_src_subnet, _dst_subnet), port in switch_routing_table.items():
            src_subnet = IPNetwork(_src_subnet)
            dst_subnet = IPNetwork(_dst_subnet)

            if src_ip in src_subnet and dst_ip in dst_subnet:
                return port, str(src_subnet), str(dst_subnet)
