import copy

def multiclass_postprocess(X_binned, feature_graphs, binned_predict_proba, feature_types):
    '''
    X_binned: Training dataset, pre-binned. Contains integer values, 0+. Each value is a unique bin.
    feature_graphs: List of 2d numpy arrays. List is size d for d features. Each numpy array is of size b for b bins in the feature. Each bin has k elements for k classes.
    binned_predict_proba: Function that takes in X_binned, returns 2d numpy array of predictions. Each row in the return vector has k elements, with probability of belonging to class k.
    feature_types: List of strings containing either "categorical" or "numeric" for each feature.
    '''
    updated_feature_graphs = copy.deepcopy(feature_graphs)
    K = feature_graphs[0].shape[1]
    d = len(feature_graphs) # num of features

    ## Compute the predicted probability on the original data.
    predprob = binned_predict_proba(X_binned)
    predprob_prev = [None]*len(feature_graphs)

    ## Compute the predicted probability on the counterfactual data with each value in feature i decrease by 1.
    for i in range(len(feature_graphs)):
        data_prev = np.copy(X_binned)
        data_prev[:,i] = np.maximum(X_binned[:,i]-1,0)
        predprob_prev[i] = binned_predict_proba(data_prev)

    intercepts = np.zeros(K)
    for i in range(len(feature_graphs)):
        bincount = np.bincount(X_binned[:,i].astype(int))
        if feature_types[i]=='numeric':
            num_bins = feature_graphs[i].shape[0]
            change = np.zeros(num_bins)
            for v in range(1,num_bins):
                subset_index = X_binned[:,i]==v
                ratio = np.divide(predprob[subset_index,:],predprob_prev[i][subset_index,:])
                sum_ratio = np.sum(np.subtract(ratio,1),axis = 0)
                difference = feature_graphs[i][v,:] - feature_graphs[i][v-1,:]+ change[v-1]
                change[v] = np.mean(difference)
                new_difference = difference - change[v]
                back_change = 0
                for k in range(K):
                    if new_difference[k]*sum_ratio[k]<0 and abs(back_change) < abs(new_difference[k]):
                        back_change = new_difference[k]
                change[v] = change[v]+back_change
            updated_feature_graphs[i] = np.subtract(updated_feature_graphs[i],change.reshape((num_bins,-1)))
        for k in range(K):
            mean = np.sum(np.multiply(updated_feature_graphs[i][:,k],bincount))/len(X_binned)
            updated_feature_graphs[i][:,k] = np.subtract(updated_feature_graphs[i][:,k],mean)
            intercepts[k] += mean
    return { 'feature_graphs' : updated_feature_graphs, 'intercepts' : intercepts}




if __name__=="__main__":
    import numpy as np
    n=1000
    d = 2
    k = 3
    b = 10

    X_binned = np.random.randint(b,size = (n,d))
    feature_graphs = []
    for _ in range(d):
        feature_graphs.append(np.random.rand(b,k))
    def binned_predict_proba(X_binned,k=3):
        n = len(X_binned)
        return 1/k * np.ones((n,k))

    feature_types = ['numeric']*d
    results = multiclass_postprocess(X_binned, feature_graphs, binned_predict_proba, feature_types)
    print('test for centering: ', [np.mean(graph, axis = 1) for graph in results['feature_graphs']])

