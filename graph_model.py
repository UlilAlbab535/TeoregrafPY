"""Core graph operations for the Teori Graf desktop application."""

from __future__ import annotations

import heapq
import math
import re
from collections import deque
from typing import TypeAlias

Weight: TypeAlias = float
Graph: TypeAlias = dict[str, list[tuple[str, Weight]]]


def build_adjacency(
    vertices: list[str], edges: list[tuple[str, str, Weight]]
) -> Graph:
    graph: Graph = {vertex: [] for vertex in vertices}
    for left, right, weight in edges:
        graph[left].append((right, weight))
        graph[right].append((left, weight))
    return graph


def format_weight(weight: Weight) -> str:
    value = float(weight)
    return str(int(value)) if value.is_integer() else f"{value:g}"


def adjacency_list_text(graph: Graph, unit: str) -> str:
    lines = []
    for vertex, neighbors in graph.items():
        if neighbors:
            links = ", ".join(
                f"{neighbor} ({format_weight(weight)} {unit})"
                for neighbor, weight in neighbors
            )
        else:
            links = "(tidak terhubung)"
        lines.append(f"{vertex}: {links}")
    return "\n".join(lines)


def adjacency_matrix(graph: Graph) -> list[list[Weight | None]]:
    vertices = list(graph)
    indexes = {vertex: index for index, vertex in enumerate(vertices)}
    matrix: list[list[Weight | None]] = [
        [None for _ in vertices] for _ in vertices
    ]
    for vertex, neighbors in graph.items():
        matrix[indexes[vertex]][indexes[vertex]] = 0
        for neighbor, weight in neighbors:
            matrix[indexes[vertex]][indexes[neighbor]] = weight
    return matrix


def dijkstra(graph: Graph, start: str, target: str) -> tuple[list[str], Weight]:
    _check_endpoints(graph, start, target)
    distances: dict[str, Weight] = {start: 0}
    previous: dict[str, str] = {}
    queue: list[tuple[Weight, str]] = [(0, start)]

    while queue:
        distance, vertex = heapq.heappop(queue)
        if distance != distances.get(vertex):
            continue
        if vertex == target:
            break
        for neighbor, weight in graph[vertex]:
            candidate = distance + weight
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = vertex
                heapq.heappush(queue, (candidate, neighbor))

    if target not in distances:
        raise ValueError(f"Tidak ada rute dari {start} ke {target}.")

    path = [target]
    while path[-1] != start:
        path.append(previous[path[-1]])
    path.reverse()
    return path, distances[target]


def manual_path(graph: Graph, route: str) -> tuple[list[str], Weight]:
    vertices = [part.strip() for part in re.split(r"\s*(?:,|->|→)\s*", route) if part.strip()]
    if not vertices:
        raise ValueError("Masukkan rute, misalnya: A, B, C.")
    for vertex in vertices:
        if vertex not in graph:
            raise ValueError(f"Simpul '{vertex}' tidak ditemukan.")

    total: Weight = 0
    for left, right in zip(vertices, vertices[1:]):
        edge = next((weight for neighbor, weight in graph[left] if neighbor == right), None)
        if edge is None:
            raise ValueError(f"Tidak ada sisi yang menghubungkan {left} dan {right}.")
        total += edge
    return vertices, total


def euler_trail(graph: Graph, start: str | None = None) -> list[str]:
    if not graph:
        raise ValueError("Tambahkan simpul terlebih dahulu.")

    edge_count = sum(len(neighbors) for neighbors in graph.values()) // 2
    if edge_count == 0:
        if start is not None and start not in graph:
            raise ValueError(f"Simpul awal '{start}' tidak ditemukan.")
        return [start or next(iter(graph))]

    active = {vertex for vertex, neighbors in graph.items() if neighbors}
    _ensure_connected(graph, active)
    odd = [vertex for vertex in active if len(graph[vertex]) % 2]
    if len(odd) not in (0, 2):
        raise ValueError(
            "Graf tidak memiliki lintasan Euler: jumlah simpul berderajat ganjil harus 0 atau 2."
        )

    if start is None:
        start = odd[0] if odd else next(iter(active))
    elif start not in graph:
        raise ValueError(f"Simpul awal '{start}' tidak ditemukan.")
    elif start not in active:
        raise ValueError("Simpul awal harus memiliki sisi untuk lintasan Euler.")
    elif odd and start not in odd:
        raise ValueError("Untuk lintasan Euler terbuka, simpul awal harus berderajat ganjil.")

    indexed: dict[str, list[tuple[str, int]]] = {vertex: [] for vertex in graph}
    edge_id = 0
    for vertex, neighbors in graph.items():
        for neighbor, _ in neighbors:
            if vertex < neighbor:
                indexed[vertex].append((neighbor, edge_id))
                indexed[neighbor].append((vertex, edge_id))
                edge_id += 1

    used: set[int] = set()
    stack = [start]
    circuit: list[str] = []
    while stack:
        vertex = stack[-1]
        while indexed[vertex] and indexed[vertex][-1][1] in used:
            indexed[vertex].pop()
        if indexed[vertex]:
            neighbor, current_edge = indexed[vertex].pop()
            used.add(current_edge)
            stack.append(neighbor)
        else:
            circuit.append(stack.pop())

    route = list(reversed(circuit))
    if len(used) != edge_count:
        raise ValueError("Tidak semua sisi dapat dilalui dalam satu lintasan Euler.")
    return route


