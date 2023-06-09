#!/usr/bin/env python
# coding: utf-8

# # A2.5 Multilayer Neural Networks for Nonlinear Regression
# 

# Thad Avery

# ## Summary

# In this assignment you will 
# * make some modifications to the supplied neural network implementation, 
# * define a function that partitions data into training, validation and test sets,
# * apply it to a data set, 
# * define a function that runs experiments with a variety of parameter values, 
# * describe your observations of these results.

# ## Optimizers

# First, we need a class that includes our optimization algorithms, `sgd` and `adam`.  The following code cell implements `sgd`.  You must complete the implementation of `adam`, following its implementation in the lecture notes.
# 
# Notice that `all_weights` is updated in place by these optimization algorithms.  The new values of `all_weights` are not returned from these functions, because the code that calls these functions allocates the memory for `all_weights` and keeps the reference to it so has direct access to the new values.

# In[1]:


import numpy as np
import matplotlib.pyplot as plt


# In[2]:


class Optimizers():

    def __init__(self, all_weights):
        '''all_weights is a vector of all of a neural networks weights concatenated into a one-dimensional vector'''
        
        self.all_weights = all_weights

        # The following initializations are only used by adam.
        # Only initializing mt, vt, beta1t and beta2t here allows multiple calls to adam to handle training
        # with multiple subsets (batches) of training data.
        self.mt = np.zeros_like(all_weights)
        self.vt = np.zeros_like(all_weights)
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.beta1t = 1  # was self.beta1
        self.beta2t = 1  # was self.beta2

        
    def sgd(self, error_f, gradient_f, fargs=[], n_epochs=100, learning_rate=0.001, error_convert_f=None):
        '''
error_f: function that requires X and T as arguments (given in fargs) and returns mean squared error.
gradient_f: function that requires X and T as arguments (in fargs) and returns gradient of mean squared error
            with respect to each weight.
error_convert_f: function that converts the standardized error from error_f to original T units.
        '''

        error_trace = []
        epochs_per_print = n_epochs // 10

        for epoch in range(n_epochs):

            error = error_f(*fargs)
            grad = gradient_f(*fargs)

            # Update all weights using -= to modify their values in-place.
            self.all_weights -= learning_rate * grad

            if error_convert_f:
                error = error_convert_f(error)
            error_trace.append(error)

            if (epoch + 1) % max(1, epochs_per_print) == 0:
                print(f'sgd: Epoch {epoch+1:d} Error={error:.5f}')

        return error_trace

    def adam(self, error_f, gradient_f, fargs=[], n_epochs=100, learning_rate=0.001, error_convert_f=None):
        '''
error_f: function that requires X and T as arguments (given in fargs) and returns mean squared error.
gradient_f: function that requires X and T as arguments (in fargs) and returns gradient of mean squared error
            with respect to each weight.
error_convert_f: function that converts the standardized error from error_f to original T units.
        '''

        alpha = learning_rate  # learning rate called alpha in original paper on adam
        epsilon = 1e-8
        error_trace = []
        epochs_per_print = n_epochs // 10

        for epoch in range(n_epochs):

            error = error_f(*fargs)
            grad = gradient_f(*fargs)

            # Finish Adam implementation here by updating
            #   self.mt
            #   self.vt
            #   self.beta1t
            #   self.beta2t
            # and updating values of self.all_weights
            
            #approximate first and second moment
            self.mt = (self.beta1 * self.mt) + (1 - self.beta1) * grad
            self.vt = (self.beta2 * self.vt) + (1 - self.beta2) * np.square(grad)
            
            #bias correction
            self.beta1t *= self.beta1
            self.beta2t *= self.beta2
            
            mhat = self.mt / (1 - self.beta1t)
            vhat = self.vt / (1 - self.beta2t)
            
            self.all_weights -= alpha * mhat / (np.sqrt(vhat) + epsilon)
            

            if error_convert_f:
                error = error_convert_f(error)
            error_trace.append(error)

            if (epoch + 1) % max(1, epochs_per_print) == 0:
                print(f'Adam: Epoch {epoch+1:d} Error={error:.5f}')

        return error_trace


# Test `Optimizers` using the function `test_optimizers`.  You should get the same results shown below.

# In[3]:


def test_optimizers():

    def parabola(wmin):
        return ((w - wmin) ** 2)[0]

    def parabola_gradient(wmin):
        return 2 * (w - wmin)

    w = np.array([0.0])
    optimizer = Optimizers(w)

    wmin = 5
    optimizer.sgd(parabola, parabola_gradient, [wmin], n_epochs=100, learning_rate=0.1)
    print(f'sgd: Minimum of parabola is at {wmin}. Value found is {w}')

    w = np.array([0.0])
    optimizer = Optimizers(w)
    optimizer.adam(parabola, parabola_gradient, [wmin], n_epochs=100, learning_rate=0.1)
    print(f'adam: Minimum of parabola is at {wmin}. Value found is {w}')


# In[4]:


test_optimizers()


# ## NeuralNetwork class

# Now we can implement the `NeuralNetwork` class that calls the above `Optimizers` functions to update the weights.
# 
# You must first complete the `use` function.  You can make use of the `forward_pass` function.

