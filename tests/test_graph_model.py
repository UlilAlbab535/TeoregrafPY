import unittest

from graph_model import (
    adjacency_matrix,
    build_adjacency,
    chromatic_number,
    dijkstra,
    euler_trail,
    greedy_coloring,
    hamilton_path,
    manual_path,
    route_weight,
)


class GraphModelTests(unittest.TestCase):
    def test_weighted_adjacency_matrix(self) -> None:
        graph = build_adjacency(["A", "B", "C"], [("A", "B", 2.5)])
        self.assertEqual(
            adjacency_matrix(graph),
            [[0, 2.5, None], [2.5, 0, None], [None, None, 0]],
        )

    def test_dijkstra_finds_lowest_weight_route(self) -> None:
        graph = build_adjacency(
            ["A", "B", "C", "D"],
            [("A", "B", 2), ("B", "D", 2), ("A", "C", 1), ("C", "D", 8)],
        )
        self.assertEqual(dijkstra(graph, "A", "D"), (["A", "B", "D"], 4))

    def test_dijkstra_reports_disconnected_target(self) -> None:
        graph = build_adjacency(["A", "B"], [])
        with self.assertRaisesRegex(ValueError, "Tidak ada rute"):
            dijkstra(graph, "A", "B")

    def test_manual_route_checks_edges_and_accumulates_weight(self) -> None:
        graph = build_adjacency(["A", "B", "C"], [("A", "B", 2), ("B", "C", 3)])
        self.assertEqual(manual_path(graph, "A -> B, C"), (["A", "B", "C"], 5))
        with self.assertRaisesRegex(ValueError, "Tidak ada sisi"):
            manual_path(graph, "A, C")

    def test_euler_trail_uses_every_edge_once(self) -> None:
        graph = build_adjacency(
            ["A", "B", "C"], [("A", "B", 1), ("B", "C", 2)]
        )
        route = euler_trail(graph, "A")
        self.assertEqual(route, ["A", "B", "C"])
        self.assertEqual(route_weight(graph, route), 3)

    def test_euler_requires_zero_or_two_odd_degree_vertices(self) -> None:
        graph = build_adjacency(
            ["A", "B", "C", "D"],
            [("A", "B", 1), ("A", "C", 1), ("A", "D", 1)],
        )
        with self.assertRaisesRegex(ValueError, "derajat ganjil"):
            euler_trail(graph)

    def test_hamilton_path_visits_each_vertex_once(self) -> None:
        graph = build_adjacency(
            ["A", "B", "C", "D"],
            [("A", "B", 1), ("B", "C", 1), ("C", "D", 1), ("A", "D", 3)],
        )
        self.assertEqual(hamilton_path(graph, "A", "D"), ["A", "B", "C", "D"])

    def test_greedy_coloring_and_exact_chromatic_number(self) -> None:
        cycle = build_adjacency(
            ["A", "B", "C", "D"],
            [("A", "B", 1), ("B", "C", 1), ("C", "D", 1), ("D", "A", 1)],
        )
        coloring = greedy_coloring(cycle)
        for vertex, neighbors in cycle.items():
            for neighbor, _ in neighbors:
                self.assertNotEqual(coloring[vertex], coloring[neighbor])
        self.assertEqual(chromatic_number(cycle), 2)

    def test_triangle_has_chromatic_number_three(self) -> None:
        triangle = build_adjacency(
            ["A", "B", "C"], [("A", "B", 1), ("B", "C", 1), ("A", "C", 1)]
        )
        self.assertEqual(chromatic_number(triangle), 3)

    def test_edgeless_nonempty_graph_has_chromatic_number_one(self) -> None:
        self.assertEqual(chromatic_number(build_adjacency(["A", "B"], [])), 1)


if __name__ == "__main__":
    unittest.main()
