import csv
from reedsolo import RSCodec

# Half of this many digits can be different across instances of the same part
CHECK = 3000

# The exponent for our galois field: code lengths of up to 2^{C_EXP} are supported
C_EXP = 14

# Increase the galois field from default to enable longer codewords
rsc = RSCodec(CHECK, c_exp=C_EXP)

# This is copied from reedsolo.py so that we can work with the same data type
# Redefine _bytearray() in case we need to support integers or messages of length > 256
global _bytearray
if C_EXP <= 8:
    _bytearray = bytearray
else:
    from array import array


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

    def __init__(self, input_file, check_digits=_bytearray()):
        """
                Constructor for the Instance class which represents an instance of a part.
                Sets the variables of data, encoded, and check digits to the appropriate values.
                :param input_file      The name of the csv file with the piezoelectric signature for the part instance
                :param check_digits    A bytearray with the check digits to be concatenated with the data.
                                        This should be left as the default for the master instance and in all other
                                        cases should be the check digits belonging to the master.
                :return: nothing
            """
        self.check_digits = check_digits
        data = _bytearray()
        with open(input_file, newline='') as csvfile:
            document_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in document_reader:
                first_value = row[1]
                second_value = row[2]
                # Assign the first 5 digits in the second column of the data to the next 5 places in our bytearray
                i = 0
                while i < 6:
                    if first_value[i].isdigit():
                        data.append(int(first_value[i]))
                    i = i + 1
                # Assign the first 5 digits in the third column of the data to the next 5 places in our bytearray
                j = 0
                while j < 6:
                    if second_value[j].isdigit():
                        data.append(int(second_value[j]))
                    j = j + 1
        self.data = data
        encoded = data
        encoded.extend(self.check_digits)
        self.encoded = encoded

    def calculate_check_digits(self):
        """
        Method to calculate the check digits for the master instance.
        :return: self.check_digits The bytearray of check digits now associated with this instance.
        """
        encoded = rsc.encode(self.data)
        self.encoded = encoded
        check_digits = self.encoded[-CHECK:]
        self.check_digits = check_digits
        return self.check_digits


class Part:
    """
    A part is represented by a Reed-Solomon code.
    This class initializes instances of candidates and determines if their associated codeword is in the code or not.
    """

    def __init__(self, master_csv_file_name):
        """
        Constructor for the Part class which initializes master as an Instance and calculates the check digits.
        :param master_csv_file_name: The name of the csv file that contains the data that will be used as the master.
        """
        self.master = Instance(master_csv_file_name)
        self.master.calculate_check_digits()

    def check_candidate(self, candidate_csv_file_name):
        """
        Determines if the candidate for this Part is an Instance or not.
        :param candidate_csv_file_name: The name of the csv file that might be an instance of this part.
        :return: A boolean true if the candidate is an instance of the part and false otherwise.
        """
        candidate = Instance(candidate_csv_file_name, self.master.check_digits)
        try:
            rsc.decode(candidate.data)
            is_instance = True
        except:
            is_instance = False
        return is_instance

    def num_differences(self, candidate_csv_file_name):
        """
        Counts the number of differences between the candidate and the master.
        Useful for determining appropriate values for CHECK because CHECK can be no smaller than double the number
        of differences for a true instance and no larger than double the number of differences for a false instance.
        :param candidate_csv_file_name: The name of the csv file that we want to check the differences between.
        :return: The integer number of differences between the two data sets.
        """
        candidate = Instance(candidate_csv_file_name, self.master.check_digits)
        num_diff = 0
        for i in range(len(self.master.data)):
            if self.master.data[i] != candidate.data[i]:
                num_diff += 1
        return num_diff


def main():
    # Initialize the testing data
    same_type = ['sen_x1_1.csv', 'sen_x1_2.csv', 'sen_x1_3.csv', 'sen_x1_4.csv', 'sen_x1_5.csv']
    diff_type = ['sen_x2_1.csv', 'sen_x2_2.csv', 'sen_x2_3.csv', 'sen_x2_4.csv', 'sen_x2_5.csv']
    master = Part(same_type[0])

    # Find the minimum and maximum values for CHECK
    min_check = 0
    max_check = 5000
    for instance in same_type:
        num_diff = master.num_differences(instance)
        if 2 * num_diff > min_check:
            min_check = 2 * num_diff
    for instance in diff_type:
        num_diff = master.num_differences(instance)
        if 2 * num_diff < max_check:
            max_check = 2 * num_diff
    print("CHECK should be between " + str(min_check) + " and " + str(max_check) +
          ". It is currently set to " + str(CHECK) + ".")

    # Test Cases
    for instance in same_type:
        if master.check_candidate(instance):
            print("Test case " + instance + " passed.")
        else:
            print("Test case " + instance + " failed.")

    for instance in diff_type:
        if not master.check_candidate(instance):
            print("Test case " + instance + " passed.")
        else:
            print("Test case " + instance + " failed.")


if __name__ == '__main__':
    main()