# In[5]:


class NeuralNetwork():


    def __init__(self, n_inputs, n_hiddens_per_layer, n_outputs):
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs

        # Set self.n_hiddens_per_layer to [] if argument is 0, [], or [0]
        if n_hiddens_per_layer == 0 or n_hiddens_per_layer == [] or n_hiddens_per_layer == [0]:
            self.n_hiddens_per_layer = []
        else:
            self.n_hiddens_per_layer = n_hiddens_per_layer

        # Initialize weights, by first building list of all weight matrix shapes.
        n_in = n_inputs
        shapes = []
        for nh in self.n_hiddens_per_layer:
            shapes.append((n_in + 1, nh))
            n_in = nh
        shapes.append((n_in + 1, n_outputs))

        # self.all_weights:  vector of all weights
        # self.Ws: list of weight matrices by layer
        self.all_weights, self.Ws = self.make_weights_and_views(shapes)

        # Define arrays to hold gradient values.
        # One array for each W array with same shape.
        self.all_gradients, self.dE_dWs = self.make_weights_and_views(shapes)

        self.trained = False
        self.total_epochs = 0
        self.error_trace = []
        self.Xmeans = None
        self.Xstds = None
        self.Tmeans = None
        self.Tstds = None


    def make_weights_and_views(self, shapes):
        # vector of all weights built by horizontally stacking flatenned matrices
        # for each layer initialized with uniformly-distributed values.
        all_weights = np.hstack([np.random.uniform(size=shape).flat / np.sqrt(shape[0])
                                 for shape in shapes])
        # Build list of views by reshaping corresponding elements from vector of all weights
        # into correct shape for each layer.
        views = []
        start = 0
        for shape in shapes:
            size =shape[0] * shape[1]
            views.append(all_weights[start:start + size].reshape(shape))
            start += size
        return all_weights, views


    # Return string that shows how the constructor was called
    def __repr__(self):
        return f'NeuralNetwork({self.n_inputs}, {self.n_hiddens_per_layer}, {self.n_outputs})'


    # Return string that is more informative to the user about the state of this neural network.
    def __str__(self):
        if self.trained:
            return self.__repr__() + f' trained for {self.total_epochs} epochs, final training error {self.error_trace[-1]}'


    def train(self, X, T, n_epochs, learning_rate, method='sgd'):
        '''
train: 
  X: n_samples x n_inputs matrix of input samples, one per row
  T: n_samples x n_outputs matrix of target output values, one sample per row
  n_epochs: number of passes to take through all samples updating weights each pass
  learning_rate: factor controlling the step size of each update
  method: is either 'sgd' or 'adam'
        '''

        # Setup standardization parameters
        if self.Xmeans is None:
            self.Xmeans = X.mean(axis=0)
            self.Xstds = X.std(axis=0)
            self.Xstds[self.Xstds == 0] = 1  # So we don't divide by zero when standardizing
            self.Tmeans = T.mean(axis=0)
            self.Tstds = T.std(axis=0)
            
        # Standardize X and T
        X = (X - self.Xmeans) / self.Xstds
        T = (T - self.Tmeans) / self.Tstds

        # Instantiate Optimizers object by giving it vector of all weights
        optimizer = Optimizers(self.all_weights)

        # Define function to convert value from error_f into error in original T units.
        error_convert_f = lambda err: (np.sqrt(err) * self.Tstds)[0] # to scalar

        if method == 'sgd':

            error_trace = optimizer.sgd(self.error_f, self.gradient_f,
                                        fargs=[X, T], n_epochs=n_epochs,
                                        learning_rate=learning_rate,
                                        error_convert_f=error_convert_f)

        elif method == 'adam':

            error_trace = optimizer.adam(self.error_f, self.gradient_f,
                                         fargs=[X, T], n_epochs=n_epochs,
                                         learning_rate=learning_rate,
                                         error_convert_f=error_convert_f)

        else:
            raise Exception("method must be 'sgd' or 'adam'")
        
        self.error_trace = error_trace

        # Return neural network object to allow applying other methods after training.
        #  Example:    Y = nnet.train(X, T, 100, 0.01).use(X)
        return self

   
    def forward_pass(self, X):
        '''X assumed already standardized. Output returned as standardized.'''
        self.Ys = [X]
        for W in self.Ws[:-1]:
            self.Ys.append(np.tanh(self.Ys[-1] @ W[1:, :] + W[0:1, :]))
        last_W = self.Ws[-1]
        self.Ys.append(self.Ys[-1] @ last_W[1:, :] + last_W[0:1, :])
        return self.Ys

    # Function to be minimized by optimizer method, mean squared error
    def error_f(self, X, T):
        Ys = self.forward_pass(X)
        mean_sq_error = np.mean((T - Ys[-1]) ** 2)
        return mean_sq_error

    # Gradient of function to be minimized for use by optimizer method
    def gradient_f(self, X, T):
        '''Assumes forward_pass just called with layer outputs in self.Ys.'''
        error = T - self.Ys[-1]
        n_samples = X.shape[0]
        n_outputs = T.shape[1]
        delta = - error / (n_samples * n_outputs)
        n_layers = len(self.n_hiddens_per_layer) + 1
        # Step backwards through the layers to back-propagate the error (delta)
        for layeri in range(n_layers - 1, -1, -1):
            # gradient of all but bias weights
            self.dE_dWs[layeri][1:, :] = self.Ys[layeri].T @ delta
            # gradient of just the bias weights
            self.dE_dWs[layeri][0:1, :] = np.sum(delta, 0)
            # Back-propagate this layer's delta to previous layer
            delta = delta @ self.Ws[layeri][1:, :].T * (1 - self.Ys[layeri] ** 2)
        return self.all_gradients

    def use(self, X):
        '''X assumed to not be standardized. Return the unstandardized prediction'''
        Xstd = (X - self.Xmeans) / self.Xstds
        Y = self.forward_pass(Xstd)
        Yunstd= (Y[-1] * self.Tstds) + self.Tmeans
        return Yunstd


