#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
from statsmodels.nonparametric.kernel_regression import KernelReg
#import matplotlib.pyplot as plt
import numpy as np

from make_1_imi_chart import get_paths

# In[4]:


def get_fitted_values(week):
    
# week - for knowing for which s_spotify values to take s_streams

    # делаем working_df с которой будет работать модель
    working_df = pd.read_csv(get_paths()[1]+"all_spotify.csv")
    working_df = working_df.drop(working_df.columns[[0]], axis=1)
    
    # делаем регрессию
    y = np.array(list(working_df["streams"]))
    x_r = np.array(list(working_df["rank"]))
    x_s = np.array(list(working_df["s_streams"]))

    var_cont = (np.var(x_s))**0.5
    b_c = var_cont*(len(y)**(-1/5))
    print(b_c)

    # count ordered discrete variable bandwidth
    b_o = len(y)**(-2/5)
    print(b_o)


    reg_new = KernelReg(y, [x_r, x_s], var_type="oc", reg_type = "ll", bw = [b_o, b_c]) 
    
    df_of_needed_week = working_df[working_df["week_f_show"] == week]
    last_week_sstreams = df_of_needed_week["s_streams"][-1:].values[0]
    fit_values = reg_new.fit([[i for i in range(1,201)],[last_week_sstreams for h in range(1,201) ]])[0]
    
    return fit_values







# In[3]:


#np.save("regression_fitted_values", fit_values, allow_pickle=True, fix_imports=True)

