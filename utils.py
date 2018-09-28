import numpy as np
import matplotlib.pyplot as plt
import os
import json

import logging
logging.basicConfig(level = logging.INFO)

#############
## General ##
#############
def get_config():
    """Get username and download directory saved in .config 
    (or create that file if necessary)
    """
    if os.path.exists('.config'):
        return json.load(open('.config'))
    else:
        username = input("Please enter your username:")
        slackfilepath = input("Please enter the absolute path where you keep the AMPEL files from Slack:")
        config = {'username': username, 'slackfilepath': slackfilepath}
        json.dump(config, open('.config', 'w'))
        return config

def match_iband_field(fieldids):
    """Quickly match fieldids to the i-band footprint
    Return dictionary with months in which each field is in i-band survey
    """
    blocks = [
        ['March', 'April', 'May'],
        ['June'],
        ['July'],
        ['August'],
        ['September', 'October', 'November']
    ]
    iband = np.genfromtxt('ztf-i-band-fields-v6.dat')

    if type(fieldids) == int:
            fieldids = [fieldids]

    out = {}
    for f_ in fieldids:
        out[f_] = []
        for k, block in enumerate(blocks):
            if f_ in iband[:, k]:
                out[f_].extend(block)

    return out

################
## Scheduling ##
################
def plot_visibility(snnames, obs_windows, dark_time, priorities=None, labeltype='index', figsize=None):
    """Function for plotting visibility of targets as previously determined in 
    ztfcosmology_visibility.ipynb
    """
    if priorities is None:
        priorities = np.zeros(len(snnames), dtype=int)
        
    if labeltype == 'index':
        labels = ['%s (%i)'%(name, k) for k, name in enumerate(snnames)]
    elif labeltype == 'priority':
        labels = ['%s (%i)'%(name, k) for k, name in zip(priorities, snnames)]
        priorities = np.zeros(len(snnames), dtype=int)
    
    show_vis = np.zeros((3*(len(obs_windows.keys())+max(priorities))-1, len(dark_time)))
    for k, snname in enumerate(snnames):
        obs_w = obs_windows[snname]
        idx = np.array([np.where(dark_time == t_)[0][0] for t_ in obs_w['visible']])
        p = priorities[k]
        show_vis[3*(k+p), idx] = obs_w['airmass']
        show_vis[3*(k+p)+1, idx] = obs_w['airmass']
    
    show_vis_m = np.ma.masked_where(show_vis == 0, show_vis)    
    
    if figsize is None:
        fig = plt.figure(figsize=(18,1+len(snnames)/3.))
    else:
        fig = plt.figure(figsize=figsize)
        
    plt.imshow(show_vis_m, vmin=1., vmax=2., cmap='viridis_r')

    full_hours = [k for k, t in enumerate(dark_time) if t.iso.endswith('00:00.000')]
    hour_labels = [t.iso[11:13] for k, t in enumerate(dark_time) if k in full_hours]
    plt.xticks(full_hours, hour_labels, fontsize='x-large')
    plt.xlabel('UTC time', fontsize='xx-large')
    plt.yticks([3*(k+priorities[k])+0.5 for k in range(len(snnames))], labels)
    cb = plt.colorbar()
    cb.set_label('airmass', rotation=270, fontsize='xx-large')
    plt.tight_layout()

    return fig

def prepare_snifs_schedule(names, coords, obs_windows, obsdate,
                           outdir='snifs', logger=None):
    """Output the files Greg needs for SNIFS"""
    logger = logger if logger is not None else logging.getLogger()

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    fchart_files = [fn for fn in os.listdir(outdir) if fn.startswith('fchart')]
    exclude = []
    for fn in fchart_files:
        f = open(os.path.join(outdir, fn))
        tmp = [line.split(',')[1][1:-1] for line in f]
        f.close()

        for n_ in tmp:
            if n_ in names:
                logger.info('%s was previously scheduled and will not be included in fchart again (but will be scheduled).'%n_)

        
    f = open(os.path.join(outdir, 'fchart_%s'%obsdate), 'w')
    for name in names:
        if name not in exclude:
            f.write("usno_fchart,'%s',ra=%.4f,dec=%.4f\n"%(name,
                                                         coords[name]['ra'],
                                                         coords[name]['dec']))
    f.close()

    out_str = '%s {type => "Candidate", start => "%s UTC", end => "%s UTC", exp => 1800, nexp => 1} '
    f = open(os.path.join(outdir, 'timelord_%s'%obsdate), 'w')
    for name in names:
        f.write(out_str%(name, obs_windows[name]['visible'][0].iso[:19],
                         obs_windows[name]['visible'][-1].iso[:19],))
    f.close()
