.. Extracted from scikit-learn/scikit-learn doc/modules/linear_model.rst (main branch): the 'Logistic regression' section only.

.. _Logistic_regression:

Logistic regression
===================

The logistic regression is implemented in :class:`LogisticRegression`. Despite
its name, it is implemented as a linear model for classification rather than
regression in terms of the scikit-learn/ML nomenclature. The logistic
regression is also known in the literature as logit regression,
maximum-entropy classification (MaxEnt) or the log-linear classifier. In this
model, the probabilities describing the possible outcomes of a single trial
are modeled using a `logistic function
<https://en.wikipedia.org/wiki/Logistic_function>`_.

This implementation can fit binary, One-vs-Rest, or multinomial logistic
regression with optional :math:`\ell_1`, :math:`\ell_2` or Elastic-Net
regularization.

.. note:: **Regularization**

    Regularization is applied by default, which is common in machine
    learning but not in statistics. Another advantage of regularization is
    that it improves numerical stability. No regularization amounts to
    setting `alpha` to zero.

.. note:: **Logistic Regression as a special case of the Generalized Linear Models (GLM)**

    Logistic regression is a special case of
    :ref:`generalized_linear_models` with a Binomial / Bernoulli conditional
    distribution and a Logit link. The numerical output of the logistic
    regression, which is the predicted probability, can be used as a classifier
    by applying a threshold (by default 0.5) to it. This is how it is
    implemented in scikit-learn, so it expects a categorical target, making
    the Logistic Regression a classifier.

.. rubric:: Examples

* :ref:`sphx_glr_auto_examples_linear_model_plot_logistic_l1_l2_sparsity.py`
* :ref:`sphx_glr_auto_examples_linear_model_plot_logistic_path.py`
* :ref:`sphx_glr_auto_examples_linear_model_plot_logistic_multinomial.py`
* :ref:`sphx_glr_auto_examples_linear_model_plot_sparse_logistic_regression_20newsgroups.py`
* :ref:`sphx_glr_auto_examples_linear_model_plot_sparse_logistic_regression_mnist.py`
* :ref:`sphx_glr_auto_examples_classification_plot_classification_probability.py`

Binary Case
-----------

For notational ease, we assume that the target :math:`y_i` takes values in the
set :math:`\{0, 1\}` for data point :math:`i`.
Once fitted, the :meth:`~sklearn.linear_model.LogisticRegression.predict_proba`
method of :class:`~sklearn.linear_model.LogisticRegression` predicts
the probability of the positive class :math:`P(y_i=1|X_i)` as

.. math:: \hat{p}(X_i) = \operatorname{expit}(X_i w) = \frac{1}{1 + \exp(-X_i w)}.


As an optimization problem, binary
class logistic regression with regularization term :math:`r(w)` minimizes the
following objective function:

.. math::
    :name: regularized-logistic-loss

    \min_{w} \frac{1}{S}\sum_{i=1}^n s_i
    \left(-y_i \log(\hat{p}(X_i)) - (1 - y_i) \log(1 - \hat{p}(X_i))\right)
    + \frac{\alpha}{S} r(w)\,,

where :math:`{s_i}` corresponds to the weights assigned by the user to a
specific training sample (the vector :math:`s` is formed by element-wise
multiplication of the class weights and sample weights),
and the sum :math:`S = \sum_{i=1}^n s_i`. For `sample_weight=None` (and no
class weights), we have :math:`s_i=1` and :math:`S = n_{\text{samples}}`.

We currently provide four choices for the regularization or penalty term :math:`r(w)`
via the arguments `alpha` and `l1_ratio`:

+-------------------------------+-------------------------------------------------+
| penalty                       | :math:`r(w)`                                    |
+===============================+=================================================+
| none (`alpha=0`)              | :math:`0`                                       |
+-------------------------------+-------------------------------------------------+
| :math:`\ell_1` (`l1_ratio=1`) | :math:`\|w\|_1`                                 |
+-------------------------------+-------------------------------------------------+
| :math:`\ell_2` (`l1_ratio=0`) | :math:`\frac{1}{2}\|w\|_2^2 = \frac{1}{2}w^T w` |
+-------------------------------+-------------------------------------------------+
| ElasticNet (`0<l1_ratio<1`)   | :math:`\frac{1 - \rho}{2}w^T w + \rho \|w\|_1`  |
+-------------------------------+-------------------------------------------------+

