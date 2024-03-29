# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 14:09:31 2024

@author: huan0707
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.optimize import minimize
import math
from scipy.optimize import least_squares

import matplotlib
# matplotlib.rcParams['mathtext.fontset'] = 'stix'
# matplotlib.rcParams['font.family'] = 'STIXGeneral'

## use model
modelvg = lambda x, alpha, n, m, thetas, thetar: ((1+(alpha*x)**n)**-m)*(thetas-thetar)+thetar

def calculate_errors(params, xdata, ydata, preferred_params):
    alpha, n, m, thetas, thetar = params
    
    # Extract preferred values for n and thetar
    alpha_pref, n_pref, m_pref = preferred_params
    
    # Calculate predicted values using the given function
    predicted_values = ((1 + (alpha * xdata) ** n) ** -m) * (thetas - thetar) + thetar
    
    # Calculate the sum of squared errors between predicted and observed values
    error1 = np.sum((predicted_values - ydata) ** 2)
    
    # Calculate the sum of squared errors between optimized parameters and preferred parameters
    error2 = (params[0] - alpha_pref) ** 2  # Error for alpha
    error3 = (params[1] - n_pref) ** 2  # Error for n
    error4 = (params[2] - m_pref) ** 2  # Error for m
    
    return error1, error2, error3, error4

def objective_function(params, xdata, ydata, preferred_params):
    errors = calculate_errors(params, xdata, ydata, preferred_params)
    total_error = errors[0] * 1 + errors[1] * 1e-1 + errors[2] * 1e-7  + errors[3] * 1e-3
    return total_error


# Initial guess for parameters: alpha, n, m, Cf, Cs
initial_guess = [0.1,100,0.005,0,0.3]#[0.40,509,0.14,0.02,0.55]#

# Preferred parameter values: alpha, n, m
preferred_params = [0.4,100,0.01]

distance = lambda x, y, x0, y0: ((x - x0) ** 2 + (y - y0) ** 2) ** 0.5
def get_x0_y0_r_split(EL_data, alpha, n, m, theta_s, theta_r, initial_s, initial_f, perc_s, perc_f):
    derivatives_s = []
    derivatives_f = []
    arctans_s = []
    arctans_f = []
    derivatives = []
    arctans = []
    EC_data = modelvg(EL_data / -10, alpha, n, m, theta_s, theta_r) * 100000 / 1000 # unit: mS/cm
    mid_EC = (0.5 * (theta_r - theta_s) + theta_s) * 100
    for i in range(1, len(EL_data)):
        d_EL = EL_data[i] - EL_data[i - 1]
        d_EC = EC_data[i] - EC_data[i - 1]
        derivative = d_EL / d_EC
        if EC_data[i] == EC_data[i - 1]:
            derivative = -1e20
        arctan_x = math.atan(derivative)
        arctan_x_degrees = math.degrees(arctan_x)
        derivatives.append(derivative)
        arctans.append(arctan_x_degrees)
        
        if EC_data[i] > mid_EC:
            derivatives_s.append(derivative)
            arctans_s.append(arctan_x_degrees)
        else:
            derivatives_f.append(derivative)
            arctans_f.append(arctan_x_degrees)
            
    d_angles_s = []
    d_angles_f = []
    d_angles = []
    for i in range(1, len(derivatives_s)):
        d_angle = np.abs(arctans_s[i] - arctans_s[i - 1])
        d_angles_s.append(d_angle)
    for i in range(1, len(derivatives_f)):
        d_angle = np.abs(arctans_f[i] - arctans_f[i - 1])
        d_angles_f.append(d_angle)
    for i in range(1, len(derivatives)):
        d_angle = np.abs(arctans[i] - arctans[i - 1])
        d_angles.append(d_angle)
    percentile_s = np.percentile(d_angles_s, perc_s)
    percentile_f = np.percentile(d_angles_f, perc_f)
    EL_salty = []
    EC_salty = []
    EL_fresh = []
    EC_fresh = []
    for i in range(1, len(d_angles)):
        if EC_data[i + 2] > mid_EC:
            if d_angles[i] > percentile_s:
                EL_salty.append(EL_data[i + 2])
                EC_salty.append(EC_data[i + 2])
        else:
            if d_angles[i] > percentile_f:
                EL_fresh.append(EL_data[i + 2])
                EC_fresh.append(EC_data[i + 2])
    def objective(params, y_cf, x_cf):
        x0, y0, r = params
        return (distance(x_cf, y_cf, x0, y0) - r) ** 2    
    initial_s = initial_s  # [x0, y0, r]
    result_s = least_squares(objective, initial_s, args=(EL_salty, EC_salty))
    optimized_s = result_s.x
    x0_s, y0_s, r_s = optimized_s

    initial_f = initial_f
    result_f = least_squares(objective, initial_f, args=(EL_fresh, EC_fresh))
    optimized_f = result_f.x
    x0_f, y0_f, r_f = optimized_f
    return x0_s, y0_s, r_s, x0_f, y0_f, r_f
