from manimlib import *
import numpy as np


class CostSurfaceGradientDescent(ThreeDScene):
    def construct(self):
        # Same data points from scatter_plot.py
        data_points = np.array([
            [0.5, 3.0],
            [1, 1.8],
            [1.5, 4.5],
            [5, 12.5],
            [5.5, 10.0],
            [6, 11.3],
            [6.5, 14.8],
            [7, 13.0],
            [7.3, 16.2],
            [8, 15.5],
            [8.5, 18.0],
            [9, 17.2],
            [9.5, 19.5],
        ])
        X = data_points[:, 0]
        Y = data_points[:, 1]
        m = len(X)

        # Optimal theta values (center of the paraboloid)
        optimal_theta0, optimal_theta1 = 2.0, 2.0

        # Parabolic cost function: J = a*(theta0 - opt0)^2 + b*(theta1 - opt1)^2
        # Equal coefficients for symmetric paraboloid
        coeff = 12  # Steepness of the parabola

        def cost_function(theta0, theta1):
            return coeff * (theta0 - optimal_theta0) ** 2 + coeff * (theta1 - optimal_theta1) ** 2

        # Gradient of the paraboloid
        def gradient(theta0, theta1):
            d_theta0 = 2 * coeff * (theta0 - optimal_theta0)
            d_theta1 = 2 * coeff * (theta1 - optimal_theta1)
            return np.array([d_theta0, d_theta1])

        # Set up 3D axes (symmetric ranges for circular cone)
        axes = ThreeDAxes(
            x_range=(-2, 6, 1),
            y_range=(-2, 6, 1),
            z_range=(0, 200, 50),
            height=6,
            width=6,
            depth=5,
        )

        # Axis labels
        x_label = Text("θ₀", font_size=36).next_to(axes.x_axis, RIGHT)
        y_label = Text("θ₁", font_size=36).next_to(axes.y_axis, UP)
        z_label = Text("J", font_size=36).next_to(axes.z_axis, OUT)

        # Create the cost surface
        surface = ParametricSurface(
            lambda u, v: axes.c2p(u, v, cost_function(u, v)),
            u_range=(-2, 6),
            v_range=(-2, 6),
            resolution=(40, 40),
        )
        surface.set_color(BLUE_E)
        surface.set_opacity(0.6)
        surface.set_shading(0.3, 0.3, 0)

        # Set camera angle (viewing from above to see ball on surface)
        frame = self.camera.frame
        frame.set_euler_angles(
            theta=-45 * DEGREES,
            phi=35 * DEGREES,
        )
        frame.move_to(axes.c2p(3.5, 3.5, 60))
        frame.scale(1.5)  # Zoom out

        # Add axes and surface
        self.play(
            ShowCreation(axes),
            FadeIn(x_label),
            FadeIn(y_label),
            FadeIn(z_label),
        )
        self.wait(0.3)
        self.play(ShowCreation(surface), run_time=2)
        self.wait(0.5)

        # Gradient descent animation
        # Starting point (symmetric position)
        theta0_current = 5.0
        theta1_current = 5.0
        learning_rate = 0.01
        num_steps = 15

        # Create the gradient descent point
        def get_point_position(t0, t1):
            z = cost_function(t0, t1)
            return axes.c2p(t0, t1, z)

        point = Sphere(radius=0.15, color=RED)
        point.move_to(get_point_position(theta0_current, theta1_current))

        # Add the starting point
        self.play(FadeIn(point, scale=0.5))
        self.wait(0.3)

        # Perform gradient descent steps with arrows
        for step in range(num_steps):
            # Calculate gradient
            grad = gradient(theta0_current, theta1_current)

            # New position after gradient step
            theta0_new = theta0_current - learning_rate * grad[0]
            theta1_new = theta1_current - learning_rate * grad[1]

            # Create arrow pointing in the direction of descent
            start_pos = get_point_position(theta0_current, theta1_current)
            end_pos = get_point_position(theta0_new, theta1_new)

            # Make arrow shorter for visibility (scale down to show direction)
            direction = end_pos - start_pos
            dir_length = np.linalg.norm(direction)
            if dir_length > 0.01:
                direction_norm = direction / dir_length
                arrow_length = min(0.6, dir_length * 0.7)
                arrow_end = start_pos + direction_norm * arrow_length

                arrow = Arrow(
                    start_pos,
                    arrow_end,
                    color=YELLOW,
                    stroke_width=6,
                    buff=0,
                )

                # Show arrow
                self.play(ShowCreation(arrow), run_time=0.5)
                self.wait(0.2)

                # Move point to new position
                new_pos = get_point_position(theta0_new, theta1_new)
                self.play(
                    point.animate.move_to(new_pos),
                    FadeOut(arrow),
                    run_time=0.8,
                )
            else:
                # Just move the point if direction is too small
                new_pos = get_point_position(theta0_new, theta1_new)
                self.play(point.animate.move_to(new_pos), run_time=0.8)

            # Update current position
            theta0_current = theta0_new
            theta1_current = theta1_new

            # Shorter wait for intermediate steps
            if step < num_steps - 1:
                self.wait(0.2)

        # Final wait at the minimum
        self.wait(1)

        # Optionally rotate the camera to show the final result
        self.play(
            frame.animate.set_euler_angles(
                theta=30 * DEGREES,
                phi=60 * DEGREES,
            ),
            run_time=2,
        )
        self.wait(1)
