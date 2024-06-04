import pickle
import os.path
from scipy.optimize import basinhopping
from scipy.optimize import minimize
from efficiencies import *
#from efficiencies_circ import *
import sys
from functions import select_data
from time import time
sys.path.append("C:\Program Files (x86)\CST Studio Suite 2023\AMD64\python_cst_libraries")
import cst
import cst.results
import cst.interface


class OptimizeCST:
    def __init__(self,
                 project_path,
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
                 tolerance,
                 splits=55,
                 fail_stop=10):

        self.project_path = project_path
        self.farfield_name = farfield_name
        self.result_file = result_path + result_file_name
        self.result_file_name = result_file_name
        self.reflector_file_name = reflector_file_name

        self.wavelength = 3e8 / frequency
        self.open_angle = open_angle
        self.diameter = diameter

        self.splits = splits
        self.fail_stop = fail_stop

        self.parameter_values_file_name = parameter_values_file_name
        self.efficiencies_file_name = efficiencies_file_name

        # make sure there is not already a file with the same name
        OptimizeCST.does_pickle_exist(self.parameter_values_file_name)
        OptimizeCST.does_pickle_exist(self.efficiencies_file_name)

        self.project, self.de = self.connect()

        self.parameter_names = parameter_names
        self.parameter_values = parameter_values
        self.parameter_bounds = parameter_bounds
        self.tolerance = tolerance

        self.iteration = 0  # how many iterations we have done

    def main(self):
        minimizer_kwargs = {"bounds": self.parameter_bounds, "tol": self.tolerance}
        #res = basinhopping(self.run_optimize,
        #                   self.parameter_values,
        #                   minimizer_kwargs=minimizer_kwargs)
        res = minimize(self.run_optimize,
                       self.parameter_values,
                       method="Nelder-Mead",
                       bounds=self.parameter_bounds,
                       tol=self.tolerance)

        print("Optimization done! \n")

        for i in range(len(res.x)):
            print("\t" + str(res.x[i]) + " = " + str(self.parameter_names[i]))

        print("\n e_ap = " + str(1 - res.fun))

    # Uses exception handling to catch errors raised by CST
    def run_cst_safe(self, fun):
        try:
            fun()
        except RuntimeError as error:
            print("\t" + str(error))

            #ans = input("An error occurred. Would you like to try the function again yes/no?")
            #ans = ans.lower()

            #accepted_ans = False
            #while not accepted_ans:
            #    if ans == "yes":
            #        accepted_ans = True
            #        self.run_cst_safe(fun)

            #    elif ans == "no":
            #        accepted_ans = True

            #    else:
            #        ans = input("Make sure you input an accepted answer. Would you like to try the function again yes/no?")
            #        ans = ans.lower()

    def run_optimize(self, parameter_values):
        tic = time()
        self.parameter_values = parameter_values
        
        OptimizeCST.save(self.parameter_values, self.parameter_values_file_name)
        self.run_cst_safe(self.set_parameters)
        self.run_cst_safe(self.run_solver)
        #self.run_cst_safe(self.move_origin)
        e_ap = self.calculate_efficiencies()

        self.iteration += 1
        toc = time() - tic
        print("After " + str(round(toc / 60,  2)) + " minutes, iteration " + str(self.iteration) + " is done!\n")

        return 1 - e_ap

    def connect(self):
        de = cst.interface.DesignEnvironment()
        my_project = de.open_project(self.project_path)

        return my_project, de

    def set_parameters(self):
        self.center_origin()  # make sure the origin is in the right place

        define = """
                Sub Main
                StoreParameter("{}","{}")
                End Sub"""
        print("Parameters set to: ")
        for i in range(len(self.parameter_names)):
            self.project.schematic.execute_vba_code(define.format(self.parameter_names[i],
                                                                  str(self.parameter_values[i])))
            print("\t" + str(self.parameter_names[i]) + " = " + str(self.parameter_values[i]))

    # stop is how many times it tries if the solver fails
    def run_solver(self):
        print("Running solver...")
        self.project.modeler.run_solver()

    def move_origin(self):
        phase, theta, phi = select_data(self.result_file, "Phase(Copol)", self.open_angle)

        phase = array(phase) * pi / 180

        #z = 0
        #for i in range(len(phase)):
        #    z += ((phase[i, 0] - phase[i, -1]) / (2 * pi * (1 - cos(phase[i, -1]))) * self.wavelength)
        #z = z / len(phase)

        #element = int(len(phase) / 4) - 1  # want the 90 degree element
        #z = ((phase[element, 0] - phase[element, -1]) / (2 * pi * (1 - cos(phase[element, -1]))) * self.wavelength)

        difference = 0
        highest = 0
        for i in range(len(phase)):
            difference += phase[i, 0] - phase[i, -1]
            highest += 1 - cos(phase[i, -1])

        z = (difference / (2 * pi * highest) * self.wavelength)

        print("Moving origin to z = " + str(z))

        define = """
                Sub Main
                WCS.setOrigin("{}","{}","{}")
                End Sub"""

        self.project.schematic.execute_vba_code(define.format(0, 0, z*1000))  # CST is set to mm

        define = """
                Sub Main
                SelectTreeItem ("Farfields\\{}")
                End Sub"""

        self.project.schematic.execute_vba_code(define.format(self.farfield_name))

        define = """
                Sub Main
                ASCIIExport.FileName ("../../Export/Farfield/{}")
                ASCIIExport.Execute
                End Sub"""

        self.project.schematic.execute_vba_code(define.format(self.result_file_name))

    def center_origin(self):
        print("Origin centered")

        define = """
                        Sub Main
                        WCS.setOrigin("{}","{}","{}")
                        End Sub"""

        self.project.schematic.execute_vba_code(define.format(0, 0, 0))

    def calculate_efficiencies(self):
        print("Calculating efficiencies...")

        eff_ill = e_ill(self.result_file, self.open_angle, self.diameter, self.reflector_file_name, self.splits)
        print("\tIllumination efficiency = " + str(eff_ill))

        eff_pol = e_pol(self.result_file, self.open_angle, self.diameter, self.reflector_file_name, self.splits)
        print("\tPolarization efficiency = " + str(eff_pol))

        eff_phase = e_phase(self.result_file, self.open_angle, self.diameter, self.reflector_file_name, self.splits)
        print("\tPhase efficiency = " + str(eff_phase))

        eff_spill = e_spill(self.result_file, self.open_angle, self.diameter, self.reflector_file_name, self.splits)
        print("\tSpillover efficiency = " + str(eff_spill))

        # todo don't set minor and major like this, now we have to keep track of which order we input the parametrs, which is not good
        #eff_block = e_block(self.result_file, self.open_angle, self.diameter, self.parameter_values[0] * self.parameter_values[1], self.parameter_values[0], self.reflector_file_name, self.splits)
        eff_block = e_block(self.result_file, self.open_angle, self.diameter, self.parameter_values[0], self.parameter_values[0], self.reflector_file_name, self.splits)
        print("\tBlockage efficiency = " + str(eff_block))

        effs = [eff_ill, eff_pol, eff_phase, eff_spill, eff_block]
        OptimizeCST.save(effs, self.efficiencies_file_name)

        e_ap_simp = eff_ill * eff_pol * eff_phase * eff_spill
        e_ap = e_ap_simp * eff_block
        print("\t-> Aperture efficiency without blockage = " + str(e_ap_simp) + " and Aperture efficiency = " + str(e_ap))
        # todo set back to e_ap
        return e_ap_simp

    @staticmethod
    def does_pickle_exist(name):
        if os.path.isfile(name):
            raise FileExistsError("The pickle file already exist.")

    @staticmethod
    def save(my_var, name):
        with open(name, 'ab') as file:
            pickle.dump(my_var, file)

    @staticmethod
    def load(name):
        my_var = []
        with (open(name, "rb")) as file:
            while True:
                try:
                    my_var.append(pickle.load(file))
                except EOFError:
                    break
        return my_var

    @staticmethod
    def load_last(name):
        my_var = OptimizeCST.load(name)
        return my_var[-1]
