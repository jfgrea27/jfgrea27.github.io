from manimlib import *


class NeuralNetwork(Scene):
    def construct(self):
        # Network architecture: [input_neurons, hidden1, hidden2, output]
        layer_sizes = [4, 6, 6, 3]
        layer_colors = [BLUE, GREEN, GREEN, RED]
        layer_labels = ["Input", "Hidden 1", "Hidden 2", "Output"]

        # Spacing configuration
        layer_spacing = 3.0
        neuron_radius = 0.25
        neuron_spacing = 0.9

        # Calculate total width and starting x position
        total_width = (len(layer_sizes) - 1) * layer_spacing
        start_x = -total_width / 2

        # Store all neurons and connections
        all_layers = []
        all_connections = VGroup()

        # Create neurons for each layer
        for layer_idx, num_neurons in enumerate(layer_sizes):
            layer = VGroup()
            x_pos = start_x + layer_idx * layer_spacing

            # Calculate total height for this layer
            total_height = (num_neurons - 1) * neuron_spacing
            start_y = total_height / 2

            for neuron_idx in range(num_neurons):
                y_pos = start_y - neuron_idx * neuron_spacing
                neuron = Circle(
                    radius=neuron_radius,
                    stroke_color=layer_colors[layer_idx],
                    stroke_width=3,
                    fill_color=BLACK,
                    fill_opacity=0.8,
                )
                neuron.move_to([x_pos, y_pos, 0])
                layer.add(neuron)

            all_layers.append(layer)

        # Create connections between layers
        for layer_idx in range(len(layer_sizes) - 1):
            current_layer = all_layers[layer_idx]
            next_layer = all_layers[layer_idx + 1]

            for neuron1 in current_layer:
                for neuron2 in next_layer:
                    connection = Line(
                        neuron1.get_center(),
                        neuron2.get_center(),
                        stroke_color=GREY,
                        stroke_width=1,
                        stroke_opacity=0.4,
                    )
                    all_connections.add(connection)

        # Create layer labels
        layer_label_group = VGroup()
        for layer_idx, label_text in enumerate(layer_labels):
            x_pos = start_x + layer_idx * layer_spacing
            label = Text(label_text, font_size=24)
            label.move_to([x_pos, -3.5, 0])
            layer_label_group.add(label)

        # Title
        title = Text("Feed-Forward Neural Network", font_size=40)
        title.to_edge(UP, buff=0.5)

        # Animation sequence
        self.play(Write(title))
        self.wait(0.5)

        # Fade in connections first (background)
        self.play(FadeIn(all_connections), run_time=1.5)

        # Animate each layer appearing
        for layer_idx, layer in enumerate(all_layers):
            self.play(
                *[GrowFromCenter(neuron) for neuron in layer],
                run_time=0.8,
            )

        # Add layer labels
        self.play(FadeIn(layer_label_group))
        self.wait(1)

        # Animate forward propagation - highlight neurons layer by layer
        for layer_idx, layer in enumerate(all_layers):
            # Highlight current layer neurons
            self.play(
                *[
                    neuron.animate.set_fill(layer_colors[layer_idx], opacity=0.6)
                    for neuron in layer
                ],
                run_time=0.5,
            )

            # If not the last layer, highlight connections to next layer
            if layer_idx < len(all_layers) - 1:
                # Find connections from this layer
                connections_to_highlight = VGroup()
                current_layer = all_layers[layer_idx]
                next_layer = all_layers[layer_idx + 1]

                connection_idx = 0
                total_prev_connections = 0
                for prev_layer_idx in range(layer_idx):
                    total_prev_connections += (
                        layer_sizes[prev_layer_idx] * layer_sizes[prev_layer_idx + 1]
                    )

                num_connections = layer_sizes[layer_idx] * layer_sizes[layer_idx + 1]
                layer_connections = all_connections[
                    total_prev_connections : total_prev_connections + num_connections
                ]

                self.play(
                    *[
                        conn.animate.set_stroke(YELLOW, width=2, opacity=0.8)
                        for conn in layer_connections
                    ],
                    run_time=0.4,
                )

            self.wait(0.3)

            # Reset colors for flow effect
            if layer_idx < len(all_layers) - 1:
                self.play(
                    *[neuron.animate.set_fill(BLACK, opacity=0.8) for neuron in layer],
                    run_time=0.3,
                )

        self.wait(2)


