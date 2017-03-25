from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import edward as ed
import numpy as np
import tensorflow as tf

from edward import models as rvs
from edward.inferences import conjugacy as conj


class test_conjugacy_class(tf.test.TestCase):

  def test_basic_bernoulli(self):
    N = 10
    z = rvs.Bernoulli(p=0.75, sample_shape=N)
    z_cond = conj.complete_conditional(z, [z])
    self.assertIsInstance(z_cond, rvs.Bernoulli)

    sess = tf.InteractiveSession()
    p_val = sess.run(z_cond.p)

    self.assertAllClose(p_val, 0.75 + np.zeros(N, np.float32))

  def test_beta_bernoulli(self):
    x_data = np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 1])

    a0 = 0.5
    b0 = 1.5
    pi = rvs.Beta(a=a0, b=b0)
    x = rvs.Bernoulli(p=pi, sample_shape=10)

    pi_cond = conj.complete_conditional(pi, [pi, x])

    self.assertIsInstance(pi_cond, rvs.Beta)

    sess = tf.InteractiveSession()
    a_val, b_val = sess.run([pi_cond.a, pi_cond.b], {x: x_data})

    self.assertAllClose(a_val, a0 + x_data.sum())
    self.assertAllClose(b_val, b0 + (1 - x_data).sum())

  def test_gamma_poisson(self):
    x_data = np.array([0, 1, 0, 7, 0, 0, 2, 0, 0, 1])

    alpha0 = 0.5
    beta0 = 1.75
    lam = rvs.Gamma(alpha=alpha0, beta=beta0)
    x = rvs.Poisson(lam=lam, value=x_data)

    lam_cond = conj.complete_conditional(lam, [lam, x])

    self.assertIsInstance(lam_cond, rvs.Gamma)

    sess = tf.InteractiveSession()
    alpha_val, beta_val = sess.run([lam_cond.alpha, lam_cond.beta], {x: x_data})
    self.assertAllClose(alpha_val, alpha0 + x_data.sum())
    self.assertAllClose(beta_val, beta0 + len(x_data))

  def test_gamma_gamma(self):
    x_data = np.array([0.1, 0.5, 3.3, 2.7])

    alpha0 = 0.5
    beta0 = 1.75
    alpha_likelihood = 2.3
    beta = rvs.Gamma(alpha=alpha0, beta=beta0)
    x = rvs.Gamma(alpha=alpha_likelihood, beta=beta,
                  value=x_data)

    beta_cond = conj.complete_conditional(beta, [beta, x])

    self.assertIsInstance(beta_cond, rvs.Gamma)

    sess = tf.InteractiveSession()
    alpha_val, beta_val = sess.run([beta_cond.alpha, beta_cond.beta],
                                   {x: x_data})
    self.assertAllClose(alpha_val, alpha0 + alpha_likelihood * len(x_data))
    self.assertAllClose(beta_val, beta0 + x_data.sum())

  def test_mul_rate_gamma(self):
    x_data = np.array([0.1, 0.5, 3.3, 2.7])

    alpha0 = 0.5
    beta0 = 1.75
    alpha_likelihood = 2.3
    beta = rvs.Gamma(alpha=alpha0, beta=beta0)
    x = rvs.Gamma(alpha=alpha_likelihood, beta=alpha_likelihood * beta,
                  value=x_data)

    beta_cond = conj.complete_conditional(beta, [beta, x])

    self.assertIsInstance(beta_cond, rvs.Gamma)

    sess = tf.InteractiveSession()
    alpha_val, beta_val = sess.run([beta_cond.alpha, beta_cond.beta],
                                   {x: x_data})
    self.assertAllClose(alpha_val, alpha0 + alpha_likelihood * len(x_data))
    self.assertAllClose(beta_val, beta0 + alpha_likelihood * x_data.sum())

  def test_normal_normal(self):
    x_data = np.array([0.1, 0.5, 3.3, 2.7])

    mu0 = 0.3
    sigma0 = 2.1
    sigma_likelihood = 1.2

    mu = rvs.Normal(mu0, sigma0)
    x = rvs.Normal(mu, sigma_likelihood, sample_shape=len(x_data))

    mu_cond = conj.complete_conditional(mu, [mu, x])
    self.assertIsInstance(mu_cond, rvs.Normal)

    sess = tf.InteractiveSession()
    mu_val, sigma_val = sess.run([mu_cond.mu, mu_cond.sigma], {x: x_data})

    self.assertAllClose(sigma_val, (1. / sigma0**2 +
                                    len(x_data) / sigma_likelihood**2) ** -0.5)
    self.assertAllClose(mu_val,
                        sigma_val**2 * (mu0 / sigma0**2 +
                                        (1. / sigma_likelihood**2 *
                                         x_data.sum())))

  def test_normal_normal_scaled(self):
    x_data = np.array([0.1, 0.5, 3.3, 2.7])

    mu0 = 0.3
    sigma0 = 2.1
    sigma_likelihood = 1.2
    c = 2.

    mu = rvs.Normal(mu0, sigma0)
    x = rvs.Normal(c * mu, sigma_likelihood, sample_shape=len(x_data))

    mu_cond = conj.complete_conditional(mu, [mu, x])
    self.assertIsInstance(mu_cond, rvs.Normal)

    sess = tf.InteractiveSession()
    mu_val, sigma_val = sess.run([mu_cond.mu, mu_cond.sigma], {x: x_data})

    self.assertAllClose(sigma_val,
                        (1. / sigma0**2 +
                         c**2 * len(x_data) / sigma_likelihood**2) ** -0.5)
    self.assertAllClose(mu_val,
                        sigma_val**2 * (mu0 / sigma0**2 +
                                        (c / sigma_likelihood**2 *
                                         x_data.sum())))

  def test_dirichlet_categorical(self):
    x_data = np.array([0, 0, 0, 0, 1, 1, 1, 2, 2, 3], np.int32)
    N = x_data.shape[0]
    D = x_data.max() + 1

    alpha = np.zeros([D]).astype(np.float32) + 2.
    sample_shape = (N,)

    theta = rvs.Dirichlet(alpha)
    x = rvs.Categorical(p=theta, sample_shape=sample_shape)

    blanket = [theta, x]
    theta_cond = conj.complete_conditional(theta, blanket)

    sess = tf.InteractiveSession()
    alpha_val = sess.run(theta_cond.alpha, {x: x_data})

    self.assertAllClose(alpha_val, np.array([6., 5., 4., 3.], np.float32))

  def test_mog(self):
    x_val = np.array([1.1, 1.2, 2.1, 4.4, 5.5, 7.3, 6.8], np.float32)
    z_val = np.array([0, 0, 0, 1, 1, 2, 2], np.int32)
    pi_val = np.array([0.2, 0.3, 0.5], np.float32)
    mu_val = np.array([1., 5., 7.], np.float32)

    N = x_val.shape[0]
    K = z_val.max() + 1

    pi_alpha = 1.3 + np.zeros(K, dtype=np.float32)
    mu_sigma = 4.
    sigmasq = 2.**2

    pi = rvs.Dirichlet(pi_alpha)
    mu = rvs.Normal(0., mu_sigma, sample_shape=[K])

    x = rvs.ParamMixture(pi, {'mu': mu, 'sigma': tf.sqrt(sigmasq)},
                         rvs.Normal, sample_shape=N)
    z = x.cat

    blanket = [x, z, mu, pi]
    mu_cond = conj.complete_conditional(mu, blanket)
    pi_cond = conj.complete_conditional(pi, blanket)
    z_cond = conj.complete_conditional(z, blanket)

    sess = tf.InteractiveSession()
    pi_cond_alpha, mu_cond_mu, mu_cond_sigma, z_cond_p = (
        sess.run([pi_cond.alpha, mu_cond.mu, mu_cond.sigma, z_cond.p],
                 {z: z_val, x: x_val, pi: pi_val, mu: mu_val}))

    true_pi = pi_alpha + np.unique(z_val, return_counts=True)[1]
    self.assertAllClose(pi_cond_alpha, true_pi)
    for k in range(K):
      sigmasq_true = (1. / 4**2 + 1. / sigmasq * (z_val == k).sum())**-1
      mu_true = sigmasq_true * (1. / sigmasq * x_val[z_val == k].sum())
      self.assertAllClose(np.sqrt(sigmasq_true), mu_cond_sigma[k])
      self.assertAllClose(mu_true, mu_cond_mu[k])
    true_log_p_z = np.log(pi_val) - 0.5 / sigmasq * (x_val[:, np.newaxis] -
                                                     mu_val)**2
    true_log_p_z -= true_log_p_z.max(1, keepdims=True)
    true_p_z = np.exp(true_log_p_z)
    true_p_z /= true_p_z.sum(1, keepdims=True)
    self.assertAllClose(z_cond_p, true_p_z)


if __name__ == '__main__':
  tf.test.main()