# Then test it with the `test_neuralnetwork` function.  Your results should be the same as those shown, because the pseudo-random number generator used to initialize the weights is set to start with the same seed.

# In[6]:


np.random.seed(42)
np.random.uniform(-0.1, 0.1, size=(2, 2))


# In[7]:


np.random.uniform(-0.1, 0.1, size=(2, 2))


# In[8]:


np.random.seed(42)
np.random.uniform(-0.1, 0.1, size=(2, 2))


# In[9]:


def test_neuralnetwork():
    
    np.random.seed(42)
    
    X = np.arange(100).reshape((-1, 1))
    T = np.sin(X * 0.04)

    n_hiddens = [10, 10]
    n_epochs = 2000
    learning_rate = 0.01
    
    nnetsgd = NeuralNetwork(1, n_hiddens, 1)
    nnetsgd.train(X, T, n_epochs, learning_rate, method='sgd')

    print()  # skip a line
    
    nnetadam = NeuralNetwork(1, n_hiddens, 1)
    nnetadam.train(X, T, n_epochs, learning_rate, method='adam')

    Ysgd = nnetsgd.use(X)
    Yadam = nnetadam.use(X)

    plt.figure(figsize=(15,10))
    plt.subplot(1, 3, 1)
    plt.plot(nnetsgd.error_trace, label='SGD')
    plt.plot(nnetadam.error_trace, label='Adam')
    plt.xlabel('Epoch')
    plt.ylabel('RMSE')
    plt.legend()
    
    plt.subplot(1, 3, 2)
    plt.plot(T, Ysgd, 'o', label='SGD')
    plt.plot(T, Yadam, 'o', label='Adam')
    a = min(np.min(T), np.min(Ysgd))
    b = max(np.max(T), np.max(Ysgd))
    plt.plot([a, b], [a, b], 'k-', lw=3, alpha=0.5, label='45 degree')
    plt.xlabel('Target')
    plt.ylabel('Predicted')
    plt.legend()

    plt.subplot(1, 3, 3)
    plt.plot(Ysgd, 'o-', label='SGD')
    plt.plot(Yadam, 'o-', label='Adam')
    plt.plot(T, label='Target')
    plt.xlabel('Sample')
    plt.ylabel('Target or Predicted')
    plt.legend()

    plt.tight_layout()


# In[10]:


test_neuralnetwork()


# ## ReLU Activation Function

# Cut and paste your `NeuralNetwork` class cell here.  Then modify it to allow the use of the ReLU activiation function, in addition to the `tanh` activation function that `NeuralNetwork` currently uses.  
# 
# Do this by
# * Add the argument `activation_function` to the `NeuralNetwork` constructor that can be given values of `tanh` or `relu`, with `tanh` being its default value.
# * Define two new class functions, `relu(s)` that accepts a matrix of weighted sums and returns the ReLU values, and `grad_relu(s)` that returns the gradient of `relu(s)` with respect to each value in `s`.
# * Add `if` statements to `forward_pass` and `gradient_f` to selectively use the `tanh` or `relu` activation function. This is easy if you assign a new class variable in the `NeuralNetwork` constructor that has the value of the argument `activation_function`.

# In[11]:


