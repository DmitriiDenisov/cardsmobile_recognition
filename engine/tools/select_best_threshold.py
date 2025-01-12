import numpy as np
import pandas as pd
import os
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def count_TP_and_FP_for_df(df):
    """
    For given dataframe calculates for all unique classses metrics TP, FP, FN, TN
    :param df: pandas Dataframe, should contain columns 'true_type' (true value), 'Predictions' (predicted value),
    'indicator' (if pred == true)
    :return: 4 lists of TP, FP, TN and FN
    """

    TP_list = []
    FP_list = []
    FN_list = []
    TN_list = []

    for one_class in df['true_type'].unique():
        TP = len(df[(df['Predictions'] == one_class) & (df['true_type'] == one_class)])
        FP = len(df[(df['Predictions'] == one_class) & (df['true_type'] != one_class)])
        FN = len(df[(df['Predictions'] != one_class) & (df['true_type'] == one_class)])
        TN = len(df[(df['true_type'] != one_class) & (df['indicator'] == True)])
        TP_list.append(TP)
        FP_list.append(FP)
        FN_list.append(FN)
        TN_list.append(TN)

    return TP_list, FP_list, FN_list, TN_list

def select_best_threshold(threshold_list, filenames, PATH_PREDICTIONS, PATH_TEST_ANSWERS, PATH_LABELS, PATH_CLASSES_IN_SET):
    labels = pd.read_csv(PATH_LABELS)
    labels = dict(zip(labels['class_index'], labels['class_name']))
    labels[-1] = 'rejected'

    pred = pd.read_csv(PATH_PREDICTIONS, header=None)
    if isinstance(pred, pd.DataFrame):
        pred = pred.values

    best_pr = np.nan
    true_answers = pd.read_excel(PATH_TEST_ANSWERS).set_index('card_id')
    classes_in_train_set = pd.read_excel(PATH_CLASSES_IN_SET)['class_name_in_training_set'].values
    true_answers.loc[~true_answers['true_type'].isin(classes_in_train_set), 'true_type'] = 'rejected'

    for thresh in threshold_list:
        bool_pred = pred > thresh
        predicted_class_indices = np.argmax(pred, axis=1)
        rows_does_not_contain_more_than_thresh = np.argwhere(bool_pred.any(1) == False)
        predicted_class_indices[rows_does_not_contain_more_than_thresh] = -1

        # labels = (train_generator.class_indices)
        # labels = dict((v,k) for k,v in labels.items())
        predictions = [labels[k] for k in predicted_class_indices]

        results = pd.DataFrame({"Filename": filenames,
                                "Predictions": predictions}).set_index('Filename')
        df = pd.concat([results, true_answers], axis=1, join_axes=[results.index])
        df['indicator'] = df['Predictions'] == df['true_type']

        TP_list, FP_list, _, _ = count_TP_and_FP_for_df(df)
        mean_pr = np.mean(TP_list) / (np.mean(TP_list) + np.mean(FP_list))

        print('For thresh {0}, mean precision: {1}'.format(thresh, mean_pr))
        if mean_pr > best_pr or best_pr is np.nan:
            best_pr = mean_pr
            best_thresh = thresh
            #best_df = df.copy()

    with open(os.path.join(os.path.dirname(PATH_PREDICTIONS), 'best_threshold.txt'), 'w') as f:
        f.write(str(best_thresh))

    return best_pr, best_thresh