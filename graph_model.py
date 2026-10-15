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
    """Bangun daftar ketetanggaan dari simpul dan sisi pada graf tak berarah."""
    # Siapkan daftar kosong untuk setiap simpul, termasuk simpul tanpa sisi.
    graph: Graph = {vertex: [] for vertex in vertices}
    # Catat sisi pada kedua ujungnya karena setiap sisi menghubungkan dua arah.
    for left, right, weight in edges:
        graph[left].append((right, weight))
        graph[right].append((left, weight))
    return graph


def format_weight(weight: Weight) -> str:
    """Tampilkan bobot tanpa akhiran desimal yang tidak diperlukan."""
    value = float(weight)
    return str(int(value)) if value.is_integer() else f"{value:g}"


def adjacency_list_text(graph: Graph, unit: str) -> str:
    """Ubah daftar ketetanggaan menjadi teks yang mudah dibaca."""
    lines = []
    for vertex, neighbors in graph.items():
        if neighbors:
            # Sertakan bobot dan satuan untuk setiap tetangga yang terhubung.
            links = ", ".join(
                f"{neighbor} ({format_weight(weight)} {unit})"
                for neighbor, weight in neighbors
            )
        else:
            # Bedakan simpul yang ada di graf tetapi tidak memiliki sisi.
            links = "(tidak terhubung)"
        lines.append(f"{vertex}: {links}")
    return "\n".join(lines)


def adjacency_matrix(graph: Graph) -> list[list[Weight | None]]:
    """Konversi graf menjadi matriks bobot dengan urutan simpul pada graf."""
    vertices = list(graph)
    # Pemetaan ini memungkinkan simpul digunakan sebagai indeks matriks.
    indexes = {vertex: index for index, vertex in enumerate(vertices)}
    # None menandakan tidak ada sisi; diagonal diisi nol.
    matrix: list[list[Weight | None]] = [
        [None for _ in vertices] for _ in vertices
    ]
    for vertex, neighbors in graph.items():
        matrix[indexes[vertex]][indexes[vertex]] = 0
        # Isi bobot hanya pada pasangan simpul yang memiliki sisi.
        for neighbor, weight in neighbors:
            matrix[indexes[vertex]][indexes[neighbor]] = weight
    return matrix


def dijkstra(graph: Graph, start: str, target: str) -> tuple[list[str], Weight]:
    """Cari rute berbobot minimum dari simpul awal ke simpul tujuan."""
    _check_endpoints(graph, start, target)
    # Simpan jarak terbaik yang diketahui, pendahulu untuk merekonstruksi rute,
    # dan antrean prioritas untuk memproses jarak terkecil lebih dahulu.
    distances: dict[str, Weight] = {start: 0}
    previous: dict[str, str] = {}
    queue: list[tuple[Weight, str]] = [(0, start)]

    while queue:
        distance, vertex = heapq.heappop(queue)
        # Lewati entri antrean lama jika jaraknya sudah diperbarui.
        if distance != distances.get(vertex):
            continue
        # Rute tujuan sudah optimal saat simpul tujuan dikeluarkan dari antrean.
        if vertex == target:
            break
        # Perbarui jarak tetangga apabila ditemukan jalur yang lebih pendek.
        for neighbor, weight in graph[vertex]:
            candidate = distance + weight
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = vertex
                heapq.heappush(queue, (candidate, neighbor))

    # Jika tujuan tidak pernah tercapai, graf tidak menyediakan rute.
    if target not in distances:
        raise ValueError(f"Tidak ada rute dari {start} ke {target}.")

    # Telusuri pendahulu dari tujuan ke awal, lalu balik urutannya.
    path = [target]
    while path[-1] != start:
        path.append(previous[path[-1]])
    path.reverse()
    return path, distances[target]


def manual_path(graph: Graph, route: str) -> tuple[list[str], Weight]:
    """Validasi rute yang dimasukkan pengguna dan hitung total bobotnya."""
    # Pisahkan simpul dengan koma, panah ASCII, atau panah Unicode.
    vertices = [part.strip() for part in re.split(r"\s*(?:,|->|→)\s*", route) if part.strip()]
    if not vertices:
        raise ValueError("Masukkan rute, misalnya: A, B, C.")
    # Pastikan setiap nama simpul dalam rute memang ada di graf.
    for vertex in vertices:
        if vertex not in graph:
            raise ValueError(f"Simpul '{vertex}' tidak ditemukan.")

    # Akumulasikan bobot setiap pasangan simpul berurutan.
    total: Weight = 0
    for left, right in zip(vertices, vertices[1:]):
        edge = next((weight for neighbor, weight in graph[left] if neighbor == right), None)
        if edge is None:
            raise ValueError(f"Tidak ada sisi yang menghubungkan {left} dan {right}.")
        total += edge
    return vertices, total


