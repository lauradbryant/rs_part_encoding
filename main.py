import csv
import random
import math
import numpy as np
from reedsolo import RSCodec
from array import array
import matplotlib.pyplot as plt

# The exponent for our galois field: code lengths of up to 2^{C_EXP} are supported
# We have 500 rows x 3 columns x 5 digits = 7500
C_EXP = 14

# This is copied from reedsolo.py so that we can work with the same data type
# Redefine _bytearray() in case we need to support integers or messages of length > 256
global _bytearray
if C_EXP <= 8:
    _bytearray = bytearray
else:
    def _bytearray(obj=0, encoding="latin-1"):
        if isinstance(obj, str):  # obj is a string, convert to list of ints
            obj = obj.encode(encoding)
            if isinstance(obj, str):
                obj = [ord(chr) for chr in obj]
            elif isinstance(obj, bytes):
                obj = [int(chr) for chr in obj]
            else:
                raise (ValueError, "Type of object not recognized!")
        elif isinstance(obj, int):
            obj = [0] * obj
        return array("i", obj)


class Instance:
    """
    An instance of a part is represented by a single codeword.
    This class calculates and keeps track of the codeword associated with a particular instance of a part.
    """

    def __init__(self, num_checks, input_file, check_digits=_bytearray()):
        """
                Constructor for the Instance class which represents an instance of a part.
                Sets the variables of data, encoded, and check digits to the appropriate values.
                :param input_file      The name of the csv file with the piezoelectric signature for the part instance
                :param check_digits    A bytearray with the check digits to be concatenated with the data.
                                        This should be left as the default for the master instance and in all other
                                        cases should be the check digits belonging to the master.
                :return: nothing
            """
        self.num_checks = num_checks
        self.check_digits = check_digits
        data = _bytearray()
        with open(input_file, 'rb') as f:
            file_reader = np.load(f, allow_pickle=True)
            for row in file_reader:
                for val in row:
                    for i in range(0, 5):
                        # Assign the first 5 digits of each value to the next 5 places in our bytearray
                        if val == 0:
                            data.append(0)
                        else:
                            if val < 0:
                                val = val * -1
                            if 0 < val < 1:
                                val = val * 10
                            digits = int(math.log10(val))
                            first_digit = int(val / pow(10, digits))
                            data.append(first_digit)
                            val = val - (first_digit * pow(10, digits))

        self.data = data
        encoded = data
        encoded.extend(self.check_digits)
        self.encoded = encoded

    def calculate_check_digits(self):
        """
        Method to calculate the check digits for the master instance.
        :return: self.check_digits The bytearray of check digits now associated with this instance.
        """
        rsc = RSCodec(self.num_checks, c_exp=C_EXP)
        encoded = rsc.encode(self.data)
        self.encoded = encoded
        check_digits = self.encoded[-self.num_checks:]
        self.check_digits = check_digits
        return self.check_digits


class Part:
    """
    A part is represented by a Reed-Solomon code.
    This class initializes instances of candidates and determines if their associated codeword is in the code or not.
    """

    def __init__(self, num_checks, master_file_name):
        """
        Constructor for the Part class which initializes master as an Instance and calculates the check digits.
        :param master_file_name: The name of the numpy file that contains the data that will be used as the master.
        """
        self.num_checks = num_checks
        self.master = Instance(self.num_checks, master_file_name)
        self.master.calculate_check_digits()

    def check_candidate(self, candidate_file_name):
        """
        Determines if the candidate for this Part is an Instance or not.
        :param candidate_file_name: The name of the numpy file that might be an instance of this part.
        :return: A boolean true if the candidate is an instance of the part and false otherwise.
        """
        # Increase the galois field from default to enable longer codewords
        rsc = RSCodec(self.num_checks, c_exp=C_EXP)
        candidate = Instance(self.num_checks, candidate_file_name, self.master.check_digits)
        maxerrors, maxerasures = rsc.maxerrata(verbose=True)
        print(maxerrors, maxerasures)
        try:
            rsc.decode(candidate.data)
            is_instance = True
        except:
            is_instance = False
        return is_instance


