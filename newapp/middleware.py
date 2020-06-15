# -*- coding: utf-8 -*-
from newapp.models import DefaultBannerImage
"""
Created on Mon Jun 15 10:01:23 2020

@author: admin
Our context processor.
"""


def default_banner(request):
    ''' It will have pushed default image banner to context '''
    banner = DefaultBannerImage.objects.first()
    # raise Exception(str(banner.image))
    return {'default_banner': banner.image}


