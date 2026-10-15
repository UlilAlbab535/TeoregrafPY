"""Tkinter and Matplotlib interface for learning and exploring graph theory."""

# Menunda evaluasi anotasi tipe agar anotasi dapat merujuk tipe tanpa evaluasi langsung.
from __future__ import annotations

# Pustaka standar: fungsi trigonometri untuk posisi simpul dan komponen antarmuka Tk.
import math  # Menghitung posisi simpul pada lingkaran.
import tkinter as tk  # Membuat jendela, kanvas, dan variabel antarmuka.
from tkinter import messagebox, ttk  # Dialog pesan dan widget bertema Tk.

# Pilih backend Tk sebelum pyplot diimpor agar Matplotlib dapat tampil di jendela Tk.
import matplotlib

matplotlib.use("TkAgg")

# Komponen Matplotlib untuk palet, kanvas Tk, dan objek figur visualisasi.
import matplotlib.pyplot as plt  # Mengakses palet warna untuk simpul.
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # Menanam graf di Tk.
from matplotlib.figure import Figure  # Menyediakan figur yang berisi sumbu graf.

# Algoritma dan formatter dari model graf; antarmuka hanya mengelola masukan/tampilan.
from graph_model import (
    adjacency_list_text,  # Mengubah graf menjadi teks daftar ketetanggaan.
    adjacency_matrix,  # Membentuk matriks bobot antarsimpul.
    build_adjacency,  # Membentuk struktur graf dari simpul dan sisi aplikasi.
    chromatic_number,  # Menghitung bilangan kromatik graf secara eksak.
    dijkstra,  # Mencari rute berbobot minimum dari simpul awal ke tujuan.
    euler_trail,  # Mencari lintasan yang melewati setiap sisi tepat satu kali.
    format_weight,  # Memformat bobot agar ringkas dan mudah dibaca.
    greedy_coloring,  # Mewarnai simpul menggunakan algoritma greedy.
    hamilton_path,  # Mencari lintasan yang mengunjungi simpul sesuai syarat Hamilton.
    manual_path,  # Memvalidasi urutan simpul yang dimasukkan pengguna.
    route_weight,  # Menjumlahkan bobot sisi sepanjang suatu rute.
)