def euler_trail(graph: Graph, start: str | None = None) -> list[str]:
    """Cari lintasan Euler yang melewati setiap sisi tepat satu kali."""
    if not graph:
        raise ValueError("Tambahkan simpul terlebih dahulu.")

    # Graf tak berarah menyimpan setiap sisi dua kali dalam daftar ketetanggaan.
    edge_count = sum(len(neighbors) for neighbors in graph.values()) // 2
    if edge_count == 0:
        # Graf tanpa sisi memiliki lintasan berupa satu simpul saja.
        if start is not None and start not in graph:
            raise ValueError(f"Simpul awal '{start}' tidak ditemukan.")
        return [start or next(iter(graph))]

    # Syarat lintasan Euler: semua simpul aktif terhubung dan jumlah simpul
    # berderajat ganjil harus nol (sirkuit) atau dua (lintasan terbuka).
    active = {vertex for vertex, neighbors in graph.items() if neighbors}
    _ensure_connected(graph, active)
    odd = [vertex for vertex in active if len(graph[vertex]) % 2]
    if len(odd) not in (0, 2):
        raise ValueError(
            "Graf tidak memiliki lintasan Euler: jumlah simpul berderajat ganjil harus 0 atau 2."
        )

    # Pilih titik awal yang sesuai; lintasan terbuka harus dimulai di simpul ganjil.
    if start is None:
        start = odd[0] if odd else next(iter(active))
    elif start not in graph:
        raise ValueError(f"Simpul awal '{start}' tidak ditemukan.")
    elif start not in active:
        raise ValueError("Simpul awal harus memiliki sisi untuk lintasan Euler.")
    elif odd and start not in odd:
        raise ValueError("Untuk lintasan Euler terbuka, simpul awal harus berderajat ganjil.")

    # Beri ID untuk setiap sisi agar sisi yang sama tidak dipakai dua kali.
    indexed: dict[str, list[tuple[str, int]]] = {vertex: [] for vertex in graph}
    edge_id = 0
    for vertex, neighbors in graph.items():
        for neighbor, _ in neighbors:
            if vertex < neighbor:
                indexed[vertex].append((neighbor, edge_id))
                indexed[neighbor].append((vertex, edge_id))
                edge_id += 1

    # Algoritma Hierholzer: telusuri sisi yang belum dipakai dan bangun
    # sirkuit saat tidak ada lagi sisi tersisa dari simpul saat ini.
    used: set[int] = set()
    stack = [start]
    circuit: list[str] = []
    while stack:
        vertex = stack[-1]
        # Bersihkan sisi yang sudah digunakan dari ujung daftar.
        while indexed[vertex] and indexed[vertex][-1][1] in used:
            indexed[vertex].pop()
        if indexed[vertex]:
            neighbor, current_edge = indexed[vertex].pop()
            used.add(current_edge)
            stack.append(neighbor)
        else:
            circuit.append(stack.pop())

    # Balik urutan hasil susunan mundur dan pastikan semua sisi telah dilalui.
    route = list(reversed(circuit))
    if len(used) != edge_count:
        raise ValueError("Tidak semua sisi dapat dilalui dalam satu lintasan Euler.")
    return route


def hamilton_path(graph: Graph, start: str, target: str) -> list[str]:
    """Cari lintasan yang mengunjungi setiap simpul tepat satu kali."""
    _check_endpoints(graph, start, target)
    if len(graph) == 1:
        return [start]
    if start == target:
        raise ValueError("Simpul awal dan akhir harus berbeda untuk lintasan Hamilton.")

    # Simpan simpul yang sedang berada pada kandidat rute agar tidak berulang.
    visited = {start}
    path = [start]

    def search(vertex: str) -> bool:
        # Rute lengkap valid hanya jika simpul terakhir adalah tujuan.
        if len(path) == len(graph):
            return vertex == target
        # Coba tetangga yang belum dikunjungi; dahulukan simpul berderajat rendah
        # agar cabang yang lebih terbatas diperiksa lebih cepat.
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
            # Jika cabang gagal, batalkan pilihan agar dapat mencoba tetangga lain.
            path.pop()
            visited.remove(neighbor)
        return False

    # Laporkan kegagalan jika pencarian mundur tidak menemukan rute lengkap.
    if not search(start):
        raise ValueError(
            f"Tidak ditemukan lintasan Hamilton dari {start} ke {target}."
        )
    return path