def plot_circle_f(x0, y0, r, ax, color):
    theta = np.linspace(0, 2*np.pi, 100)
    x = x0 + r * np.cos(theta)
    y = y0 + r * np.sin(theta)
    ax.plot(x, y, color = color,linestyle = '--')#, label = f"r1 = {r:.1f} "
    ax.axis('equal')
    # ax.set_xlim(xlim)
    # ax.set_ylim(ylim)
def plot_circle_s(x0, y0, r, ax, color):
    theta = np.linspace(0, 2*np.pi, 100)
    x = x0 + r * np.cos(theta)
    y = y0 + r * np.sin(theta)
    ax.plot(x, y, color = color,linestyle = '--')#, label = f"r2 = {r:.1f} "
    ax.axis('equal')     
    
# plt.rcParams.update({
#     'font.size': 11,
#     'text.usetex': False,
#     'font.family': 'Serif',
#     'font.serif': ['Times New Roman']
# })

plt.rc('font', **{'family': 'serif', 'serif': ['Times'], 'size': 11})
plt.rc('text', usetex=True)
# rc('font',**{'family':'serif','serif':['Times'], 'size': 11})
# rc('text', usetex=True)
# matplotlib.rcParams['text.usetex'] = True
# matplotlib.rcParams['text.latex.preamble'] = [
#     r'\usepackage{amsmath}',
#     r'\usepackage{amssymb}',
#     r'\usepackage{times}']

z_r = lambda target, alpha, n, m, cf, cs: ((((target/100000-cs)/(cf-cs))**(-1/m)-1)**(1/n))/alpha*-10
# this s_m is derivative of EC in terms of z (EC gradients per m AHD)
s_m = lambda C, alpha, n, m, thetas, thetar: (10**n * (10**n * (-1 + ((thetas - thetar) / (C - thetar))**(1/m)))**(-1 + 1/n) * (thetas - thetar) * ((thetas - thetar) / (C - thetar))**(-1 + 1/m)) / alpha / (C - thetar)**2 / m / n  

# fp = "C:/Users/huan0707/OneDrive - Flinders/4. LBD1/Authority Area boundary/LBW_Authority_Area_Boundary.shp"
# # fp = "E:\LBGS\Authority Area boundary\LBW_Authority_Area_Boundary.shp"

# LBW_area = gpd.read_file(fp)
# LBW_area = LBW_area.to_crs({'init': 'epsg:4326'})
file_path = f"LS_SCREEN_AHD_dataset_delete.xlsx"
data = pd.read_excel(file_path)
data['RDATE']=pd.to_datetime(data['RDATE'], dayfirst=True)#, format='%d/%m/%Y %H:%M:%S'
data = data.sort_values(by=['RN', 'RDATE'])
data = data[data['RN']==12000969]
# data = data[data['RDATE']=='1992-01-29 00:00:00'] # this is to check the results of r2 and rmse in comparison with results in excel LS_SCREEN_AHD_dataset_delete sheet2. 
data_g = data.groupby(['RN','RDATE'])
rn_color_dict = {}
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive']
for i, rn in enumerate(data['RN'].unique()):
    rn_color_dict[rn] = colors[i % len(colors)]
