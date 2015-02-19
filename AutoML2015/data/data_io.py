# Functions performing various input/output operations for the ChaLearn AutoML challenge

# Main contributors: Arthur Pesah and Isabelle Guyon, August-October 2014

# ALL INFORMATION, SOFTWARE, DOCUMENTATION, AND DATA ARE PROVIDED "AS-IS". 
# ISABELLE GUYON, CHALEARN, AND/OR OTHER ORGANIZERS OR CODE AUTHORS DISCLAIM
# ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR ANY PARTICULAR PURPOSE, AND THE
# WARRANTY OF NON-INFRIGEMENT OF ANY THIRD PARTY'S INTELLECTUAL PROPERTY RIGHTS. 
# IN NO EVENT SHALL ISABELLE GUYON AND/OR OTHER ORGANIZERS BE LIABLE FOR ANY SPECIAL, 
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF SOFTWARE, DOCUMENTS, MATERIALS, 
# PUBLICATIONS, OR INFORMATION MADE AVAILABLE FOR THE CHALLENGE. 

from contextlib import closing
from glob import glob
from pip import get_installed_distributions as lib
import os
import shutil
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from scipy.sparse import * # used in data_binary_sparse
import yaml
from shutil import copy2

import AutoML2015.data.data_converter as data_converter


# ================ Small auxiliary functions =================

swrite = sys.stderr.write

if (os.name == "nt"):
       filesep = '\\'
else:
       filesep = '/'
       
def write_list(lst):
    ''' Write a list of items to stderr (for debug purposes)'''
    for item in lst:
        swrite(item + "\n") 
        
def print_dict(verbose, dct):
    ''' Write a dict to stderr (for debug purposes)'''
    if verbose:
        for item in dct:
            print(item + " = " + str(dct[item]))

def mkdir(d):
    ''' Create a new directory'''
    if not os.path.exists(d):
        os.makedirs(d)
        
def mvdir(source, dest):
    ''' Move a directory'''
    if os.path.exists(source):
        os.rename(source, dest)

def rmdir(d):
    ''' Remove an existingdirectory'''
    if os.path.exists(d):
        shutil.rmtree(d)
        
def vprint(mode, t):
    ''' Print to stdout, only if in verbose mode'''
    if(mode):
            print(t) 
        
# ================ Output prediction results and prepare code submission =================
        
def write(filename, predictions):
    ''' Write prediction scores in prescribed format'''
    with open(filename, "w") as output_file:
        for row in predictions:
            if type(row) is not np.ndarray and type(row) is not list:
                row = [row]
            for val in row:
                output_file.write('{:g} '.format(float(val)))
            output_file.write('\n')

def zipdir(archivename, basedir):
    '''Zip directory, from J.F. Sebastian http://stackoverflow.com/'''
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
        for root, dirs, files in os.walk(basedir):
            #NOTE: ignore empty directories
            for fn in files:
                if fn[-4:]!='.zip':
                    absfn = os.path.join(root, fn)
                    zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
                    z.write(absfn, zfn)
                    
# ================ Inventory input data and create data structure =================
   
def inventory_data(input_dir):
    ''' Inventory the datasets in the input directory and return them in alphabetical order'''
    # Assume first that there is a hierarchy dataname/dataname_train.data
    training_names = inventory_data_dir(input_dir)
    ntr=len(training_names)
    if ntr==0:
        # Try to see if there is a flat directory structure
        training_names = inventory_data_nodir(input_dir)
    ntr=len(training_names)
    if ntr==0:
        print('WARNING: Inventory data - No data file found')
        training_names = []
    training_names.sort()
    return training_names
        
def inventory_data_nodir(input_dir):
    ''' Inventory data, assuming flat directory structure'''
    training_names = glob(os.path.join(input_dir, '*_train.data'))
    for i in range(0,len(training_names)):
        name = training_names[i]
        training_names[i] = name[-name[::-1].index(filesep):-name[::-1].index('_')-1]
        check_dataset(input_dir, training_names[i])
    return training_names
    
def inventory_data_dir(input_dir):
    ''' Inventory data, assuming flat directory structure, assuming a directory hierarchy'''
    training_names = glob(input_dir + '/*/*_train.data') # This supports subdirectory structures obtained by concatenating bundles
    for i in range(0,len(training_names)):
        name = training_names[i]
        training_names[i] = name[-name[::-1].index(filesep):-name[::-1].index('_')-1]
        check_dataset(os.path.join(input_dir, training_names[i]), training_names[i])
    return training_names
    
def check_dataset(dirname, name):
    ''' Check the test and valid files are in the directory, as well as the solution'''
    valid_file = os.path.join(dirname, name + '_valid.data')
    if not os.path.isfile(valid_file):
        print('No validation file for ' + name)
        exit(1)  
    test_file = os.path.join(dirname, name + '_test.data')
    if not os.path.isfile(test_file):
        print('No test file for ' + name)
        exit(1)
    # Check the training labels are there
    training_solution = os.path.join(dirname, name + '_train.solution')
    if not os.path.isfile(training_solution):
        print('No training labels for ' + name)
        exit(1)
    return True

