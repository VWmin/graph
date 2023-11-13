import heapq


class PriorityQueue:
    container = []

    def push(self, item):
        heapq.heappush(self.container, item)

    def pop(self):
        return heapq.heappop(self.container)

    def size(self):
        return len(self.container)
