import math
import numpy as np
import numba as nb


def get_model_list():
    return(['gaussian','dgaussian','lorentzian','asym_dgaussian','tgaussian'])



kwd = {"parallel": False, "fastmath": True}

@nb.njit(**kwd)
def gaussian(x, mu, sigma,A,B):
    return (A+B / np.sqrt(2 * np.pi) / sigma * np.exp(-(x - mu)**2 / 2. / sigma**2))

@nb.njit(**kwd)
def double_gaussian(x, mu, sigma,mu_2,sigma_2,A,B,C):
    return (A + B * np.exp(-(x - mu)**2 / 2. / sigma**2)+ C * np.exp(-(x - mu_2)**2 / 2. / sigma_2** 2))

@nb.njit(**kwd)
def triple_gaussian(x, A, mu, sigma,mu_2,sigma_2,mu_3,sigma_3, B,C, D):
    return (A + B * np.exp(-(x - mu)**2 / 2. / sigma**2)+ C * np.exp(-(x - mu_2)**2 / 2. / sigma_2** 2)+  D * np.exp(-(x - mu_3)**2 / 2. / sigma_3** 2))

    
@nb.njit(**kwd)
def assymetric_gaussian_pdf(x,mu,sigma1,sigma2):
    if x<=mu:
            return(2 / np.sqrt(2 * np.pi) / (sigma1+sigma2) * np.exp(-(x - mu) ** 2 / 2. / sigma1 ** 2))
    else:
            return(2 / np.sqrt(2 * np.pi) / (sigma1+sigma2) * np.exp(-(x - mu) ** 2 / 2. / sigma2 ** 2))
        
@nb.njit(**kwd)
def assymetric_double_gaussian(x, mu, sigma1,sigma2,mu_2,sigma1_2,sigma2_2,A,B,C):
    #assymetric_gaussian_pdf_vec=np.vectorize(assymetric_gaussian_pdf)
    return (A+B*assymetric_gaussian_pdf(x,mu,sigma1,sigma2)+C*assymetric_gaussian_pdf(x,mu_2,sigma1_2,sigma2_2))/(A+B+C)
    

@nb.njit(**kwd)  
def lorentz_pdf(x,mu,gamma):
    return 1/(np.pi*gamma)*(gamma**2)/((x-mu)**2+gamma**2)

@nb.njit(**kwd)
def double_lorentz(x, mu_1, gamma_1,mu_2,gamma_2,A,B,C):
    #lorentz_pdf_vec=np.vectorize(lorentz_pdf)
    return (A+B*lorentz_pdf(x,mu_1,gamma_1)+C*lorentz_pdf(x,mu_2,gamma_2))/(A+B+C)