def num_differences(master_file_name, candidate_file_name):
    """
    Counts the number of differences between the candidate and the master.
    Useful for determining appropriate values for CHECK because CHECK can be no smaller than double the number
    of differences for a true instance and no larger than double the number of differences for a false instance.
    :param candidate_file_name: The name of the numpy file that we want to check the differences between.
    :return: The integer number of differences between the two data sets.
    """
    master_data = _bytearray()
    candidate_data = _bytearray()
    with open(master_file_name, 'rb') as f:
        master = np.load(f, allow_pickle=True)
        for row in master:
            for val in row:
                for i in range(0, 5):
                    # Assign the first 5 digits of each value to the next 5 places in our bytearray
                    if val == 0:
                        master_data.append(0)
                    else:
                        if val < 0:
                            val = val * -1
                        if 0 < val < 1:
                            val = val * 10
                        digits = int(math.log10(val))
                        first_digit = int(val / pow(10, digits))
                        master_data.append(first_digit)
                        val = val - (first_digit * pow(10, digits))
    with open(candidate_file_name, 'rb') as g:
        candidate = np.load(g, allow_pickle=True)
        for row in candidate:
            for val in row:
                for i in range(0, 5):
                    # Assign the first 5 digits of each value to the next 5 places in our bytearray
                    if val == 0:
                        candidate_data.append(0)
                    else:
                        if val < 0:
                            val = val * -1
                        if 0 < val < 1:
                            val = val * 10
                        digits = int(math.log10(val))
                        first_digit = int(val / pow(10, digits))
                        candidate_data.append(first_digit)
                        val = val - (first_digit * pow(10, digits))
    num_diff = 0
    for i in range(len(master_data)):
        if master_data[i] != candidate_data[i]:
            num_diff += 1
    return num_diff


def make_graph(tests, part_names):
    """
        Graphs each part with its average number of check digits and the range that the check digits can be set to.
        A higher range of acceptable check digits makes a part more suitable for being decoded with a Reed-Solomon code.
        A smaller average number of check digits is better, and any value over 7500 means that the part cannot be
        used as a Reed_Solomon code.
        :param tests: The array of testing sets.
        :param part_names: The array of part names.
        """

    # Cycle through each part and calculate the maximum and minimum number of check digits
    # with open('check_digit_stats.csv', 'w', newline='') as file:
    #     writer = csv.writer(file)
    #     row_titles = ["part", "minimum", "maximum", "difference", "mean"]
    #     writer.writerow(row_titles)
    #     print("Calculating graph values...")
    #     for part in tests:
    #         cum_max = 0
    #         for master in part:
    #             minimum = 0
    #             maximum = 7500
    #             for instance in part:
    #                 num_diff = num_differences(master, instance)
    #                 if 2 * num_diff > minimum:
    #                     minimum = 2 * num_diff
    #             for diff_part in tests:
    #                 if diff_part != part:
    #                     for instance in diff_part:
    #                         num_diff = num_differences(master, instance)
    #                         if 2 * num_diff < maximum:
    #                             maximum = 2 * num_diff
    #             cum_max += maximum
    #         avg_max = cum_max / len(part)
    #         row = [part_names[tests.index(part)], minimum, avg_max, avg_max - minimum, (avg_max + minimum) / 2]
    #         writer.writerow(row)

    # Graph
    print("Creating graph...")
    part = []
    differences = []
    avg_values = []

    with open('check_digit_stats.csv', 'r') as csvfile:
        lines = csv.reader(csvfile, delimiter=',')
        next(lines)
        for row in lines:
            part.append(row[0])
            differences.append(int(float(row[3])))
            avg_values.append(int(float(row[4])))

    # Plot the difference between maximum and minimum checks
    # print("Plotting average distance...")
    # plt.plot(part, differences, "o")
    # plt.xticks(rotation=50, minor=False)
    # plt.xlabel('Part')
    # plt.ylabel('Acceptable Range for Check Digits')
    # plt.title('Parts and the Acceptable Size of Range for Check Digits ', fontsize=20)

    # Plot the average check number
    print("Plotting average check value...")
    plt.plot(part, avg_values, "o")
    plt.xticks(rotation=50, minor=False)
    plt.xlabel('Part')
    plt.ylabel('Average Check Value')
    plt.title('Parts and their Average Check Values', fontsize=20)

    plt.show()