class NeuralNetworkWithEquations(Scene):
    def construct(self):
        # Network architecture: [input, hidden, output]
        layer_sizes = [3, 4, 2]
        layer_colors = [BLUE_C, TEAL_C, MAROON_C]
        glow_colors = [BLUE_A, TEAL_A, MAROON_A]

        # Spacing configuration
        layer_spacing = 2.5
        neuron_radius = 0.32
        neuron_spacing = 1.0

        # Shift network to the left
        network_shift = LEFT * 3

        # Calculate starting position
        total_width = (len(layer_sizes) - 1) * layer_spacing
        start_x = -total_width / 2

        all_layers = []
        all_connections = []  # List of lists for organized connections
        all_connections_flat = VGroup()

        # Create neurons with glow effect
        for layer_idx, num_neurons in enumerate(layer_sizes):
            layer = VGroup()
            x_pos = start_x + layer_idx * layer_spacing

            total_height = (num_neurons - 1) * neuron_spacing
            start_y = total_height / 2

            for neuron_idx in range(num_neurons):
                y_pos = start_y - neuron_idx * neuron_spacing

                # Outer glow circle
                glow = Circle(
                    radius=neuron_radius + 0.08,
                    stroke_color=glow_colors[layer_idx],
                    stroke_width=6,
                    stroke_opacity=0.0,
                    fill_opacity=0,
                )
                glow.move_to([x_pos, y_pos, 0])
                glow.shift(network_shift)

                # Main neuron
                neuron = Circle(
                    radius=neuron_radius,
                    stroke_color=layer_colors[layer_idx],
                    stroke_width=3,
                    fill_color=BLACK,
                    fill_opacity=0.9,
                )
                neuron.move_to([x_pos, y_pos, 0])
                neuron.shift(network_shift)

                # Store glow as attribute for later access
                neuron.glow = glow
                layer.add(glow, neuron)

            all_layers.append(layer)

        # Create connections with varying weights (visual thickness)
        import random

        random.seed(42)

        for layer_idx in range(len(layer_sizes) - 1):
            layer_connections = []
            current_layer = all_layers[layer_idx]
            next_layer = all_layers[layer_idx + 1]

            # Get only the neuron circles (every other element after glow)
            current_neurons = [
                current_layer[i] for i in range(1, len(current_layer), 2)
            ]
            next_neurons = [next_layer[i] for i in range(1, len(next_layer), 2)]

            for neuron1 in current_neurons:
                for neuron2 in next_neurons:
                    # Random weight for visual effect
                    weight = random.uniform(0.3, 1.0)
                    connection = Line(
                        neuron1.get_center(),
                        neuron2.get_center(),
                        stroke_color=GREY_B,
                        stroke_width=weight * 2,
                        stroke_opacity=0.3,
                    )
                    connection.weight = weight
                    layer_connections.append(connection)
                    all_connections_flat.add(connection)

            all_connections.append(layer_connections)

        # Add input labels (x1, x2, x3)
        input_labels = VGroup()
        input_neurons = [all_layers[0][i] for i in range(1, len(all_layers[0]), 2)]
        for i, neuron in enumerate(input_neurons):
            label = Text(f"x{i + 1}", font_size=26, color=BLUE_B)
            label.next_to(neuron, LEFT, buff=0.4)
            input_labels.add(label)

        # Add output labels (y1, y2)
        output_labels = VGroup()
        output_neurons = [all_layers[-1][i] for i in range(1, len(all_layers[-1]), 2)]
        for i, neuron in enumerate(output_neurons):
            label = Text(f"ŷ{i + 1}", font_size=26, color=MAROON_B)
            label.next_to(neuron, RIGHT, buff=0.4)
            output_labels.add(label)

        # Create equations on the right side with colored components
        equation_title = Text("Forward Pass", font_size=32, color=WHITE)
        equation_title.move_to(RIGHT * 3.5 + UP * 2.8)
        underline = Line(
            equation_title.get_left() + DOWN * 0.15,
            equation_title.get_right() + DOWN * 0.15,
            stroke_color=YELLOW,
            stroke_width=2,
        )

        # Equation 1: z = Wx + b (with colors)
        eq1_parts = VGroup(
            Text("z", font_size=26, color=TEAL_B),
            Text(" = ", font_size=26, color=WHITE),
            Text("W", font_size=26, color=ORANGE),
            Text("x", font_size=26, color=BLUE_B),
            Text(" + ", font_size=26, color=WHITE),
            Text("b", font_size=26, color=PURPLE_B),
        )
        eq1_parts.arrange(RIGHT, buff=0.05)
        eq1_parts.next_to(equation_title, DOWN, buff=0.6)

        # Equation 2: a = σ(z) (with colors)
        eq2_parts = VGroup(
            Text("a", font_size=26, color=GREEN_B),
            Text(" = ", font_size=26, color=WHITE),
            Text("σ", font_size=26, color=YELLOW),
            Text("(", font_size=26, color=WHITE),
            Text("z", font_size=26, color=TEAL_B),
            Text(")", font_size=26, color=WHITE),
        )
        eq2_parts.arrange(RIGHT, buff=0.05)
        eq2_parts.next_to(eq1_parts, DOWN, buff=0.4)

        # Create surrounding boxes for equations (initially invisible)
        eq1_box = SurroundingRectangle(eq1_parts, color=TEAL, buff=0.15, stroke_width=2)
        eq1_box.set_stroke(opacity=0)
        eq2_box = SurroundingRectangle(
            eq2_parts, color=GREEN, buff=0.15, stroke_width=2
        )
        eq2_box.set_stroke(opacity=0)

        # Legend with colored items
        legend_title = Text("Legend", font_size=24, color=GREY_A)
        legend_title.move_to(RIGHT * 3.5 + DOWN * 1.0)

        legend_items = VGroup()
        legend_data = [
            ("W", "weights", ORANGE),
            ("b", "bias", PURPLE_B),
            ("σ", "activation (ReLU/sigmoid)", YELLOW),
        ]

        for i, (symbol, desc, color) in enumerate(legend_data):
            sym = Text(symbol, font_size=20, color=color)
            eq_sign = Text(" = ", font_size=20, color=GREY)
            description = Text(desc, font_size=18, color=GREY)
            item = VGroup(sym, eq_sign, description).arrange(RIGHT, buff=0.05)
            item.next_to(legend_title, DOWN, buff=0.3 + i * 0.35, aligned_edge=LEFT)
            legend_items.add(item)

        # ===== ANIMATION SEQUENCE =====

        # 1. Draw connections with a sweep effect
        self.play(
            LaggedStart(
                *[ShowCreation(conn) for conn in all_connections_flat],
                lag_ratio=0.02,
            ),
            run_time=1.5,
        )

        # 2. Pop in neurons layer by layer with glow
        for layer_idx, layer in enumerate(all_layers):
            neurons = [layer[i] for i in range(1, len(layer), 2)]
            glows = [layer[i] for i in range(0, len(layer), 2)]

            self.play(
                *[GrowFromCenter(n) for n in neurons],
                *[FadeIn(g) for g in glows],
                run_time=0.7,
            )

        # 3. Fade in labels
        self.play(
            LaggedStart(
                *[FadeIn(l, shift=LEFT * 0.2) for l in input_labels], lag_ratio=0.1
            ),
            LaggedStart(
                *[FadeIn(l, shift=RIGHT * 0.2) for l in output_labels], lag_ratio=0.1
            ),
            run_time=0.8,
        )
        self.wait(0.3)

        # 4. Show equation title with underline
        self.play(Write(equation_title), ShowCreation(underline), run_time=0.8)

        # 5. Show equations with highlighting
        self.play(Write(eq1_parts), run_time=1.0)
        self.add(eq1_box)
        self.play(Write(eq2_parts), run_time=1.0)
        self.add(eq2_box)
        self.wait(0.3)

        # 6. Show legend
        self.play(FadeIn(legend_title), run_time=0.4)
        self.play(
            LaggedStart(
                *[FadeIn(item, shift=UP * 0.1) for item in legend_items], lag_ratio=0.15
            )
        )
        self.wait(0.5)

        # ===== FORWARD PROPAGATION ANIMATION =====

        # Helper to get neurons from layer
        def get_neurons(layer):
            return [layer[i] for i in range(1, len(layer), 2)]

        def get_glows(layer):
            return [layer[i] for i in range(0, len(layer), 2)]

        # Propagate through network
        for layer_idx in range(len(layer_sizes)):
            neurons = get_neurons(all_layers[layer_idx])
            glows = get_glows(all_layers[layer_idx])

            # Highlight equation box based on layer
            eq_highlight_anims = []
            if layer_idx > 0:
                eq_highlight_anims.append(eq1_box.animate.set_stroke(opacity=0.8))

            # Activate neurons with glow
            self.play(
                *[
                    n.animate.set_fill(layer_colors[layer_idx], opacity=0.7)
                    for n in neurons
                ],
                *[g.animate.set_stroke(opacity=0.6) for g in glows],
                *eq_highlight_anims,
                run_time=0.5,
            )

            # Animate connections to next layer
            if layer_idx < len(layer_sizes) - 1:
                layer_conns = all_connections[layer_idx]

                # Create traveling dots along connections
                dots = VGroup()
                for conn in layer_conns:
                    dot = Dot(radius=0.06, color=YELLOW)
                    dot.move_to(conn.get_start())
                    dots.add(dot)

                self.add(dots)

                # Animate dots traveling and connections lighting up
                self.play(
                    *[
                        conn.animate.set_stroke(color=YELLOW_C, opacity=0.7)
                        for conn in layer_conns
                    ],
                    *[
                        dot.animate.move_to(layer_conns[i].get_end())
                        for i, dot in enumerate(dots)
                    ],
                    run_time=0.6,
                )

                # Show activation equation
                if layer_idx > 0:
                    self.play(
                        eq1_box.animate.set_stroke(opacity=0),
                        eq2_box.animate.set_stroke(opacity=0.8),
                        run_time=0.3,
                    )

                # Fade dots and reset connections
                self.play(
                    FadeOut(dots),
                    *[
                        conn.animate.set_stroke(color=GREY_B, opacity=0.3)
                        for conn in layer_conns
                    ],
                    eq2_box.animate.set_stroke(opacity=0),
                    run_time=0.4,
                )

            # Keep output layer lit, dim others
            if layer_idx < len(layer_sizes) - 1:
                self.play(
                    *[n.animate.set_fill(BLACK, opacity=0.9) for n in neurons],
                    *[g.animate.set_stroke(opacity=0) for g in glows],
                    run_time=0.3,
                )

        # Final pulse on output
        output_neurons = get_neurons(all_layers[-1])
        output_glows = get_glows(all_layers[-1])
        self.play(
            *[g.animate.set_stroke(opacity=1.0) for g in output_glows],
            run_time=0.3,
        )
        self.play(
            *[g.animate.set_stroke(opacity=0.4) for g in output_glows],
            run_time=0.3,
        )
        self.play(
            *[g.animate.set_stroke(opacity=0.8) for g in output_glows],
            run_time=0.3,
        )

        self.wait(2)


