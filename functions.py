import re
from numpy import *
import matplotlib.pyplot as plt
from stl import mesh
from mpl_toolkits import mplot3d
import pickle


def read_farfield(file_name):
    header_line = 0
    data_start_line = 2

    # a list of dictionaries containing all the data
    data = {}

    # read and clean the data
    with open(file_name) as f:
        lines = f.readlines()

        header = lines[header_line]
        lines = lines[data_start_line:]

        # remove junk
        header = re.sub("[\[].*?[\]]", "", header.strip())
        header = re.sub('\(\s*(.*?)\s*\)', r'(\1)', header)
        header = re.sub('[, ]+', ',', header)
        for i in range(len(lines)):
            lines[i] = re.sub('[, ]+', ',', lines[i].strip(" />\n:"))

        header = header.split(",")
        for key in header:
            data[key] = []
        for i in range(len(lines)):
            values = lines[i].split(",")
            for j in range(len(values)):
                data[header[j]].append(float(values[j]))

    return data


def select_data(file_name, field_name, stop_angle=90, phi_cut=None):
    data = read_farfield(file_name)

    if phi_cut is not None:
        field_1 = []
        theta_1 = []
        field_2 = []
        theta_2 = []
        phi = []
        i = 0
        while i < len(data["Theta"]):
            if data["Phi"][i] == phi_cut:
                if 0 <= data["Theta"][i] <= stop_angle:
                    field_1.append(data[field_name][i])
                    theta_1.append(data["Theta"][i])
                    phi.append(phi_cut)
            #elif data["Phi"][i] == phi_cut + 180:
            #    if 0 <= data["Theta"][i] <= stop_angle:
            #        field_2.append(data[field_name][i])
            #        theta_2.append(-data["Theta"][i])
            #        phi.append(phi_cut)
            i = i + 1

        #field_1 = flip(field_1)
        #theta_1 = flip(theta_1)

        #field = append(field_1, field_2)
        #theta = append(theta_1, theta_2)

        return field_1, theta_1, phi_cut

    else:
        field = []
        theta = []
        phi = []

        phi_number = 0  # the number of phi values
        phi_value = 0  # finds the number of unique phi values. Put it to the first phi value.
        # We have the data -pi/2 < phi < pi/2 and -pi/2 < theta < pi/2, we want
        # -pi < phi < pi and 0 < theta < pi/2, this solves that
        for i in range(len(data["Theta"])):
            if 0 < data["Theta"][i] <= stop_angle:
                if not data["Phi"][i] == phi_value:
                    phi_number += 1
                    phi_value += 1

                field.append(data[field_name][i])
                theta.append(data["Theta"][i])
                phi.append(data["Phi"][i])

        phi = array(phi).reshape(phi_number + 1, stop_angle)
        field = array(field).reshape(phi_number + 1, stop_angle)
        theta = array(theta).reshape(phi_number + 1, stop_angle)

        return field, theta, phi


def import_stl(file_name, return_area=False, do_plot=False):
    surf = mesh.Mesh.from_file(file_name)

    x = surf.x[:].flatten()
    y = surf.y[:].flatten()
    z = surf.z[:].flatten()

    if do_plot:
        figure = plt.figure()
        axes = figure.add_subplot(projection='3d')
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(surf.vectors))
        scale = surf.points.flatten()
        axes.auto_scale_xyz(scale, scale, scale)
        plt.show()

    if not return_area:
        return x, y, z
    else:
        areas = surf.areas
        area = 0
        for a in areas:
            area += float(a)

        return x, y, z, area


def cartesian_to_polar(x, y):
    r = sqrt(x ** 2 + y ** 2)
    phi = arctan2(x, y)
    for i in range(len(phi)):
        if phi[i] < 0:
            phi[i] = 2 * pi + phi[i]
    return r, phi


def outline(r, phi, splits=20):
    # sort from the smallest phi to the biggest
    phi, r = zip(*sorted(zip(phi, r)))
    phi = array(phi)
    r = array(r)

    # The first value is the start of the outline
    r_outline = array([])
    phi_outline = array([])

    # The sections which are used to calculate the outline, bigger splits gives higher accuracy
    sections = linspace(0, 2*pi, splits)
    for i in range(1, len(sections)):
        index = where((phi > sections[i - 1]) & (phi < sections[i]))[0]
        phis = take(phi, index)
        rs = take(r, index)
        index = argmax(rs)

        r_outline = append(r_outline, rs[index])
        phi_outline = append(phi_outline, phis[index])

    # the last value is the end of the outline
    r_outline = append(r_outline, r[-1])
    phi_outline = append(phi_outline, phi[-1])

    return r_outline, phi_outline


def angles_to_radius(angles, open_angle, diameter):
    r = diameter / 2 * sin(angles) / sin(open_angle * pi / 180)
    return r