def main():
    # Initialize the testing data
    container_1 = ['container/con_Ax1_1.npy', 'container/con_Ax1_2.npy', 'container/con_Ax1_3.npy',
                   'container/con_Ax1_4.npy', 'container/con_Ax1_5.npy']
    container_2 = ['container/con_Bx2_1.npy', 'container/con_Bx2_2.npy', 'container/con_Bx2_3.npy',
                   'container/con_Bx2_4.npy', 'container/con_Bx2_5.npy', 'container/con_Bx2_6.npy',
                   'container/con_Bx2_7.npy', 'container/con_Bx2_8.npy', 'container/con_Bx2_9.npy']
    container_3 = ['container/con_Cx3_1.npy', 'container/con_Cx3_2.npy', 'container/con_Cx3_3.npy',
                   'container/con_Cx3_4.npy', 'container/con_Cx3_5.npy']
    lid_1 = ['lid/lid_Ax4_1.npy', 'lid/lid_Ax4_2.npy', 'lid/lid_Ax4_3.npy', 'lid/lid_Ax4_4.npy', 'lid/lid_Ax4_5.npy']
    lid_2 = ['lid/lid_Bx5_1.npy', 'lid/lid_Bx5_2.npy', 'lid/lid_Bx5_3.npy', 'lid/lid_Bx5_4.npy', 'lid/lid_Bx5_5.npy',
             'lid/lid_Bx5_6.npy', 'lid/lid_Bx5_7.npy', 'lid/lid_Bx5_8.npy', 'lid/lid_Bx5_9.npy']
    lid_3 = ['lid/lid_Cx6_1.npy', 'lid/lid_Cx6_2.npy', 'lid/lid_Cx6_3.npy', 'lid/lid_Cx6_4.npy', 'lid/lid_Cx6_5.npy']
    tube = ['tube/tube_Dx7_1.npy', 'tube/tube_Dx7_2.npy', 'tube/tube_Dx7_3.npy', 'tube/tube_Dx7_4.npy',
            'tube/tube_Dx7_5.npy']
    damaged_tube = ['tube/tube_Dx7_1_damage.npy', 'tube/tube_Dx7_2_damage.npy', 'tube/tube_Dx7_3_damage.npy']
    sensor_1 = ['sensors/sen_x1_1.npy', 'sensors/sen_x1_2.npy', 'sensors/sen_x1_3.npy', 'sensors/sen_x1_4.npy',
                'sensors/sen_x1_5.npy']
    sensor_2 = ['sensors/sen_x2_1.npy', 'sensors/sen_x2_2.npy', 'sensors/sen_x2_3.npy', 'sensors/sen_x2_4.npy',
                'sensors/sen_x2_5.npy']
    sensor_3 = ['sensors/sen_x3_1.npy', 'sensors/sen_x3_2.npy', 'sensors/sen_x3_3.npy', 'sensors/sen_x3_4.npy',
                'sensors/sen_x3_5.npy']
    sensor_4 = ['sensors/sen_x4_1.npy', 'sensors/sen_x4_2.npy', 'sensors/sen_x4_3.npy', 'sensors/sen_x4_4.npy',
                'sensors/sen_x4_5.npy']
    sensor_5 = ['sensors/sen_x5_1.npy', 'sensors/sen_x5_2.npy', 'sensors/sen_x5_3.npy', 'sensors/sen_x5_4.npy',
                'sensors/sen_x5_5.npy']
    tests = [container_1, container_2, container_3, lid_1, lid_2, lid_3, tube, damaged_tube, sensor_1, sensor_2,
             sensor_3, sensor_4, sensor_5]
    part_names = ['container_1', 'container_2', 'container_3', 'lid_1', 'lid_2', 'lid_3', 'tube', 'damaged_tube',
                  'sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5']

    # Graph the average check values, comment this line out to only run tests
    make_graph(tests, part_names)

    # Count passed and failed tests
    print("Testing...")
    passed_tests = 0
    failed_tests = 0

    # Run Test Cases
    for part in tests:
        # Find the minimum and maximum values for CHECK
        master_name = part[random.randint(0, len(part) - 1)]
        print("\nTesting with " + str(master_name) + " as master.")

        min_check = 0
        max_check = 7500
        for instance in part:
            num_diff = num_differences(master_name, instance)
            if 2 * num_diff > min_check:
                min_check = 2 * num_diff
        for diff_part in tests:
            if diff_part != part:
                for instance in diff_part:
                    num_diff = num_differences(master_name, instance)
                    if 2 * num_diff < max_check:
                        max_check = 2 * num_diff
        # Half of this many digits can be different across instances of the same part
        check = int((min_check + max_check) / 2)
        print("Check should be between " + str(min_check) + " and " + str(max_check) +
              ". It is currently set to " + str(check) + ".")

        if min_check >= max_check:
            print("Hamming distance is too large to be decoded with a Reed-Solomon Code.\n")
        else:
            master = Part(check, master_name)
            # Check that all instances of this part decode correctly
            for instance in part:
                if master.check_candidate(instance):
                    print("Test case " + instance + " passed.")
                    passed_tests += 1
                else:
                    print("TEST CASE " + instance + " FAILED.")
                    failed_tests += 1

            # Check that a random instance of each of the other parts does not decode to the master
            for diff_part in tests:
                if diff_part != part:
                    instance = diff_part[random.randint(0, len(diff_part) - 1)]
                    if not master.check_candidate(instance):
                        print("Test case " + instance + " passed.")
                        passed_tests += 1
                    else:
                        print("TEST CASE " + instance + " FAILED.")
                        failed_tests += 1

            print("Failed " + str(failed_tests) + " tests. Passed " + str(passed_tests) + ".")


if __name__ == '__main__':
    main()
