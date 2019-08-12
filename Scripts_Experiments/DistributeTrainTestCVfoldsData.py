#
# created by
# Antonio Garcia-Uceda Juarez
# PhD student
# Medical Informatics
#
# created on 09/02/2018
# Last update: 09/02/2018
########################################################################################

from Common.Constants import *
from Common.FunctionsUtil import *
from Common.WorkDirsManager import *
import argparse



def main(args):
    # ---------- SETTINGS ----------
    nameInputImagesDataRelPath = 'Images_WorkData/'
    nameInputLabelsDataRelPath = 'Labels_WorkData/'
    nameInputReferFilesRelPath = 'Images_Proc/'
    nameTrainingAllDataRelPath = 'TrainingAllData/'
    nameTestingAllDataRelPath  = 'TestingAllData/'
    nameTrainDataSubRelPath    = 'Train-CV%0.2i/'
    nameTestDataSubRelPath     = 'Test-CV%0.2i/'
    nameCVfoldsRelPath         = 'CV-folds/'
    nameInputImagesFiles       = 'images*' + getFileExtension(FORMATTRAINDATA)
    nameInputLabelsFiles       = 'labels*' + getFileExtension(FORMATTRAINDATA)
    nameInputReferFiles        = '*.nii.gz'
    nameCVfoldsFiles           = 'test[0-9].txt'
    # ---------- SETTINGS ----------


    workDirsManager     = WorkDirsManager(args.basedir)
    InputImagesDataPath = workDirsManager.getNameExistBaseDataPath(nameInputImagesDataRelPath)
    InputLabelsDataPath = workDirsManager.getNameExistBaseDataPath(nameInputLabelsDataRelPath)
    InputReferFilesPath = workDirsManager.getNameExistBaseDataPath(nameInputReferFilesRelPath)
    CVfoldsPath         = workDirsManager.getNameExistPath        (nameCVfoldsRelPath)
    TrainingAllDataPath = workDirsManager.getNameNewPath          (nameTrainingAllDataRelPath)
    TestingAllDataPath  = workDirsManager.getNameNewPath          (nameTestingAllDataRelPath)

    listInputImagesFiles = findFilesDirAndCheck(InputImagesDataPath, nameInputImagesFiles)
    listInputLabelsFiles = findFilesDirAndCheck(InputLabelsDataPath, nameInputLabelsFiles)
    listInputReferFiles  = findFilesDirAndCheck(InputReferFilesPath, nameInputReferFiles)
    listCVfoldsFiles     = findFilesDirAndCheck(CVfoldsPath, nameCVfoldsFiles)
    # create list with only basenames
    listInputReferFiles  = [basename(elem) for elem in listInputReferFiles]

    if (len(listInputImagesFiles) != len(listInputLabelsFiles)):
        message = 'num images in dir \'%s\', not equal to num labels in dir \'%i\'...' %(len(listInputImagesFiles),
                                                                                         len(listInputLabelsFiles))
        CatchErrorException(message)

    num_imagedata_files = len(listInputImagesFiles)


    for i, in_cvfold_file in enumerate(listCVfoldsFiles):
        print("\nInput: \'%s\'..." % (basename(in_cvfold_file)))
        print("Create Training and Testing sets for the CV fold %i..." %(i))

        TrainingDataPath = joinpathnames(TrainingAllDataPath, nameTrainDataSubRelPath%(i+1))
        TestingDataPath  = joinpathnames(TestingAllDataPath,  nameTestDataSubRelPath %(i+1))

        makedir(TrainingDataPath)
        makedir(TestingDataPath)


        fout = open(in_cvfold_file, 'r')
        in_cvfold_testfile_names = [elem.replace('\n','.nii.gz') for elem in fout.readlines()]

        indexes_testing_files = []
        for icvfold_testfile in in_cvfold_testfile_names:
            index_tesfile = listInputReferFiles.index(icvfold_testfile)
            indexes_testing_files.append(index_tesfile)
        #endfor
        indexes_training_files = [ind for ind in range(num_imagedata_files) if ind not in indexes_testing_files]


        # TRAINING DATA
        print("Files assigned to Training Data:")
        for index in indexes_training_files:
            print("%s" % (basename(listInputImagesFiles[index])))
            makelink(listInputImagesFiles[index], joinpathnames(TrainingDataPath, basename(listInputImagesFiles[index])))
            makelink(listInputLabelsFiles[index], joinpathnames(TrainingDataPath, basename(listInputLabelsFiles[index])))
        # endfor

        # TESTING DATA
        print("Files assigned to Testing Data:")
        for index in indexes_testing_files:
            print("%s" % (basename(listInputImagesFiles[index])))
            makelink(listInputImagesFiles[index], joinpathnames(TestingDataPath, basename(listInputImagesFiles[index])))
            makelink(listInputLabelsFiles[index], joinpathnames(TestingDataPath, basename(listInputLabelsFiles[index])))
        # endfor
    #endfor



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir', type=str, default=BASEDIR)
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).iteritems():
        print("\'%s\' = %s" %(key, value))

    main(args)