pipe_color_dict = {}
unique_pipes = data['PIPE'].unique()
for i, pipe in enumerate(unique_pipes):
    pipe_color_dict[pipe] = colors[i % len(colors)]
                          
initial_s = [18, -40, 0.1]  # for 0841
initial_f = [4.5, -5.5, 0]  # 98%,94.5/95%

initial_s = [18, -46, 10]  # for 0842
initial_f = [4.5, -20, 1]  # 99%, 98/97%

initial_s = [18, -46, 10]  # for 0843
initial_f = [4.5, -20, 1] #99%,98%

initial_s = [18, -46, 10]  # for 0844
initial_f = [4.5, -20, 0]  # 99%, 98%
initial_f = [10,-20,0]   # for 2011-05-12, 99%, 97%
initial_f = [37.5,-20,0.1] # for 1994/01/17 99%, 97%

initial_s = [18, -46, 10]  # for 0969
initial_f = [4.5, -20, 1] # 99%, 98/97%

combined_df2 = pd.DataFrame()
i=0
# paras_circles = pd.DataFrame(columns=['RN','RDATE','alpha', 'n', 'm','thetas' ,'thetar','R2','RMSE',
                                       # 'total error', 'weighted error obs', 'weighted error alpha',
                                       # 'weighted error n', 'weighted error m',
                                       # 'rf','rs'])
paras_circles = []                                      
# fig = plt.figure(figsize=(16.5/2.54, 25/2.54))
fig, axes = plt.subplots(
    nrows=4, ncols=3,
    figsize=(17/2.54, 25/2.54),
    gridspec_kw={
        'wspace': 0.1,
        'hspace': 0.25,
        # 'width_ratios': [7.5,6],
        # 'height_ratios': [subplot_size[1]]*2,
        'left': 0.1,    # Adjust this value to set the distance from the left boundary
        'right': 0.98,   # Adjust this value to set the distance from the right boundary
        'bottom': 0.05,  # Adjust this value to set the distance from the bottom boundary
        'top': 0.95      # Adjust this value to set the distance from the top boundary
    },
    sharey=True
)
for i, ax_row in enumerate(axes):
    for j, ax in enumerate(ax_row):
        ax.set_ylim([-55, 0])
        ax.set_xlim([0, 90])
        ax.set_xticks([0, 20, 40, 60, 80])

        # Show x-axis tick labels only for the last row of subplots
        if i == len(axes) - 1:
            ax.set_xticklabels([0, 20, 40, 60, 80])
            ax.set_xlabel('EC (mS/cm)')  # Set your desired x-axis tick positions

        # Set ylabel only on the first column for all rows except the last one
        if j == 0 and i != len(axes) - 1:
            ax.set_ylabel('Elevation (mAHD)')
            ax.set_xticklabels([])
        if j == 0 and i == len(axes) - 1:
            ax.set_ylabel('Elevation (mAHD)')
            ax.set_xticklabels([0, 20, 40, 60, 80])

        # Set x-axis tick labels to an empty list for all rows except the last one
        elif i != len(axes) - 1:
            ax.set_xticklabels([])