class NeuralNetworkDeep(Scene):
    def construct(self):
        # Deep network: more layers
        layer_sizes = [5, 8, 8, 8, 4, 2]
        layer_colors = [BLUE, TEAL, GREEN, YELLOW, ORANGE, RED]

        layer_spacing = 2.0
        neuron_radius = 0.18
        neuron_spacing = 0.6

        total_width = (len(layer_sizes) - 1) * layer_spacing
        start_x = -total_width / 2

        all_layers = []
        all_connections = VGroup()

        # Create neurons
        for layer_idx, num_neurons in enumerate(layer_sizes):
            layer = VGroup()
            x_pos = start_x + layer_idx * layer_spacing

            total_height = (num_neurons - 1) * neuron_spacing
            start_y = total_height / 2

            for neuron_idx in range(num_neurons):
                y_pos = start_y - neuron_idx * neuron_spacing
                neuron = Circle(
                    radius=neuron_radius,
                    stroke_color=layer_colors[layer_idx],
                    stroke_width=2,
                    fill_color=layer_colors[layer_idx],
                    fill_opacity=0.3,
                )
                neuron.move_to([x_pos, y_pos, 0])
                layer.add(neuron)

            all_layers.append(layer)

        # Create connections
        for layer_idx in range(len(layer_sizes) - 1):
            current_layer = all_layers[layer_idx]
            next_layer = all_layers[layer_idx + 1]

            for neuron1 in current_layer:
                for neuron2 in next_layer:
                    connection = Line(
                        neuron1.get_center(),
                        neuron2.get_center(),
                        stroke_color=WHITE,
                        stroke_width=0.5,
                        stroke_opacity=0.2,
                    )
                    all_connections.add(connection)

        # Title
        title = Text("Deep Neural Network", font_size=36)
        title.to_edge(UP, buff=0.4)

        # Layer size indicators
        size_labels = VGroup()
        for layer_idx, size in enumerate(layer_sizes):
            x_pos = start_x + layer_idx * layer_spacing
            label = Text(str(size), font_size=20, color=layer_colors[layer_idx])
            label.move_to([x_pos, -3.2, 0])
            size_labels.add(label)

        neurons_label = Text("neurons per layer", font_size=18, color=GREY)
        neurons_label.move_to([0, -3.6, 0])

        # Animation
        self.play(Write(title))
        self.play(FadeIn(all_connections), run_time=1)

        for layer in all_layers:
            self.play(*[FadeIn(n, scale=0.5) for n in layer], run_time=0.4)

        self.play(FadeIn(size_labels), Write(neurons_label))
        self.wait(2)


