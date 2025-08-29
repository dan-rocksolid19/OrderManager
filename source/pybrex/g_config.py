#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Global configuration
# Created: 02.01.2018
# Copyright (C) 2018, Timothy Hoover

import configparser
import uno
import os
import traceback

from librepy.pybrex.msgbox import msgbox

import logging
logger = logging.getLogger(__name__)


    
class ConfigBase(dict):
    ''' Config base'''
    def __getattr__(self, name):
        if name not in self.keys():
            raise AttributeError
        else:
            return super().__getitem__(name)
        
    def __setattr__(self, name, value):
        super().__setitem__(name, value)
        
    def __delattr__(self, name):
        super().__delitem__(name)
        
    def copy(self):
        return ConfigBase(self.items())
    
#Default config files, more configurations are loaded from the configs directory
    
class MainWindowConfig(ConfigBase):
    _config_group = 'MainWindow'
    _config_attr = 'mw'
    _config_values = [
    ('font_name', str, 'DejaVu Serif'),
    ('pos_x', int, 0),
    ('pos_y', int, 0),
    ('width', int, 700),
    ('height', int, 400),
    ('show_treebar', bool, True),
    ('treebar_width', int, 200),
    ('show_msgtab', bool, True),
    ('msgtab_height', int, 150)]
    
class EditorConfig(ConfigBase):
    _config_group = 'Editor'
    _config_attr = 'ed'
    _config_values = [
    ('indent_type', str, 'SPACE'), #Options are 'TAB' and 'SPACE'
    ('indent_count', int, 4),
    ('font_name', str, 'Dejavu Sans'),
    ('font_size', float, 12.0),
    ('default_scale', int, 100),
    ('show_linenumbers', bool, False)]
    

    
    
class GlobalConfig(object):
    '''Load/read/write global configuration settings'''
    LOADED = False
    BASE_DIR = os.path.join(os.path.split(__file__)[0], 'configs')
    FILETYPE_DIR = os.path.join(BASE_DIR, 'filetypes')
    USER_DIR = os.path.join(BASE_DIR, 'user')
    
    def __init__(self, ctx):
        self.ctx = ctx
        if not GlobalConfig.LOADED:
            self.load()
            GlobalConfig.LOADED = True
            
    def load(self):
        'Load all the configurations files'
        
        #Load user config files
        setattr(GlobalConfig, 'user', ConfigBase())
        self.show = True
        for name in os.listdir(self.USER_DIR):
            if name.endswith('.conf'):
                file_path = os.path.join(self.USER_DIR, name)
                p_name = name.split('.')[0]
                self.load_path(getattr(GlobalConfig, 'user'), p_name, file_path)
        
        #Load file type  config files
        setattr(GlobalConfig, 'filetypes', ConfigBase())
        for name in os.listdir(self.FILETYPE_DIR):
            file_path = os.path.join(self.FILETYPE_DIR, name)
            p_type = name.split('.').pop()
            self.load_path(getattr(GlobalConfig, 'filetypes'), p_type, file_path)
            
        #Set defaults
        set_all_default_configs(GlobalConfig)
            
        #Set old variables for backword compatibility
        defaults = getattr(GlobalConfig, 'user')
        user_d = getattr(defaults, 'librepy')
        setattr(GlobalConfig, 'mw', getattr(user_d, 'mainwindow'))
        setattr(GlobalConfig, 'ed', getattr(user_d, 'editor'))
        
        
    def load_path(self, base_obj, child_name, path):
        'Load a single configuration file'
        config = configparser.ConfigParser(interpolation = None)
        if os.path.exists(path):
            config.read(path)
        else:
            return
            
        setattr(base_obj, child_name, ConfigBase())
        base_cfg = getattr(base_obj, child_name)
        num = 0
        for name, section in config.items():
            setattr(base_cfg, name, ConfigBase())
            sect_cfg = getattr(base_cfg, name)
            for key, value in section.items():
                num += 1
                val = self.get_type(value, section)
                setattr(sect_cfg, key, val)
                
                
    """This seems like an odd way to do this
        but if it ain't broke why fix it. Tim Hoover"""
    def get_type(self, string, parser):
        'Generate a value from string'
        s = string.strip()
        if s == 'true' or s == 'True':
            return True
        elif s == 'false' or s == 'False':
            return False
            
        try:
            val = int(s)
            return val
        except: pass
        
        try:
            val = float(s)
            return val
        except: pass
        
        return string
                
    def write(self):
        '''Write the configuration values to file'''
        logger.debug('Starting config save')
        try:
            defaults = getattr(GlobalConfig, 'user')
            user_d = getattr(defaults, 'librepy')
            path = os.path.join(self.USER_DIR, 'librepy.conf')
            config = configparser.ConfigParser(interpolation = None)
            config.read(path)
            
            #Set current configuration
            for sect_name, sect_section in user_d.items():
                if sect_name == 'DEFAULT':
                    continue
                #logger.debug('Sect = %s:Val = %s' % (sect_name, sect_section))
                #Make sure the section exists
                if not config.has_section(sect_name):
                    config.add_section(sect_name)
                #Set each configuration
                for conf_name, conf_val in sect_section.items():
                    config[sect_name][conf_name] = str(conf_val)
                    
            #Write to file
            with open(path, 'w') as f:
                config.write(f)
                
        except Exception as e:
            msgbox(traceback.format_exc()) 
            logger.error(traceback.format_exc())
            
        logger.debug('Ending config save')
        
    def get_config_path(self, path):
        pst = self.ctx.getServiceManager().createInstanceWithContext(
            "com.sun.star.util.PathSubstitution", self.ctx)
        url = pst.substituteVariables(path, True)
        return uno.fileUrlToSystemPath(url)
    
    def __getattr__(self, name):
        return self.__dict__[name]
    
    def __setattr__(self, name, value):
        self.__dict__[name] = value