class NeuralNetwork():


    def __init__(self, n_inputs, n_hiddens_per_layer, n_outputs, activation_function='tanh'):
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        self.activation_function = activation_function

        # Set self.n_hiddens_per_layer to [] if argument is 0, [], or [0]
        if n_hiddens_per_layer == 0 or n_hiddens_per_layer == [] or n_hiddens_per_layer == [0]:
            self.n_hiddens_per_layer = []
        else:
            self.n_hiddens_per_layer = n_hiddens_per_layer

        # Initialize weights, by first building list of all weight matrix shapes.
        n_in = n_inputs
        shapes = []
        for nh in self.n_hiddens_per_layer:
            shapes.append((n_in + 1, nh))
            n_in = nh
        shapes.append((n_in + 1, n_outputs))

        # self.all_weights:  vector of all weights
        # self.Ws: list of weight matrices by layer
        self.all_weights, self.Ws = self.make_weights_and_views(shapes)

        # Define arrays to hold gradient values.
        # One array for each W array with same shape.
        self.all_gradients, self.dE_dWs = self.make_weights_and_views(shapes)

        self.trained = False
        self.total_epochs = 0
        self.error_trace = []
        self.Xmeans = None
        self.Xstds = None
        self.Tmeans = None
        self.Tstds = None


    def make_weights_and_views(self, shapes):
        # vector of all weights built by horizontally stacking flatenned matrices
        # for each layer initialized with uniformly-distributed values.
        all_weights = np.hstack([np.random.uniform(size=shape).flat / np.sqrt(shape[0])
                                 for shape in shapes])
        # Build list of views by reshaping corresponding elements from vector of all weights
        # into correct shape for each layer.
        views = []
        start = 0
        for shape in shapes:
            size =shape[0] * shape[1]
            views.append(all_weights[start:start + size].reshape(shape))
            start += size
        return all_weights, views


    # Return string that shows how the constructor was called
    def __repr__(self):
        return f'NeuralNetwork({self.n_inputs}, {self.n_hiddens_per_layer}, {self.n_outputs})'


    # Return string that is more informative to the user about the state of this neural network.
    def __str__(self):
        if self.trained:
            return self.__repr__() + f' trained for {self.total_epochs} epochs, final training error {self.error_trace[-1]}'


    def train(self, X, T, n_epochs, learning_rate, method='sgd'):
        '''
train: 
  X: n_samples x n_inputs matrix of input samples, one per row
  T: n_samples x n_outputs matrix of target output values, one sample per row
  n_epochs: number of passes to take through all samples updating weights each pass
  learning_rate: factor controlling the step size of each update
  method: is either 'sgd' or 'adam'
        '''

        # Setup standardization parameters
        if self.Xmeans is None:
            self.Xmeans = X.mean(axis=0)
            self.Xstds = X.std(axis=0)
            self.Xstds[self.Xstds == 0] = 1  # So we don't divide by zero when standardizing
            self.Tmeans = T.mean(axis=0)
            self.Tstds = T.std(axis=0)
            
        # Standardize X and T
        X = (X - self.Xmeans) / self.Xstds
        T = (T - self.Tmeans) / self.Tstds

        # Instantiate Optimizers object by giving it vector of all weights
        optimizer = Optimizers(self.all_weights)

        # Define function to convert value from error_f into error in original T units.
        error_convert_f = lambda err: (np.sqrt(err) * self.Tstds)[0] # to scalar

        if method == 'sgd':

            error_trace = optimizer.sgd(self.error_f, self.gradient_f,
                                        fargs=[X, T], n_epochs=n_epochs,
                                        learning_rate=learning_rate,
                                        error_convert_f=error_convert_f)

        elif method == 'adam':

            error_trace = optimizer.adam(self.error_f, self.gradient_f,
                                         fargs=[X, T], n_epochs=n_epochs,
                                         learning_rate=learning_rate,
                                         error_convert_f=error_convert_f)

        else:
            raise Exception("method must be 'sgd' or 'adam'")
        
        self.error_trace = error_trace

        # Return neural network object to allow applying other methods after training.
        #  Example:    Y = nnet.train(X, T, 100, 0.01).use(X)
        return self

   
    def forward_pass(self, X):
        '''X assumed already standardized. Output returned as standardized.'''
        self.Ys = [X]
        for W in self.Ws[:-1]:
            if self.activation_function == "tanh":
                self.Ys.append(np.tanh(self.Ys[-1] @ W[1:, :] + W[0:1, :]))
            elif self.activation_function == "relu":
                self.Ys.append(self.relu(self.Ys[-1] @ W[1:, :] + W[0:1, :]))
        last_W = self.Ws[-1]
        self.Ys.append(self.Ys[-1] @ last_W[1:, :] + last_W[0:1, :])
        return self.Ys

    # Function to be minimized by optimizer method, mean squared error
    def error_f(self, X, T):
        Ys = self.forward_pass(X)
        mean_sq_error = np.mean((T - Ys[-1]) ** 2)
        return mean_sq_error

    # Gradient of function to be minimized for use by optimizer method
    def gradient_f(self, X, T):
        '''Assumes forward_pass just called with layer outputs in self.Ys.'''
        error = T - self.Ys[-1]
        n_samples = X.shape[0]
        n_outputs = T.shape[1]
        delta = - error / (n_samples * n_outputs)
        n_layers = len(self.n_hiddens_per_layer) + 1
        # Step backwards through the layers to back-propagate the error (delta)
        for layeri in range(n_layers - 1, -1, -1):
            # gradient of all but bias weights
            self.dE_dWs[layeri][1:, :] = self.Ys[layeri].T @ delta
            # gradient of just the bias weights
            self.dE_dWs[layeri][0:1, :] = np.sum(delta, 0)
            # Back-propagate this layer's delta to previous layer
            if self.activation_function == "tanh":
                delta = delta @ self.Ws[layeri][1:, :].T * (1 - self.Ys[layeri] ** 2)
            elif self.activation_function == "relu":
                delta = delta @ self.Ws[layeri][1:, :].T * self.grad_relu(self.Ys[layeri])
        return self.all_gradients

    def use(self, X):
        '''X assumed to not be standardized. Return the unstandardized prediction'''
        Xstd = (X - self.Xmeans) / self.Xstds
        Y = self.forward_pass(Xstd)
        Yunstd= (Y[-1] * self.Tstds) + self.Tmeans
        return Yunstd
    
    def relu(self, s): 
        Y = s.copy()
        Y[Y < 0] = 0
        return Y
    
    def grad_relu(self, s):
        dY = s.copy()
        dY[s < 0] = 0 #not clean oh whelp
        dY[s > 0] = 1
        dY[s == 0] = 0
        return dY
        