For ElasticNet, :math:`\rho` (which corresponds to the `l1_ratio` parameter)
controls the strength of :math:`\ell_1` regularization vs. :math:`\ell_2`
regularization. Elastic-Net is equivalent to :math:`\ell_1` when
:math:`\rho = 1` and equivalent to :math:`\ell_2` when :math:`\rho=0`.

Multinomial Case
----------------

The binary case can be extended to :math:`K` classes leading to the multinomial
logistic regression, see also `log-linear model
<https://en.wikipedia.org/wiki/Multinomial_logistic_regression#As_a_log-linear_model>`_.

.. note::
   It is possible to parameterize a :math:`K`-class classification model
   using only :math:`K-1` weight vectors, leaving one class probability fully
   determined by the other class probabilities by leveraging the fact that all
   class probabilities must sum to one. We deliberately choose to overparameterize the model
   using :math:`K` weight vectors for ease of implementation and to preserve the
   symmetrical inductive bias regarding ordering of classes, see [16]_. This effect becomes
   especially important when using regularization. The choice of overparameterization can be
   detrimental for unpenalized models since then the solution may not be unique, as shown in [16]_.

.. dropdown:: Mathematical details

  Let :math:`y_i \in \{1, \ldots, K\}` be the label (ordinal) encoded target variable for observation :math:`i`.
  Instead of a single coefficient vector, we now have
  a matrix of coefficients :math:`W` where each row vector :math:`W_k` corresponds to class
  :math:`k`. We aim at predicting the class probabilities :math:`P(y_i=k|X_i)` via
  :meth:`~sklearn.linear_model.LogisticRegression.predict_proba` as:

  .. math:: \hat{p}_k(X_i) = \frac{\exp(X_i W_k + W_{0, k})}{\sum_{l=0}^{K-1} \exp(X_i W_l + W_{0, l})}.

  The objective for the optimization becomes

  .. math::
    \min_W -\frac{1}{S}\sum_{i=1}^n \sum_{k=0}^{K-1} s_{ik} [y_i = k] \log(\hat{p}_k(X_i))
    + \frac{\alpha}{S} r(W)\,,

  where :math:`[P]` represents the Iverson bracket which evaluates to :math:`0`
  if :math:`P` is false, otherwise it evaluates to :math:`1`.

  Again, :math:`s_{ik}` are the weights assigned by the user (multiplication of sample
  weights and class weights) with their sum :math:`S = \sum_{i=1}^n \sum_{k=0}^{K-1} s_{ik}`.
  For `sample_weight=None` (and no class weights), we have :math:`s_i=1` and
  :math:`S = n_{\text{samples}}`.

  We currently provide four choices for the regularization or penalty term :math:`r(W)`
  via the arguments `alpha` and `l1_ratio`, where :math:`m` is the number of features:

  +-------------------------------+----------------------------------------------------------------------------------+
  | penalty                       | :math:`r(W)`                                                                     |
  +===============================+==================================================================================+
  | none (`alpha=0`)              | :math:`0`                                                                        |
  +-------------------------------+----------------------------------------------------------------------------------+
  | :math:`\ell_1` (`l1_ratio=1`) | :math:`\|W\|_{1,1} = \sum_{i=1}^m\sum_{j=1}^{K}|W_{i,j}|`                        |
  +-------------------------------+----------------------------------------------------------------------------------+
  | :math:`\ell_2` (`l1_ratio=0`) | :math:`\frac{1}{2}\|W\|_F^2 = \frac{1}{2}\sum_{i=1}^m\sum_{j=1}^{K} W_{i,j}^2`   |
  +-------------------------------+----------------------------------------------------------------------------------+
  | ElasticNet (`0<l1_ratio<1`)   | :math:`\frac{1 - \rho}{2}\|W\|_F^2 + \rho \|W\|_{1,1}`                           |
  +-------------------------------+----------------------------------------------------------------------------------+

.. _logistic_regression_solvers:

Solvers
-------

The solvers implemented in the class :class:`LogisticRegression`
are "lbfgs", "liblinear", "newton-cholesky", "newton-cd", "newton-cd-gram",
"newton-cg", "sag" and "saga":

The following table summarizes the penalties and multinomial multiclass supported by
each solver:

