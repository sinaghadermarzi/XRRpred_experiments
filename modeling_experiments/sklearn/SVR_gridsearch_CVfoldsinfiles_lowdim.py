
import pandas
import itertools
import numpy
from scipy.stats import pearsonr,spearmanr
from sklearn.metrics.regression import mean_absolute_error,mean_squared_error
from sklearn.preprocessing import StandardScaler


from sklearn.svm import SVR


def MAE(Y1,Y2):
    return mean_absolute_error(Y1,Y2)
def MSE(Y1, Y2):
    return mean_squared_error(Y1, Y2)
def SPC(y_true, y_pred):
    corr , _ = spearmanr(y_true,y_pred)
    return corr
def PNC(y_true, y_pred):
    corr , _ = pearsonr(y_true,y_pred)
    return corr




def normalize_df(df,features,target_col,scaler):
    X = df.loc[:,features].values
    Y = df.loc[:,target_col].values
    X = scaler.transform(X)
    out_df = pandas.DataFrame(X,index = df.index, columns=features)
    out_df[target_col]= Y
    return out_df



def normalize_train_test(training_set_df , test_set_df, feature_cols, target_col):
    train_set_X = training_set_df.loc[ :, feature_cols].values
    scaler = StandardScaler()
    scaler.fit(train_set_X)
    test_set_norm_df = normalize_df(test_set_df,input_features,target_col,scaler)
    training_set_norm_df = normalize_df(training_set_df,input_features,target_col,scaler)
    return training_set_norm_df, test_set_norm_df





def avg_cross_validation_score(model,scorer,trainfolds_dfs,testfolds_dfs,feature_set,target_col_name):
    scores = [None]*len(testfolds_dfs)
    for i in range(len(testfolds_dfs)):
        train_X = trainfolds_dfs[i].loc[:,feature_set].values
        train_Y = trainfolds_dfs[i].loc[:,target_col_name].values
        test_X = testfolds_dfs[i].loc[:,feature_set].values
        test_Y = testfolds_dfs[i].loc[:,target_col_name].values
        model.fit(train_X,train_Y)
        test_pred = model.predict(test_X)
        scores[i] = scorer(test_pred,test_Y)
    # if float("nan") in scores:
    #     print("None seen in scores")
    avg_score  = numpy.mean(scores)
    if numpy.isnan(avg_score):
        print("None seen in scores")
    # print("cross validation on ",feature_set)
    # print("scores: ",scores)
    return avg_score



def get_resutls_column(model,trainfolds_dfs,testfolds_dfs,train_set,test_set,feature_set,target_col_name):
    MSEs = [None]*len(testfolds_dfs)
    MAEs = [None]*len(testfolds_dfs)
    SPs = [None]*len(testfolds_dfs)
    PNs = [None]*len(testfolds_dfs)
    for i in range(len(testfolds_dfs)):
        train_X = trainfolds_dfs[i].loc[:,feature_set].values
        train_Y = trainfolds_dfs[i].loc[:,target_col_name].values
        test_X = testfolds_dfs[i].loc[:,feature_set].values
        test_Y = testfolds_dfs[i].loc[:,target_col_name].values
        model.fit(train_X,train_Y)
        test_pred = model.predict(test_X)
        MAEs[i] = MAE(test_pred,test_Y)
        MSEs[i] = MSE(test_pred, test_Y)
        SPs[i] = SPC(test_pred, test_Y)
        PNs[i] = PNC(test_pred, test_Y)

    train_cvavg_MAE  = numpy.mean(MAEs)
    train_cvavg_MSE = numpy.mean(MSEs)
    train_cvavg_PN = numpy.mean(PNs)
    train_cvavg_SP = numpy.mean(SPs)


    test_Y = test_set.loc[:, target_col].values
    test_X = test_set.loc[:, feature_set].values
    train_X = train_set.loc[:, feature_set].values
    train_Y = train_set.loc[:, target_col].values

    model.fit(train_X, train_Y)
    test_pred = model.predict(test_X)

    testset_pn, _ = pearsonr(test_Y, test_pred)
    testset_sp, _ = spearmanr(test_Y, test_pred)
    testset_mae = mean_absolute_error(test_Y, test_pred)
    testset_mse = mean_squared_error(test_Y, test_pred)

    column = [testset_mae, testset_mse,testset_pn, testset_sp, train_cvavg_MAE, train_cvavg_MSE, train_cvavg_PN, train_cvavg_SP ,feature_set,len(feature_set)]
    column += list(test_pred)
    return column




