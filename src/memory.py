class Memory:

    def __init__(self):
        self.trip_type = None
        self.destination = None
        self.duration = None
        self.items = []

    def save_trip(self, trip_type, destination, duration):
        """Saves the trip context (type, destination, duration)."""
        self.trip_type = trip_type
        self.destination = destination
        self.duration = duration

    def add_item(self, item):
        """Adds an item to the memory state."""
        if item not in self.items:
            self.items.append(item)

    def get_memory(self):
        """Returns the full memory state."""
        return {
            "trip_type": self.trip_type,
            "destination": self.destination,
            "duration": self.duration,
            "items": self.items
        }
