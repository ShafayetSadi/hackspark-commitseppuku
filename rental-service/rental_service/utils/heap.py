import heapq


def push_bounded(heap: list[tuple], item: tuple, k: int) -> None:
    if len(heap) < k:
        heapq.heappush(heap, item)
        return

    if item > heap[0]:
        heapq.heapreplace(heap, item)