class GraphTheoryApp:
    def __init__(self, root: tk.Tk) -> None:
        """Inisialisasi status graf, variabel antarmuka, jendela, dan tampilan awal."""
        self.root = root
        self.root.title("Aplikasi Teori Graf")
        # Sesuaikan ukuran awal jendela dengan layar tanpa melampaui batas UI.
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(1450, max(640, screen_width - 80))
        window_height = min(900, max(480, screen_height - 100))
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(min(1050, window_width), min(700, window_height))

        self.vertices: list[str] = []
        self.edges: list[tuple[str, str, float]] = []
        self.name_entries: list[ttk.Entry] = []
        self.route: list[str] | None = None
        self.route_description = ""
        self.route_total = 0.0
        self.route_step = 0
        self.palette_var = tk.StringVar(value="tab10")
        self.unit_var = tk.StringVar(value="km")
        self.mapping_algorithm_var = tk.StringVar(value="Euler (semua sisi)")
        self.start_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.manual_route_var = tk.StringVar()
        self.chromatic_var = tk.StringVar(value="Bilangan kromatik: -")
        self.step_status_var = tk.StringVar(value="Belum ada rute.")

        # Bangun komponen antarmuka sebelum memperbarui tampilan graf kosong.
        self._build_interface()
        self._refresh_graph()

    def _build_interface(self) -> None:
        """Susun tata letak utama: kontrol yang dapat digulir dan panel hasil graf."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        # Panel kiri berisi kontrol; panel kanan menampilkan graf dan representasi.
        panes = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        panes.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        controls = ttk.Frame(panes, padding=4)
        display = ttk.Frame(panes, padding=8)
        panes.add(controls, weight=1)
        panes.add(display, weight=3)
        controls.columnconfigure(0, weight=1)
        controls.rowconfigure(0, weight=1)
        display.columnconfigure(0, weight=1)
        display.rowconfigure(0, weight=3)
        display.rowconfigure(1, weight=2)

        controls_canvas = tk.Canvas(controls, highlightthickness=0, width=390)
        controls_scrollbar = ttk.Scrollbar(
            controls, orient=tk.VERTICAL, command=controls_canvas.yview
        )
        self.controls_content = ttk.Frame(controls_canvas, padding=6)
        # Perbarui area gulir saat isi atau lebar panel berubah.
        self.controls_content.bind(
            "<Configure>",
            lambda _event: controls_canvas.configure(
                scrollregion=controls_canvas.bbox("all")
            ),
        )
        self.controls_window = controls_canvas.create_window(
            (0, 0), window=self.controls_content, anchor="nw", width=390
        )
        controls_canvas.configure(yscrollcommand=controls_scrollbar.set)
        controls_canvas.bind(
            "<Configure>",
            lambda event: controls_canvas.itemconfigure(
                self.controls_window, width=event.width
            ),
        )
        controls_canvas.grid(row=0, column=0, sticky="nsew")
        controls_scrollbar.grid(row=0, column=1, sticky="ns")
        self.controls_content.columnconfigure(0, weight=1)

        # Setiap pembangun mengisi satu bagian antarmuka yang terpisah.
        self._build_vertex_controls(self.controls_content)
        self._build_edge_controls(self.controls_content)
        self._build_route_controls(self.controls_content)
        self._build_graph_display(display)
        self._build_text_display(display)

    def _build_vertex_controls(self, parent: ttk.Frame) -> None:
        """Buat formulir untuk menentukan jumlah simpul dan mengubah nama-namanya."""
        section = ttk.LabelFrame(parent, text="1. Simpul", padding=8)
        section.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        section.columnconfigure(1, weight=1)

        ttk.Label(section, text="Jumlah simpul:").grid(row=0, column=0, sticky="w")
        self.vertex_count_var = tk.StringVar(value="4")
        ttk.Spinbox(
            section, from_=1, to=100, textvariable=self.vertex_count_var, width=8
        ).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Button(
            section, text="Siapkan nama", command=self._prepare_vertex_names
        ).grid(row=0, column=2, sticky="e")

        self.names_frame = ttk.Frame(section)
        self.names_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        self.names_canvas = tk.Canvas(self.names_frame, height=110, highlightthickness=0)
        names_scroll = ttk.Scrollbar(
            self.names_frame, orient=tk.VERTICAL, command=self.names_canvas.yview
        )
        self.names_inner = ttk.Frame(self.names_canvas)
        self.names_inner.bind(
            "<Configure>",
            lambda _event: self.names_canvas.configure(
                scrollregion=self.names_canvas.bbox("all")
            ),
        )
        self.names_canvas.create_window((0, 0), window=self.names_inner, anchor="nw")
        self.names_canvas.configure(yscrollcommand=names_scroll.set)
        self.names_canvas.grid(row=0, column=0, sticky="ew")
        names_scroll.grid(row=0, column=1, sticky="ns")
        self.names_frame.columnconfigure(0, weight=1)
        ttk.Button(
            section, text="Terapkan simpul", command=self._apply_vertices
        ).grid(row=2, column=0, columnspan=3, sticky="ew")

    def _build_edge_controls(self, parent: ttk.Frame) -> None:
        """Buat kontrol pemilihan ujung sisi, bobot, satuan, serta daftar sisi."""
        section = ttk.LabelFrame(parent, text="2. Sisi dan bobot", padding=8)
        section.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        section.columnconfigure(1, weight=1)

        ttk.Label(section, text="Dari:").grid(row=0, column=0, sticky="w")
        self.edge_from = ttk.Combobox(section, state="readonly", width=14)
        self.edge_from.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(section, text="Ke:").grid(row=1, column=0, sticky="w")
        self.edge_to = ttk.Combobox(section, state="readonly", width=14)
        self.edge_to.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(section, text="Bobot:").grid(row=2, column=0, sticky="w")
        self.weight_var = tk.StringVar(value="1")
        ttk.Entry(section, textvariable=self.weight_var, width=10).grid(
            row=2, column=1, sticky="w", padx=4, pady=2
        )
        ttk.Label(section, text="Satuan:").grid(row=3, column=0, sticky="w")
        unit_combo = ttk.Combobox(
            section,
            textvariable=self.unit_var,
            values=("km", "m", "mil", "menit", "jam", "detik"),
            state="readonly",
            width=12,
        )
        unit_combo.grid(row=3, column=1, sticky="ew", padx=4, pady=2)
        unit_combo.bind("<<ComboboxSelected>>", self._on_unit_changed)
        ttk.Button(section, text="Tambahkan sisi", command=self._add_edge).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(4, 2)
        )
        self.edge_list = tk.Listbox(section, height=4, exportselection=False)
        self.edge_list.grid(row=5, column=0, columnspan=2, sticky="ew", pady=2)
        ttk.Button(
            section, text="Hapus sisi terpilih", command=self._remove_edge
        ).grid(row=6, column=0, columnspan=2, sticky="ew")

    def _build_route_controls(self, parent: ttk.Frame) -> None:
        """Buat pilihan palet dan algoritma rute beserta kontrol navigasi langkah."""
        section = ttk.LabelFrame(parent, text="3. Rute dan pewarnaan", padding=8)
        section.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        section.columnconfigure(0, weight=1)

        ttk.Label(section, textvariable=self.chromatic_var).grid(
            row=0, column=0, sticky="w", pady=2
        )
        ttk.Label(section, text="Palet warna simpul:").grid(row=1, column=0, sticky="w")
        palette = ttk.Combobox(
            section,
            textvariable=self.palette_var,
            values=("tab10", "Set3", "Dark2", "Paired"),
            state="readonly",
        )
        palette.grid(row=2, column=0, sticky="ew", pady=2)
        palette.bind("<<ComboboxSelected>>", lambda _event: self._draw_graph())

        self.route_notebook = ttk.Notebook(section)
        self.route_notebook.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        dijkstra_tab = ttk.Frame(self.route_notebook, padding=6)
        mapping_tab = ttk.Frame(self.route_notebook, padding=6)
        manual_tab = ttk.Frame(self.route_notebook, padding=6)
        self.route_notebook.add(dijkstra_tab, text="Dijkstra")
        self.route_notebook.add(mapping_tab, text="Euler / Hamilton")
        self.route_notebook.add(manual_tab, text="Manual")
        for tab in (dijkstra_tab, mapping_tab, manual_tab):
            tab.columnconfigure(1, weight=1)

        ttk.Label(dijkstra_tab, text="Simpul awal:").grid(row=0, column=0, sticky="w")
        self.start_combo = ttk.Combobox(
            dijkstra_tab, textvariable=self.start_var, state="readonly"
        )
        self.start_combo.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(dijkstra_tab, text="Simpul tujuan:").grid(row=1, column=0, sticky="w")
        self.target_combo = ttk.Combobox(
            dijkstra_tab, textvariable=self.target_var, state="readonly"
        )
        self.target_combo.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        ttk.Button(
            dijkstra_tab, text="Cari rute terpendek", command=self._find_dijkstra_route
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        self.mapping_start_var = tk.StringVar()
        self.mapping_target_var = tk.StringVar()
        ttk.Label(mapping_tab, text="Jenis pemetaan:").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Combobox(
            mapping_tab,
            textvariable=self.mapping_algorithm_var,
            values=("Euler (semua sisi)", "Hamilton (semua simpul)"),
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(mapping_tab, text="Simpul awal:").grid(row=1, column=0, sticky="w")
        self.mapping_start_combo = ttk.Combobox(
            mapping_tab, textvariable=self.mapping_start_var, state="readonly"
        )
        self.mapping_start_combo.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(mapping_tab, text="Tujuan (Hamilton):").grid(
            row=2, column=0, sticky="w"
        )
        self.mapping_target_combo = ttk.Combobox(
            mapping_tab, textvariable=self.mapping_target_var, state="readonly"
        )
        self.mapping_target_combo.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
        ttk.Button(
            mapping_tab,
            text="Buat pemetaan lintasan",
            command=self._find_mapping_route,
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        ttk.Label(
            mapping_tab,
            text="Euler melewati setiap sisi; Hamilton mengunjungi setiap simpul.",
            wraplength=300,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))

        ttk.Label(manual_tab, text="Urutan simpul (, atau →):").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Entry(manual_tab, textvariable=self.manual_route_var).grid(
            row=0, column=1, sticky="ew", padx=4, pady=2
        )
        ttk.Button(
            manual_tab, text="Tampilkan rute manual", command=self._find_manual_route
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        navigation = ttk.Frame(section)
        navigation.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        navigation.columnconfigure((0, 1), weight=1)
        ttk.Button(
            navigation, text="◀ Sebelumnya", command=self._previous_route_step
        ).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(
            navigation, text="Berikutnya ▶", command=self._next_route_step
        ).grid(row=0, column=1, sticky="ew", padx=(3, 0))
        ttk.Label(
            section, textvariable=self.step_status_var, wraplength=330, justify="left"
        ).grid(row=5, column=0, sticky="ew", pady=(4, 0))

        self.route_output = tk.Text(section, height=4, wrap="word", state="disabled")
        self.route_output.grid(row=6, column=0, sticky="ew", pady=(5, 0))

    def _build_graph_display(self, parent: ttk.Frame) -> None:
        """Siapkan dan pasang kanvas Matplotlib untuk visualisasi graf."""
        graph_frame = ttk.LabelFrame(parent, text="Visualisasi graf", padding=4)
        graph_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        graph_frame.rowconfigure(0, weight=1)
        graph_frame.columnconfigure(0, weight=1)
        self.figure = Figure(figsize=(8, 5), dpi=100, constrained_layout=True)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _build_text_display(self, parent: ttk.Frame) -> None:
        """Siapkan panel teks bergulir untuk representasi daftar dan matriks ketetanggaan."""
        representation = ttk.LabelFrame(
            parent, text="Adjacency List dan Adjacency Matrix", padding=4
        )
        representation.grid(row=1, column=0, sticky="nsew")
        representation.rowconfigure(0, weight=1)
        representation.columnconfigure(0, weight=1)
        self.representation_output = tk.Text(
            representation, wrap="none", state="disabled", font=("Consolas", 10)
        )
        vertical = ttk.Scrollbar(
            representation, orient=tk.VERTICAL, command=self.representation_output.yview
        )
        horizontal = ttk.Scrollbar(
            representation,
            orient=tk.HORIZONTAL,
            command=self.representation_output.xview,
        )
        self.representation_output.configure(
            yscrollcommand=vertical.set, xscrollcommand=horizontal.set
        )
        self.representation_output.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

    def _prepare_vertex_names(self) -> None:
        """Validasi jumlah simpul dan buat kolom nama dengan nilai awal yang sesuai."""
        try:
            count = int(self.vertex_count_var.get())
            if not 1 <= count <= 100:
                raise ValueError("Jumlah simpul harus antara 1 dan 100.")
        except ValueError as error:
            messagebox.showerror("Jumlah simpul tidak valid", str(error))
            return

        # Ganti seluruh isian sebelumnya agar jumlah kolom sesuai masukan terbaru.
        for child in self.names_inner.winfo_children():
            child.destroy()
        self.name_entries.clear()
        for index in range(count):
            ttk.Label(self.names_inner, text=f"Simpul {index + 1}:").grid(
                row=index, column=0, sticky="w", padx=(0, 6), pady=1
            )
            default_name = chr(65 + index) if index < 26 else f"S{index + 1}"
            entry = ttk.Entry(self.names_inner, width=18)
            entry.insert(0, default_name)
            entry.grid(row=index, column=1, sticky="ew", pady=1)
            self.name_entries.append(entry)
        self.names_inner.columnconfigure(1, weight=1)
        self.names_canvas.configure(
            scrollregion=self.names_canvas.bbox("all"),
            height=min(count * 28, 150),
        )

    def _apply_vertices(self) -> None:
        """Validasi keunikan nama, ganti simpul graf, lalu segarkan pilihan dan tampilan."""
        if not self.name_entries:
            self._prepare_vertex_names()
            if not self.name_entries:
                return
        vertices = [entry.get().strip() for entry in self.name_entries]
        if any(not vertex for vertex in vertices):
            messagebox.showerror("Nama tidak valid", "Nama simpul tidak boleh kosong.")
            return
        if len({vertex.casefold() for vertex in vertices}) != len(vertices):
            messagebox.showerror(
                "Nama tidak unik", "Setiap simpul harus memiliki nama yang berbeda."
            )
            return

        # Perubahan himpunan simpul menghapus sisi lama yang mungkin tidak valid.
        self.vertices = vertices
        self.edges.clear()
        self._clear_route()
        self._update_vertex_choices()
        self._update_edge_list()
        self._refresh_graph()

    def _update_vertex_choices(self) -> None:
        """Perbarui pilihan semua combobox dan atur nilai awal berdasarkan simpul aktif."""
        for combo in (
            self.edge_from,
            self.edge_to,
            self.start_combo,
            self.target_combo,
            self.mapping_start_combo,
            self.mapping_target_combo,
        ):
            combo.configure(values=self.vertices)
        if self.vertices:
            # Pilih nilai awal yang berguna agar pengguna tidak perlu mengisi ulang.
            self.edge_from.set(self.vertices[0])
            self.edge_to.set(self.vertices[1] if len(self.vertices) > 1 else "")
            self.start_var.set(self.vertices[0])
            self.target_var.set(self.vertices[-1])
            self.mapping_start_var.set(self.vertices[0])
            self.mapping_target_var.set(self.vertices[-1])
        else:
            # Kosongkan pilihan agar tidak menyisakan simpul dari graf sebelumnya.
            self.edge_from.set("")
            self.edge_to.set("")
            self.start_var.set("")
            self.target_var.set("")
            self.mapping_start_var.set("")
            self.mapping_target_var.set("")

    def _add_edge(self) -> None:
        """Validasi ujung serta bobot sisi, simpan sisi baru, dan segarkan tampilan graf."""
        left = self.edge_from.get()
        right = self.edge_to.get()
        if not left or not right:
            messagebox.showerror("Sisi tidak valid", "Terapkan simpul terlebih dahulu.")
            return
        if left == right:
            messagebox.showerror("Sisi tidak valid", "Simpul tidak dapat dihubungkan ke dirinya sendiri.")
            return
        if any({a, b} == {left, right} for a, b, _ in self.edges):
            messagebox.showerror("Sisi duplikat", f"Sisi {left} — {right} sudah ada.")
            return
        try:
            # Bobot harus terbatas dan positif agar dapat digunakan algoritma rute.
            weight = float(self.weight_var.get())
            if not 0 < weight < float("inf"):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Bobot tidak valid", "Bobot harus berupa angka positif yang valid."
            )
            return

        # Setelah perubahan struktur graf, rute lama tidak lagi dapat dipercaya.
        self.edges.append((left, right, weight))
        self._clear_route()
        self._update_edge_list()
        self._refresh_graph()

    def _remove_edge(self) -> None:
        """Hapus sisi terpilih, batalkan rute lama, dan perbarui representasi graf."""
        selection = self.edge_list.curselection()
        if not selection:
            return
        del self.edges[selection[0]]
        self._clear_route()
        self._update_edge_list()
        self._refresh_graph()

    def _update_edge_list(self) -> None:
        """Tampilkan ulang semua sisi dengan bobot yang diformat dalam satuan aktif."""
        self.edge_list.delete(0, tk.END)
        for left, right, weight in self.edges:
            self.edge_list.insert(
                tk.END, f"{left} — {right}  |  {format_weight(weight)} {self.unit_var.get()}"
            )

    def _on_unit_changed(self, _event: object | None = None) -> None:
        """Tangani perubahan satuan dengan memperbarui label bobot dan visualisasi."""
        self._clear_route()
        self._update_edge_list()
        self._refresh_graph()

    def _find_dijkstra_route(self) -> None:
        """Cari rute terpendek berbobot dari pilihan pengguna dan tampilkan hasil atau galat."""
        if not self.vertices:
            messagebox.showerror("Graf kosong", "Tambahkan simpul terlebih dahulu.")
            return
        graph = build_adjacency(self.vertices, self.edges)
        try:
            route, total = dijkstra(graph, self.start_var.get(), self.target_var.get())
        except ValueError as error:
            messagebox.showerror("Rute tidak ditemukan", str(error))
            return
        self._set_route(route, total, "Rute terpendek (Dijkstra)")

    def _find_mapping_route(self) -> None:
        """Cari lintasan Euler atau Hamilton sesuai pilihan, lalu hitung bobot lintasannya."""
        if not self.vertices:
            messagebox.showerror("Graf kosong", "Tambahkan simpul terlebih dahulu.")
            return
        graph = build_adjacency(self.vertices, self.edges)
        start = self.mapping_start_var.get()
        try:
            # Pilih algoritma dan deskripsi hasil dari jenis pemetaan aktif.
            if self.mapping_algorithm_var.get() == "Euler (semua sisi)":
                route = euler_trail(graph, start)
                description = "Pemetaan Euler (setiap sisi dilalui satu kali)"
            else:
                route = hamilton_path(graph, start, self.mapping_target_var.get())
                description = "Pemetaan Hamilton (setiap simpul dikunjungi satu kali)"
            total = route_weight(graph, route)
        except ValueError as error:
            messagebox.showerror("Lintasan tidak ditemukan", str(error))
            return
        self._set_route(route, total, description)

    def _find_manual_route(self) -> None:
        """Validasi urutan simpul manual, hitung bobotnya, dan tampilkan jika sah."""
        if not self.vertices:
            messagebox.showerror("Graf kosong", "Tambahkan simpul terlebih dahulu.")
            return
        graph = build_adjacency(self.vertices, self.edges)
        try:
            route, total = manual_path(graph, self.manual_route_var.get())
        except ValueError as error:
            messagebox.showerror("Rute tidak valid", str(error))
            return
        self._set_route(route, total, "Rute manual")

    def _set_route(self, route: list[str], total: float, description: str) -> None:
        """Simpan hasil rute beserta keterangannya dan tampilkan dari langkah pertama."""
        self.route = route
        self.route_total = total
        self.route_description = description
        self.route_step = 0
        self._update_route_step()

    def _clear_route(self) -> None:
        """Reset status rute dan teksnya ketika struktur graf atau satuan berubah."""
        self.route = None
        self.route_total = 0
        self.route_description = ""
        self.route_step = 0
        self.step_status_var.set("Belum ada rute.")
        if hasattr(self, "route_output"):
            self._set_text(self.route_output, "")

    def _previous_route_step(self) -> None:
        """Mundurkan sorotan rute satu langkah, dengan batas di simpul pertama."""
        if self.route is not None:
            self.route_step = max(0, self.route_step - 1)
            self._update_route_step()

    def _next_route_step(self) -> None:
        """Majukan sorotan rute satu langkah, dengan batas di simpul terakhir."""
        if self.route is not None:
            self.route_step = min(len(self.route) - 1, self.route_step + 1)
            self._update_route_step()

    def _update_route_step(self) -> None:
        """Hitung progres rute, perbarui teks status, lalu gambar ulang sorotannya."""
        if self.route is None:
            return
        graph = build_adjacency(self.vertices, self.edges)
        # Hitung bobot hanya sampai simpul yang sedang ditampilkan.
        route_so_far = self.route[: self.route_step + 1]
        accumulated = route_weight(graph, route_so_far)
        edge_count = len(self.route) - 1
        if edge_count:
            # Tampilkan indeks langkah dan bobot yang sudah ditempuh.
            progress = (
                f"Langkah {self.route_step}/{edge_count} | "
                f"Posisi: {self.route[self.route_step]} | "
                f"Akumulasi: {format_weight(accumulated)} {self.unit_var.get()}"
            )
        else:
            # Rute satu simpul tidak mempunyai sisi atau langkah perjalanan.
            progress = f"Posisi: {self.route[0]} | Tidak ada sisi yang dilalui."
        self.step_status_var.set(progress)
        output = (
            f"{self.route_description}\n"
            f"Rute: {' → '.join(self.route)}\n"
            f"Total bobot: {format_weight(self.route_total)} {self.unit_var.get()}\n"
            f"{progress}"
        )
        self._set_text(self.route_output, output)
        self._draw_graph()

    def _refresh_graph(self) -> None:
        """Hitung informasi warna graf dan perbarui teks serta visualisasinya."""
        graph = build_adjacency(self.vertices, self.edges)
        if self.vertices:
            # Tampilkan hasil pewarnaan eksak dan jumlah warna pendekatan greedy.
            coloring = greedy_coloring(graph)
            exact_number = chromatic_number(graph)
            greedy_count = max(coloring.values(), default=-1) + 1
            self.chromatic_var.set(
                f"Bilangan kromatik: {exact_number}  |  "
                f"Warna greedy: {greedy_count}"
            )
        else:
            self.chromatic_var.set("Bilangan kromatik: -")
        self._update_representation(graph)
        self._draw_graph()

    def _update_representation(self, graph: dict[str, list[tuple[str, float]]]) -> None:
        """Format daftar ketetanggaan dan matriks bobot ke panel representasi teks."""
        lines = [
            "ADJACENCY LIST",
            adjacency_list_text(graph, self.unit_var.get()) or "(belum ada simpul)",
            "",
            "ADJACENCY MATRIX (bobot dalam " + self.unit_var.get() + ")",
        ]
        if graph:
            # Atur lebar kolom berdasarkan nama simpul agar matriks tetap sejajar.
            vertices = list(graph)
            matrix = adjacency_matrix(graph)
            width = max(5, *(len(vertex) for vertex in vertices))
            lines.append("".ljust(width) + "  " + "  ".join(v.rjust(width) for v in vertices))
            for vertex, row in zip(vertices, matrix):
                values = [
                    "—" if weight is None else format_weight(weight)
                    for weight in row
                ]
                lines.append(
                    vertex.ljust(width)
                    + "  "
                    + "  ".join(value.rjust(width) for value in values)
                )
        else:
            # Beri placeholder yang jelas ketika belum ada simpul.
            lines.append("(belum ada simpul)")
        self._set_text(self.representation_output, "\n".join(lines))

    def _draw_graph(self) -> None:
        """Gambar graf beserta bobot, warna simpul, dan kemajuan lintasan yang aktif."""
        self.axes.clear()
        self.axes.axis("off")
        if not self.vertices:
            # Tampilkan petunjuk jika graf belum memiliki simpul.
            self.axes.text(
                0.5, 0.5, "Tambahkan simpul untuk menampilkan graf",
                ha="center", va="center", transform=self.axes.transAxes,
            )
            self.canvas.draw_idle()
            return

        graph = build_adjacency(self.vertices, self.edges)
        coloring = greedy_coloring(graph)
        palette = plt.get_cmap(self.palette_var.get())
        color_count = max(coloring.values(), default=0) + 1
        # Ubah nomor warna graf menjadi warna dari palet visualisasi yang dipilih.
        node_colors = [
            palette(color / max(color_count - 1, 1))
            for color in (coloring[vertex] for vertex in self.vertices)
        ]

        positions: dict[str, tuple[float, float]] = {}
        if len(self.vertices) == 1:
            positions[self.vertices[0]] = (0, 0)
        else:
            # Tempatkan simpul merata pada lingkaran agar mudah dibaca.
            for index, vertex in enumerate(self.vertices):
                angle = 2 * math.pi * index / len(self.vertices) - math.pi / 2
                positions[vertex] = (1.2 * math.cos(angle), math.sin(angle))

        # Gunakan pasangan tak berarah agar penyorotan cocok dengan sisi graf.
        completed_edges = {
            frozenset((left, right))
            for left, right in zip(
                (self.route or [])[: self.route_step],
                (self.route or [])[1 : self.route_step + 1],
            )
        }
        active_edge = None
        active_direction = None
        if self.route is not None and self.route_step > 0:
            # Simpan arah langkah aktif untuk menggambar panah pada sisi tersebut.
            active_direction = (
                self.route[self.route_step - 1],
                self.route[self.route_step],
            )
            active_edge = frozenset(active_direction)
        for left, right, weight in self.edges:
            edge = frozenset((left, right))
            is_active = edge == active_edge
            is_completed = edge in completed_edges
            x1, y1 = positions[left]
            x2, y2 = positions[right]
            self.axes.plot(
                (x1, x2),
                (y1, y2),
                color="#f28e2b" if is_active else "#e45756" if is_completed else "#8993a4",
                linewidth=3.5 if is_active else 3 if is_completed else 1.6,
                zorder=1,
            )
            if is_active:
                # Panah menunjukkan arah perjalanan pada langkah aktif.
                source_x, source_y = positions[active_direction[0]]
                target_x, target_y = positions[active_direction[1]]
                self.axes.annotate(
                    "",
                    xy=(target_x, target_y),
                    xytext=(source_x, source_y),
                    arrowprops={
                        "arrowstyle": "-|>",
                        "color": "#b45309",
                        "linewidth": 2,
                        "shrinkA": 22,
                        "shrinkB": 22,
                        "mutation_scale": 18,
                    },
                    zorder=2,
                )
            self.axes.text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                format_weight(weight),
                fontsize=9,
                ha="center",
                va="center",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1},
                zorder=3,
            )

        # Tandai simpul yang sudah dikunjungi dan bedakan posisi saat ini.
        route_vertices = set((self.route or [])[: self.route_step + 1])
        for vertex, color in zip(self.vertices, node_colors):
            x, y = positions[vertex]
            is_current = (
                self.route is not None
                and vertex == self.route[self.route_step]
            )
            self.axes.scatter(
                [x],
                [y],
                s=900,
                c=[color],
                edgecolors="#f28e2b" if is_current else "#d62728" if vertex in route_vertices else "#344054",
                linewidths=3.5 if is_current else 3 if vertex in route_vertices else 1.5,
                zorder=4,
            )
            self.axes.text(x, y, vertex, ha="center", va="center", fontsize=10, zorder=5)

        self.axes.set_title(
            "Graf tak berarah berbobot"
            + (" — lintasan ditampilkan bertahap" if self.route else "")
        )
        self.axes.margins(0.25)
        self.canvas.draw_idle()

    @staticmethod
    def _set_text(widget: tk.Text, value: str) -> None:
        """Ganti isi widget teks terkunci lalu kunci kembali agar hanya-baca."""
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state="disabled")


def main() -> None:
    """Buat aplikasi utama dan jalankan event loop Tkinter sampai jendela ditutup."""
    root = tk.Tk()
    GraphTheoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
