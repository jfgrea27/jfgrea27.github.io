---
title: "02 - Feed-forward Neural Network"
author: "James"
date: "2026-01-31"
summary: "A simple neural netwrok."
tags: ["math", "ai"]
draft: false
hideHeader: true
math: true
---

Neural networks are now _ubiquitous_ and are the foundation for Large Language Models (LLMs).

This article will explain the architecture of a simple Feed-forward Neural Network (FFNN), starting from first principles.

## A simple perceptron

Neural networks are not new. Back in the 1950s, scientists were already researching **perceptrons**. A perceptron is a function that takes in an input vector, applies a higher order linear transformation to explore hidden dimensions, an activation function to fit complex relationship in the higher order space.

Like other optimization problems, we can then use a loss function to compare the result of the perceptron with the expected value.

To illustrate this, lets look at

## A brief description of Neural Networks

A feed-forward neural network (FFNN) is the simplest artificial neural network. It is composed of nodes that are organised in layers. Each layer is made up of a linear transformation of its input vector with a **weights matrix** and a **bias** sum. An **activation function** which centers the output of the node to be read by the next layer is used to ensure the input values of the next layer fall in a reasonable range.

<img src="ffnn.gif" alt="A simple FFNN" />

The process of training a neural network is as follows:

1. Featurise your dataset into a set of vectors.
2. Feed the input vectors through the neural network.
3. A cost function associated with the output of the last layer is used to calculate how far off the overall output is from the intended value.
4. Apply back propagation through the network updating the values of the weights and bias parameters using a **learning rate**

The following illustrates the above process:

<img src="forward-pass.gif" alt="Forward pass for FFNN" />

<img src="back-propagation.gif" alt="Backward propagation for FNN" />

The following hyper-parameters are required for building a FFNN:

- activation function to be used at a given layer.
- number of layers.
- learning rate.

## Derivations

There are two equation to remember when dealing with neural networks is

Linear transformation:

$$
\begin{equation}
Z = WX + b
\end{equation}
$$

where $W$ represents a matrix of weights, $X$ is our input and $b$ is a bias.

What this does is project the points in the input vector space into a new space. We update the values of $W$ (the linear transformation) in a way to minimise the loss function (a.k.a. how far we are from predicting the right output).

Activation

$$
\begin{equation}
\sigma(z) = a(Z)
\end{equation}
$$

This is used to add non-linear (a.k.a. complex patterns) to the learning between the layers.

FFNN have a lot of parameters. To simplify, let's consider a small FFNN with 3 layers:

- Input layer: vectors of dimension 3
- Hidden layer: vector of dimension 2
- Output layer: vector of dimension 1

So a feed forward would look like this

input layer -> hidden layer:

$$
Z^1 = W^1X + b^1
$$

$$
\sigma(z)^1 = a(Z^1)
$$

hidden layer -> output layer

$$
Z^2 = W^2a(\sigma(z)^1) + b^2
$$

$$
\sigma(z)^2 = a(Z^2)
$$

We then apply some cost function (e.g. **MSE** or **Cross Entropy**).

## Geometric intuition behind neural networks

## Backprogagation

The Loss function (here we are using MSE) but there are other loss functions is a function of the following form

Given that our resultant estimation is defined in terms of $W^n$ weights and $b^n$ biases, we can write $\hat{y}$ as follows:

$$
\begin{equation}
\hat{Y} = F(W^n; b^n)
\end{equation}
$$

where $F$ represent the forward propagation with linear transformation and activation function explained above.

We can now use a loss function (here MSE) for instance:

$$
MSE = J(W^n, b^n) =  \frac{1}{m}\sum_{i=1}^{m}(Y - \hat{Y})^2 = \frac{1}{m}\sum_{i=1}^{m}(Y - F(W^n, b^n))^2
$$

where the last equality holds from above.

Similar to [01: Linear Regression](01-linear-regression.md), we apply **gradient descent** to reduce the error between the measured and actual:

$$
\begin{equation}
W^{k} = W^{k-1} - \alpha\frac{\partial{J(W^{n},b^{n} )}}{\partial{W^{k-1}}}
\end{equation}
$$

$$
\begin{equation}
b^{k} = b^{k-1} - \alpha\frac{\partial{J(W^{n},b^{n} )}}{\partial{b^{k-1}}}
\end{equation}
$$

We apply this gradient descent for each layer in the neural network.

Let's look at the last layer in the neural network $n$

$$
\frac{\partial{J(W^{n},b^{n} )}}{\partial{W^{n}}} = \frac{\partial{\frac{1}{m}\sum_{i=1}^{m}(Y - F(W^n, b^n))^2}}{\partial{W^{n}}}
$$

Setting $u = Y - F(W^n, b^n)$, we get

$$
\frac{\partial{J(W^{n},b^{n} )}}{\partial{W^{n}}} = \frac{\partial{\frac{1}{m}\sum_{i=1}^{m}(u)^2}}{\partial{u}} . \frac{\partial{u}}{\partial{W^{n}}} = \frac{1}{m}2mu .\frac{\partial{u}}{\partial{W^{n}}}
$$

Let's compute $\frac{\partial{u}}{\partial{W^{n}}}$
Recall that only $-F(W^n, b^n)$ actually is impacted by $W^n$.

Recall that $F(W^{n}, b^{n}) = \sigma(W^{n}Z^{n-1} + b^{n})$
where $Z^{n-1}$ is the result of the previous layer.

This means

$$
\frac{\partial{u}}{\partial{W^{n}}} = \frac{\partial{-F(W^n, b^n)}}{\partial{W^{n}}} = \frac{\partial{\sigma(W^{k}Z^{k-1} + b^{k})}}{\partial{W^{n}}}
$$

Applying chain rule again, setting $v = W^{n}Z^{n-1} + b^{n}$, this gives

$$
\frac{\partial{u}}{\partial{W^{n}}} = \frac{\partial{\sigma(v)}}{\partial{W^{n}}} = \frac{\partial{\sigma(v)}}{\partial{v}}\frac{\partial{v}}{\partial{W^{n}}}
$$

Recalling that $\frac{\partial{v}}{\partial{W^{v}}} = Z^{n-1}$, we get 

$$
\frac{\partial{J(W^{n},b^{n} )}}{\partial{W^{n}}} = -\frac{\partial{\sigma(v)}}{\partial{v}}*Z^{n-1}
$$

Similar for $b^n$, we get 
$$
\frac{\partial{J(W^{n},b^{n} )}}{\partial{b^{n}}} = -\frac{\partial{\sigma(v)}}{\partial{v}}
$$

Looking at the $ith$ layer now:

$$
\frac{\partial{J(W^{n},b^{i} )}}{\partial{W^{i}}} = -\frac{\partial{\sigma(v^n)}}{\partial{v^n}}*Z^{n-1}\frac{\partial{\sigma(v^{n-1})}}{{\partial{v^{n-1}}}}...*\frac{\partial{\sigma(v^i)}}{\partial{v^i}}Z^{n-1}
$$