def data_in_outline(field, theta_field, phi_field, r_field, phi_outline, r_outline):
    for i in range(len(phi_field)):
        index = argmin(abs(phi_outline - phi_field[i]))
        if r_field[i] > r_outline[index]:
            field[i] = field[i - 1]
            theta_field[i] = theta_field[i - 1]
            #phi_field[i] = phi_field[i - 1]
            #field[i] = 0

    return field, theta_field, phi_field


def select_data_asymmetric(field_file_name, reflector_file_name, field_name, open_angle, diameter, splits=20, do_plot=False):
    field, theta, phi = select_data(field_file_name, field_name, open_angle)

    rows = size(field, axis=0)
    cols = size(field, axis=1)

    field = array(field).flatten()
    theta = (array(theta) * pi / 180).flatten()
    phi = (array(phi) * pi / 180).flatten()

    r = angles_to_radius(theta, open_angle, diameter)

    x, y, z = import_stl(reflector_file_name)
    r_ref, phi_ref = cartesian_to_polar(x, y)
    r_outline, phi_outline = outline(r_ref, phi_ref, splits)

    #plt.plot(phi * 180 / pi, r, ".")
    #plt.plot(phi_outline * 180 / pi, r_outline)
    #plt.xlabel(r"Angle [$^\circ$]", fontsize=14)
    #plt.ylabel(r"Radius [mm]", fontsize=14)
    #plt.yticks(fontsize=14)
    #plt.xticks(fontsize=14)
    #plt.show()

    field, theta, phi = data_in_outline(field, theta, phi, r, phi_outline, r_outline)
    r = angles_to_radius(theta, open_angle, diameter)

    if do_plot:
        #index = where(field > 0)[0]
        plt.plot(phi*180/pi, r, ".")
        plt.plot(phi_outline *180/pi, r_outline)
        plt.xlabel(r"Angle [$^\circ$]", fontsize=14)
        plt.ylabel(r"Radius [mm]", fontsize=14)
        plt.yticks(fontsize=14)
        plt.xticks(fontsize=14)
        plt.show()

    field = field.reshape(rows, cols)
    theta = theta.reshape(rows, cols)
    phi = phi.reshape(rows, cols)

    theta = theta * 180 / pi
    phi = phi * 180 / pi

    return field, theta, phi


def plot(field_file_name, field_name, phi_cut=0, stop_angle=180, db=False, polar=False, style=""):
    field_1, theta_1, phi = select_data(field_file_name, field_name, stop_angle, phi_cut=phi_cut)
    field_2, theta_2, phi_ignore = select_data(field_file_name, field_name, stop_angle, phi_cut=phi_cut + 180)

    field_1 = flip(field_1)
    theta_1 = flip(theta_1)

    theta_2 = -array(theta_2)
    field = append(field_1, field_2)
    theta = append(theta_1, theta_2)

    if db:
        field = 10 * log10(field)

    if polar:
        theta = [theta[i] * pi / 180 for i in range(len(theta))]
        plt.axes(projection='polar')

    plt.plot(theta, field, style)
    plt.show()


def plot_3d(field_file_name, field_name, reflector_file_name="", diameter=None, stop_angle=180, spherical=False, db=False, splits=20):
    if reflector_file_name == "":
        field, theta, phi = select_data(field_file_name, field_name, stop_angle)
    else:
        # not good to just raise "Exception" but I don't really care
        if diameter is None:
            raise Exception("Invalid diameter")
        if stop_angle > 90:
            raise Exception("Angle is bigger than 90 degrees")

        field, theta, phi = select_data_asymmetric(field_file_name, reflector_file_name, field_name, stop_angle, diameter, splits=splits)

    field = array(field)
    theta = array(theta) * pi / 180
    phi = array(phi) * pi / 180

    ax = plt.axes(projection='3d')

    if db:
        field = 10 * log10(field)

    if spherical:
        ax.plot_surface(field * sin(theta) * cos(phi),
                        field * sin(theta) * sin(phi),
                        field * cos(theta))
    else:
        ax.plot_surface(theta, phi, field)

    plt.show()


def plot_values(file_name):
    values = []
    with (open(file_name, "rb")) as file:
        while True:
            try:
                values.append(pickle.load(file))
            except EOFError:
                break

    values = array(values)

    plt.plot(values[:, 0], label="$e_{ill}$")
    plt.plot(values[:, 1], label="$e_{pol}$")
    plt.plot(values[:, 2], label="$e_{\Phi}$")
    plt.plot(values[:, 3], label="$e_{sp}$")
    plt.legend()
    plt.rcParams['text.usetex'] = True
    plt.show()


def plot_parameters(file_name):
    values = []
    with (open(file_name, "rb")) as file:
        while True:
            try:
                values.append(pickle.load(file))
            except EOFError:
                break

    values = array(values)

    plt.plot(values[:, 0], label="Dsr")
    plt.plot(values[:, 1], label="ratio")
    plt.plot(values[:, 2], label="theta_e")
    plt.plot(values[:, 3], label="horn")
    plt.plot(values[:, 4], label="m")
    plt.plot(values[:, 5], label="feed_offset")
    plt.legend()
    plt.rcParams['text.usetex'] = True
    plt.show()