+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
|                              |                       **Solvers**                                                                                                         |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| **Penalties**                | **'lbfgs'** | **'liblinear'** | **'newton-cholesky'** | **'newton-cd'** | **'newton-cd-gram'** | **'newton-cg'** | **'sag'** | **'saga'** |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| L2 penalty                   |     yes     |       yes       |     yes               |     yes         |     yes              |       yes       |    yes    |    yes     |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| L1 penalty                   |     no      |       yes       |     no                |     yes         |     yes              |       no        |    no     |    yes     |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| Elastic-Net (L1 + L2)        |     no      |       no        |     no                |     yes         |     yes              |       no        |    no     |    yes     |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| No penalty                   |     yes     |       no        |     yes               |     yes         |     yes              |       yes       |    yes    |    yes     |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| **Multiclass support**       |                                                                                                                                           |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| multinomial multiclass       |     yes     |       no        |     yes               |     yes         |     yes              |       yes       |    yes    |    yes     |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| **Behaviors**                |                                                                                                                                           |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| Penalize the intercept (bad) |     no      |       yes       |     no                |     no          |     no               |       no        |    no     |    no      |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| Faster for large datasets    |     no      |       no        |     no                |     no          |     no               |       no        |    yes    |    yes     |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+
| Robust to unscaled datasets  |     yes     |       yes       |     yes               |     yes         |     yes              |       yes       |    no     |    no      |
+------------------------------+-------------+-----------------+-----------------------+-----------------+----------------------+-----------------+-----------+------------+

The "lbfgs" solver is used by default for its robustness. For
`n_samples >> n_features`, "newton-cholesky" is a good choice and can reach high
precision (tiny `tol` values). With L1 or Elastic-Net penalty, "newton-cd-gram" is
a good choice for `n_samples >> n_features`, while "newton-cd" is a good choice for
`n_features > n_samples` (or both large).
For large datasets the "saga" solver is usually faster (than "lbfgs"), in particular
for low precision (high `tol`).
For large dataset, you may also consider using :class:`SGDClassifier`
with `loss="log_loss"`, which might be even faster but requires more tuning.

.. dropdown:: References

  The following references explain some of the solvers.

  * For "lbfgs", see documentation of
    :func:`SciPy minimize <scipy:scipy.optimize.minimize>`

  * "liblinear"

    * Fan, R. E., Chang, K. W., Hsieh, C. J., Wang, X. R., & Lin, C. J. (2008).
      LIBLINEAR: A library for large linear classification.
      the Journal of machine Learning research, 9, 1871-1874.
      https://www.jmlr.org/papers/volume9/fan08a/fan08a.pdf

    * :doi:`Yu, H. F., Huang, F. L., & Lin, C. J. (2011).
      Dual coordinate descent methods for logistic regression and maximum entropy
      models. Machine Learning, 85(1), 41-75.
      <10.1007/s10994-010-5221-8>`

  * SAG -- :arxiv:`Schmidt, M., Le Roux, N., & Bach, F. (2017).
    Minimizing finite sums with the stochastic average gradient.
    Mathematical Programming, 162(1), 83-112.
    <1309.2388>`

  * SAGA -- :arxiv:`Defazio, A., Bach, F., & Lacoste-Julien, S. (2014).
    SAGA: A fast incremental gradient method with support for non-strongly convex
    composite objectives. Advances in neural information processing systems, 27.
    <1407.0202>`

.. _liblinear_differences:

Differences between solvers
^^^^^^^^^^^^^^^^^^^^^^^^^^^

There might be a difference in the scores obtained between
:class:`LogisticRegression` with ``solver=liblinear`` or
:class:`~sklearn.svm.LinearSVC` and the external liblinear library directly,
when ``fit_intercept=False`` and the fit ``coef_`` (or) the data to be predicted
are zeroes. This is because for the sample(s) with ``decision_function`` zero,
:class:`LogisticRegression` and :class:`~sklearn.svm.LinearSVC` predict the
negative class, while liblinear predicts the positive class. Note that a model
with ``fit_intercept=False`` and having many samples with ``decision_function``
zero, is likely to be an underfit, bad model and you are advised to set
``fit_intercept=True`` and increase the ``intercept_scaling``.