fig2, axes2 = plt.subplots(
    nrows=4, ncols=3,
    figsize=(17/2.54, 25/2.54),
    gridspec_kw={
        'wspace': 0.1,
        'hspace': 0.25,
        # 'width_ratios': [7.5,6],
        # 'height_ratios': [subplot_size[1]]*2,
        'left': 0.1,    # Adjust this value to set the distance from the left boundary
        'right': 0.98,   # Adjust this value to set the distance from the right boundary
        'bottom': 0.05,  # Adjust this value to set the distance from the bottom boundary
        'top': 0.95      # Adjust this value to set the distance from the top boundary
    },
    sharey=True
)
for i, ax_row in enumerate(axes2):
    for j, ax in enumerate(ax_row):
        ax.set_ylim([-55, 0])
        ax.set_xlim([0, 90])
        ax.set_xticks([0, 20, 40, 60, 80])

        # Show x-axis tick labels only for the last row of subplots
        if i == len(axes2) - 1:
            ax.set_xticklabels([0, 20, 40, 60, 80])
            ax.set_xlabel('EC (mS/cm)')  # Set your desired x-axis tick positions

        # Set ylabel only on the first column for all rows except the last one
        if j == 0 and i != len(axes2) - 1:
            ax.set_ylabel('Elevation (mAHD)')
            ax.set_xticklabels([])
        if j == 0 and i == len(axes2) - 1:
            ax.set_xticklabels([0, 20, 40, 60, 80])
            ax.set_ylabel('Elevation (mAHD)')

        # Set x-axis tick labels to an empty list for all rows except the last one
        elif i != len(axes2) - 1:
            ax.set_xticklabels([])

fig3, axes3 = plt.subplots(
    nrows=4, ncols=3,
    figsize=(17/2.54, 25/2.54),
    gridspec_kw={
        'wspace': 0.1,
        'hspace': 0.25,
        # 'width_ratios': [7.5,6],
        # 'height_ratios': [subplot_size[1]]*2,
        'left': 0.1,    # Adjust this value to set the distance from the left boundary
        'right': 0.98,   # Adjust this value to set the distance from the right boundary
        'bottom': 0.05,  # Adjust this value to set the distance from the bottom boundary
        'top': 0.95      # Adjust this value to set the distance from the top boundary
    },
    sharey=True
)
for i, ax_row in enumerate(axes3):
    for j, ax in enumerate(ax_row):
        ax.set_ylim([-55, 0])
        ax.set_xlim([0, 90])
        ax.set_xticks([0, 20, 40, 60, 80])

        # Show x-axis tick labels only for the last row of subplots
        if i == len(axes3) - 1:
            ax.set_xticklabels([0, 20, 40, 60, 80])
            ax.set_xlabel('EC (mS/cm)')  # Set your desired x-axis tick positions

        # Set ylabel only on the first column for all rows except the last one
        if j == 0 and i != len(axes3) - 1:
            ax.set_ylabel('Elevation (mAHD)')
            ax.set_xticklabels([])
        if j == 0 and i == len(axes3) - 1:
            ax.set_xticklabels([0, 20, 40, 60, 80])
            ax.set_ylabel('Elevation (mAHD)')

        # Set x-axis tick labels to an empty list for all rows except the last one
        elif i != len(axes3) - 1:
            ax.set_xticklabels([])

