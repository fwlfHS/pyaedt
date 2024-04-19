"""
HFSS: Eigenmode filter
----------------------
This example shows how you can use PyAEDT to automate the eigenmode solver in HFSS.
Eigenmode analysis can be applied to open, radiating structures
using an absorbing boundary condition. This type of analysis is useful for
determining the resonant frequency of a geometry or an antenna and can be used to refine
the mesh at the resonance, even when the resonant frequency of the antenna is not known.

The challenge posed by this method is to identify and filter the non-physical modes
resulting from reflection from boundaries of the main domain.
Because the Eigenmode solver sorts by frequency and does not filter on the
quality factor, these virtual modes are present when the eigenmode approach is
applied to nominally open structures.
When looking for resonant modes over a wide frequency range for nominally
enclosed structures, several iterations may be required because the minimum frequency
is determined manually and simulations re-run until the complete frequency range is covered
and all important physical modes are calculated.

The following script finds the physical modes of a model in a wide frequency range by automating the solution setup.
During each simulation, a user-defined number of modes is simulated, and the modes with a Q higher than a user- defined value are filtered.
The next simulation automatically continues to find modes having a frequency higher than the last mode of the previous analysis.
This continues until the maximum frequency in the desired range is achieved.
"""

###############################################################################
# Perform required imports
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Run through each cell. This cell imports the required packages.

import sys
import os
import pyaedt

# Create a temporary folder to download the example to.

temp_folder = pyaedt.generate_unique_folder_name()
project_path = pyaedt.downloads.download_file("eigenmode", "emi_PCB_house.aedt", temp_folder)

##########################################################
# Set AEDT version
# ~~~~~~~~~~~~~~~~
# Set AEDT version.

aedt_version = "2024.1"

###############################################################################
# Set non-graphical mode
# ~~~~~~~~~~~~~~~~~~~~~~
# Set non-graphical mode. 
# You can set ``non_graphical`` either to ``True`` or ``False``.

non_graphical = False

###############################################################################
# Launch AEDT
# ~~~~~~~~~~~
# Launch AEDT 2023 R2 in graphical mode.

d = pyaedt.launch_desktop(aedt_version, non_graphical=non_graphical, new_desktop_session=True)

###############################################################################
# Launch HFSS
# ~~~~~~~~~~~
# Launch HFSS 2023 R2 in graphical mode.

hfss = pyaedt.Hfss(projectname=project_path, non_graphical=non_graphical)

###############################################################################
# Input parameters for eigenmode solver
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The geometry and material should be already set. The analyses are generated by the code.
# Number of modes during each analysis, max allowed number is 20.
# Entering a number higher than 10 might need long simulation time as the
# eigenmode solver needs to converge on modes. ``fmin`` is the lowest frequency
# of interest. ``fmax`` is the highest frequency of interest.
# ``limit`` is the parameter limit that determines which modes are ignored.

num_modes = 6
fmin = 1
fmax = 2
next_fmin = fmin
setup_nr = 1

limit = 10
resonance = {}


###############################################################################
# Find the modes
# ~~~~~~~~~~~~~~
# The following cell is a function.  If called, it creates an eigenmode setup and solves it.
# After the solve, each mode, along with its corresponding real frequency and quality factor,
# are saved for further processing.

def find_resonance():
    # setup creation
    next_min_freq = str(next_fmin) + " GHz"
    setup_name = "em_setup" + str(setup_nr)
    setup = hfss.create_setup(setup_name)
    setup.props['MinimumFrequency'] = next_min_freq
    setup.props['NumModes'] = num_modes
    setup.props['ConvergeOnRealFreq'] = True
    setup.props['MaximumPasses'] = 10
    setup.props['MinimumPasses'] = 3
    setup.props['MaxDeltaFreq'] = 5
    # analyzing the eigenmode setup
    hfss.analyze_setup(setup_name, cores=8, use_auto_settings=True)
    # getting the Q and real frequency of each mode
    eigen_q = hfss.post.available_report_quantities(quantities_category="Eigen Q")
    eigen_mode = hfss.post.available_report_quantities()
    data = {}
    cont = 0
    for i in eigen_mode:
        eigen_q_value = hfss.post.get_solution_data(expressions=eigen_q[cont],
                                                    setup_sweep_name=setup_name + ' : LastAdaptive',
                                                    report_category="Eigenmode")
        eigen_mode_value = hfss.post.get_solution_data(expressions=eigen_mode[cont],
                                                       setup_sweep_name=setup_name + ' : LastAdaptive',
                                                       report_category="Eigenmode")
        data[cont] = [eigen_q_value.data_real()[0], eigen_mode_value.data_real()[0]]
        cont += 1

    print(data)
    return data


###############################################################################
# Automate eigenmode solution
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Running the next cell calls the resonance function and saves only those modes with a Q higher than the defined
# limit. The ``find_resonance`` function is called until the complete frequency range is covered.
# When the automation ends, the physical modes in the whole frequency range are reported.

while next_fmin < fmax:
    output = find_resonance()
    next_fmin = output[len(output) - 1][1] / 1e9
    setup_nr += 1
    cont_res = len(resonance)
    for q in output:
        if output[q][0] > limit:
            resonance[cont_res] = output[q]
            cont_res += 1

resonance_frequencies = [f"{resonance[i][1] / 1e9:.5} GHz" for i in resonance]
print(str(resonance_frequencies))

###############################################################################
# Save project
# ~~~~~~~~~~~~
# Save the project.

hfss.modeler.fit_all()
hfss.plot(show=False, export_path=os.path.join(hfss.working_directory, "Image.jpg"), plot_air_objects=False)

###############################################################################
# Save project and close AEDT
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Save the project and close AEDT.

hfss.save_project()
hfss.release_desktop()