class BackPropagation(Scene):
    def construct(self):
        # Network architecture
        layer_sizes = [3, 4, 2]
        layer_colors = [BLUE_C, TEAL_C, MAROON_C]
        glow_colors = [BLUE_A, TEAL_A, MAROON_A]

        # Spacing
        layer_spacing = 2.5
        neuron_radius = 0.3
        neuron_spacing = 0.95

        network_shift = LEFT * 3.2

        total_width = (len(layer_sizes) - 1) * layer_spacing
        start_x = -total_width / 2

        all_layers = []
        all_connections = []
        all_connections_flat = VGroup()

        import random

        random.seed(42)

        # Create neurons with glow
        for layer_idx, num_neurons in enumerate(layer_sizes):
            layer = VGroup()
            x_pos = start_x + layer_idx * layer_spacing

            total_height = (num_neurons - 1) * neuron_spacing
            start_y = total_height / 2

            for neuron_idx in range(num_neurons):
                y_pos = start_y - neuron_idx * neuron_spacing

                glow = Circle(
                    radius=neuron_radius + 0.08,
                    stroke_color=glow_colors[layer_idx],
                    stroke_width=6,
                    stroke_opacity=0.0,
                    fill_opacity=0,
                )
                glow.move_to([x_pos, y_pos, 0])
                glow.shift(network_shift)

                neuron = Circle(
                    radius=neuron_radius,
                    stroke_color=layer_colors[layer_idx],
                    stroke_width=3,
                    fill_color=BLACK,
                    fill_opacity=0.9,
                )
                neuron.move_to([x_pos, y_pos, 0])
                neuron.shift(network_shift)

                layer.add(glow, neuron)

            all_layers.append(layer)

        # Create connections
        for layer_idx in range(len(layer_sizes) - 1):
            layer_connections = []
            current_layer = all_layers[layer_idx]
            next_layer = all_layers[layer_idx + 1]

            current_neurons = [
                current_layer[i] for i in range(1, len(current_layer), 2)
            ]
            next_neurons = [next_layer[i] for i in range(1, len(next_layer), 2)]

            for neuron1 in current_neurons:
                for neuron2 in next_neurons:
                    weight = random.uniform(0.3, 1.0)
                    connection = Line(
                        neuron1.get_center(),
                        neuron2.get_center(),
                        stroke_color=GREY_B,
                        stroke_width=weight * 2,
                        stroke_opacity=0.4,
                    )
                    connection.weight = weight
                    layer_connections.append(connection)
                    all_connections_flat.add(connection)

            all_connections.append(layer_connections)

        # Helper functions
        def get_neurons(layer):
            return [layer[i] for i in range(1, len(layer), 2)]

        def get_glows(layer):
            return [layer[i] for i in range(0, len(layer), 2)]

        # Labels
        input_labels = VGroup()
        for i, neuron in enumerate(get_neurons(all_layers[0])):
            label = Text(f"x{i + 1}", font_size=24, color=BLUE_B)
            label.next_to(neuron, LEFT, buff=0.35)
            input_labels.add(label)

        output_labels = VGroup()
        for i, neuron in enumerate(get_neurons(all_layers[-1])):
            label = Text(f"ŷ{i + 1}", font_size=24, color=MAROON_B)
            label.next_to(neuron, RIGHT, buff=0.35)
            output_labels.add(label)

        # Target labels (y - ground truth)
        target_labels = VGroup()
        for i, neuron in enumerate(get_neurons(all_layers[-1])):
            label = Text(f"y{i + 1}", font_size=24, color=GREEN_B)
            label.next_to(neuron, RIGHT, buff=1.2)
            target_labels.add(label)

        # Title
        title = Text("Backpropagation", font_size=38, color=WHITE)
        title.to_edge(UP, buff=0.4)

        # Equation panel on the right
        eq_panel_x = RIGHT * 3.8

        # Phase labels
        forward_label = Text("1. Forward Pass", font_size=26, color=YELLOW)
        forward_label.move_to(eq_panel_x + UP * 2.8)

        loss_label = Text("2. Compute Loss", font_size=26, color=RED_B)
        loss_label.move_to(eq_panel_x + UP * 2.8)

        backward_label = Text("3. Backward Pass", font_size=26, color=ORANGE)
        backward_label.move_to(eq_panel_x + UP * 2.8)

        update_label = Text("4. Update Weights", font_size=26, color=GREEN_B)
        update_label.move_to(eq_panel_x + UP * 2.8)

        # Loss equation
        loss_eq = VGroup(
            Text("L", font_size=24, color=RED_B),
            Text(" = ", font_size=24, color=WHITE),
            Text("½", font_size=24, color=WHITE),
            Text("(y - ŷ)²", font_size=24, color=WHITE),
        ).arrange(RIGHT, buff=0.05)
        loss_eq.move_to(eq_panel_x + UP * 1.8)

        # Gradient equations
        grad_title = Text("Gradients (Chain Rule):", font_size=20, color=GREY_A)
        grad_title.move_to(eq_panel_x + UP * 1.0)

        grad_eq1 = VGroup(
            Text("∂L/∂W", font_size=22, color=ORANGE),
            Text(" = ", font_size=22, color=WHITE),
            Text("∂L/∂ŷ", font_size=22, color=RED_B),
            Text(" · ", font_size=22, color=WHITE),
            Text("∂ŷ/∂z", font_size=22, color=TEAL_B),
            Text(" · ", font_size=22, color=WHITE),
            Text("∂z/∂W", font_size=22, color=BLUE_B),
        ).arrange(RIGHT, buff=0.03)
        grad_eq1.move_to(eq_panel_x + UP * 0.4)
        grad_eq1.scale(0.85)

        # Weight update equation
        update_eq = VGroup(
            Text("W", font_size=24, color=ORANGE),
            Text(" ← ", font_size=24, color=WHITE),
            Text("W", font_size=24, color=ORANGE),
            Text(" - ", font_size=24, color=WHITE),
            Text("α", font_size=24, color=GREEN_B),
            Text("·", font_size=24, color=WHITE),
            Text("∂L/∂W", font_size=24, color=ORANGE),
        ).arrange(RIGHT, buff=0.05)
        update_eq.move_to(eq_panel_x + DOWN * 0.5)

        learning_rate_note = Text("α = learning rate", font_size=18, color=GREY)
        learning_rate_note.next_to(update_eq, DOWN, buff=0.3)

        # ===== ANIMATION SEQUENCE =====

        # Initial setup - show network
        self.play(Write(title))
        self.play(FadeIn(all_connections_flat), run_time=0.8)

        for layer in all_layers:
            neurons = get_neurons(layer)
            glows = get_glows(layer)
            self.play(
                *[GrowFromCenter(n) for n in neurons],
                *[FadeIn(g) for g in glows],
                run_time=0.5,
            )

        self.play(FadeIn(input_labels), FadeIn(output_labels))
        self.wait(0.3)

        # ===== PHASE 1: FORWARD PASS =====
        self.play(Write(forward_label))

        # Quick forward pass animation
        for layer_idx in range(len(layer_sizes)):
            neurons = get_neurons(all_layers[layer_idx])
            glows = get_glows(all_layers[layer_idx])

            self.play(
                *[
                    n.animate.set_fill(layer_colors[layer_idx], opacity=0.6)
                    for n in neurons
                ],
                *[g.animate.set_stroke(opacity=0.5) for g in glows],
                run_time=0.35,
            )

            if layer_idx < len(layer_sizes) - 1:
                layer_conns = all_connections[layer_idx]
                dots = VGroup()
                for conn in layer_conns:
                    dot = Dot(radius=0.05, color=YELLOW)
                    dot.move_to(conn.get_start())
                    dots.add(dot)

                self.add(dots)
                self.play(
                    *[
                        conn.animate.set_stroke(color=YELLOW_C, opacity=0.6)
                        for conn in layer_conns
                    ],
                    *[
                        dot.animate.move_to(layer_conns[i].get_end())
                        for i, dot in enumerate(dots)
                    ],
                    run_time=0.4,
                )
                self.play(
                    FadeOut(dots),
                    *[
                        conn.animate.set_stroke(color=GREY_B, opacity=0.4)
                        for conn in layer_conns
                    ],
                    run_time=0.25,
                )

            if layer_idx < len(layer_sizes) - 1:
                self.play(
                    *[n.animate.set_fill(BLACK, opacity=0.9) for n in neurons],
                    *[g.animate.set_stroke(opacity=0) for g in glows],
                    run_time=0.2,
                )

        self.wait(0.3)

        # ===== PHASE 2: COMPUTE LOSS =====
        self.play(
            ReplacementTransform(forward_label, loss_label),
        )

        # Show target values
        self.play(
            LaggedStart(
                *[FadeIn(t, shift=RIGHT * 0.3) for t in target_labels], lag_ratio=0.15
            ),
            run_time=0.6,
        )

        # Draw comparison lines between ŷ and y
        comparison_lines = VGroup()
        for i, (out_label, tgt_label) in enumerate(zip(output_labels, target_labels)):
            line = Line(
                out_label.get_right() + RIGHT * 0.15,
                tgt_label.get_left() + LEFT * 0.15,
                stroke_color=RED_B,
                stroke_width=3,
            )
            # Add "vs" text
            vs_text = Text("≠", font_size=20, color=RED_B)
            vs_text.move_to(line.get_center())
            comparison_lines.add(VGroup(line, vs_text))

        self.play(
            *[ShowCreation(c[0]) for c in comparison_lines],
            *[FadeIn(c[1]) for c in comparison_lines],
            run_time=0.5,
        )

        # Show loss equation
        self.play(Write(loss_eq), run_time=0.8)

        # Pulse output neurons red to show error
        output_neurons = get_neurons(all_layers[-1])
        output_glows = get_glows(all_layers[-1])
        self.play(
            *[n.animate.set_stroke(RED, width=4) for n in output_neurons],
            *[g.animate.set_stroke(color=RED_A, opacity=0.8) for g in output_glows],
            run_time=0.4,
        )
        self.play(
            *[n.animate.set_stroke(layer_colors[-1], width=3) for n in output_neurons],
            *[
                g.animate.set_stroke(color=glow_colors[-1], opacity=0.5)
                for g in output_glows
            ],
            run_time=0.4,
        )

        self.wait(0.3)

        # ===== PHASE 3: BACKWARD PASS =====
        self.play(
            ReplacementTransform(loss_label, backward_label),
            FadeOut(comparison_lines),
            FadeOut(target_labels),
        )

        # Show gradient equations
        self.play(Write(grad_title), run_time=0.5)
        self.play(Write(grad_eq1), run_time=1.0)
        self.wait(0.3)

        # Backward propagation animation (reverse order)
        for layer_idx in range(len(layer_sizes) - 1, -1, -1):
            neurons = get_neurons(all_layers[layer_idx])
            glows = get_glows(all_layers[layer_idx])

            # Activate neurons with gradient color (orange/red)
            self.play(
                *[n.animate.set_fill(ORANGE, opacity=0.6) for n in neurons],
                *[g.animate.set_stroke(color=ORANGE, opacity=0.6) for g in glows],
                run_time=0.4,
            )

            # Animate gradients flowing backward through connections
            if layer_idx > 0:
                layer_conns = all_connections[layer_idx - 1]

                # Create backward traveling dots (from end to start)
                dots = VGroup()
                for conn in layer_conns:
                    dot = Dot(radius=0.06, color=RED_B)
                    dot.move_to(conn.get_end())
                    dots.add(dot)

                self.add(dots)

                # Connections light up orange/red for gradients
                self.play(
                    *[
                        conn.animate.set_stroke(color=RED_C, opacity=0.7)
                        for conn in layer_conns
                    ],
                    *[
                        dot.animate.move_to(layer_conns[i].get_start())
                        for i, dot in enumerate(dots)
                    ],
                    run_time=0.5,
                )

                self.play(
                    FadeOut(dots),
                    *[
                        conn.animate.set_stroke(color=ORANGE, opacity=0.5)
                        for conn in layer_conns
                    ],
                    run_time=0.3,
                )

            self.wait(0.15)

        self.wait(0.3)

        # ===== PHASE 4: UPDATE WEIGHTS =====
        self.play(
            ReplacementTransform(backward_label, update_label),
        )

        # Show weight update equation
        self.play(Write(update_eq), run_time=0.8)
        self.play(FadeIn(learning_rate_note), run_time=0.4)

        # Animate weight updates - connections flash and change thickness
        for layer_conns in all_connections:
            # Flash green to show update
            self.play(
                *[
                    conn.animate.set_stroke(
                        color=GREEN_B, opacity=0.8, width=conn.weight * 2.5
                    )
                    for conn in layer_conns
                ],
                run_time=0.3,
            )
            self.play(
                *[
                    conn.animate.set_stroke(
                        color=GREY_B, opacity=0.5, width=conn.weight * 2.2
                    )
                    for conn in layer_conns
                ],
                run_time=0.3,
            )

        # Reset neurons
        for layer_idx, layer in enumerate(all_layers):
            neurons = get_neurons(layer)
            glows = get_glows(layer)
            self.play(
                *[n.animate.set_fill(BLACK, opacity=0.9) for n in neurons],
                *[
                    g.animate.set_stroke(color=glow_colors[layer_idx], opacity=0)
                    for g in glows
                ],
                run_time=0.2,
            )

        # Final summary - show all phases
        summary_title = Text("Training Loop", font_size=28, color=WHITE)
        summary_title.move_to(eq_panel_x + UP * 2.8)

        summary_items = VGroup(
            Text("1. Forward → compute ŷ", font_size=20, color=YELLOW),
            Text("2. Loss → compare ŷ vs y", font_size=20, color=RED_B),
            Text("3. Backward → compute ∂L/∂W", font_size=20, color=ORANGE),
            Text("4. Update → W = W - α·∂L/∂W", font_size=20, color=GREEN_B),
        )
        summary_items.arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        summary_items.next_to(summary_title, DOWN, buff=0.5)

        self.play(
            ReplacementTransform(update_label, summary_title),
            FadeOut(loss_eq),
            FadeOut(grad_title),
            FadeOut(grad_eq1),
            FadeOut(update_eq),
            FadeOut(learning_rate_note),
        )

        self.play(
            LaggedStart(*[Write(item) for item in summary_items], lag_ratio=0.2),
            run_time=1.5,
        )

        # One more forward-backward cycle to reinforce
        self.wait(0.5)

        # Quick forward
        for layer_idx in range(len(layer_sizes)):
            neurons = get_neurons(all_layers[layer_idx])
            self.play(
                *[n.animate.set_fill(YELLOW, opacity=0.5) for n in neurons],
                run_time=0.15,
            )
        self.wait(0.2)

        # Quick backward
        for layer_idx in range(len(layer_sizes) - 1, -1, -1):
            neurons = get_neurons(all_layers[layer_idx])
            self.play(
                *[n.animate.set_fill(ORANGE, opacity=0.5) for n in neurons],
                run_time=0.15,
            )

        # Reset
        for layer in all_layers:
            neurons = get_neurons(layer)
            self.play(
                *[n.animate.set_fill(BLACK, opacity=0.9) for n in neurons],
                run_time=0.1,
            )

        self.wait(2)


