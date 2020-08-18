
from common.functionutil import *
from common.workdirmanager import GeneralDirManager
from dataloaders.imagefilereader import ImageFileReader
from preprocessing.preprocessing_manager import *
import argparse


def main(args):

    # ---------- SETTINGS ----------
    nameInputImagesRelPath  = 'Images_WorkData/'
    nameInputLabelsRelPath  = 'Labels_WorkData/'
    nameVisualImagesRelPath = 'VisualWorkData/'

    if (args.createImagesBatches):
        nameOutputVisualImagesFiles = 'visualImages-%0.2i_dim%s-batch%0.2i.nii.gz'
        nameOutputVisualLabelsFiles = 'visualLabels-%0.2i_dim%s-batch%0.2i.nii.gz'
    else:
        nameOutputVisualImagesFiles = 'visualImages-%0.2i_dim%s-batch%s.nii.gz'
        nameOutputVisualLabelsFiles = 'visualLabels-%0.2i_dim%s-batch%s.nii.gz'
    # ---------- SETTINGS ----------


    workDirsManager  = GeneralDirManager(args.datadir)
    InputImagesPath  = workDirsManager.get_pathdir_exist(nameInputImagesRelPath)
    InputLabelsPath  = workDirsManager.get_pathdir_exist(nameInputLabelsRelPath)
    VisualImagesPath = workDirsManager.get_pathdir_new  (nameVisualImagesRelPath)

    listInputImagesFiles = list_files_dir(InputImagesPath)
    listInputLabelsFiles = list_files_dir(InputLabelsPath)

    if (len(listInputImagesFiles) != len(listInputLabelsFiles)):
        message = 'num files in dir 1 \'%s\', not equal to num files in dir 2 \'%i\'...' %(len(listInputImagesFiles),
                                                                                           len(listInputLabelsFiles))
        catch_error_exception(message)



    for i, (in_image_file, in_label_file) in enumerate(zip(listInputImagesFiles, listInputLabelsFiles)):
        print("\nInput: \'%s\'..." % (basename(in_image_file)))
        print("And: \'%s\'..." % (basename(in_label_file)))

        (in_image_array, in_label_array) = ImageFileReader.get_2image_arrays_and_check(in_image_file, in_label_file)
        print("Original dims : \'%s\'..." %(str(in_image_array.shape)))


        if (args.createImagesBatches):
            in_batches_shape = in_image_array.shape[1:]
            print("Input work data stored as batches of size  \'%s\'. Visualize batches..." % (str(in_batches_shape)))

            images_generator = getImagesVolumeTransformator3D(in_image_array,
                                                              args.transformationImages,
                                                              args.elasticDeformationImages)

            (out_visualimage_array, out_visuallabel_array) = images_generator._get_image(in_image_array, in2nd_array=in_label_array)

            for j, (in_batchimage_array, in_batchlabel_array) in enumerate(zip(out_visualimage_array, out_visuallabel_array)):

                out_image_filename = join_path_names(VisualImagesPath, nameOutputVisualImagesFiles % (i + 1, tuple2str(out_visualimage_array.shape[1:]), j + 1))
                out_label_filename = join_path_names(VisualImagesPath, nameOutputVisualLabelsFiles % (i + 1, tuple2str(out_visuallabel_array.shape[1:]), j + 1))

                ImageFileReader.write_image(out_image_filename, in_batchimage_array)
                ImageFileReader.write_image(out_label_filename, in_batchlabel_array)
            # endfor
        else:
            print("Input work data stored as volume. Generate batches of size \'%s\'. Visualize batches..." % (str(IMAGES_DIMS_Z_X_Y)))

            images_generator = getImagesDataGenerator3D(args.slidingWindowImages,
                                                        args.prop_overlap_Z_X_Y,
                                                        args.transformationImages,
                                                        args.elasticDeformationImages)
            batch_data_generator = BatchDataGenerator_2Arrays(IMAGES_DIMS_Z_X_Y,
                                                              in_image_array,
                                                              in_label_array,
                                                              images_generator,
                                                              size_batch=1,
                                                              shuffle=False)
            num_batches_total = len(batch_data_generator)
            print("Generate total \'%s\' batches by sliding-window, with coordinates:..." %(num_batches_total))

            for j in range(num_batches_total):
                coords_sliding_window_box = images_generator.slidingWindow_generator.get_limits_image(j)

                (out_visualimage_array, out_visuallabel_array) = next(batch_data_generator)

                out_visualimage_array = np.squeeze(out_visualimage_array, axis=0)
                out_visuallabel_array = np.squeeze(out_visuallabel_array, axis=0)

                out_image_filename = join_path_names(VisualImagesPath, nameOutputVisualImagesFiles % (i + 1, tuple2str(out_visualimage_array.shape), tuple2str(coords_sliding_window_box)))
                out_label_filename = join_path_names(VisualImagesPath, nameOutputVisualLabelsFiles % (i + 1, tuple2str(out_visuallabel_array.shape), tuple2str(coords_sliding_window_box)))

                ImageFileReader.write_image(out_image_filename, out_visualimage_array)
                ImageFileReader.write_image(out_label_filename, out_visuallabel_array)
            # endfor
    #endfor



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir', type=str, default=DATADIR)
    parser.add_argument('--slidingWindowImages', type=str2bool, default=SLIDINGWINDOWIMAGES)
    parser.add_argument('--slidewin_propOverlap', type=str2tuple_float, default=SLIDEWINDOW_PROPOVERLAP_Z_X_Y)
    parser.add_argument('--transformationImages', type=str2bool, default=TRANSFORMATIONRIGIDIMAGES)
    parser.add_argument('--elasticDeformationImages', type=str2bool, default=TRANSFORMELASTICDEFORMIMAGES)
    parser.add_argument('--createImagesBatches', type=str2bool, default=CREATEIMAGESBATCHES)
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).items():
        print("\'%s\' = %s" %(key, value))

    main(args)