def route_weight(graph: Graph, route: list[str]) -> Weight:
    """Hitung total bobot sisi pada rute yang telah ditentukan."""
    total: Weight = 0
    # Periksa setiap pasangan simpul berurutan lalu jumlahkan bobot sisinya.
    for left, right in zip(route, route[1:]):
        edge = next((weight for neighbor, weight in graph[left] if neighbor == right), None)
        if edge is None:
            raise ValueError(f"Tidak ada sisi yang menghubungkan {left} dan {right}.")
        total += edge
    return total


def greedy_coloring(graph: Graph) -> dict[str, int]:
    """Warnai simpul secara rakus dengan warna terkecil yang tersedia."""
    colors: dict[str, int] = {}
    # Proses simpul berderajat tertinggi lebih dahulu; nama menjadi pemecah seri.
    order = sorted(graph, key=lambda vertex: (-len(graph[vertex]), vertex.casefold()))
    for vertex in order:
        # Warna tetangga yang sudah diproses tidak boleh digunakan simpul ini.
        unavailable = {
            colors[neighbor]
            for neighbor, _ in graph[vertex]
            if neighbor in colors
        }
        # Ambil nomor warna nonnegatif terkecil yang belum dipakai tetangga.
        color = 0
        while color in unavailable:
            color += 1
        colors[vertex] = color
    return colors


def chromatic_number(graph: Graph) -> int:
    """Tentukan jumlah warna minimum yang diperlukan untuk mewarnai graf."""
    if not graph:
        return 0
    # Pewarnaan rakus memberi batas atas jumlah warna yang perlu dicoba.
    upper_bound = max(greedy_coloring(graph).values(), default=-1) + 1
    vertices = list(graph)
    colors: dict[str, int] = {}

    def can_color(limit: int) -> bool:
        # Semua simpul berhasil diwarnai dengan batas jumlah warna ini.
        if len(colors) == len(vertices):
            return True
        uncolored = [vertex for vertex in vertices if vertex not in colors]
        # Pilih simpul yang paling terkendala: banyak warna tetangga terpakai,
        # lalu derajat tertinggi; urutan awal memecahkan seri secara stabil.
        vertex = max(
            uncolored,
            key=lambda item: (
                len({colors[n] for n, _ in graph[item] if n in colors}),
                len(graph[item]),
                -vertices.index(item),
            ),
        )
        # Hindari warna yang sudah digunakan oleh tetangga simpul terpilih.
        unavailable = {
            colors[neighbor]
            for neighbor, _ in graph[vertex]
            if neighbor in colors
        }
        # Coba semua warna yang diizinkan secara rekursif; hapus pilihan
        # sementara saat cabang tersebut tidak menghasilkan pewarnaan lengkap.
        for color in range(limit):
            if color in unavailable:
                continue
            colors[vertex] = color
            if can_color(limit):
                return True
            del colors[vertex]
        return False

    # Uji jumlah warna dari satu ke atas hingga ditemukan pewarnaan yang valid.
    for count in range(1, upper_bound + 1):
        colors.clear()
        if can_color(count):
            return count
    return upper_bound


def _check_endpoints(graph: Graph, start: str, target: str) -> None:
    """Pastikan simpul awal dan tujuan tersedia di dalam graf."""
    if start not in graph:
        raise ValueError(f"Simpul awal '{start}' tidak ditemukan.")
    if target not in graph:
        raise ValueError(f"Simpul tujuan '{target}' tidak ditemukan.")


def _ensure_connected(graph: Graph, vertices: set[str]) -> None:
    """Pastikan semua simpul dalam himpunan dapat dicapai satu sama lain."""
    first = next(iter(vertices))
    reached = {first}
    queue = deque([first])
    # Lakukan BFS hanya melalui simpul yang termasuk dalam himpunan yang diuji.
    while queue:
        vertex = queue.popleft()
        for neighbor, _ in graph[vertex]:
            if neighbor in vertices and neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    # Ketidaksamaan himpunan berarti ada bagian graf yang tidak terhubung.
    if reached != vertices:
        raise ValueError("Semua sisi harus berada dalam satu komponen terhubung.")