class LinearTransformation2Dto3D(ThreeDScene):
    def construct(self):
        import numpy as np

        # Camera setup
        frame = self.camera.frame
        frame.set_euler_angles(theta=-30 * DEGREES, phi=70 * DEGREES)

        # Title
        title = Text("Linear Transformation: 2D → 3D", font_size=36)
        title.to_edge(UP)
        title.fix_in_frame()

        # ===== TARGET SURFACE =====
        # Create a complex 3D surface that represents "learned representation"
        def target_surface_func(u, v):
            x = u
            y = v
            # Complex surface: combination of sine waves and gaussian
            z = (
                0.5 * np.sin(2 * u) * np.cos(2 * v)
                + 0.3 * np.exp(-0.5 * (u**2 + v**2))
                + 0.2 * np.sin(3 * u + v)
            )
            return np.array([x, y, z])

        target_surface = ParametricSurface(
            target_surface_func,
            u_range=[-2, 2],
            v_range=[-2, 2],
            resolution=(30, 30),
            color=BLUE_D,
            opacity=0.4,
        )

        # ===== 2D INPUT POINTS =====
        # Generate grid of 2D input points
        np.random.seed(42)
        num_points = 25
        input_2d = []
        for i in range(5):
            for j in range(5):
                x = -1.5 + i * 0.75 + np.random.uniform(-0.1, 0.1)
                y = -1.5 + j * 0.75 + np.random.uniform(-0.1, 0.1)
                input_2d.append([x, y])
        input_2d = np.array(input_2d)

        # ===== WEIGHT MATRIX AND BIAS =====
        # Initial random weights (2x3 matrix to go from 2D to 3D)
        # Actually we need 3x2 to transform 2D input to 3D output
        W_initial = np.array(
            [
                [0.5, 0.3],  # weights for x output
                [0.2, 0.6],  # weights for y output
                [0.1, 0.1],  # weights for z output
            ]
        )
        b_initial = np.array([0.0, 0.0, 0.5])

        # Target weights that better fit the surface
        W_target = np.array(
            [
                [1.0, 0.0],  # x stays mostly as x
                [0.0, 1.0],  # y stays mostly as y
                [0.3, 0.4],  # z is learned combination
            ]
        )
        b_target = np.array([0.0, 0.0, 0.0])

        # Create ValueTrackers for animation
        weight_progress = ValueTracker(0)

        def get_current_W():
            t = weight_progress.get_value()
            return W_initial * (1 - t) + W_target * t

        def get_current_b():
            t = weight_progress.get_value()
            return b_initial * (1 - t) + b_target * t

        # Function to transform 2D points to 3D
        def transform_points(W, b):
            # z = Wx + b
            return np.dot(input_2d, W.T) + b

        # ===== CREATE 3D COORDINATE SYSTEM =====
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-2, 2, 1],
            height=6,
            width=6,
            depth=4,
        )

        # Axis labels
        x_label = Text("x", font_size=24).next_to(axes.x_axis.get_end(), RIGHT)
        y_label = Text("y", font_size=24).next_to(axes.y_axis.get_end(), UP)
        z_label = Text("z", font_size=24).next_to(axes.z_axis.get_end(), OUT)

        # ===== CREATE ANIMATED POINTS =====
        def create_projected_points():
            W = get_current_W()
            b = get_current_b()
            points_3d = transform_points(W, b)

            dots = Group()  # Use Group instead of VGroup for 3D objects
            for i, pt in enumerate(points_3d):
                # Color based on distance to surface
                target_z = (
                    target_surface_func(pt[0], pt[1])[2]
                    if -2 <= pt[0] <= 2 and -2 <= pt[1] <= 2
                    else 0
                )
                error = abs(pt[2] - target_z)
                # Interpolate color from green (close) to red (far)
                color = interpolate_color(GREEN, RED, min(error * 2, 1))

                dot = Sphere(radius=0.08, color=color)
                dot.move_to(axes.c2p(pt[0], pt[1], pt[2]))
                dots.add(dot)
            return dots

        projected_points = always_redraw(create_projected_points)

        # ===== EQUATION DISPLAY =====
        eq_background = Rectangle(
            width=4.5,
            height=2.2,
            fill_color=BLACK,
            fill_opacity=0.8,
            stroke_color=WHITE,
            stroke_width=1,
        )
        eq_background.to_corner(UL, buff=0.3)
        eq_background.fix_in_frame()

        eq_title = Text("Transformation:", font_size=22, color=WHITE)
        eq_title.next_to(eq_background.get_top(), DOWN, buff=0.2)
        eq_title.fix_in_frame()

        eq_main = Text("z = Wx + b", font_size=26, color=YELLOW)
        eq_main.next_to(eq_title, DOWN, buff=0.25)
        eq_main.fix_in_frame()

        eq_dims = Text("W: 3×2    b: 3×1", font_size=18, color=GREY_A)
        eq_dims.next_to(eq_main, DOWN, buff=0.2)
        eq_dims.fix_in_frame()

        eq_input = Text("input: 2D → output: 3D", font_size=16, color=TEAL_B)
        eq_input.next_to(eq_dims, DOWN, buff=0.15)
        eq_input.fix_in_frame()

        eq_group = VGroup(eq_background, eq_title, eq_main, eq_dims, eq_input)

        # ===== LOSS INDICATOR =====
        def get_loss():
            W = get_current_W()
            b = get_current_b()
            points_3d = transform_points(W, b)
            total_loss = 0
            count = 0
            for pt in points_3d:
                if -2 <= pt[0] <= 2 and -2 <= pt[1] <= 2:
                    target_z = target_surface_func(pt[0], pt[1])[2]
                    total_loss += (pt[2] - target_z) ** 2
                    count += 1
            return total_loss / max(count, 1)

        loss_label = Text("Loss: ", font_size=22, color=WHITE)
        loss_label.to_corner(UR, buff=0.5)
        loss_label.shift(DOWN * 0.5)
        loss_label.fix_in_frame()

        loss_value = DecimalNumber(get_loss(), num_decimal_places=3, color=RED_B)
        loss_value.next_to(loss_label, RIGHT, buff=0.1)
        loss_value.fix_in_frame()
        loss_value.add_updater(lambda m: m.set_value(get_loss()))
        loss_value.add_updater(
            lambda m: m.set_color(interpolate_color(GREEN, RED, min(get_loss() * 3, 1)))
        )

        # ===== LEGEND =====
        legend_bg = Rectangle(
            width=3,
            height=1.2,
            fill_color=BLACK,
            fill_opacity=0.8,
            stroke_width=1,
        )
        legend_bg.to_corner(DR, buff=0.3)
        legend_bg.fix_in_frame()

        legend_title = Text("Legend", font_size=18, color=WHITE)
        legend_title.next_to(legend_bg.get_top(), DOWN, buff=0.1)
        legend_title.fix_in_frame()

        surface_legend = VGroup(
            Square(
                side_length=0.2, fill_color=BLUE_D, fill_opacity=0.5, stroke_width=0
            ),
            Text("Target surface", font_size=14, color=GREY_A),
        ).arrange(RIGHT, buff=0.1)
        surface_legend.next_to(legend_title, DOWN, buff=0.15)
        surface_legend.fix_in_frame()

        points_legend = VGroup(
            Dot(radius=0.08, color=YELLOW),
            Text("Projected points", font_size=14, color=GREY_A),
        ).arrange(RIGHT, buff=0.1)
        points_legend.next_to(surface_legend, DOWN, buff=0.1, aligned_edge=LEFT)
        points_legend.fix_in_frame()

        legend_group = VGroup(legend_bg, legend_title, surface_legend, points_legend)

        # ===== ANIMATION SEQUENCE =====

        # Show title
        self.play(Write(title))
        self.wait(0.3)

        # Show axes
        self.play(ShowCreation(axes), run_time=1.5)
        self.wait(0.3)

        # Show equation panel
        self.play(FadeIn(eq_group))
        self.wait(0.5)

        # Show target surface
        surface_intro = Text(
            "Target: Complex 3D surface to learn", font_size=20, color=BLUE_B
        )
        surface_intro.next_to(title, DOWN, buff=0.3)
        surface_intro.fix_in_frame()

        self.play(Write(surface_intro))
        self.play(ShowCreation(target_surface), run_time=2)
        self.wait(0.5)
        self.play(FadeOut(surface_intro))

        # Show initial projected points
        points_intro = Text(
            "Initial projection with random W, b", font_size=20, color=YELLOW
        )
        points_intro.next_to(title, DOWN, buff=0.3)
        points_intro.fix_in_frame()

        self.play(Write(points_intro))
        self.add(projected_points)
        self.play(FadeIn(loss_label), FadeIn(loss_value))
        self.wait(0.5)
        self.play(FadeOut(points_intro))

        # Show legend
        self.play(FadeIn(legend_group))

        # Rotate camera to show 3D
        self.play(
            frame.animate.set_euler_angles(theta=20 * DEGREES, phi=60 * DEGREES),
            run_time=2,
        )
        self.wait(0.5)

        # ===== MAIN ANIMATION: LEARNING =====
        learning_text = Text(
            "Learning: Adjusting W and b...", font_size=22, color=GREEN_B
        )
        learning_text.next_to(title, DOWN, buff=0.3)
        learning_text.fix_in_frame()

        self.play(Write(learning_text))

        # Animate weight optimization
        self.play(
            weight_progress.animate.set_value(1.0),
            frame.animate.set_euler_angles(theta=-20 * DEGREES, phi=70 * DEGREES),
            run_time=5,
            rate_func=smooth,
        )

        self.wait(0.5)
        self.play(FadeOut(learning_text))

        # Final text
        final_text = Text(
            "Points now approximate the target surface!", font_size=20, color=GREEN
        )
        final_text.next_to(title, DOWN, buff=0.3)
        final_text.fix_in_frame()

        self.play(Write(final_text))

        # Final rotation to show result
        self.play(
            frame.animate.set_euler_angles(theta=60 * DEGREES, phi=65 * DEGREES),
            run_time=3,
        )
        self.play(
            frame.animate.set_euler_angles(theta=-30 * DEGREES, phi=75 * DEGREES),
            run_time=3,
        )

        self.wait(2)