.. dropdown:: Solvers' details

  * The solver "liblinear" uses a coordinate descent (CD) algorithm, and relies
    on the excellent C++ `LIBLINEAR library
    <https://www.csie.ntu.edu.tw/~cjlin/liblinear/>`_, which is shipped with
    scikit-learn. However, the CD algorithm implemented in liblinear cannot learn a
    true multinomial (multiclass) model. If you still want to use "liblinear" on
    multiclass problems, you can use a "one-vs-rest" scheme
    `OneVsRestClassifier(LogisticRegression(solver="liblinear"))`, see
    `:class:`~sklearn.multiclass.OneVsRestClassifier`. Note that minimizing the
    multinomial loss is expected to give better calibrated results as compared to
    a "one-vs-rest" scheme.
    For :math:`\ell_1` regularization :func:`sklearn.svm.l1_min_c` allows to
    calculate the lower bound for C, which equals 1/alpha in order
    to get a non "null" (all feature weights to zero) model.

  * The "lbfgs", "newton-cg", "newton-cholesky" and "sag" solvers only support
    :math:`\ell_2` regularization or no regularization, and are found to converge
    faster for some high-dimensional data. These solvers (and "saga")
    learn a true multinomial logistic regression model [5]_.

  * The "sag" solver uses Stochastic Average Gradient descent [6]_. It is faster
    than other solvers for large datasets, when both the number of samples and the
    number of features are large.

  * The "saga" solver [7]_ is a variant of "sag" that also supports the non-smooth
    :math:`\ell_1` penalty (`l1_ratio=1`). This is therefore the solver of choice for
    sparse multinomial logistic regression. It is also the only solver that supports
    Elastic-Net (`0 < l1_ratio < 1`).

  * The "lbfgs" is an optimization algorithm that approximates the
    Broyden–Fletcher–Goldfarb–Shanno algorithm [8]_, which belongs to
    quasi-Newton methods. As such, it can deal with a wide range of different training
    data and is therefore the default solver. Its performance, however, suffers on poorly
    scaled datasets and on datasets with one-hot encoded categorical features with rare
    categories.

  * The "newton-cholesky" solver is an exact Newton solver that calculates the Hessian
    matrix and solves the resulting linear system. It is a very good choice for
    `n_samples` >> `n_features` and can reach high precision (tiny values of `tol`),
    but has a few shortcomings: Only :math:`\ell_2` regularization is supported.
    Furthermore, because the Hessian matrix is explicitly computed, the memory usage
    has a quadratic dependency on `n_features` as well as on `n_classes`.

  For a comparison of some of these solvers, see [9]_.

  .. rubric:: References

  .. [5] Christopher M. Bishop: Pattern Recognition and Machine Learning, Chapter 4.3.4

  .. [6] Mark Schmidt, Nicolas Le Roux, and Francis Bach: `Minimizing Finite Sums with the Stochastic Average Gradient. <https://hal.inria.fr/hal-00860051/document>`_

  .. [7] Aaron Defazio, Francis Bach, Simon Lacoste-Julien:
      :arxiv:`SAGA: A Fast Incremental Gradient Method With Support for
      Non-Strongly Convex Composite Objectives. <1407.0202>`

  .. [8] https://en.wikipedia.org/wiki/Broyden%E2%80%93Fletcher%E2%80%93Goldfarb%E2%80%93Shanno_algorithm

  .. [9] Thomas P. Minka `"A comparison of numerical optimizers for logistic regression"
          <https://tminka.github.io/papers/logreg/minka-logreg.pdf>`_

  .. [16] :arxiv:`Simon, Noah, J. Friedman and T. Hastie.
      "A Blockwise Descent Algorithm for Group-penalized Multiresponse and
      Multinomial Regression." <1311.6529>`


.. note:: **Feature selection with sparse logistic regression**

   A logistic regression with :math:`\ell_1` penalty yields sparse models, and can
   thus be used to perform feature selection, as detailed in
   :ref:`l1_feature_selection`.

.. note:: **P-value estimation**

    It is possible to obtain the p-values and confidence intervals for
    coefficients in cases of regression without penalization. The `statsmodels
    package <https://pypi.org/project/statsmodels/>`_ natively supports this.
    Within sklearn, one could use bootstrapping instead as well.


:class:`LogisticRegressionCV` implements Logistic Regression with built-in
cross-validation support, to find the optimal `alpha` and `l1_ratio` parameters
according to the ``scoring`` attribute. The "newton-cg", "sag", "saga" and
"lbfgs" solvers are found to be faster for high-dimensional dense data, due
to warm-starting (see :term:`Glossary <warm_start>`).

.. _Generalized_linear_regression:

.. _Generalized_linear_models:
