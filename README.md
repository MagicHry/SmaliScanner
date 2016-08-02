# SmaliScanner
A smali scanner in python, can be used for finding all the ICC (Inter-Component-Communication) widgets in one or many Android applications, and also can be used to inject some information into the xml layout file.

--------
## Usage
The smali scanner is available for scanning one application at a time, or serveral applications at one shot, for users want to scan one application at a time, just type in:
* python RYLauncher.py -s [Your smali file folder location]
And for those users who want to scan several applications at a time, please type in:
* python RYLauncher.py -c [Your file folder`s root folder location]
--------
## Result & Other stuff
The result will be provided in json format, actually this small project made use of the smalisca, but [smalisca](https://github.com/dorneanu/smalisca) is not available for tracing the variable name or conditional case, so I made this scanner. Hope you guys like it, cheers XD.