class SurfaceFittingWithActivation(ThreeDScene):
    def construct(self):
        import numpy as np

        # Camera setup
        frame = self.camera.frame
        frame.set_euler_angles(theta=-20 * DEGREES, phi=70 * DEGREES)

        # Title
        title = Text("Neural Network: Learning Complex Surfaces", font_size=32)
        title.to_edge(UP)
        title.fix_in_frame()

        # ===== TARGET SURFACE (more complex) =====
        def target_func(x, y):
            # Complex non-linear surface
            return (
                0.5 * np.sin(2.5 * x) * np.cos(2.5 * y)
                + 0.3 * np.cos(3 * x - y)
                + 0.2 * np.sin(x + 2 * y)
            )

        def target_surface_func(u, v):
            return np.array([u, v, target_func(u, v)])

        target_surface = ParametricSurface(
            target_surface_func,
            u_range=[-2, 2],
            v_range=[-2, 2],
            resolution=(40, 40),
            color=BLUE_E,
            opacity=0.35,
        )

        # Axes
        axes = ThreeDAxes(
            x_range=[-2.5, 2.5, 1],
            y_range=[-2.5, 2.5, 1],
            z_range=[-1.5, 1.5, 0.5],
            height=5,
            width=5,
            depth=3,
        )

        # ===== LEARNABLE SURFACE =====
        # Simulate a neural network learning: start with flat, end with target-like

        # Parameters that will be animated
        learning_progress = ValueTracker(0)

        # Coefficients for the learned surface
        # Start: flat plane, End: approximation of target
        def learned_func(x, y, t):
            # Linear interpolation from flat to complex
            flat = 0.0
            learned = (
                0.45 * np.sin(2.5 * x) * np.cos(2.5 * y)
                + 0.28 * np.cos(3 * x - y)
                + 0.18 * np.sin(x + 2 * y)
            )
            return flat * (1 - t) + learned * t

        def create_learned_surface():
            t = learning_progress.get_value()

            def surface_func(u, v):
                return np.array([u, v, learned_func(u, v, t)])

            # Color based on progress: red (bad) -> yellow -> green (good)
            color = interpolate_color(RED, GREEN, t)

            surface = ParametricSurface(
                surface_func,
                u_range=[-2, 2],
                v_range=[-2, 2],
                resolution=(25, 25),
                color=color,
                opacity=0.6,
            )
            return surface

        learned_surface = always_redraw(create_learned_surface)

        # ===== EQUATION PANEL =====
        eq_bg = Rectangle(
            width=5,
            height=2.5,
            fill_color=BLACK,
            fill_opacity=0.85,
            stroke_color=WHITE,
            stroke_width=1,
        )
        eq_bg.to_corner(UL, buff=0.2)
        eq_bg.fix_in_frame()

        nn_eq_title = Text("Neural Network Layer:", font_size=20, color=WHITE)
        nn_eq_title.next_to(eq_bg.get_top(), DOWN, buff=0.15)
        nn_eq_title.fix_in_frame()

        nn_eq1 = Text("h = σ(W₁x + b₁)", font_size=22, color=TEAL_B)
        nn_eq1.next_to(nn_eq_title, DOWN, buff=0.2)
        nn_eq1.fix_in_frame()

        nn_eq2 = Text("y = W₂h + b₂", font_size=22, color=YELLOW)
        nn_eq2.next_to(nn_eq1, DOWN, buff=0.15)
        nn_eq2.fix_in_frame()

        nn_note = Text("σ = ReLU/tanh (non-linear)", font_size=16, color=GREY_A)
        nn_note.next_to(nn_eq2, DOWN, buff=0.2)
        nn_note.fix_in_frame()

        eq_panel = VGroup(eq_bg, nn_eq_title, nn_eq1, nn_eq2, nn_note)

        # ===== ERROR METRIC =====
        def get_mse():
            t = learning_progress.get_value()
            # Simulated MSE that decreases with learning
            return 0.5 * (1 - t) ** 2 + 0.01

        error_label = Text("MSE: ", font_size=20, color=WHITE)
        error_label.to_corner(UR, buff=0.4)
        error_label.shift(DOWN * 0.3)
        error_label.fix_in_frame()

        error_value = DecimalNumber(get_mse(), num_decimal_places=4, color=RED)
        error_value.next_to(error_label, RIGHT, buff=0.1)
        error_value.fix_in_frame()
        error_value.add_updater(lambda m: m.set_value(get_mse()))
        error_value.add_updater(
            lambda m: m.set_color(interpolate_color(GREEN, RED, min(get_mse() * 5, 1)))
        )

        epoch_label = Text("Epoch: ", font_size=18, color=GREY_A)
        epoch_label.next_to(error_label, DOWN, buff=0.2, aligned_edge=LEFT)
        epoch_label.fix_in_frame()

        epoch_value = DecimalNumber(0, num_decimal_places=0, color=WHITE)
        epoch_value.next_to(epoch_label, RIGHT, buff=0.1)
        epoch_value.fix_in_frame()
        epoch_value.add_updater(
            lambda m: m.set_value(int(learning_progress.get_value() * 1000))
        )

        # ===== LEGEND =====
        legend_bg = Rectangle(
            width=3.5,
            height=1.4,
            fill_color=BLACK,
            fill_opacity=0.85,
            stroke_width=1,
        )
        legend_bg.to_corner(DR, buff=0.2)
        legend_bg.fix_in_frame()

        target_legend = VGroup(
            Square(
                side_length=0.25, fill_color=BLUE_E, fill_opacity=0.5, stroke_width=0
            ),
            Text("Target surface (y_true)", font_size=14, color=GREY_A),
        ).arrange(RIGHT, buff=0.15)
        target_legend.move_to(legend_bg.get_center() + UP * 0.3)
        target_legend.fix_in_frame()

        learned_legend = VGroup(
            Square(
                side_length=0.25, fill_color=ORANGE, fill_opacity=0.7, stroke_width=0
            ),
            Text("Learned surface (ŷ)", font_size=14, color=GREY_A),
        ).arrange(RIGHT, buff=0.15)
        learned_legend.next_to(target_legend, DOWN, buff=0.15, aligned_edge=LEFT)
        learned_legend.fix_in_frame()

        legend_group = VGroup(legend_bg, target_legend, learned_legend)

        # ===== ANIMATION SEQUENCE =====

        self.play(Write(title))
        self.play(ShowCreation(axes), run_time=1)
        self.wait(0.3)

        # Show target surface
        target_intro = Text(
            "Target: Complex surface to approximate", font_size=18, color=BLUE_B
        )
        target_intro.next_to(title, DOWN, buff=0.2)
        target_intro.fix_in_frame()

        self.play(Write(target_intro))
        self.play(ShowCreation(target_surface), run_time=2)
        self.wait(0.5)
        self.play(FadeOut(target_intro))

        # Show equation panel
        self.play(FadeIn(eq_panel))
        self.wait(0.5)

        # Show initial (flat) learned surface
        init_text = Text(
            "Initial: Random weights (flat surface)", font_size=18, color=RED
        )
        init_text.next_to(title, DOWN, buff=0.2)
        init_text.fix_in_frame()

        self.play(Write(init_text))
        self.add(learned_surface)
        self.play(FadeIn(error_label), FadeIn(error_value))
        self.play(FadeIn(epoch_label), FadeIn(epoch_value))
        self.wait(0.5)
        self.play(FadeOut(init_text))

        # Show legend
        self.play(FadeIn(legend_group))

        # Rotate to show 3D
        self.play(
            frame.animate.set_euler_angles(theta=30 * DEGREES, phi=65 * DEGREES),
            run_time=2,
        )

        # ===== MAIN LEARNING ANIMATION =====
        learning_text = Text(
            "Training... (Gradient Descent)", font_size=20, color=GREEN_B
        )
        learning_text.next_to(title, DOWN, buff=0.2)
        learning_text.fix_in_frame()

        self.play(Write(learning_text))

        # Animate learning with camera rotation
        self.play(
            learning_progress.animate.set_value(1.0),
            frame.animate.set_euler_angles(theta=-40 * DEGREES, phi=70 * DEGREES),
            run_time=8,
            rate_func=smooth,
        )

        self.play(FadeOut(learning_text))

        # Final result
        final_text = Text(
            "Converged! Learned surface ≈ Target", font_size=20, color=GREEN
        )
        final_text.next_to(title, DOWN, buff=0.2)
        final_text.fix_in_frame()

        self.play(Write(final_text))

        # Show overlay by making learned surface semi-transparent
        self.play(
            frame.animate.set_euler_angles(theta=0 * DEGREES, phi=90 * DEGREES),
            run_time=2,
        )
        self.wait(0.5)

        # Final rotation
        self.play(
            frame.animate.set_euler_angles(theta=45 * DEGREES, phi=60 * DEGREES),
            run_time=3,
        )
        self.play(
            frame.animate.set_euler_angles(theta=-30 * DEGREES, phi=70 * DEGREES),
            run_time=3,
        )

        self.wait(2)
