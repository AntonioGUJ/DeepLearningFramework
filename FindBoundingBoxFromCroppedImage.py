#
# created by
# Antonio Garcia-Uceda Juarez
# PhD student
# Medical Informatics
#
# created on 09/02/2018
# Last update: 09/02/2018
########################################################################################

from CommonUtil.Constants import *
from CommonUtil.ErrorMessages import *
from CommonUtil.FileReaders import *
from CommonUtil.FunctionsUtil import *
from CommonUtil.WorkDirsManager import *
from Preprocessing.BoundingBoxMasks import *
from Preprocessing.OperationsImages import *
import argparse



def main(args):

    # ---------- SETTINGS ----------
    nameRawImagesFullRelPath    = 'RawImages_Full'
    nameRawImagesCroppedRelPath = 'RawImages_Cropped'

    # Get the file list:
    nameImagesFiles = '*.dcm'

    #test_range_boundbox = ((16, 352), (109, 433), (45, 460))
    _eps = 1.0e-06
    _alpha_relax = 0.6
    _z_min_top = 15
    _z_numtest = 10

    nameTempOutResFile = 'temp_found_boundBoxes_vol16.csv'
    nameOutResultFileNPY = 'found_boundBoxes_vol16.npy'
    nameOutResultFileCSV = 'found_boundBoxes_vol16.csv'
    # ---------- SETTINGS ----------


    workDirsManager     = WorkDirsManager(args.basedir)
    BaseDataPath        = workDirsManager.getNameBaseDataPath()
    RawImagesFullPath   = workDirsManager.getNameExistPath(BaseDataPath, nameRawImagesFullRelPath)
    RawImagesCroppedPath= workDirsManager.getNameExistPath(BaseDataPath, nameRawImagesCroppedRelPath)

    listImagesFullFiles    = findFilesDir(RawImagesFullPath,    nameImagesFiles)[15:16]
    listImagesCroppedFiles = findFilesDir(RawImagesCroppedPath, nameImagesFiles)[15:16]

    print listImagesFullFiles

    nbImagesFullFiles   = len(listImagesFullFiles)
    nbImagesCroppedFiles= len(listImagesCroppedFiles)

    # Run checkers
    if (nbImagesFullFiles == 0):
        message = "num CTs Images found in dir \'%s\'" %(RawImagesFullPath)
        CatchErrorException(message)
    if (nbImagesFullFiles != nbImagesCroppedFiles):
        message = "num CTs Images %i not equal to num CTs cropped Images %i" %(nbImagesFullFiles, nbImagesCroppedFiles)
        CatchErrorException(message)

    dict_found_boundingBoxes = {}

    nameTempOutResFile = joinpathnames(BaseDataPath, nameTempOutResFile)

    fout = open(nameTempOutResFile, 'w')


    for images_full_file, images_cropped_file in zip(listImagesFullFiles, listImagesCroppedFiles):

        print('\'%s\'...' % (images_full_file))
        print('\'%s\'...' % (images_cropped_file))

        images_full_array    = FileReader.getImageArray(images_full_file)
        images_cropped_array = FileReader.getImageArray(images_cropped_file)

        images_cropped_array = FlippingImages.compute(images_cropped_array, axis=0)

        if (images_cropped_array.shape > images_full_array.shape):
            message = 'size cropped image: %s, larger than the size full image: %s...' %(images_cropped_array.shape,
                                                                                         images_full_array.shape)
            CatchErrorException(message)


        images_full_shape    = np.array(images_full_array.shape)
        images_cropped_shape = np.array(images_cropped_array.shape)

        test_range_boundbox = compute_test_range_boundbox(images_full_shape,
                                                          images_cropped_shape,
                                                          alpha_relax=_alpha_relax,
                                                          z_min_top=_z_min_top,
                                                          z_numtest=_z_numtest)

        test_range_boundbox_shape = BoundingBoxMasks.compute_size_bounding_box(test_range_boundbox)

        if (test_range_boundbox_shape < images_cropped_array.shape):
            message = 'size test range of bounding boxes: %s, smaller than the size of cropped image: %s...' %(test_range_boundbox_shape,
                                                                                                               images_cropped_array.shape)
            CatchErrorException(message)
        else:
            test_range_boundbox_shape = np.array(test_range_boundbox_shape)

        (num_test_boundbox, num_tests_total) = compute_num_tests_boundbox(test_range_boundbox_shape,
                                                                          images_cropped_shape)

        print("size full image: %s..." %(images_full_shape))
        print("size cropped image: %s..." %(images_cropped_shape))
        print("test range bounding boxes: %s..." %(test_range_boundbox))
        print("size test range bounding boxes: %s..." %(test_range_boundbox_shape))
        print("num test bounding boxes: %s..." %(num_test_boundbox))
        print("num tests total: %s..." %(num_tests_total))


        flag_found_boundbox = False
        min_sum_test_res = 1.0e+10
        found_boundbox = None
        counter = 1

        for k in range(num_test_boundbox[0]):
            (z0, zm) = get_limits_test_boundbox(test_range_boundbox[0],
                                                images_cropped_shape[0],
                                                k,
                                                option='start_end')
            for j in range(num_test_boundbox[1]):
                (y0, ym) = get_limits_test_boundbox(test_range_boundbox[1],
                                                    images_cropped_shape[1],
                                                    j,
                                                    option='start_begin')
                for i in range(num_test_boundbox[2]):
                    (x0, xm) = get_limits_test_boundbox(test_range_boundbox[2],
                                                        images_cropped_shape[2],
                                                        i,
                                                        option='start_begin')
                    #print("test \"%s\" of \"%s\"..." %(counter, num_tests_total))
                    #counter = counter + 1

                    test_bounding_box = ((z0,zm),(y0,ym),(x0,xm))

                    #print("test bounding box: %s..." %(test_bounding_box))

                    test_res_matrix = images_full_array[test_bounding_box[0][0]:test_bounding_box[0][1],
                                                        test_bounding_box[1][0]:test_bounding_box[1][1],
                                                        test_bounding_box[2][0]:test_bounding_box[2][1]] - images_cropped_array

                    sum_test_res = np.abs(np.sum(test_res_matrix))

                    if (sum_test_res <_eps):
                        flag_found_boundbox = True
                        min_sum_test_res = 0.0
                        found_boundbox = test_bounding_box
                        break
                    elif (sum_test_res < min_sum_test_res):
                        min_sum_test_res = sum_test_res
                        found_boundbox = test_bounding_box

                if (flag_found_boundbox):
                    break
            if (flag_found_boundbox):
                break
                #endfor
            #endfor
        #endfor

        if (flag_found_boundbox):
            print("SUCESS: found perfect bounding-box: %s, with null error: %s..." % (str(found_boundbox),
                                                                                      sum_test_res))
            rootimagescroppedname = filenamenoextension(images_cropped_file)
            dict_found_boundingBoxes[rootimagescroppedname] = found_boundbox
            message = "%s,\"%s\"\n" %(rootimagescroppedname, str(found_boundbox))
            fout.write(message)
        else:
            print("ERROR: not found perfect bounding-box. Closest found is: %s, with error: %s..." % (str(found_boundbox),
                                                                                                      min_sum_test_res))
            rootimagescroppedname = filenamenoextension(images_cropped_file)
            dict_found_boundingBoxes[rootimagescroppedname] = found_boundbox
            message = "%s,\"%s\" ...NOT PERFECT...\n" % (rootimagescroppedname, str(found_boundbox))
            fout.write(message)
    #endfor


    # Save dictionary in csv file
    nameoutfile = joinpathnames(BaseDataPath, nameOutResultFileNPY)
    saveDictionary(nameoutfile, dict_found_boundingBoxes)
    nameoutfile = joinpathnames(BaseDataPath, nameOutResultFileCSV)
    saveDictionary_csv(nameoutfile, dict_found_boundingBoxes)

    fout.close()