def optimize_params_SVR(train_fold_dfs,test_fold_dfs,input_features,target_col,eval_func,tolerance,maximize,param_vals):
    gammas = param_vals["gammas"]
    Cs = param_vals["Cs"]
    kernels = param_vals["kernels"]

    current_best_params  = None
    current_best_score = float("inf")
    if maximize:
        current_best_score = -current_best_score

    for (gamma, C,kernel) in itertools.product(gammas,Cs,kernels):
        print("_________________\ngamma = ",gamma)
        print("C = ", C)
        print("kernel = ", kernel)
        print("\n",end="")
        model = SVR(gamma= gamma, C = C, kernel=kernel)
        new_score = avg_cross_validation_score(model, eval_func, train_fold_dfs, test_fold_dfs,input_features, target_col)
        print("score:",new_score)
        if maximize:
            if new_score - current_best_score >= tolerance:
                current_best_score = new_score
                current_best_params = (gamma, C, kernel)
        else:
            if current_best_score - new_score >= tolerance:
                current_best_score = new_score
                current_best_params = (gamma, C, kernel)

    return current_best_params




param_pool ={
    "gammas" : [0.25,0.5,0.75,1],
    "Cs" : [0.25,0.5,1,5,10,100],
    "kernels" : ["linear","rbf"]
}


############## read configurations

import json
with open("configurations.json") as jsonfile:
    conf = json.load(jsonfile)
dataset_root_dir = conf["dataset_root_dir"]
sampling_methods = conf["sampling_methods"]
sampling_methods = [x+"_lowdim" for x in sampling_methods]
test_set_path = dataset_root_dir + conf["file_locations"]["test_set"]
test_folds_relpath = conf["file_locations"]["test_folds"]
test_folds_path = [dataset_root_dir + relpath for relpath in test_folds_relpath]
input_features = conf["input_features"]

#
# sampling_methods = ["nosampling"]
#
# param_pool ={
# "criterions" : ["friedman_mse"],
# "max_depths" : [5],
# "max_featuress"  : [None],
# "min_samples_splits" : [10]
# }


#####################################


test_set_df = pandas.read_csv(test_set_path)
num_CV_folds = len(test_folds_path)



row_labels  = ["test_MAE",
               "test_MSE",
               "test_pearson",
               "test_spearman",
               "avg_training_MAE",
               "avg_test_MSE",
               "avg_training_pearson",
               "avg_training_spearman",
               "feature_list",
               "num_features"] + list(test_set_df["PDB ID"].values)



for target_var in ["resolution","rfree"]:
    results_df = pandas.DataFrame()
    target_col = conf["target_col"][target_var]
    input_features = conf["input_features"]["selected"][target_var]
    results_df[target_col] = ["", "", "", "", "", "", "", "", "", ""] + list(test_set_df[target_col].values)
    for sampling in sampling_methods:
        training_set_path = dataset_root_dir+conf["file_locations"]["training_set"][sampling][target_var]
        train_folds_relpath  = conf["file_locations"]["training_folds"][sampling][target_var]
        train_folds_path = [dataset_root_dir + relpath for relpath in train_folds_relpath]
        test_fold_norm_df = [None] * num_CV_folds
        train_fold_norm_df = [None] * num_CV_folds
        for i in range(num_CV_folds):
            train_fold_norm_df[i],test_fold_norm_df[i] = normalize_train_test(pandas.read_csv(train_folds_path[i]), pandas.read_csv(test_folds_path[i]), input_features, target_col)
        train_set_norm_df, test_set_norm_df = normalize_train_test(pandas.read_csv(training_set_path), pandas.read_csv(test_set_path), input_features, target_col)


        (gamma,C, kernel) = optimize_params_SVR(train_fold_norm_df,test_fold_norm_df,input_features,target_col,SPC,0.001,True,param_pool)


        print("grid search done! best parameters:")
        print("gamma", gamma)
        print("C", C)
        print("kernel", kernel)

        working_model  = SVR(gamma= gamma, C = C, kernel=kernel)

        results_df["SVR_" + sampling] = get_resutls_column(working_model, train_fold_norm_df, test_fold_norm_df, train_set_norm_df, test_set_norm_df, input_features, target_col)




    results_df.to_csv("results_SVR_"+target_col+"_lowdim_.csv",columns=sorted(results_df.columns),
                      index = row_labels)