i=0
for (RN,date), df in data_g:
        # formatted_date = date.strftime('%Y-%m-%d')  # Format as YYYY-MM-DD_HH-MM-SS
    df = df.sort_values(['DEPTH_R'], ascending=False)
    i=i+1
    if 0<i<13:
        # ax = axes[i]
        ax = axes[(i-1) // 3, (i-1) % 3]
        # ax = fig.add_subplot(8, 5, i)

        color = pipe_color_dict[pipe]  # Get the color for this PIPE value
        ax.scatter(df['MEASUREMENT']/1000, df['DEPTH_R'], marker='o', color=color, s=12,facecolor = 'none')

        # combined_df2 = pd.concat([combined_df2, df], ignore_index=True)
        # fit
        matric = np.linspace(0, 5.5, 1000)
        xdata = -df['DEPTH_R']/10
        ydata = df['MEASUREMENT']/100000
        result = minimize(
           objective_function,
           initial_guess,
           args=(xdata,ydata,preferred_params),
           method='trust-constr',
           bounds=[(0, None), (0, None), (0, None),(0, None), (0, None)],  # Bounds for lambda_x, n, m
       )
       
        optimal_parameters = result.x
        a1, a2, a3,a4,a5 = optimal_parameters
        y_fitvg = modelvg(matric, a1,a2,a3,a4,a5)
        total_error = result.fun
        individual_errors = calculate_errors(optimal_parameters, xdata, ydata, preferred_params)
        e1, e2, e3, e4 = individual_errors
        # plt.plot(y_fitvg*100000,matric*(-10),  '-y', label='VG curve with regulization',linewidth=2)
        # r_squared = r2_score(ydata,modelvg(xdata, a1,a2,a3,a4,a5))
        # # rmse = np.sqrt(mean_squared_error(ydata, modelvg(xdata, a1,a2,a3,a4,a5)))
        r_squared = 1 - np.sum((ydata - modelvg(xdata, a1,a2,a3,a4,a5))**2)/np.sum((ydata-np.mean(ydata))**2)
        rmse = np.sqrt(np.sum((ydata - modelvg(xdata, a1,a2,a3,a4,a5))**2))/len(ydata)
        # ax.set_title(f"RN {RN:.0f}\n{date}")
        ax.set_title(f"RN {RN:.0f}\n{date.strftime('%Y-%m-%d')}",fontsize = 11)
        ax.plot(y_fitvg * 100000 / 1000, matric * (-10),  '-r',
        label=f"$\\alpha$={a1:.2f}\n$n$={a2:.0f}\n$m$={a3:.3f}\n$C_f$={a4:.3f}\n$C_s$={a5:.2f}\n$R^2$={r_squared:.2f}\nRMSE={rmse:.4f}",
        linewidth=2)
        # print(f"date: {date}, zi = {zi}")
        # ax.plot(interface * 100000 / 1000, zi, marker='o', markersize=2, color='r',
        #          markerfacecolor='r', linestyle='--')

        # ax.legend(handlelength=0, handletextpad=0,loc='best',fontsize = 10)
        legend = ax.legend(handlelength=0, handletextpad=0, loc='upper right',fontsize=10,
                           frameon=False)
        legend.get_frame().set_facecolor('none')  # Set background color to none
        legend.get_frame().set_linewidth(0)
        row = {"RN": RN, 'RDATE': date,
               'alpha': a1, 'n': a2, 'm': a3,'thetas':a4,'thetar':a5, 
               'R2': r_squared,'RMSE':rmse,
               # # 'zf':zf, 'zs':zs, 'zi':zi}
                'total error':total_error, 'weighted error obs': e1, 'weighted error alpha': e2*1e-1,
                'weighted error n': e3* 1e-7 , 'weighted error m': e4* 1e-3,}
                # 'rf':r_f,'rs':r_s}
    figure_path = os.path.join(f"{RN}_1_screen_AHD_SI.tif")
    fig.savefig(figure_path, dpi = 300, pil_kwargs={"compression": "tiff_lzw"}) 
    if 12 < i < 25:
        ax = axes2[(i-13) // 3, (i-13) % 3]

        color = pipe_color_dict[pipe]  # Get the color for this PIPE value
        ax.scatter(df['MEASUREMENT']/1000, df['DEPTH_R'], marker='o', color=color, s=12,facecolor = 'none')

        combined_df2 = pd.concat([combined_df2, df], ignore_index=True)
        # fit
        matric = np.linspace(0, 5.5, 1000)
        xdata = -df['DEPTH_R']/10
        ydata = df['MEASUREMENT']/100000
        result = minimize(
           objective_function,
           initial_guess,
           args=(xdata,ydata,preferred_params),
           method='trust-constr',
           bounds=[(0, None), (0, None), (0, None),(0, None), (0, None)],  # Bounds for lambda_x, n, m
       )
       
        optimal_parameters = result.x
        a1, a2, a3,a4,a5 = optimal_parameters
        y_fitvg = modelvg(matric, a1,a2,a3,a4,a5)
        total_error = result.fun
        individual_errors = calculate_errors(optimal_parameters, xdata, ydata, preferred_params)
        e1, e2, e3, e4 = individual_errors
        # plt.plot(y_fitvg*100000,matric*(-10),  '-y', label='VG curve with regulization',linewidth=2)
        r_squared = 1 - np.sum((ydata - modelvg(xdata, a1,a2,a3,a4,a5))**2)/np.sum((ydata-np.mean(ydata))**2)
        rmse = np.sqrt(np.sum((ydata - modelvg(xdata, a1,a2,a3,a4,a5))**2))/len(ydata)
        # ax.set_title(f"RN {RN:.0f}\n{date}")
        ax.set_title(f"RN {RN:.0f}\n{date.strftime('%Y-%m-%d')}",fontsize = 11)
        ax.plot(y_fitvg*100000/1000,matric*(-10),  '-r',
                label=f"$\\alpha$={a1:.2f}\n$n$={a2:.0f}\n$m$={a3:.3f}\n$C_f$={a4:.3f}\n$C_s$={a5:.2f}\n$R^2$={r_squared:.2f}\nRMSE={rmse:.4f}",
                # \nrf={r_f:.1f}\nrs={r_s:.1f}",
                linewidth=2)# print(yba)
        # x0_s, y0_s, r_s, x0_f, y0_f, r_f = get_x0_y0_r_split(
        #                         matric*-10, a1, a2, a3,a4,a5, initial_s, initial_f,
        #                         99, 97)   #perc_s, perc_f

        # plot_circle_f(x0_f, y0_f, r_f, ax,'g')
        # ax.plot(x0_f,y0_f,'orange',marker = 'o',markerfacecolor='orange',markersize = 2)
        # plot_circle_s(x0_s, y0_s, r_s, ax, 'g')
        # ax.plot(x0_s,y0_s,'orange',marker = 'o',markerfacecolor='orange',markersize = 2)
        # ax.plot(y_fitvg*100000/1000,matric*(-10),  '-r'
        #         # label=f"alpha={a1:.2f}\nn={a2:.2f}\nm={a3:.2f}\nthetas={a4:.2f}\nthetar={a5:.2f}\nR2={r_squared:.2f}\nRMSE={rmse:.2f}\nrf={r_f:.1f}\nrs={r_s:.1f}"
        #        ,linewidth=2)
        
        # ax.legend(handlelength=0, handletextpad=0,loc='best',fontsize = 10)
        legend = ax.legend(handlelength=0, handletextpad=0, loc='upper right', fontsize=10,
                           frameon=False)
        legend.get_frame().set_facecolor('none')  # Set background color to none
        legend.get_frame().set_linewidth(0)
        row = {"RN": RN, 'RDATE': date,
               'alpha': a1, 'n': a2, 'm': a3,'thetas':a4,'thetar':a5, 
               'R2': r_squared,'RMSE':rmse,
                'total error':total_error, 'weighted error obs': e1, 'weighted error alpha': e2*1e-1,
                'weighted error n': e3* 1e-7 , 'weighted error m': e4* 1e-3,}
                # 'rf':r_f,'rs':r_s}
    figure_path = os.path.join(f"{RN}_2_screen_AHD_fit_SI.tif")
    fig2.savefig(figure_path, dpi = 300, pil_kwargs={"compression": "tiff_lzw"})

        
    
    if 37 > i > 24:
        ax = axes3[(i-25) // 3, (i-25) % 3]

        color = pipe_color_dict[pipe]  # Get the color for this PIPE value
        ax.scatter(df['MEASUREMENT']/1000, df['DEPTH_R'], marker='o', color=color, s=12,facecolor = 'none')

        combined_df2 = pd.concat([combined_df2, df], ignore_index=True)
        # fit
        matric = np.linspace(0, 5.5, 1000)
        xdata = -df['DEPTH_R']/10
        ydata = df['MEASUREMENT']/100000
        result = minimize(
           objective_function,
           initial_guess,
           args=(xdata,ydata,preferred_params),
           method='trust-constr',
           bounds=[(0, None), (0, None), (0, None),(0, None), (0, None)],  # Bounds for lambda_x, n, m
       )
       
        optimal_parameters = result.x
        a1, a2, a3,a4,a5 = optimal_parameters
        y_fitvg = modelvg(matric, a1,a2,a3,a4,a5)
        total_error = result.fun
        individual_errors = calculate_errors(optimal_parameters, xdata, ydata, preferred_params)
        e1, e2, e3, e4 = individual_errors
        # plt.plot(y_fitvg*100000,matric*(-10),  '-y', label='VG curve with regulization',linewidth=2)
        r_squared = 1 - np.sum((ydata - modelvg(xdata, a1,a2,a3,a4,a5))**2)/np.sum((ydata-np.mean(ydata))**2)
        rmse = np.sqrt(np.sum((ydata - modelvg(xdata, a1,a2,a3,a4,a5))**2))/len(ydata)
        # ax.set_title(f"RN {RN:.0f}\n{date}")
        ax.set_title(f"RN {RN:.0f}\n{date.strftime('%Y-%m-%d')}")
        ax.plot(y_fitvg*100000/1000,matric*(-10),  '-r',
                label=f"$\\alpha$={a1:.2f}\n$n$={a2:.0f}\n$m$={a3:.3f}\n$C_f$={a4:.3f}\n$C_s$={a5:.2f}\n$R^2$={r_squared:.2f}\nRMSE={rmse:.4f}",
                # \nrf={r_f:.1f}\nrs={r_s:.1f}",
                linewidth=2)# print(yba)        # x0_s, y0_s, r_s, x0_f, y0_f, r_f = get_x0_y0_r_split(
        #                         matric*-10, a1, a2, a3,a4,a5, initial_s, initial_f,
        #                         99, 98)   #perc_s, perc_f

        # plot_circle_f(x0_f, y0_f, r_f, ax,'g')
        # ax.plot(x0_f,y0_f,'orange',marker = 'o',markerfacecolor='orange',markersize = 2)
        # plot_circle_s(x0_s, y0_s, r_s, ax, 'g')
        # ax.plot(x0_s,y0_s,'orange',marker = 'o',markerfacecolor='orange',markersize = 2)
        # ax.plot(y_fitvg*100000/1000,matric*(-10),  '-r'
        #        # label=f"alpha={a1:.2f}\nn={a2:.2f}\nm={a3:.2f}\nthetas={a4:.2f}\nthetar={a5:.2f}\nR2={r_squared:.2f}\nRMSE={rmse:.2f}\nrf={r_f:.1f}\nrs={r_s:.1f}"
        #        ,linewidth=2)
        ax.set_title(f"RN {RN:.0f}\n{date.strftime('%Y-%m-%d')}",fontsize = 11)
        # ax.legend(handlelength=0, handletextpad=0,loc='best',fontsize = 10)
        legend = ax.legend(handlelength=0, handletextpad=0, loc='upper right', fontsize=10, frameon=False)
        legend.get_frame().set_facecolor('none')  # Set background color to none
        legend.get_frame().set_linewidth(0)

        figure_path = os.path.join(f"{RN}_3_screen_AHD_fit_SI.tif")
        fig3.savefig(figure_path, dpi = 300, pil_kwargs={"compression": "tiff_lzw"})
        row = {"RN": RN, 'RDATE': date,
               'alpha': a1, 'n': a2, 'm': a3,'thetas':a4,'thetar':a5, 
               'R2': r_squared,'RMSE':rmse,
                'total error':total_error, 'weighted error obs': e1, 'weighted error alpha': e2*1e-1,
                'weighted error n': e3* 1e-7 , 'weighted error m': e4* 1e-3,}
                # 'rf':r_f,'rs':r_s}
         
    paras_circles.append(row)

  
paras_circles_df = pd.DataFrame(paras_circles)

    
# Add x-label only to the last four subplots
    # if i in [7,5,6]:
    #     ax.set_xlabel('EC (mS/cm)')
    
    # # Add y-label only to specific subplots
    # if i in [1,4,7]:
    #     ax.set_ylabel('Elevation (m AHD)')
    
    # ax.set_title(f'RN {RN:.0f}', fontsize=12)    
plt.tight_layout()
paras_circles_df.to_excel(os.path.join(f"LS_LBD_paras_VG_SupportingInfo_5.xlsx"),index=False)
# plt.savefig('MC_bores_LBD_filtered_screen_mz_AHD.tiff',dpi=300)