# ## Now for the Experiments!

# Now that your code is working, let's apply it to some interesting data.
# 
# Read in the `auto-mpg.data` that we have used in lectures.  Let's apply neural networks to predict `mpg` using various neural network architectures, numbers of epochs, and our two activation functions.
# 
# This time we will partition the data into five parts after randomly rearranging the samples.  We will assign the first partition as the validation set, the second one as the test set, and the remaining parts will be vertically stacked to form the training set, as discussed in lecture.  We can use the RMSE on the validation set to pick the best values of the number of epochs and the network architecture.  Then to report on the RMSE we expect on new data, we will report the test set RMSE.

# Read in the `auto-mpg.data` using `pandas` and remove all samples that contain missing values.  You should end up with 392 samples.
# 
# Now randomly reorder the samples.  First run `np.random.seed(42)` to guarantee that we all use the same random ordering of samples.
# 
# Partition the data into five folds, as shown in lecture.  To do this, complete the following function.

# In[12]:


get_ipython().system('curl -O https://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data-original')
get_ipython().system('curl -O https://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.names')


# In[13]:


import pandas as pd
df  = pd.read_csv("auto-mpg.data-original", header=None, delim_whitespace=True, na_values='?')
df = df.dropna()
data = df.iloc[:, :-1].values
df


# In[14]:


np.random.seed(42)


# In[15]:


def partition(X, T, n_folds, random_shuffle=True):
    rows = np.arange(X.shape[0])
    if(random_shuffle == True):
        np.random.shuffle(rows)  # shuffle the row indices in-place (rows is changed)
    X = X[rows, :]
    T = T[rows, :]

#     n_folds = 5
    n_samples = X.shape[0]
    n_per_fold = n_samples // n_folds # double-slash = "floor division" which rounds down to the nearest number
    n_last_fold = n_samples - n_per_fold * (n_folds - 1)  # handles case when n_samples not evenly divided by n_folds

    folds = []
    start = 0
    for foldi in range(n_folds-1):
        folds.append( (X[start:start + n_per_fold, :], T[start:start + n_per_fold, :]) )
        start += n_per_fold
    folds.append( (X[start:, :], T[start:, :]) )   # Changed in notes 07.2
    len(folds), len(folds[0]), folds[0][0].shape, folds[0][1].shape
    
    Xvalidate, Tvalidate = folds[0]
    Xtest, Ttest = folds[1]
    Xtrain, Ttrain = np.vstack([X for (X, _) in folds[2:]]), np.vstack([T for (_, T) in folds[2:]])
    
    
    return Xtrain, Ttrain, Xvalidate, Tvalidate, Xtest, Ttest


# Write a function named `run_experiment` that uses three nested for loops to try different values of the parameters `n_epochs`, `n_hidden_units_per_layer` and `activation_function` which will just be either `tanh` or `relu`. Don't forget to try `[0]` for one of the values of `n_hidden_units_per_layer` to include a linear model in your tests.  For each set of parameter values, create and train a neural network using the 'adam' optimization method and use the neural network on the training, validation and test sets.  Collect the parameter values and the RMSE for the training, validation, and test set in a list.  When your loops are done, construct a `pandas.DataFrame` from the list of results, for easy printing.  The first five lines might look like:
# 
# ```
#    epochs        nh    lr act func  RMSE Train  RMSE Val  RMSE Test
# 0    1000       [0]  0.01     tanh    3.356401  3.418705   3.116480
# 1    1000       [0]  0.01     relu    3.354528  3.428324   3.125064
# 2    1000      [20]  0.01     tanh    1.992509  2.355746   2.459506
# 3    1000      [20]  0.01     relu    2.448536  2.026954   2.581707
# 4    1000  [20, 20]  0.01     tanh    1.518916  2.468188   3.118376
# ```
# Your function must return a `pandas.DataFrame` like this one.
# 
# Before starting the nested for loops, your `run_experiment` function must first call your `partition` function to form the training, validation and test sets.

# In[16]:


def rmse(A, B) : 
    return np.sqrt(np.mean((A-B)**2))