def compute_test_range_boundbox(images_full_shape, images_cropped_shape, alpha_relax=0.5, z_min_top=0, z_numtest=1):

    test_range_boundbox = np.zeros((3, 2), dtype=np.int)

    y_0 = (1.0 - alpha_relax) * (int(np.float(images_full_shape[1]) / 2) - int(np.ceil(np.float(images_cropped_shape[1]) / 2)))
    x_0 = (1.0 - alpha_relax) * (int(np.float(images_full_shape[2]) / 2) - int(np.ceil(np.float(images_cropped_shape[2]) / 2)))
    z_m = images_full_shape[0] - z_min_top
    z_0 = z_m - images_cropped_shape[0] - (z_numtest-1)

    test_range_boundbox[0, 0] = z_0
    test_range_boundbox[0, 1] = z_m
    test_range_boundbox[1, 0] = y_0
    test_range_boundbox[1, 1] = images_full_shape[1] - y_0
    test_range_boundbox[2, 0] = x_0
    test_range_boundbox[2, 1] = images_full_shape[2] - x_0

    return test_range_boundbox


def compute_num_tests_boundbox(test_range_boundbox_shape, images_cropped_shape):
    num_test_boundbox = test_range_boundbox_shape - images_cropped_shape + [1, 1, 1]
    num_tests_total = num_test_boundbox[0] * num_test_boundbox[1] * num_test_boundbox[2]

    return (num_test_boundbox, num_tests_total)


def get_limits_test_boundbox(test_range_boundbox, size_cropped_image, index, option='start_begin'):
    if (option=='start_begin'):
        x0 = test_range_boundbox[0] + index
        xm = x0 + size_cropped_image
    elif (option=='start_end'):
        xm = test_range_boundbox[1] - index
        x0 = xm - size_cropped_image
    else:
        return None
    return (x0, xm)



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir', default=BASEDIR)
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).iteritems():
        print("\'%s\' = %s" %(key, value))

    main(args)