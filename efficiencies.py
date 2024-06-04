import matplotlib.pyplot as plt

from functions import select_data
from functions import select_data_asymmetric
from numpy import *

"""
def calc_theta_0(theta):
    theta_0 = 0
    for i in range(len(theta)):
        theta_0 += max(theta[i, :])
    return theta_0 / 360


def calc_tan(theta):
    t = 0
    for i in range(len(theta)):
        theta_0 = max(theta[i, :])
        t += (1 / (tan(theta_0 / 2))) ** 2

    return t / 360
"""


def calc_theta_0(theta):
    theta_0 = zeros([len(theta), len(theta[0])])
    for i in range(len(theta)):
        theta_0[i, :] = theta[i, -1]
    return theta_0


def calc_phase_center(co, phase, theta, phi):
    w = co * tan(theta)
    I_w = trapz(trapz(w, theta), phi[:, 0])
    I_w_c = trapz(trapz(w * (cos(theta) - 1), theta), phi[:, 0])
    I_w_2 = trapz(trapz(w * (cos(theta) - 1) ** 2, theta), phi[:, 0])
    I_w_phi = trapz(trapz(w * (phase - phase[0, :]), theta), phi[:, 0])
    I_w_phi_c = trapz(trapz(w * (cos(theta) - 1) * (phase - phase[0, :]), theta), phi[:, 0])

    k_delta = ((I_w * I_w_phi_c) - (I_w_phi * I_w_c)) / ((I_w_2 * I_w) - I_w_c ** 2)

    return phase - (k_delta * cos(theta))


def e_ill(file_name, open_angle, diameter, reflector_file_name="", splits=55):
    if reflector_file_name == "":
        co, theta, phi = select_data(file_name, "Abs(Copol)", open_angle)
    else:
        co, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Abs(Copol)", open_angle, diameter, splits)

    theta = array(theta) * pi / 180
    phi = array(phi) * pi / 180
    co = array(co)
    theta_0 = calc_theta_0(theta)

    num = 2 * trapz(trapz(co * tan(theta / 2), theta) ** 2, phi[:, 0])
    den = trapz(trapz(tan(theta_0 / 2) ** 2 * co ** 2 * sin(theta), theta), phi[:, 0])

    return num / den


# Is this for linear or circular pol? The book has different formulas, but maybe it is not needed since the integration
# is done over the whole field?
def e_pol(file_name, open_angle, diameter, reflector_file_name="", splits=55):
    if reflector_file_name == "":
        xp, theta, phi = select_data(file_name, "Abs(Cross)", open_angle)
        co, theta, phi = select_data(file_name, "Abs(Copol)", open_angle)
    else:
        co, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Abs(Copol)", open_angle, diameter,
                                                splits)
        xp, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Abs(Cross)", open_angle, diameter,
                                                splits)

    theta = array(theta) * pi / 180
    phi = array(phi) * pi / 180

    co = array(co)
    xp = array(xp)

    num = trapz(trapz(co ** 2 * sin(theta), theta), phi[:, 0])
    den = trapz(trapz((co ** 2 + xp ** 2) * sin(theta), theta), phi[:, 0])

    return num / den


def e_phase(file_name, open_angle, diameter, reflector_file_name="", splits=55):
    if reflector_file_name == "":
        co, theta, phi = select_data(file_name, "Abs(Copol)", open_angle)
        phase, theta, phi = select_data(file_name, "Phase(Copol)", open_angle)
    else:
        co, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Abs(Copol)", open_angle, diameter,
                                                splits)
        phase, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Phase(Copol)", open_angle, diameter,
                                                splits)

    theta = array(theta) * pi / 180
    phi = array(phi) * pi / 180
    phase = array(phase) * pi / 180
    co = array(co)

    phase_delta = calc_phase_center(co, phase, theta, phi)

    #plt.plot(theta[0, :], unwrap(phase[0, :]))
    #plt.show()

    num = trapz(abs(trapz(co * exp(1j * phase_delta) * tan(theta/2), theta)) ** 2, phi[:, 0])
    #num = trapz(abs(trapz(co * exp(1j * phase) * tan(theta / 2), theta)) ** 2, phi[:, 0])
    den = (trapz(trapz(co * tan(theta/2), theta) ** 2, phi[:, 0]))

    return num / den


def e_spill(file_name, open_angle, diameter, reflector_file_name="", splits=55):
    co_0, theta_0, phi_0 = select_data(file_name, "Abs(Copol)", 180)
    xp_0, theta_0, phi_0 = select_data(file_name, "Abs(Cross)", 180)

    if reflector_file_name == "":
        co, theta, phi = select_data(file_name, "Abs(Copol)", open_angle)
        xp, theta, phi = select_data(file_name, "Abs(Cross)", open_angle)

    else:
        co, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Abs(Copol)", open_angle, diameter,
                                                splits)
        xp, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Abs(Cross)", open_angle, diameter,
                                                splits)

    theta = array(theta) * pi / 180
    phi = array(phi) * pi / 180
    co = array(co)
    xp = array(xp)

    theta_0 = array(theta_0) * pi / 180
    phi_0 = array(phi_0) * pi / 180
    co_0 = array(co_0)
    xp_0 = array(xp_0)

    num = trapz(trapz((co ** 2 + xp ** 2) * sin(theta), theta), phi[:, 0])
    den = (trapz(trapz((co_0 ** 2 + xp_0 ** 2) * sin(theta_0), theta_0), phi_0[:, 0]))

    return num / den


def e_block(file_name, open_angle, diameter, minor, major, reflector_file_name="", splits=55):
    if reflector_file_name == "":
        co, theta, phi = select_data(file_name, "Abs(Copol)", open_angle)
        phase, theta, phi = select_data(file_name, "Phase(Copol)", open_angle)
    else:
        co, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Abs(Copol)", open_angle, diameter,
                                                splits)
        phase, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Phase(Copol)", open_angle, diameter,
                                                splits)

    theta = array(theta) * pi / 180
    phi = array(phi) * pi / 180
    co = array(co)
    theta_0 = calc_theta_0(theta)

    A = 89703.2  # todo don't set this manually here
    a = pi * minor * major

    c_b_num = trapz(tan(theta_0[:, 0] / 2) ** 2 * co[:, 0] ** 2, phi[:, 0])
    c_b_den = trapz(trapz(co * tan(theta / 2), theta), phi[:, 0])
    c_b = c_b_num / c_b_den
    delta_cb = c_b * (a / A) ** 2
    return abs(1 - delta_cb) ** 2


def find_phase_center(file_name, open_angle, diameter, reflector_file_name):
    phase, theta, phi = select_data_asymmetric(file_name, reflector_file_name, "Phase(Copol)", open_angle, diameter, splits=55)
    phase = array(phase) * pi / 180

    wavelength = 3e8/19.5e9

    difference = 0
    highest = 0
    for i in range(len(phase)):
        difference += phase[i, 0] - phase[i, -1]
        highest += 1 - cos(phase[i, -1])

    z = (difference / (2 * pi * highest) * wavelength)
    return z*1000



#file = "farfields/farfield_custom.txt"
#file = "farfields/2_feed_new.txt"
#file = "farfields/1_feed.txt"
#file = "farfields/wg_3.txt"
#file = "farfields/wg.txt"
#angle = 90
#d = 450
#ref = "geometry/reflector.stl"

#print(e_ill(file, angle, d))
#print(e_pol(file, angle, d))
#print(e_phase(file, angle, d))
#print(e_spill(file, angle, d))