def run_experiment(X, T, n_folds, n_epochs_choices , n_hidden_units_per_layer_choices, activation_function_choices) : 
    output = []
    n_epochs = n_epochs_choices
    n_hidden_units_per_layer = n_hidden_units_per_layer_choices
    activation_function_options = activation_function_choices
    
    Xtrain, Ttrain, Xvalidate, Tvalidate, Xtest, Ttest = partition(X, T, n_folds)
    
    learn_rate = .01
    
    for epoch in n_epochs : 
        for layer in n_hidden_units_per_layer :
            for activation in activation_function_options : 
                
                
                adam_sample = NeuralNetwork(X.shape[1], layer, 1, activation_function = activation)
                adam_sample.train(Xtrain, Ttrain, epoch, learn_rate, method = "adam")
                
                train_pred = adam_sample.use(Xtrain)
                validate_pred = adam_sample.use(Xvalidate)
                test_pred = adam_sample.use(Xtest)
                
                train_error = rmse(Ttrain, train_pred)
                validate_error = rmse(Tvalidate, validate_pred)
                test_error = rmse(Ttest, test_pred)
                
                output.append([epoch, layer, learn_rate, activation, train_error, validate_error, test_error])
       
    return pd.DataFrame(output, columns=['epochs', 'layer', 'learning_rate', 'activation_function', 'RMSE Train', 'RMSE Val', 'RMSE Test'])



# An example call of your function would look like this:

# In[17]:


df
data = df.values
# print(data)
# print(data.shape)

data = df.iloc[:, :-1].values
# print(data.shape)
X = data[:, 1:]
T = data[:, 0:1]

# X, T

result_df = run_experiment(X, T, n_folds=5, 
                           n_epochs_choices=[1000, 2000],
                           n_hidden_units_per_layer_choices=[[0], [10], [100, 10]],
                           activation_function_choices=['tanh', 'relu'])
result_df


# In[18]:


# min_rmse = result_df[result_df.RMSE_Val== result_df.validation_error.min()]
# min_rmse


# Find the lowest value of `RMSE Val` in your table and report the `RMSE Test` and the parameter values that produced this.  This is your expected error in predicted miles per gallon.  Discuss how good this prediction is.

# My lowest RMSE Val in the table was 2.441 and it has the following parameter values:
# 
# - 2000 epochs
# - 10 hidden layers
# - learning rate 0.01
# - relu
# 
# This error in expected miles per gallon is expected because ReLU is a better activation function than tanh. ReLU does not have the vanishing gradient problem and becuase of the piecewise nature of ReLU, not all neurons are required to be activated at the same time. An error in miles per gallon of 3.394 is a decent prediction, however if this was a model that was being sold I would like that error to be lower.

# Plot the RMSE values for training, validation and test sets versus the combined parameter values of number of epochs and network architecture.  Make one plot for `tanh` as the activation function and a second one for `relu`. 

# In[19]:


plt.figure(figsize=(15,10))

plt.subplot(1, 3, 1)
relu_df = result_df[ result_df['activation_function'] == 'relu']
relu_train = relu_df[['RMSE Train']]
relu_val = relu_df[['RMSE Val']]
relu_test = relu_df[['RMSE Test']]
xticks = result_df[['epochs', 'layer']].apply(lambda x: f'{x[0]}, {x[1]}', axis=1)
plt.xticks(range(len(xticks)), xticks, rotation=45, ha='right')
plt.plot(relu_train, label = 'train relu')
plt.plot(relu_val, label = 'val relu')
plt.plot(relu_test, label = 'test relu')
plt.legend()
plt.xlabel('iterations')
plt.ylabel('RMSE')
plt.title('relu')
plt.legend()

plt.subplot(1, 3, 2)
tanh_df = result_df[ result_df['activation_function'] == 'tanh']
tanh_train = tanh_df[['RMSE Train']]
tanh_val = tanh_df[['RMSE Val']]
tanh_test = tanh_df[['RMSE Test']]
xticks = result_df[['epochs', 'layer']].apply(lambda x: f'{x[0]}, {x[1]}', axis=1)
plt.xticks(range(len(xticks)), xticks, rotation=45, ha='right') 
plt.plot(tanh_train, label='train tanh')
plt.plot(tanh_val, label='val tanh')
plt.plot(tanh_test, label='test tanh')
plt.xlabel('iterations')
plt.ylabel('RMSE')
plt.title('tanh')
plt.legend()


# Describe at least three different observations you make about these plots.  What do you find interesting?
# 
# 1. The tanh has closer correlation between the validation and test sets. This is interesting because the lowest RMSE observed was from the relu activation function. The data being closer correlated for test and validation on tanh could be from the tanh's different method for gradient decent. 
# 
# 2. The training data had lower rmse than the test and val data. This could be from overfitting the data. Overfitting is when overly incorrect parameters are being treated with too much weight, and they are not able to properly predict what we want. It is kinda like if the data in training was being memorized instead of learned and then making predictions for the test was less accurate because of this.
# 
# 3. I thought the amount of epochs would have a more dramatic effect on the RMSE. I thought the RMSE from 2000 epochs would be closer to zero than the 1000 epochs, which does ok. I guess like A1, there is a happy medium of learning rates and epochs. If I were to continue this experiment, I would have options to change more parameters to see the best RMSE.
# 

