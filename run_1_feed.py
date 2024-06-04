from optimize_relector import OptimizeCST
from numpy import *


def main():
    project_path = "1_feed_dual_reflector_2.cst"
    farfield_name = "farfield (f=19.5) [1(1)]"
    result_path = ".\\1_feed_dual_reflector_2\\Export\\Farfield\\"
    result_file_name = farfield_name + ".txt"
    reflector_file_name = "reflector.stl"

    frequency = 19.5e9
    open_angle = 90
    diameter = 450

    parameter_values_file_name = "1parameters.pkl"
    efficiencies_file_name = "1efficiencies.pkl"

    parameter_names = array(["Dsr", "ratio", "theta_e", "horn", "m", "feed_offset"])
    parameter_values = array([70, 0.7, 1.08, 0, 20, 0])
    parameter_bounds = ((30, 85), (0.4, 1), (pi/10, 1.55), (0, 30), (10, 70), (-40, 30))
    tolerance = 0.01

    opt = OptimizeCST(project_path,
                      farfield_name,
                      result_path,
                      result_file_name,
                      reflector_file_name,
                      parameter_values_file_name,
                      efficiencies_file_name,
                      frequency,
                      open_angle,
                      diameter,
                      parameter_names,
                      parameter_values,
                      parameter_bounds,
                      tolerance)
    opt.main()


if __name__ == "__main__":
    main()