def hamilton_path(graph: Graph, start: str, target: str) -> list[str]:
    _check_endpoints(graph, start, target)
    if len(graph) == 1:
        return [start]
    if start == target:
        raise ValueError("Simpul awal dan akhir harus berbeda untuk lintasan Hamilton.")

    visited = {start}
    path = [start]

    def search(vertex: str) -> bool:
        if len(path) == len(graph):
            return vertex == target
        candidates = [
            neighbor for neighbor, _ in graph[vertex]
            if neighbor not in visited
        ]
        candidates.sort(key=lambda neighbor: len(graph[neighbor]))
        for neighbor in candidates:
            visited.add(neighbor)
            path.append(neighbor)
            if search(neighbor):
                return True
            path.pop()
            visited.remove(neighbor)
        return False

    if not search(start):
        raise ValueError(
            f"Tidak ditemukan lintasan Hamilton dari {start} ke {target}."
        )
    return path


def route_weight(graph: Graph, route: list[str]) -> Weight:
    total: Weight = 0
    for left, right in zip(route, route[1:]):
        edge = next((weight for neighbor, weight in graph[left] if neighbor == right), None)
        if edge is None:
            raise ValueError(f"Tidak ada sisi yang menghubungkan {left} dan {right}.")
        total += edge
    return total


def greedy_coloring(graph: Graph) -> dict[str, int]:
    colors: dict[str, int] = {}
    order = sorted(graph, key=lambda vertex: (-len(graph[vertex]), vertex.casefold()))
    for vertex in order:
        unavailable = {
            colors[neighbor]
            for neighbor, _ in graph[vertex]
            if neighbor in colors
        }
        color = 0
        while color in unavailable:
            color += 1
        colors[vertex] = color
    return colors


def chromatic_number(graph: Graph) -> int:
    if not graph:
        return 0
    upper_bound = max(greedy_coloring(graph).values(), default=-1) + 1
    vertices = list(graph)
    colors: dict[str, int] = {}

    def can_color(limit: int) -> bool:
        if len(colors) == len(vertices):
            return True
        uncolored = [vertex for vertex in vertices if vertex not in colors]
        vertex = max(
            uncolored,
            key=lambda item: (
                len({colors[n] for n, _ in graph[item] if n in colors}),
                len(graph[item]),
                -vertices.index(item),
            ),
        )
        unavailable = {
            colors[neighbor]
            for neighbor, _ in graph[vertex]
            if neighbor in colors
        }
        for color in range(limit):
            if color in unavailable:
                continue
            colors[vertex] = color
            if can_color(limit):
                return True
            del colors[vertex]
        return False

    for count in range(1, upper_bound + 1):
        colors.clear()
        if can_color(count):
            return count
    return upper_bound


def _check_endpoints(graph: Graph, start: str, target: str) -> None:
    if start not in graph:
        raise ValueError(f"Simpul awal '{start}' tidak ditemukan.")
    if target not in graph:
        raise ValueError(f"Simpul tujuan '{target}' tidak ditemukan.")


def _ensure_connected(graph: Graph, vertices: set[str]) -> None:
    first = next(iter(vertices))
    reached = {first}
    queue = deque([first])
    while queue:
        vertex = queue.popleft()
        for neighbor, _ in graph[vertex]:
            if neighbor in vertices and neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    if reached != vertices:
        raise ValueError("Semua sisi harus berada dalam satu komponen terhubung.")