# ## Grading and Check-in
# 
# You and your partner will score of 70 points if your functions are defined correctly. You can test this grading process yourself by downloading [A2grader.zip](https://www.cs.colostate.edu/~cs445/notebooks/A2grader.zip) and extract `A2grader.py` parallel to this notebook.  We recommend keeping this notebook and the grader script in a dedicated folder with *just those two files.* Run the code in the in the following cell to see an example grading run.  If your functions are defined correctly, you should see a score of 70/70.  The remaining 30 points will be based on 1) other testing and the results you obtain, and 2) your discussions.

# In[20]:


get_ipython().run_line_magic('run', '-i A2grader.py')


# Name this notebook as `Lastname1-Lastname2-A2.ipynb`| with Lastname1 being then name of the last name of the person who is turning in the notebook.
# 
# A different but similar grading script will be used to grade your checked-in notebook.  It will include different tests.

# ## Extra Credit: 5 point
# 
# Add the Swish activation function as a third choice in your `train` function in your `NeuralNetwork` class.
# A little googling will find definitions of it and its gradient.  Start with [this article](https://www.machinecurve.com/index.php/2019/05/30/why-swish-could-perform-better-than-relu/#todays-activation-functions).
# 
# Use your `run_experiment` function to compare results for all three activation functions.  Discuss the results.

# In[21]:


import math


# In[22]:


class NeuralNetwork():


    def __init__(self, n_inputs, n_hiddens_per_layer, n_outputs, activation_function='tanh'):
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        self.activation_function = activation_function

        # Set self.n_hiddens_per_layer to [] if argument is 0, [], or [0]
        if n_hiddens_per_layer == 0 or n_hiddens_per_layer == [] or n_hiddens_per_layer == [0]:
            self.n_hiddens_per_layer = []
        else:
            self.n_hiddens_per_layer = n_hiddens_per_layer

        # Initialize weights, by first building list of all weight matrix shapes.
        n_in = n_inputs
        shapes = []
        for nh in self.n_hiddens_per_layer:
            shapes.append((n_in + 1, nh))
            n_in = nh
        shapes.append((n_in + 1, n_outputs))

        # self.all_weights:  vector of all weights
        # self.Ws: list of weight matrices by layer
        self.all_weights, self.Ws = self.make_weights_and_views(shapes)

        # Define arrays to hold gradient values.
        # One array for each W array with same shape.
        self.all_gradients, self.dE_dWs = self.make_weights_and_views(shapes)

        self.trained = False
        self.total_epochs = 0
        self.error_trace = []
        self.Xmeans = None
        self.Xstds = None
        self.Tmeans = None
        self.Tstds = None


    def make_weights_and_views(self, shapes):
        # vector of all weights built by horizontally stacking flatenned matrices
        # for each layer initialized with uniformly-distributed values.
        all_weights = np.hstack([np.random.uniform(size=shape).flat / np.sqrt(shape[0])
                                 for shape in shapes])
        # Build list of views by reshaping corresponding elements from vector of all weights
        # into correct shape for each layer.
        views = []
        start = 0
        for shape in shapes:
            size =shape[0] * shape[1]
            views.append(all_weights[start:start + size].reshape(shape))
            start += size
        return all_weights, views


    # Return string that shows how the constructor was called
    def __repr__(self):
        return f'NeuralNetwork({self.n_inputs}, {self.n_hiddens_per_layer}, {self.n_outputs})'


    # Return string that is more informative to the user about the state of this neural network.
    def __str__(self):
        if self.trained:
            return self.__repr__() + f' trained for {self.total_epochs} epochs, final training error {self.error_trace[-1]}'


    def train(self, X, T, n_epochs, learning_rate, method='sgd'):
        '''
train: 
  X: n_samples x n_inputs matrix of input samples, one per row
  T: n_samples x n_outputs matrix of target output values, one sample per row
  n_epochs: number of passes to take through all samples updating weights each pass
  learning_rate: factor controlling the step size of each update
  method: is either 'sgd' or 'adam'
        '''

        # Setup standardization parameters
        if self.Xmeans is None:
            self.Xmeans = X.mean(axis=0)
            self.Xstds = X.std(axis=0)
            self.Xstds[self.Xstds == 0] = 1  # So we don't divide by zero when standardizing
            self.Tmeans = T.mean(axis=0)
            self.Tstds = T.std(axis=0)
            
        # Standardize X and T
        X = (X - self.Xmeans) / self.Xstds
        T = (T - self.Tmeans) / self.Tstds

        # Instantiate Optimizers object by giving it vector of all weights
        optimizer = Optimizers(self.all_weights)

        # Define function to convert value from error_f into error in original T units.
        error_convert_f = lambda err: (np.sqrt(err) * self.Tstds)[0] # to scalar

        if method == 'sgd':

            error_trace = optimizer.sgd(self.error_f, self.gradient_f,
                                        fargs=[X, T], n_epochs=n_epochs,
                                        learning_rate=learning_rate,
                                        error_convert_f=error_convert_f)

        elif method == 'adam':

            error_trace = optimizer.adam(self.error_f, self.gradient_f,
                                         fargs=[X, T], n_epochs=n_epochs,
                                         learning_rate=learning_rate,
                                         error_convert_f=error_convert_f)

        else:
            raise Exception("method must be 'sgd' or 'adam'")
        
        self.error_trace = error_trace

        # Return neural network object to allow applying other methods after training.
        #  Example:    Y = nnet.train(X, T, 100, 0.01).use(X)
        return self

   
    def forward_pass(self, X):
        '''X assumed already standardized. Output returned as standardized.'''
        self.Ys = [X]
        for W in self.Ws[:-1]:
            if self.activation_function == "tanh":
                self.Ys.append(np.tanh(self.Ys[-1] @ W[1:, :] + W[0:1, :]))
            elif self.activation_function == "relu":
                self.Ys.append(self.relu(self.Ys[-1] @ W[1:, :] + W[0:1, :]))
            elif self.activation_function == "swish":
                self.Ys.append(self.swish(self.Ys[-1] @ W[1:, :] + W[0:1, :]))
        last_W = self.Ws[-1]
        self.Ys.append(self.Ys[-1] @ last_W[1:, :] + last_W[0:1, :])
        return self.Ys

    # Function to be minimized by optimizer method, mean squared error
    def error_f(self, X, T):
        Ys = self.forward_pass(X)
        mean_sq_error = np.mean((T - Ys[-1]) ** 2)
        return mean_sq_error

    # Gradient of function to be minimized for use by optimizer method
    def gradient_f(self, X, T):
        '''Assumes forward_pass just called with layer outputs in self.Ys.'''
        error = T - self.Ys[-1]
        n_samples = X.shape[0]
        n_outputs = T.shape[1]
        delta = - error / (n_samples * n_outputs)
        n_layers = len(self.n_hiddens_per_layer) + 1
        # Step backwards through the layers to back-propagate the error (delta)
        for layeri in range(n_layers - 1, -1, -1):
            # gradient of all but bias weights
            self.dE_dWs[layeri][1:, :] = self.Ys[layeri].T @ delta
            # gradient of just the bias weights
            self.dE_dWs[layeri][0:1, :] = np.sum(delta, 0)
            # Back-propagate this layer's delta to previous layer
            if self.activation_function == "tanh":
                delta = delta @ self.Ws[layeri][1:, :].T * (1 - self.Ys[layeri] ** 2)
            elif self.activation_function == "relu":
                delta = delta @ self.Ws[layeri][1:, :].T * self.grad_relu(self.Ys[layeri])
            elif self.activation_function == "swish":
                delta = delta @ self.Ws[layeri][1:, :].T * self.grad_swish(self.Ys[layeri])
        return self.all_gradients

    def use(self, X):
        '''X assumed to not be standardized. Return the unstandardized prediction'''
        Xstd = (X - self.Xmeans) / self.Xstds
        Y = self.forward_pass(Xstd)
        Yunstd= (Y[-1] * self.Tstds) + self.Tmeans
        return Yunstd
    
    def relu(self, s): 
        Y = s.copy()
        Y[Y < 0] = 0
        return Y
    
    def grad_relu(self, s):
        dY = s.copy()
        dY[s < 0] = 0 #not clean oh whelp
        dY[s > 0] = 1
        dY[s == 0] = 0
        return dY
    
    def sigmoid(self, number):
        
        return 1/(1 + math.exp(-num))
    
    def swish(self, s):
        Y = s.copy()
        swished = [self.sigmoid(i) for i in Y]
        return swished
    
    def grad_swish(self, s):
        Y = s.copy()
        dswish = self.swish(Y) * (1 - self.swish(Y))
        return dswish
        


