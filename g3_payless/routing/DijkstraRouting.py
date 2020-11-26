from g3_payless.routing.RoutingAlgorithm import RoutingAlgorithm


class DijkstraRouting(RoutingAlgorithm):
    """
    Class that uses Dijkstra's algorithm to calculate a routing table
    """

    def calculate_routing_table(self):
        """
        Calculates the routing table using Dijkstra's algorithm
        :return: The routing table in the following format:
                    {switch_id: {(src_ip, dst_ip): port}}
        :rtype: dict
        """

        instructions = {switch: {} for switch in self.topology.keys()}

        for src_host, src_subnet in self.host_subnets.items():

            src_switch = [
                switch for switch, info in self.topology.items()
                if src_host in info
            ][0]
            switch_paths = self.calculate_paths_for_switch(src_switch)

            for dst_host, dst_subnet in self.host_subnets.items():

                if dst_host == src_host:
                    continue

                dst_switch = [
                    switch for switch, info in self.topology.items()
                    if dst_host in info
                ][0]

                host_port = self.topology[dst_switch][dst_host][0]
                instructions[dst_switch][(src_subnet, dst_subnet)] = host_port

                current_node = dst_switch
                while True:
                    path_info = switch_paths[current_node]
                    previous = path_info[1]

                    if previous is None:
                        break

                    port = self.topology[previous][current_node][0]
                    instructions[previous][(src_subnet, dst_subnet)] = port

                    current_node = previous

        return instructions

    def calculate_paths_for_switch(self, src_switch):
        """
        Calculates the shortest paths for a switch to all other switches
        using Dijkstra's algorithm
        :param src_switch: The name of the source switch
        :type src_switch: str
        :return: The distance/cost and last hop for each destination switch
        """
        unvisited = {
            x: (float("inf"), None)
            for x in self.topology.keys()
        }
        unvisited[src_switch] = (0, None)
        visited = {}

        while len(unvisited) > 0:
            current_node, (current_cost, last_node) = \
                min(unvisited.items(), key=lambda x: x[1][0])
            unvisited.pop(current_node)

            neighbours = [
                x for x in self.topology[current_node]
                if x in unvisited
            ]

            for neighbour in neighbours:

                link_cost = self.topology[current_node][neighbour][1]
                total_cost = link_cost + current_cost

                if total_cost < unvisited[neighbour][0]:
                    unvisited[neighbour] = (total_cost, current_node)

            visited[current_node] = (current_cost, last_node)

        return visited
