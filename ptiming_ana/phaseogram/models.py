import numpy as np
import numba as nb


def get_model_list():
    return [
        "gaussian",
        "dgaussian",
        "double_lorentz",
        "asym_dgaussian",
        "tgaussian",
        "lorentzian",
    ]


kwd = {"parallel": False, "fastmath": True}


@nb.njit(**kwd)
def gaussian(x, mu, sigma, A, B):
    return A + B / np.sqrt(2 * np.pi) / sigma * np.exp(
        -((x - mu) ** 2) / 2.0 / sigma**2
    )


@nb.njit(**kwd)
def double_gaussian(x, mu, sigma, mu_2, sigma_2, A, B, C):
    return (
        A
        + B / np.sqrt(2 * np.pi) / sigma * np.exp(-((x - mu) ** 2) / 2.0 / sigma**2)
        + C
        / (2 * np.pi) ** (1 / 2)
        / sigma_2
        * np.exp(-((x - mu_2) ** 2) / 2.0 / sigma_2**2)
    )


@nb.njit(**kwd)
def triple_gaussian(x, Bkg, mu, sigma, mu_2, sigma_2, mu_3, sigma_3, A, B, C):
    return (
        Bkg
        + A / np.sqrt(2 * np.pi) / sigma * np.exp(-((x - mu) ** 2) / 2.0 / sigma**2)
        + B
        / np.sqrt(2 * np.pi)
        / sigma_2
        * np.exp(-((x - mu_2) ** 2) / 2.0 / sigma_2**2)
        + C
        / np.sqrt(2 * np.pi)
        / sigma_3
        * np.exp(-((x - mu_3) ** 2) / 2.0 / sigma_3**2)
    )


@nb.njit(**kwd)
def assymetric_gaussian_pdf(x, mu, sigma1, sigma2):
    if x <= mu:
        return (
            2
            / np.sqrt(2 * np.pi)
            / (abs(sigma1) + abs(sigma2))
            * np.exp(-((x - mu) ** 2) / 2.0 / sigma1**2)
        )
    else:
        return (
            2
            / np.sqrt(2 * np.pi)
            / (abs(sigma1) + abs(sigma2))
            * np.exp(-((x - mu) ** 2) / 2.0 / sigma2**2)
        )


@nb.njit(**kwd)
def assymetric_double_gaussian(
    x, mu, sigma1, sigma2, mu_2, sigma1_2, sigma2_2, A, B, C
):
    return (
        A
        + B * assymetric_gaussian_pdf(x, mu, sigma1, sigma2)
        + C * assymetric_gaussian_pdf(x, mu_2, sigma1_2, sigma2_2)
    )


@nb.njit(**kwd)
def lorentz_pdf(x, mu, gamma):
    return 1 / (np.pi * gamma) * (gamma**2) / ((x - mu) ** 2 + gamma**2)


def lorentzian(x, mu, gamma, A, B):
    return A + B / (np.pi * gamma) * (gamma**2) / ((x - mu) ** 2 + gamma**2)


@nb.njit(**kwd)
def double_lorentz(x, mu_1, gamma_1, mu_2, gamma_2, A, B, C):
    # lorentz_pdf_vec=np.vectorize(lorentz_pdf)
    return A + B * lorentz_pdf(x, mu_1, gamma_1) + C * lorentz_pdf(x, mu_2, gamma_2)
