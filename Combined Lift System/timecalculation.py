def compute_dwell_time(self, num_boarding, num_alighting, door_overhead=2.0, min_time=0.1, max_time=0.5):
        """
        Compute the dwell time for an elevator stop.
        
        Parameters:
        num_boarding (int): Number of passengers boarding.
        num_alighting (int): Number of passengers alighting.
        door_overhead (float): Fixed time for door opening/closing.
        min_time (float): Minimum time for a passenger to board/alight.
        max_time (float): Maximum time for a passenger to board/alight.
        
        Returns:
        float: Total dwell time.
        """
        if num_boarding + num_alighting == 0:
            return 0.0
        # Sum time for all boarding passengers
        boarding_time = sum(random.uniform(min_time, max_time) for _ in range(num_boarding))
        # Sum time for all alighting passengers
        alighting_time = sum(random.uniform(min_time, max_time) for _ in range(num_alighting))
        # Total dwell time includes door overhead plus per-passenger times
        total_dwell_time = door_overhead + boarding_time + alighting_time
        print(num_boarding)
        print(num_alighting)
        print(total_dwell_time)
        # input("Press Enter to continue...")
        return total_dwell_time