# In[23]:


def rmse(A, B) : 
    return np.sqrt(np.mean((A-B)**2))


def run_experiment(X, T, n_folds, n_epochs_choices , n_hidden_units_per_layer_choices, activation_function_choices) : 
    output = []
    n_epochs = n_epochs_choices
    n_hidden_units_per_layer = n_hidden_units_per_layer_choices
    activation_function_options = activation_function_choices
    
    Xtrain, Ttrain, Xvalidate, Tvalidate, Xtest, Ttest = partition(X, T, n_folds)
    
    learn_rate = .01
    
    for epoch in n_epochs : 
        for layer in n_hidden_units_per_layer :
            for activation in activation_function_options : 
                
                
                adam_sample = NeuralNetwork(X.shape[1], layer, 1, activation_function = activation)
                adam_sample.train(Xtrain, Ttrain, epoch, learn_rate, method = "adam")
                
                train_pred = adam_sample.use(Xtrain)
                validate_pred = adam_sample.use(Xvalidate)
                test_pred = adam_sample.use(Xtest)
                
                train_error = rmse(Ttrain, train_pred)
                validate_error = rmse(Tvalidate, validate_pred)
                test_error = rmse(Ttest, test_pred)
                
                output.append([epoch, layer, learn_rate, activation, train_error, validate_error, test_error])
       
    return pd.DataFrame(output, columns=['epochs', 'layer', 'learning_rate', 'activation_function', 'RMSE Train', 'RMSE Val', 'RMSE Test'])


# In[24]:


result_df = run_experiment(X, T, n_folds=5, 
                           n_epochs_choices=[1000, 2000],
                           n_hidden_units_per_layer_choices=[[0], [10], [100, 10]],
                           activation_function_choices=['tanh', 'relu', 'swish'])
result_df


# In[ ]:




