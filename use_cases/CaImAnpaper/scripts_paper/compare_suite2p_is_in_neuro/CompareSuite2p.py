import caiman as cm
import numpy as np
import os
import time
import pylab as pl
import scipy
import h5py
import sys
from caiman.utils.visualization import plot_contours
from caiman.source_extraction.cnmf import cnmf as cnmf

from caiman.source_extraction.cnmf.estimates import Estimates, compare_components
from caiman.cluster import setup_cluster
from caiman.source_extraction.cnmf import params as params
n_processes = 24
base_folder = '/mnt/ceph/neuro/DataForPublications/DATA_PAPER_ELIFE/'

# %%
params_movies = []
# %%
params_movie = {'fname': 'N.03.00.t/Yr_d1_498_d2_467_d3_1_order_C_frames_2250_.mmap',
                's2p_file': 'N.03.00.t/2018-09-01/1/python_out.mat',
                'gSig': [8, 8],  # expected half size of neurons
                }
params_movies.append(params_movie.copy())
# %%
params_movie = {'fname': 'N.04.00.t/Yr_d1_512_d2_512_d3_1_order_C_frames_3000_.mmap',
                's2p_file': 'N.04.00.t/2018-09-01/1/python_out.mat',
                'gSig': [5, 5],  # expected half size of neurons
                }
params_movies.append(params_movie.copy())

# %% yuste
params_movie = {'fname': 'YST/Yr_d1_200_d2_256_d3_1_order_C_frames_3000_.mmap',
                's2p_file': 'YST/2018-09-01/1/python_out.mat',
                'gSig': [5, 5],  # expected half size of neurons
                }
params_movies.append(params_movie.copy())
# %% neurofinder 00.00
params_movie = {'fname': 'N.00.00/Yr_d1_512_d2_512_d3_1_order_C_frames_2936_.mmap',
                's2p_file': 'N.00.00/2018-09-01/1/python_out.mat',
                'gSig': [6, 6],  # expected half size of neurons
                }
params_movies.append(params_movie.copy())
# %% neurofinder 01.01
params_movie = {'fname': 'N.01.01/Yr_d1_512_d2_512_d3_1_order_C_frames_1825_.mmap',
                's2p_file': 'N.01.01/2018-09-01/1/python_out.mat',
                'gSig': [6, 6],  # expected half size of neurons
                }
params_movies.append(params_movie.copy())
# %% neurofinder 02.00
params_movie = {
    # 'fname': '/opt/local/Data/labeling/neurofinder.02.00/Yr_d1_512_d2_512_d3_1_order_C_frames_8000_.mmap',
    'fname': 'N.02.00/Yr_d1_512_d2_512_d3_1_order_C_frames_8000_.mmap',
    's2p_file': 'N.02.00/2018-09-01/1/python_out.mat',
    'gSig': [5, 5],  # expected half size of neurons

}
params_movies.append(params_movie.copy())
#%% K53
params_movie = {
    # 'fname': '/opt/local/Data/labeling/neurofinder.02.00/Yr_d1_512_d2_512_d3_1_order_C_frames_8000_.mmap',
    'fname': 'K53/Yr_d1_512_d2_512_d3_1_order_C_frames_116043_.mmap',
    's2p_file': 'K53/2018-09-01/1/python_out.mat',
    'gSig': [6, 6],  # expected half size of neurons

}
params_movies.append(params_movie.copy())
#%% J115
params_movie = {
    # 'fname': '/opt/local/Data/labeling/neurofinder.02.00/Yr_d1_512_d2_512_d3_1_order_C_frames_8000_.mmap',
    'fname': 'J115/Yr_d1_463_d2_472_d3_1_order_C_frames_90000_.mmap',
    's2p_file': 'J115/2018-09-01/1/python_out.mat',
    'gSig': [7, 7],  # expected half size of neurons

}
params_movies.append(params_movie.copy())
#%% J123
# params_movie = {
#     # 'fname': '/opt/local/Data/labeling/neurofinder.02.00/Yr_d1_512_d2_512_d3_1_order_C_frames_8000_.mmap',
#     'fname': 'J123/Yr_d1_458_d2_477_d3_1_order_C_frames_41000_.mmap',
#     's2p_file': 'J123/2018-09-01/1/python_out.mat',
#     'gSig': [8, 8],  # expected half size of neurons
#
# }
# params_movies.append(params_movie.copy())

try:
    if 'pydevconsole' in sys.argv[0]:
        raise Exception()
    ID = sys.argv[1]
    ID = str(np.int(ID) - 1)
    print('Processing ID:' + str(ID))
    ID = [np.int(ID)]
except:
    ID = np.arange(0,8)
    print('ID NOT PASSED')

#%%
onlycell = False
generate_data = False
results = []
#%%
for params_movie in np.array(params_movies)[ID]:
    # %% start cluster
    #
    # TODO: show screenshot 10
    fname_new = os.path.join(base_folder, params_movie['fname'])
    if generate_data:
        try:
            cm.stop_server()
            dview.terminate()
        except:
            print('No clusters to stop')

        c, dview, n_processes = setup_cluster(
            backend='multiprocessing', n_processes=20, single_thread=False)



        # %% prepare ground truth masks

        gt_file = os.path.join(os.path.split(fname_new)[0], os.path.split(fname_new)[1][:-4] + 'match_masks.npz')
        gSig = params_movie['gSig']
        with np.load(gt_file, encoding='latin1') as ld:
            Cn_orig = ld['Cn']
            dims = (ld['d1'][()], ld['d2'][()])
            gt_estimate = Estimates(A=scipy.sparse.csc_matrix(ld['A_gt'][()]), b=ld['b_gt'], C=ld['C_gt'],
                                    f=ld['f_gt'], R=ld['YrA_gt'], dims=(ld['d1'], ld['d2']))


        min_size_neuro = 3 * 2 * np.pi
        max_size_neuro = (2 * gSig[0]) ** 2 * np.pi
        gt_estimate.threshold_spatial_components(maxthr=0.2, dview=dview)
        gt_estimate.remove_small_large_neurons(min_size_neuro, max_size_neuro)
        _ = gt_estimate.remove_duplicates(predictions=None, r_values=None, dist_thr=0.1, min_dist=10,
                                          thresh_subset=0.6)
        print(gt_estimate.A_thr.shape)
    #%% create estimate from suite2p output
    counter = 0
    nSVDforROI = range(500,1501,500);#500:500:1500
    NavgFramesSVD = range(2000,6001, 2000)#2000:2000:6000;
    sig__ = np.arange(0.25,0.76,0.25)#0.25:0.25:0.75;

    for nSVD in nSVDforROI:
        for Navg in NavgFramesSVD:
            for ss in sig__:

                counter = counter + 1

                # base_folder_ = '/opt/local/Data/Example/DATA/F_' + str(nSVD) + '_' + str(Navg) + '_' + str(ss) + '/'
                base_folder_ = '/mnt/ceph/neuro/DataForPublications/DATA_PAPER_ELIFE/Suite2pComparison/DATA/F_' + str(nSVD) + '_' + str(Navg) + '_' + str(ss) + '/'

                suite2p_file = os.path.join(base_folder_, params_movie['s2p_file'])
                if generate_data:
                    with h5py.File(suite2p_file, 'r') as ld:
                        masks = np.array(ld['masks']).transpose([2,1,0])
                        traces = np.array(ld['traces']).T
                        iscell = np.array(ld['iscell'])
                #    ld = scipy.io.loadmat(suite2p_file)
                        if onlycell:
                            A_2p = scipy.sparse.csc_matrix(np.reshape(masks[:, :, np.where(iscell == 1)[1]], (np.prod(dims), -1)))
                        else:
                            A_2p = scipy.sparse.csc_matrix(np.reshape(masks[:, :, :], (np.prod(dims), -1)))

                        s2p_estimate = Estimates(A=A_2p, b=None, C=traces,f=None, R=None, dims=dims)

                        min_size_neuro = 3 * 2 * np.pi
                        max_size_neuro = (2 *gSig[0]) ** 2 * np.pi
                        s2p_estimate .threshold_spatial_components(maxthr=0.2, dview=dview)
                        # s2p_estimate .remove_small_large_neurons(min_size_neuro, max_size_neuro)
                        _ = s2p_estimate .remove_duplicates(predictions=None, r_values=None, dist_thr=0.1, min_dist=10,
                                                          thresh_subset=0.6)
                        print(s2p_estimate.A_thr.shape)


                    #%%
                    pl.close('all')
                    params_display = {
                        'downsample_ratio': .2,
                        'thr_plot': 0.8
                    }

                    pl.rcParams['pdf.fonttype'] = 42
                    font = {'family': 'Arial',
                            'weight': 'regular',
                            'size': 20}
                    pl.rc('font', **font)

                    plot_results = False
                    if plot_results:
                        pl.figure(figsize=(30, 20))



                    tp_gt, tp_comp, fn_gt, fp_comp, performance_suite2p = compare_components(gt_estimate, s2p_estimate,
                                                                                                      Cn=Cn_orig, thresh_cost=.8,
                                                                                                      min_dist=10,
                                                                                                      print_assignment=False,
                                                                                                      labels=['GT', 'Suite_2p'],
                                                                                                      plot_results=False)
                    print(params_movie['fname'])
                    print({a: b.astype(np.float16) for a, b in performance_suite2p.items()})

                    if onlycell:
                        name_to_load = os.path.join(base_folder_,
                                                    os.path.split(fname_new)[1][:-4] + '_comparison_GT_only_cell.npz')
                    else:
                        name_to_load = os.path.join(base_folder_,
                                                os.path.split(fname_new)[1][:-4] + '_comparison_GT_all_struct.npz')

                    np.savez(name_to_load, tp_gt=tp_gt, tp_comp=tp_comp, fn_gt=fn_gt, fp_comp=fp_comp, performance_suite2p=performance_suite2p)
                    # pl.savefig(os.path.join(base_folder_, 'comparison_GT_all_struct.pdf'))
                else:
                    if onlycell:
                        name_to_load = os.path.join(base_folder_,
                                                    os.path.split(fname_new)[1][:-4] + '_comparison_GT_only_cell.npz')
                    else:

                        name_to_load = os.path.join(base_folder_,
                                                os.path.split(fname_new)[1][:-4] + '_comparison_GT_all_struct.npz')

                    with np.load(name_to_load) as ld:

                        performance_suite2p = ld['performance_suite2p'][()]
                        # print(os.path.split(fname_new)[1][:-4])
                        # print({a: b.astype(np.float16) for a, b in performance_suite2p.items()}['f1_score'])
                        results.append([fname_new.split('/')[-2],nSVD,Navg,ss,{a: b.astype(np.float16) for a, b in performance_suite2p.items()}['f1_score']])


