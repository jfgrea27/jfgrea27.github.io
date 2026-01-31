from manimlib import *
from matplotlib.pyplot import axes


class CoordinateSystemExample(Scene):
    def construct(self):
        axes = Axes(
            # x-axis ranges from -1 to 10, with a default step size of 1
            x_range=(0, 10),
            # y-axis ranges from -2 to 2 with a step size of 0.5
            y_range=(0, 20),
            # The axes will be stretched so as to match the specified
            # height and width
            height=6,
            width=10,
            # Axes is made of two NumberLine mobjects.  You can specify
            # their configuration with axis_config
            axis_config={
                "stroke_color": GREY_A,
                "stroke_width": 2,
            },
            # Alternatively, you can specify configuration for just one
            # of them, like this.
            y_axis_config={
                "include_tip": False,
            },
        )
        # Keyword arguments of add_coordinate_labels can be used to
        # configure the DecimalNumber mobjects which it creates and
        # adds to the axes
        axes.add_coordinate_labels(
            font_size=20,
            num_decimal_places=1,
        )
        self.add(axes)

        # Data points that roughly follow y = 2x + 1 with noisy scatter
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

        dots = VGroup()
        for x, y in data_points:
            dot = Dot(color=RED)
            dot.move_to(axes.c2p(x, y))
            dots.add(dot)

        self.play(FadeIn(dots, scale=0.5))
        self.wait(0.5)

        # Line parameters: y = mx + b
        slope = ValueTracker(1.0)
        intercept = ValueTracker(5.0)

        # Create the line of best fit
        def get_line():
            m = slope.get_value()
            b = intercept.get_value()
            return axes.get_graph(lambda x: m * x + b, color=BLUE)

        line = always_redraw(get_line)

        # Green dot on y-axis representing theta_0 (y-intercept)
        theta0_dot = Dot(radius=0.15)
        theta0_dot.set_color(GREEN)
        theta0_dot.set_z_index(10)  # Ensure it's on top
        theta0_dot.move_to(axes.c2p(0, intercept.get_value()))
        theta0_dot.add_updater(lambda d: d.move_to(axes.c2p(0, intercept.get_value())))

        # Orange delta triangle representing theta_1 (slope = rise/run)
        def get_slope_triangle():
            m = slope.get_value()
            b = intercept.get_value()
            # Triangle starts at x=2 on the line
            x_start = 2
            run = 2  # horizontal distance
            y_start = m * x_start + b
            y_end = m * (x_start + run) + b

            # Create the triangle: horizontal line, vertical line, and labels
            horizontal = Line(
                axes.c2p(x_start, y_start),
                axes.c2p(x_start + run, y_start),
                color=ORANGE,
                stroke_width=3,
            )
            vertical = Line(
                axes.c2p(x_start + run, y_start),
                axes.c2p(x_start + run, y_end),
                color=ORANGE,
                stroke_width=3,
            )
            # Labels for run and rise
            run_label = Text("Δx", font_size=24, color=ORANGE)
            run_label.next_to(horizontal, DOWN, buff=0.1)
            rise_label = Text("Δy", font_size=24, color=ORANGE)
            rise_label.next_to(vertical, RIGHT, buff=0.1)

            return VGroup(horizontal, vertical, run_label, rise_label)

        slope_triangle = always_redraw(get_slope_triangle)

        # Create theta labels with dynamic values (using Text to avoid LaTeX dependency)
        theta0_label = Text("θ₀ = ", font_size=36).set_color(GREEN)
        theta0_value = DecimalNumber(intercept.get_value(), num_decimal_places=2)
        theta0_value.set_color(GREEN)
        theta0_value.add_updater(lambda m: m.set_value(intercept.get_value()))
        theta0_group = VGroup(theta0_label, theta0_value).arrange(RIGHT, buff=0.1)
        theta0_group.to_corner(UR).shift(DOWN * 0.5)
        theta0_value.add_updater(lambda m: m.next_to(theta0_label, RIGHT, buff=0.1))

        theta1_label = Text("θ₁ = ", font_size=36).set_color(ORANGE)
        theta1_value = DecimalNumber(slope.get_value(), num_decimal_places=2)
        theta1_value.set_color(ORANGE)
        theta1_value.add_updater(lambda m: m.set_value(slope.get_value()))
        theta1_group = VGroup(theta1_label, theta1_value).arrange(RIGHT, buff=0.1)
        theta1_group.next_to(theta0_group, DOWN, aligned_edge=LEFT, buff=0.3)
        theta1_value.add_updater(lambda m: m.next_to(theta1_label, RIGHT, buff=0.1))

        self.play(
            FadeIn(line),
            FadeIn(theta0_dot),
            FadeIn(slope_triangle),
            FadeIn(theta0_group),
            FadeIn(theta1_group),
        )
        self.wait(0.5)

        # Create delta lines (residuals) from points to the line
        def get_deltas():
            m = slope.get_value()
            b = intercept.get_value()
            deltas = VGroup()
            for x, y in data_points:
                y_pred = m * x + b
                delta_line = Line(
                    axes.c2p(x, y),
                    axes.c2p(x, y_pred),
                    color=YELLOW,
                    stroke_width=2,
                )
                deltas.add(delta_line)
            return deltas

        deltas = always_redraw(get_deltas)
        self.play(FadeIn(deltas))
        self.wait(0.5)

        # Animate changing the y-intercept
        self.play(intercept.animate.set_value(0), run_time=2)
        self.wait(0.3)
        self.play(intercept.animate.set_value(8), run_time=2)
        self.wait(0.3)
        self.play(intercept.animate.set_value(1), run_time=1.5)
        self.wait(0.5)

        # Animate changing the gradient/slope
        self.play(slope.animate.set_value(0.5), run_time=2)
        self.wait(0.3)
        self.play(slope.animate.set_value(3.0), run_time=2)
        self.wait(0.3)
        self.play(slope.animate.set_value(2.0), run_time=1.5)
        self.wait(1)
