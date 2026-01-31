from manimlib import *


class YDistanceExample(Scene):
    def construct(self):
        # Same axes as scatter_plot.py
        axes = Axes(
            x_range=(0, 10),
            y_range=(0, 20),
            height=6,
            width=10,
            axis_config={
                "stroke_color": GREY_A,
                "stroke_width": 2,
            },
            y_axis_config={
                "include_tip": False,
            },
        )
        axes.add_coordinate_labels(
            font_size=20,
            num_decimal_places=1,
        )

        # Same data points as scatter_plot.py
        data_points = [
            (0.5, 3.0),
            (1, 1.8),
            (1.5, 4.5),
            (5, 12.5),
            (5.5, 10.0),
            (6, 11.3),
            (6.5, 14.8),
            (7, 13.0),
            (7.3, 16.2),
            (8, 15.5),
            (8.5, 18.0),
            (9, 17.2),
            (9.5, 19.5),
        ]

        # Create all the dots
        dots = VGroup()
        for x, y in data_points:
            dot = Dot(color=RED)
            dot.move_to(axes.c2p(x, y))
            dots.add(dot)

        # Final line of best fit: y = 2x + 1
        slope = 2.0
        intercept = 1.0
        line = axes.get_graph(lambda x: slope * x + intercept, color=BLUE)

        # Show everything at once (final state from scatter_plot.py)
        self.add(axes, dots, line)
        self.wait(1)

        # Pick a specific point to highlight (index 3: x=5, y=12.5)
        x_i = 5
        y_i = 12.5
        y_hat_i = slope * x_i + intercept  # Predicted: 2*5 + 1 = 11

        # Highlight the chosen point
        highlight_dot = Dot(color=YELLOW, radius=0.15)
        highlight_dot.move_to(axes.c2p(x_i, y_i))
        self.play(FadeIn(highlight_dot, scale=2))
        self.wait(0.5)

        # Group everything for zooming
        full_scene = VGroup(axes, dots, line, highlight_dot)

        # Zoom in on the highlighted point
        zoom_center = axes.c2p(x_i, (y_i + y_hat_i) / 2)
        self.play(
            full_scene.animate.scale(2.5).move_to(ORIGIN - zoom_center * 2.5 + ORIGIN),
            run_time=2
        )
        self.wait(0.5)

        # Create the predicted point on the line (y_hat_i)
        point_yhat = Dot(color=BLUE, radius=0.08)
        point_yhat.move_to(axes.c2p(x_i, y_hat_i))
        point_yhat.scale(2.5)  # Match the zoom scale

        self.play(FadeIn(point_yhat))
        self.wait(0.3)

        # Label for y_i (actual) - positioned relative to zoomed scene
        label_yi = Text("yᵢ", font_size=28, color=RED)
        label_yi.next_to(highlight_dot, RIGHT, buff=0.15)

        # Label for y_hat_i (predicted)
        label_yhat = Text("ŷᵢ", font_size=28, color=BLUE)
        label_yhat.next_to(point_yhat, RIGHT, buff=0.15)

        self.play(FadeIn(label_yi), FadeIn(label_yhat))
        self.wait(0.5)

        # Create the distance line between y_i and y_hat_i
        distance_line = Line(
            point_yhat.get_center(),
            highlight_dot.get_center(),
            color=YELLOW,
            stroke_width=3,
        )
        self.play(ShowCreation(distance_line))
        self.wait(0.3)

        # Create a brace showing the distance
        brace = Brace(distance_line, direction=LEFT, color=YELLOW)

        # Label for the distance
        distance_label = Text("yᵢ - ŷᵢ", font_size=24, color=YELLOW)
        distance_label.next_to(brace, LEFT, buff=0.15)

        self.play(GrowFromCenter(brace), FadeIn(distance_label))
        self.wait(0.5)

        # Show the actual numerical distance
        distance_value = y_i - y_hat_i
        value_label = Text(f"= {distance_value:.1f}", font_size=24, color=YELLOW)
        value_label.next_to(distance_label, DOWN, buff=0.1, aligned_edge=LEFT)

        self.play(FadeIn(value_label))
        self.wait(1)
