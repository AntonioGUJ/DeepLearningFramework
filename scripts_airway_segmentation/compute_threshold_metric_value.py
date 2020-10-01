
from common.constant import *
from common.functionutil import *
from common.workdirmanager import TrainDirManager
from dataloaders.imagefilereader import ImageFileReader
from models.model_manager import get_metric
from imageoperators.imageoperator import MorphoDilateMask, ThresholdImage, ThinningMask, FirstConnectedRegionMask
from imageoperators.maskoperator import MaskOperator
from tqdm import tqdm
import argparse



def main(args):
    # ---------- SETTINGS ----------
    metric_eval_threshold = args.metric_eval_threshold
    metrics_value_sought  = args.metric_value_sought
    num_iter_evaluate_max = args.num_iter_evaluate_max
    rel_error_eval_max    = args.rel_error_eval_max
    init_threshold_value  = args.init_threshold_value

    ref0_threshold_value = 0.0
    if (metric_eval_threshold == 'DiceCoefficient' or
        metric_eval_threshold == 'AirwayCompleteness'):
        ref0_metrics_value = 0.0
    elif (metric_eval_threshold == 'AirwayVolumeLeakage'):
        ref0_metrics_value = 1.0
    else:
        message = 'MetricsEvalThreshold \'%s\' not found...' % (metric_eval_threshold)
        catch_error_exception(message)
    _epsilon = 1.0e-06
    # ---------- SETTINGS ----------


    workdir_manager                 = TrainDirManager(args.basedir)
    input_posteriors_path           = workdir_manager.get_pathdir_exist(args.input_posteriors_dir)
    input_reference_masks_path      = workdir_manager.get_datadir_exist(args.name_input_reference_masks_relpath)
    in_reference_keys_file          = workdir_manager.get_datafile_exist(args.name_input_reference_keys_file)
    list_input_posteriors_files     = list_files_dir(input_posteriors_path)
    list_input_reference_masks_files= list_files_dir(input_reference_masks_path)
    indict_reference_keys           = read_dictionary(in_reference_keys_file)
    pattern_search_input_files      = get_pattern_refer_filename(list(indict_reference_keys.values())[0])

    if (args.is_remove_trachea_calc_metrics):
        input_coarse_airways_path       = workdir_manager.get_datadir_exist(args.name_input_coarse_airways_relpath)
        list_input_coarse_airways_files = list_files_dir(input_coarse_airways_path)
        

    new_metric = get_metric(metric_eval_threshold)
    fun_metric_eval_threshold = new_metric.compute
    is_load_reference_cenlines_files = new_metric._is_use_ytrue_cenlines
    is_load_predicted_cenlines_files = new_metric._is_use_ypred_cenlines

    if (is_load_reference_cenlines_files):
        print("Loading Reference Centrelines...")
        input_reference_centrelines_path       = workdir_manager.get_datadir_exist(args.name_input_reference_centrelines_relpath)
        list_input_reference_centrelines_files = list_files_dir(input_reference_centrelines_path)


    num_valid_predict_files = len(list_input_posteriors_files)
    curr_thres_value  = init_threshold_value
    old_thres_value   = ref0_threshold_value
    old_metrics_value = ref0_metrics_value
    is_comp_converged = False


    print("Load all predictions where to evaluate the metrics, total of \'%s\' files..." %(num_valid_predict_files))
    list_in_posteriors = []
    list_in_references = []
    list_in_coarse_airways = []
    with tqdm(total=num_valid_predict_files) as progressbar:
        for i, in_posterior_file in enumerate(list_input_posteriors_files):

            in_posterior = ImageFileReader.get_image(in_posterior_file)
            list_in_posteriors.append(in_posterior)

            if (is_load_reference_cenlines_files):
                in_reference_cenline_file = find_file_inlist_same_prefix(basename(in_posterior_file), list_input_reference_centrelines_files,
                                                                         pattern_prefix=pattern_search_input_files)
                in_reference_cenline = ImageFileReader.get_image(in_reference_cenline_file)
                in_reference_data = in_reference_cenline
            else:
                in_reference_mask = find_file_inlist_same_prefix(basename(in_posterior_file), list_input_reference_masks_files,
                                                                 pattern_prefix=pattern_search_input_files)
                in_reference_mask = ImageFileReader.get_image(in_reference_mask)
                in_reference_data = in_reference_mask

            if (args.is_remove_trachea_calc_metrics):
                in_coarse_airways_file = find_file_inlist_same_prefix(basename(in_posterior_file), list_input_coarse_airways_files,
                                                                      pattern_prefix=pattern_search_input_files)
                in_coarse_airways = ImageFileReader.get_image(in_coarse_airways_file)

                in_coarse_airways = MorphoDilateMask.compute(in_coarse_airways, num_iters=4)
                list_in_coarse_airways.append(in_coarse_airways)

                in_reference_data = MaskOperator.substract_two_masks(in_reference_data, in_coarse_airways)

            list_in_references.append(in_reference_data)
            progressbar.update(1)
        # endfor
    # *******************************************************************************


    for iter in range(num_iter_evaluate_max):
        print("Iteration \'%s\'. Evaluate predictions with threshold \'%s\'..." %(iter, curr_thres_value))

        # Loop over all prediction files and compute the mean metrics over the dataset
        with tqdm(total=num_valid_predict_files) as progressbar:
            sumrun_res_metrics = 0.0
            for i, (in_posterior, in_reference_data) in enumerate(zip(list_in_posteriors, list_in_references)):

                # Compute the binary masks by thresholding the posteriors
                in_predicted_mask = ThresholdImage.compute(in_posterior, curr_thres_value)

                if (args.is_connected_masks):
                    # Compute the first connected component from the binary masks
                    in_predicted_mask = FirstConnectedRegionMask.compute(in_predicted_mask, connectivity_dim=1)

                if (is_load_predicted_cenlines_files):
                    # Compute centrelines by thinning the binary masks
                    try:
                        #'try' statement to 'catch' issues when predictions are 'weird' (for extreme threshold values)
                        in_predicted_cenline = ThinningMask.compute(in_predicted_mask)
                    except:
                        in_predicted_cenline = np.zeros_like(in_predicted_mask)
                    in_predicted_data = in_predicted_cenline
                else:
                    in_predicted_data = in_predicted_mask

                if (args.is_remove_trachea_calc_metrics):
                    # Remove the trachea and main bronchii from the binary masks
                    in_predicted_data = MaskOperator.substract_two_masks(in_predicted_data, in_coarse_airways)
                # **********************************************

                out_val_metric = fun_metric_eval_threshold(in_reference_data, in_predicted_data)
                sumrun_res_metrics += out_val_metric

                progressbar.update(1)
            # endfor
            curr_res_metrics = sumrun_res_metrics / num_valid_predict_files


        # Compare the mean metrics with the one desired, compute the relative error, and evaluate whether it's close enough
        curr_rel_error = (curr_res_metrics - metrics_value_sought) / metrics_value_sought

        if abs(curr_rel_error) < rel_error_eval_max:
            print("CONVERGED. Found threshold \'%s\', with result metrics \'%s\', rel. error: \'%s\'..." %(curr_thres_value, curr_res_metrics, abs(curr_rel_error)))
            is_comp_converged = True
            break
        else:
            # Update the threshold following a Newton-Raphson formula
            new_threshold = curr_thres_value + (curr_thres_value - old_thres_value)/(curr_res_metrics - old_metrics_value +_epsilon)*(metrics_value_sought - curr_res_metrics)
            new_threshold = np.clip(new_threshold, 0.0, 1.0)   # clip new value to bounded limits

            print("Not Converged. Result metrics \'%s\', rel. error: \'%s\'. New threshold \'%s\'..." %(curr_res_metrics, curr_rel_error, new_threshold))
            old_thres_value  = curr_thres_value
            old_metrics_value= curr_res_metrics
            curr_thres_value = new_threshold
    # endfor

    if not is_comp_converged:
        print("ERROR. COMPUTATION NOT CONVERGED...")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir', type=str, default=BASEDIR)
    parser.add_argument('input_posteriors_dir', type=str)
    parser.add_argument('--metric_eval_threshold', type=str, default=METRIC_EVALUATE_THRESHOLD)
    parser.add_argument('--metric_value_sought', type=float, default=0.13)
    parser.add_argument('--is_remove_trachea_calc_metrics', type=str2bool, default=IS_REMOVE_TRACHEA_CALC_METRICS)
    parser.add_argument('--is_connected_masks', type=str2bool, default=False)
    parser.add_argument('--name_input_reference_masks_relpath', type=str, default=NAME_RAW_LABELS_RELPATH)
    parser.add_argument('--name_input_coarse_airways_relpath', type=str, default=NAME_RAW_COARSEAIRWAYS_RELPATH)
    parser.add_argument('--name_input_reference_centrelines_relpath', type=str, default=NAME_RAW_CENTRELINES_RELPATH)
    parser.add_argument('--name_input_reference_keys_file', type=str, default=NAME_REFERENCE_KEYS_PROCIMAGE_FILE)
    parser.add_argument('--num_iter_evaluate_max', type=int, default=20)
    parser.add_argument('--rel_error_eval_max', type=float, default=1.0e-04)
    parser.add_argument('--init_threshold_value', type=float, default=0.5)
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).items():
        print("\'%s\' = %s" %(key, value))

    main(args)