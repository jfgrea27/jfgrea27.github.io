from manimlib import *


class LinearTransformation2Dto3D(ThreeDScene):
    def construct(self):
        import numpy as np

        # ===== INITIAL CAMERA SETUP (2D) =====
        frame = self.camera.frame
        frame.set_euler_angles(theta=0, phi=0)  # Looking down at x-y plane

        # ===== CREATE 2D COORDINATE SYSTEM (shown first) =====
        axes_2d = Axes(
            x_range=[0, 2, 0.5],
            y_range=[0, 100, 20],
            height=6,
            width=6,
        )

        # 2D Axis labels
        x_label_2d = Text("height (m)", font_size=20).next_to(
            axes_2d.x_axis.get_end(), RIGHT
        )
        y_label_2d = Text("weight (kg)", font_size=20).next_to(
            axes_2d.y_axis.get_end(), UP
        )
        axis_labels_2d = VGroup(x_label_2d, y_label_2d)

        # ===== CREATE 3D COORDINATE SYSTEM (shown later) =====
        axes = ThreeDAxes(
            x_range=[0, 2, 0.5],
            y_range=[0, 100, 20],
            z_range=[0, 1, 0.2],
            height=6,
            width=6,
            depth=4,
        )

        # 3D Axis labels
        x_label = Text("height (m)", font_size=20).next_to(axes.x_axis.get_end(), RIGHT)
        y_label = Text("weight (kg)", font_size=20).next_to(axes.y_axis.get_end(), UP)
        z_label = Text("z", font_size=20).next_to(axes.z_axis.get_end(), OUT)
        axis_labels_3d = VGroup(x_label, y_label, z_label)

        # ===== SIGMOID FUNCTION =====
        def sigmoid(x):
            return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

        # ===== LINEAR TRANSFORMATION PLANE (before bias) =====
        # z = W1[2,0]*x + W1[2,1]*y = 0.8*x + 0.02*y
        linear_plane = ParametricSurface(
            lambda u, v: axes.c2p(u, v, 0.8 * u + 0.02 * v),
            u_range=[0, 2],
            v_range=[0, 100],
            resolution=(4, 4),
            color=GREEN,
            opacity=0.3,
        )

        # ===== BIASED PLANE (after adding bias) =====
        # z = 0.8*x + 0.02*y + (-1.2) = 0.8*x + 0.02*y - 1.2
        biased_plane = ParametricSurface(
            lambda u, v: axes.c2p(u, v, 0.8 * u + 0.02 * v - 1.2),
            u_range=[0, 2],
            v_range=[0, 100],
            resolution=(4, 4),
            color=GREEN,
            opacity=0.3,
        )

        # ===== ACTIVATED SURFACE (after sigmoid element-wise) =====
        # All outputs get sigmoid: (sigmoid(x), sigmoid(y), sigmoid(0.8*x + 0.02*y - 1.2))
        activated_plane = ParametricSurface(
            lambda u, v: axes.c2p(
                sigmoid(u),
                sigmoid(v),
                sigmoid(0.8 * u + 0.02 * v - 1.2)
            ),
            u_range=[0, 2],
            v_range=[0, 100],
            resolution=(10, 10),
            color=GREEN,
            opacity=0.3,
        )

        # ===== PERFECT PLANES (for pink point transformation) =====
        # Perfect weights: W_perfect[2] = [0.6, 0.012], b_perfect[2] = -0.8

        # Perfect linear plane: z = 0.6*x + 0.012*y
        perfect_linear_plane = ParametricSurface(
            lambda u, v: axes.c2p(u, v, 0.6 * u + 0.012 * v),
            u_range=[0, 2],
            v_range=[0, 100],
            resolution=(4, 4),
            color=PINK,
            opacity=0.3,
        )

        # Perfect biased plane: z = 0.6*x + 0.012*y - 0.8
        perfect_biased_plane = ParametricSurface(
            lambda u, v: axes.c2p(u, v, 0.6 * u + 0.012 * v - 0.8),
            u_range=[0, 2],
            v_range=[0, 100],
            resolution=(4, 4),
            color=PINK,
            opacity=0.3,
        )

        # Perfect activated surface: all outputs get sigmoid element-wise
        perfect_activated_plane = ParametricSurface(
            lambda u, v: axes.c2p(
                sigmoid(u),
                sigmoid(v),
                sigmoid(0.6 * u + 0.012 * v - 0.8)
            ),
            u_range=[0, 2],
            v_range=[0, 100],
            resolution=(10, 10),
            color=PINK,
            opacity=0.3,
        )

        # ===== ALL INPUT POINTS =====
        np.random.seed(42)
        all_input_points = []
        for i in range(5):
            for j in range(5):
                x = np.random.uniform(0.3, 1.8)
                y = np.random.uniform(10, 90)
                all_input_points.append([x, y, 0])
        all_input_points = np.array(all_input_points)

        # Pick one point to track (index 12 - roughly middle)
        tracked_idx = 12
        tracked_x, tracked_y = (
            all_input_points[tracked_idx][0],
            all_input_points[tracked_idx][1],
        )

        # Create dots for all input points (on z=0 plane)
        yellow_dots = Group()
        for i, pt in enumerate(all_input_points):
            dot = Sphere(radius=0.06, color=YELLOW)
            dot.move_to(axes.c2p(pt[0], pt[1], 0))
            yellow_dots.add(dot)

        # ===== WEIGHTS AND BIASES =====
        # W transforms [x, y, 0] -> [out_x, out_y, out_z]
        # Initial weights (not perfect fit)
        W1 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.8, 0.02, 0.0]])
        b1 = np.array([0.0, 0.0, -1.2])

        # Perfect weights (for pink point - matches target function)
        W_perfect = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.6, 0.012, 0.0],  # Tuned to match target_z after sigmoid
            ]
        )
        b_perfect = np.array([0.0, 0.0, -0.8])

        # Updated weights (closer to perfect)
        W2 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.65, 0.014, 0.0]])
        b2 = np.array([0.0, 0.0, -0.9])

        # ===== COMPUTE TRANSFORMATIONS FOR ALL POINTS =====
        def forward_pass(points, W, b):
            results = []
            for pt in points:
                linear = W @ pt
                biased = linear + b
                # Apply sigmoid element-wise to ALL outputs (real neural network behavior)
                activated = sigmoid(biased)
                results.append(
                    {
                        "input": pt,
                        "linear": linear,
                        "biased": biased,
                        "activated": activated,
                    }
                )
            return results

        results1 = forward_pass(all_input_points, W1, b1)
        results_perfect = forward_pass(all_input_points, W_perfect, b_perfect)
        results2 = forward_pass(all_input_points, W2, b2)

        # Create transformed dot groups
        def create_dots_at_stage(results, stage, color=YELLOW, radius=0.06):
            dots = Group()
            for r in results:
                dot = Sphere(radius=radius, color=color)
                dot.move_to(axes.c2p(*r[stage]))
                dots.add(dot)
            return dots

        linear_dots = create_dots_at_stage(results1, "linear")
        biased_dots = create_dots_at_stage(results1, "biased")
        activated_dots = create_dots_at_stage(results1, "activated")

        # ===== TRACKED ORANGE POINT STAGES =====
        orange_input = Sphere(radius=0.08, color=ORANGE)
        orange_input.move_to(axes.c2p(tracked_x, tracked_y, 0))

        orange_linear = Sphere(radius=0.08, color=ORANGE)
        orange_linear.move_to(axes.c2p(*results1[tracked_idx]["linear"]))

        orange_biased = Sphere(radius=0.08, color=ORANGE)
        orange_biased.move_to(axes.c2p(*results1[tracked_idx]["biased"]))

        orange_activated = Sphere(radius=0.08, color=ORANGE)
        orange_activated.move_to(axes.c2p(*results1[tracked_idx]["activated"]))

        # Orange after weight update
        orange_updated = Sphere(radius=0.08, color=ORANGE)
        orange_updated.move_to(axes.c2p(*results2[tracked_idx]["activated"]))

        # ===== PINK POINT (PERFECT TRANSFORMATION) =====
        pink_input = Sphere(radius=0.08, color=PINK)
        pink_input.move_to(axes.c2p(tracked_x, tracked_y, 0))

        pink_linear = Sphere(radius=0.08, color=PINK)
        pink_linear.move_to(axes.c2p(*results_perfect[tracked_idx]["linear"]))

        pink_biased = Sphere(radius=0.08, color=PINK)
        pink_biased.move_to(axes.c2p(*results_perfect[tracked_idx]["biased"]))

        # Pink lands at perfect activated position
        pink_final = Sphere(radius=0.08, color=PINK)
        pink_final.move_to(axes.c2p(*results_perfect[tracked_idx]["activated"]))

        # ===== ERROR LINE =====
        # Error between orange (our model) and pink (perfect model)
        error_line = Line(
            axes.c2p(*results1[tracked_idx]["activated"]),
            axes.c2p(*results_perfect[tracked_idx]["activated"]),
            color=RED,
            stroke_width=4,
        )

        error_line_updated = Line(
            axes.c2p(*results2[tracked_idx]["activated"]),
            axes.c2p(*results_perfect[tracked_idx]["activated"]),
            color=RED,
            stroke_width=4,
        )

        # ===== WEIGHTS PANEL =====
        def create_weights_panel(W, b, position=UR):
            # Show 3x2 matrix (projecting 2D input [x,y] to 3D output [out_x, out_y, out_z])
            # W is 3x3 but third column is zeros, so we show only first 2 columns
            W_display = W[:, :2]  # 3x2 matrix
            b_display = b.reshape(-1, 1)  # 3x1 bias vector

            weights_matrix = Matrix(W_display.round(2), v_buff=0.4, h_buff=0.5)
            biases_vector = Matrix(b_display.round(2), v_buff=0.4)
            weights_matrix.scale(0.45)
            biases_vector.scale(0.45)

            weights_label = Text("W", font_size=18)
            biases_label = Text("b", font_size=18)
            weights_label.next_to(weights_matrix, UP, buff=0.1)
            biases_label.next_to(biases_vector, UP, buff=0.1)

            weights_group = VGroup(weights_label, weights_matrix).arrange(
                DOWN, buff=0.1
            )
            biases_group = VGroup(biases_label, biases_vector).arrange(DOWN, buff=0.1)

            matrix_content = VGroup(weights_group, biases_group).arrange(
                RIGHT, buff=0.3
            )

            box_padding = 0.15
            matrix_box = Rectangle(
                width=matrix_content.get_width() + 2 * box_padding,
                height=matrix_content.get_height() + 2 * box_padding,
                fill_color=BLACK,
                fill_opacity=0.8,
                stroke_color=WHITE,
                stroke_width=1,
            )
            matrix_content.move_to(matrix_box.get_center())

            panel = VGroup(matrix_box, matrix_content)
            panel.to_corner(position, buff=0.3)
            panel.fix_in_frame()
            return panel, weights_matrix, biases_vector

        matrix_panel1, weights_matrix1, biases_vector1 = create_weights_panel(W1, b1)
        matrix_panel2, weights_matrix2, biases_vector2 = create_weights_panel(W2, b2)
        matrix_panel_perfect, _, _ = create_weights_panel(W_perfect, b_perfect)

        # Activation function label
        activation_label = Tex(r"\sigma(z) = \frac{1}{1 + e^{-z}}", font_size=22)
        activation_label.next_to(matrix_panel1, DOWN, buff=0.15)
        activation_label.fix_in_frame()

        # Error label
        error_label = Text("Error", font_size=18, color=RED)
        error_label.fix_in_frame()

        # ===== ANIMATIONS =====

        # (1) Draw 2D height and weight axes first
        self.play(ShowCreation(axes_2d), run_time=1.5)
        self.play(FadeIn(axis_labels_2d), run_time=0.5)

        # (2) Draw all points (yellow) on 2D plane
        self.play(LaggedStartMap(FadeIn, yellow_dots), run_time=1.5)
        self.wait(0.5)

        # (3) Change one yellow point to orange
        self.play(
            yellow_dots[tracked_idx].animate.set_color(ORANGE),
            run_time=1,
        )
        self.wait(0.5)

        # Transition from 2D to 3D axes
        self.play(
            FadeOut(axes_2d),
            FadeOut(axis_labels_2d),
            FadeIn(axes),
            FadeIn(axis_labels_3d),
            run_time=1.5,
        )

        # Rotate to 3D view and zoom out to see all points
        self.play(
            frame.animate.reorient(-30, 70, 0).set_height(12),
            run_time=2,
        )

        # Show weights panel
        self.play(FadeIn(matrix_panel1), run_time=0.5)

        # (4) All points linearly transformed + show linear plane
        step_label = Text("Step 1: W × input", font_size=18, color=YELLOW)
        step_label.to_corner(UL, buff=0.3)
        step_label.fix_in_frame()
        self.play(FadeIn(step_label), run_time=0.5)
        self.play(
            Transform(yellow_dots, linear_dots),
            ShowCreation(linear_plane),
            run_time=2,
        )
        self.wait(0.5)

        # (5) All points have bias added + plane shifts down
        step_label2 = Text("Step 2: + bias", font_size=18, color=YELLOW)
        step_label2.to_corner(UL, buff=0.3)
        step_label2.fix_in_frame()
        self.play(FadeOut(step_label), FadeIn(step_label2), run_time=0.5)
        self.play(
            Transform(yellow_dots, biased_dots),
            Transform(linear_plane, biased_plane),
            run_time=2,
        )
        self.wait(0.5)

        # (6) All points have activation (hide plane after sigmoid)
        self.play(FadeIn(activation_label), run_time=0.5)
        step_label3 = Text("Step 3: σ(z) activation", font_size=18, color=YELLOW)
        step_label3.to_corner(UL, buff=0.3)
        step_label3.fix_in_frame()
        self.play(FadeOut(step_label2), FadeIn(step_label3), run_time=0.5)

        # Fade out the plane and transform points with activation
        self.play(
            Transform(yellow_dots, activated_dots),
            FadeOut(linear_plane),
            run_time=2,
        )
        self.wait(0.5)

        self.play(FadeOut(step_label3), run_time=0.5)

        # Zoom out to see the activated points
        self.play(frame.animate.set_height(14), run_time=1)

        # (7) Only orange point remains - fade out yellow dots
        other_dots = Group(
            *[yellow_dots[i] for i in range(len(yellow_dots)) if i != tracked_idx]
        )
        self.play(
            FadeOut(other_dots),
            run_time=1,
        )

        # Make the remaining dot clearly orange
        self.play(yellow_dots[tracked_idx].animate.set_color(ORANGE), run_time=0.5)
        self.wait(0.5)

        # Move camera for better view
        self.play(frame.animate.reorient(-45, 60, 0), run_time=1.5)

        # (8) Show perfect transformation with perfect weights
        perfect_label = Text("Perfect weights (pink)", font_size=18, color=PINK)
        perfect_label.to_corner(UL, buff=0.3)
        perfect_label.fix_in_frame()
        self.play(FadeIn(perfect_label), run_time=0.5)

        # Show perfect weights panel (on the left side)
        matrix_panel_perfect.to_corner(UL, buff=0.3)
        matrix_panel_perfect.shift(DOWN * 1.5)
        self.play(FadeIn(matrix_panel_perfect), run_time=0.5)

        # Zoom out to see both planes
        self.play(frame.animate.set_height(14), run_time=1)

        # Start pink at same 2D position as orange
        self.play(FadeIn(pink_input), run_time=0.5)

        # Pink: linear transformation + show perfect linear plane
        step_perfect1 = Text("Step 1: W × input", font_size=16, color=PINK)
        step_perfect1.next_to(perfect_label, DOWN, buff=0.1)
        step_perfect1.fix_in_frame()
        self.play(FadeIn(step_perfect1), run_time=0.3)
        self.play(
            Transform(pink_input, pink_linear),
            ShowCreation(perfect_linear_plane),
            run_time=1.5,
        )
        self.wait(0.3)

        # Pink: add bias + shift perfect plane
        step_perfect2 = Text("Step 2: + bias", font_size=16, color=PINK)
        step_perfect2.next_to(perfect_label, DOWN, buff=0.1)
        step_perfect2.fix_in_frame()
        self.play(FadeOut(step_perfect1), FadeIn(step_perfect2), run_time=0.3)
        self.play(
            Transform(pink_input, pink_biased),
            Transform(perfect_linear_plane, perfect_biased_plane),
            run_time=1.5,
        )
        self.wait(0.3)

        # Pink: activation (hide plane after sigmoid)
        step_perfect3 = Text("Step 3: σ(z) activation", font_size=16, color=PINK)
        step_perfect3.next_to(perfect_label, DOWN, buff=0.1)
        step_perfect3.fix_in_frame()
        self.play(FadeOut(step_perfect2), FadeIn(step_perfect3), run_time=0.3)
        self.play(
            Transform(pink_input, pink_final),
            FadeOut(perfect_linear_plane),
            run_time=1.5,
        )
        self.wait(0.5)

        self.play(FadeOut(perfect_label), FadeOut(step_perfect3), run_time=0.5)

        # (9) Show error line between orange and pink
        self.play(ShowCreation(error_line), run_time=1)
        error_label.next_to(error_line, RIGHT, buff=0.1)
        self.play(FadeIn(error_label), run_time=0.5)

        # Zoom in on the error (focus on orange and pink points)
        error_midpoint = (
            axes.c2p(*results1[tracked_idx]["activated"])
            + axes.c2p(*results_perfect[tracked_idx]["activated"])
        ) / 2
        self.play(
            frame.animate.set_height(4).move_to(error_midpoint),
            run_time=1.5,
        )
        self.wait(1)

        # (11) Update weights and move orange closer to pink
        update_label = Text("Update weights to reduce error", font_size=18, color=GREEN)
        update_label.to_corner(UL, buff=0.3)
        update_label.fix_in_frame()
        self.play(FadeIn(update_label), run_time=0.5)

        # Animate the entire panel transforming (W1, b1 -> W2, b2)
        self.play(
            Transform(matrix_panel1, matrix_panel2),
            run_time=1.5,
        )
        self.play(
            error_label.animate.next_to(error_line, RIGHT, buff=0.1),
            run_time=0.5,
        )

        # Move orange point closer to pink simultaneously with error line shrinking
        self.play(
            yellow_dots[tracked_idx].animate.move_to(
                axes.c2p(*results2[tracked_idx]["activated"])
            ),
            Transform(error_line, error_line_updated),
            run_time=2,
        )

        self.play(FadeOut(update_label), run_time=0.5)

        # Zoom back out to see the full picture
        self.play(
            frame.animate.set_height(12).move_to(ORIGIN),
            run_time=1.5,
        )

        self.wait(2)