def data(filename, feat_type=None, verbose = False):
    ''' The 2nd parameter makes possible a using of the 3 functions of data reading (data, data_sparse, data_binary_sparse) without changing parameters'''
    if verbose: print (np.array(data_converter.file_to_array(filename)))
    return np.array(data_converter.file_to_array(filename), dtype=float)
            
def data_sparse (filename, feat_type):
    ''' This function takes as argument a file representing a sparse matrix
    sparse_matrix[i][j] = "a:b" means matrix[i][a] = b
    It converts it into a numpy array, using sparse_list_to_array function, and returns this array'''
    sparse_list = data_converter.sparse_file_to_sparse_list(filename)
    return data_converter.sparse_list_to_csr_sparse (sparse_list,
                                                     len(feat_type))
    #return data_converter.sparse_list_to_array (sparse_list, nbr_features)

def data_binary_sparse (filename, feat_type):
    ''' This function takes as an argument a file representing a binary sparse matrix
    binary_sparse_matrix[i][j] = a means matrix[i][j] = 1
    It converts it into a numpy array an returns this array. '''
    
    data = data_converter.file_to_array (filename)
    nbr_samples = len(data)
    # the construction is easier w/ dok_sparse
    dok_sparse = dok_matrix ((nbr_samples, len(feat_type)))
    print ("Converting {} to dok sparse matrix".format(filename))
    for row in range (nbr_samples):
        for feature in data[row]:
            dok_sparse[row, int(feature)-1] = 1
    print ("Converting {} to csr sparse matrix".format(filename))
    return dok_sparse.tocsr()
 
# ================ Copy results from input to output ==========================
 
def copy_results(datanames, result_dir, output_dir, verbose):
    ''' This function copies all the [dataname.predict] results from result_dir to output_dir'''
    for basename in datanames:
        try:
            test_files = glob(result_dir + "/" + basename + "*_test*.predict")
            if len(test_files)==0: 
                vprint(verbose, "[-] Missing 'test' result files for " + basename) 
                return 0
            for f in test_files: copy2(f, output_dir)
            valid_files = glob(result_dir + "/" + basename + "*_valid*.predict")
            if len(valid_files)==0: 
                vprint(verbose, "[-] Missing 'valid' result files for " + basename) 
                return 0
            for f in valid_files: copy2(f, output_dir)
            vprint( verbose,  "[+] " + basename.capitalize() + " copied")
        except:
            vprint(verbose, "[-] Missing result files")
            return 0
    return 1

# ================ Display directory structure and code version (for debug purposes) =================
      
def show_dir(run_dir):
    print('\n=== Listing run dir ===')
    write_list(glob(run_dir))
    write_list(glob(run_dir + '/*'))
    write_list(glob(run_dir + '/*/*'))
    write_list(glob(run_dir + '/*/*/*'))
    write_list(glob(run_dir + '/*/*/*/*'))
      
def show_io(input_dir, output_dir):     
    swrite('\n=== DIRECTORIES ===\n\n')
    # Show this directory
    swrite("-- Current directory " + os.getcwd() + ":\n")
    write_list(glob('.'))
    write_list(glob('./*'))
    write_list(glob('./*/*'))
    swrite("\n")
    
    # List input and output directories
    swrite("-- Input directory " + input_dir + ":\n")
    write_list(glob(input_dir))
    write_list(glob(input_dir + '/*'))
    write_list(glob(input_dir + '/*/*'))
    write_list(glob(input_dir + '/*/*/*'))
    swrite("\n")
    swrite("-- Output directory  " + output_dir + ":\n")
    write_list(glob(output_dir))
    write_list(glob(output_dir + '/*'))
    swrite("\n")
        
    # write meta data to sdterr
    swrite('\n=== METADATA ===\n\n')
    swrite("-- Current directory " + os.getcwd() + ":\n")
    try:
        metadata = yaml.load(open('metadata', 'r'))
        for key, value in metadata.items():
            swrite(key + ': ')
            swrite(str(value) + '\n')
    except:
        swrite("none\n")
    swrite("-- Input directory " + input_dir + ":\n")
    try:
        metadata = yaml.load(open(os.path.join(input_dir, 'metadata'), 'r'))
        for key, value in metadata.items():
            swrite(key + ': ')
            swrite(str(value) + '\n')
        swrite("\n")
    except:
        swrite("none\n")
    
def show_version():
    # Python version and library versions
    swrite('\n=== VERSIONS ===\n\n')
    # Python version
    swrite("Python version: " + sys.version + "\n\n")
    # Give information on the version installed
    swrite("Versions of libraries installed:\n")
    map(swrite, sorted(["%s==%s\n" % (i.key, i.version) for i in lib()]))