if onlycell:
    df_only = DataFrame(results)
    grp_only = df_only.groupby(by=[0])
    grp_only.mean()
    grp_only.max()
    df_only.mean()
    cc_only = df_only.groupby(by=[1, 2, 3])
    ds_only = cc_only.describe()
    print(ds_only.iloc[:, 1].max())
    pars = ds_only.iloc[:,1].idxmax()
    print(pars)
    df_result = df_only[((df_only[1] == pars[0]) & (df_only[2] == pars[1]) & (df_only[3] == pars[2]))]
    df_result.columns = ['name','par1', 'par2', 'par3', 'f1_score']
    print(df_result)

    ax = df_result.plot(x='name',y='f1_score', xticks=range(len(df_result)), marker = 'o')
    ax.set_xticklabels(df_result.name)
    pl.xlabel('Dataset')
    pl.ylabel('F1 score')
else:
    df = DataFrame(results)
    grp = df.groupby(by=[0])
    grp.mean()
    grp.max()
    df.mean()
    cc = df.groupby(by=[1, 2, 3])
    ds = cc.describe()
    print(ds.iloc[:, 1].max())
    pars = ds.iloc[:, 1].idxmax()
    print(pars)
    df_result = df[((df[1] == pars[0]) & (df[2] == pars[1]) & (df[3] == pars[2]))]
    df_result.columns = ['name', 'par1', 'par2', 'par3', 'f1_score']
    print(df_result)

    df_result.plot(x='name', y='f1_score', xticks=range(len(df_result)), marker='o', ax=ax)
    pl.xlabel('Dataset')
    pl.ylabel('F1 score')
    pl.legend(['Classifier', 'No classifier')
