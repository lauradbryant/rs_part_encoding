> **Honors Enrichment Project for CS 4277 - Cyber Security**

# Using Reed-Solomon Codes to Compare Piezoelectric Signatures for Manufacturing Security

## Background

When assembling machines, it is important for manufacturers to know that every part is authentic and high quality. 
Since the creation of many parts is outsourced, these objects are vulnerable to being replaced by counterfeit 
products of lesser quality or being tampered with before they are integrated. If security measures are not taken to 
ensure that the components of planes and other devices are legitimate, people and systems are put at risk. 
The security measures currently in practice include barcodes and serial numbers which can be cheaply copied onto a 
counterfeit part and still allow for the product to be altered. A physically unclonable function that can identify an 
authentic part would be a much more secure method to ensure the integrity of a product throughout its transport and 
usage. Piezoelectric signatures appear to be a promising solution, as each instance of a part has a unique impedance 
identity. This is due to the fact that there is slight variation in the process of manufacturing a part, the way that 
the piezoelectric sensor is attached, and the sensor itself. If a piezoelectric sensor is attached to an item, the 
impedance identity can be measured by the recipient and compared to the signature that was measured by the 
manufacturer, confirming that the product has not been altered in any way in transit. It would be likely impossible, 
and certainly costly, for an attacker to guess an item’s impedance identity, which makes this method secure. 
One of the remaining tasks before implementing the use of piezoelectric signatures in manufacturing security is to 
establish a method for encoding the impedance identity in an efficient and meaningful way. 

## Hypothesis

This project was based on the hypothesis that Reed-Solomon codes might be useful for developing a scheme for encoding 
and comparing piezoelectric signatures, and this work indicates that this hypothesis shows great promise. 

## Reed-Solomon Codes
Reed-Solomon codes were chosen because of their ability to correct a large number of errors as well as their ease of 
encryption and decryption. They work by constructing a unique function that passes through each of the (x, y) data 
points where x is the position of the data in the file and y is the data and then calculating check digits based on 
what y value would be required if the function were to continue on to successive x values. This allows for a certain 
number of points to be omitted and the same function still be computed. Decoding is then a process of determining if 
there are minimal enough values in the data that can be omitted or changed in order for the same function to pass 
through every remaining data point. The primary disadvantage that Reed-Solomon codes present is that they only detect 
when two digits are different regardless of how different they are. For example, they make no distinction between the 
comparison between the digits 5 and 6 and the comparison between 3 and 9. In our case, we want to see if two data sets 
are close enough to be considered the same, so lacking the feature of knowing which numbers are closer and farther is 
not ideal, but we found that the signatures of two different parts had enough differences that this feature was not 
necessary to categorize parts as the same or different.

## About This Implementation

For this project, each instance of a part is represented by a codeword, or series of points, and each part type is 
represented by a code, or function. One representative instance is chosen to be the “master” example for that part 
type and then encoded as a Reed-Solomon code. In other words, we use one instance of a part to calculate the unique 
function and check digits that are associated with the data set. Then these check digits are concatenated with other 
sets of data collected from different piezoelectric sensors to check if the combined sequence decodes to the same 
value as the master or not. When the right number of check digits are added on, instances that are the same part type 
as the master decode successfully and instances that are of a different part type will not decode.

## Challenges
The main challenge that was faced while working on this project was realizing that the data type that was required to 
be passed to the reedsolo python library functions was, in our case, much more limited than the documentation for the 
library claimed. While the library advertised being able to work with both strings and bytearrays, we found neither of 
these general categories to work without errors. The problem with passing in a string in our case is that the library 
converts the string to a bytearray and uses the ASCII values for integers in this conversion. While this could be 
accounted for if we were only interfacing with reedsolo once, we interface with it multiple times. The library 
returns check numbers that are multiple digits long and the delineations between these numbers must be preserved when 
being passed back and forth between our code and the library which is impossible using the string data type and the 
method for string to bytearray conversion being used. Although it seems like we should be able to work in bytearrays 
when passing data back and forth, using bytearrays ended up with errors being thrown within the reedsolo library. 
Upon further inspection of the code, we discovered that the library had overwritten the data type to account for the out of range errors that 
were being thrown but did not convert all incoming data to the appropriate new format. The solution to this problem of 
the data type was solved by copying the code used in reedsolo to overwrite the bytearray data type to the top of 
our file so that we store our data in their special format throughout the process.

## Using rs_part_encoding

This code can be used to check if the data from piezoelectric signatures stored in csv files is of the same type as 
the master instance or not. To make the file sen_x1_1.csv the master file for instances of the sen_x1 part initialize 
sen_x1 as`sen_x1=Part('sen_x1_1.csv)` and to check if sen_x1_2.csv is an instance of sen_x1, call 
`sen_x1.check_candidate('sen_x2_1.csv')`.

If you do not already have reedsolo installed, install it by running `pip install reedsolo` within the project directory. The documentation for the reedsolo library is here https://pypi.org/project/reedsolo/#basic-usage-with-high-level-rscodec-class. 



