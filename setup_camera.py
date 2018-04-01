#!/usr/bin/env python3
import time

import requests
from lxml import etree
from yarl import URL


def set_parameter(parameter_name, parameter_value):
    page = etree.Element('set')
    page_element = etree.SubElement(page, 'value')
    page_element.text = parameter_value
    xml_data = etree.tostring(page, pretty_print=True, encoding=None).decode()
    parameters = {
        'com':  'set',
        'name': parameter_name
    }
    headers = {
        'Host':         '192.168.0.10',
        'User-Agent':   'OI.Share v2',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post('http://192.168.0.10/set_camprop.cgi', headers=headers, params=parameters, data=xml_data)
    print(response.status_code)
    print(response.text)


def take_and_get_photo():
    BaseParameters().set_mode()
    headers = BaseParameters.headers
    take_misc_url = BaseParameters.camera_url.with_path('/exec_takemisc.cgi')
    take_motion_url = BaseParameters.camera_url.with_path('/exec_takemotion.cgi')
    live_view_query = [('com', 'startliveview'), ('port', '12345')]
    autofocus_query = [('com', 'assignafframe'), ('point', '0160x0120')]
    autofocus_release_query = [('com', 'releaseafframe')]
    take_photo_query = [('com', 'starttake')]
    get_photo_query = [('com', 'getlastjpg')]
    requests.get(take_misc_url, headers=headers, params=live_view_query).raise_for_status()
    time.sleep(0.5)
    response = requests.get(take_motion_url, headers=headers, params=autofocus_query)
    response.raise_for_status()
    if etree.fromstring(response.content).xpath('affocus')[0].text == 'ng':
        raise RuntimeError('Autofocus failed!')
    time.sleep(0.5)
    response = requests.get(take_motion_url, headers=headers, params=take_photo_query)
    response.raise_for_status()
    if etree.fromstring(response.content).xpath('take')[0].text == 'ng':
        raise RuntimeError('Camera refuses to take a photo!')
    requests.get(take_motion_url, headers=headers, params=autofocus_release_query).raise_for_status()
    time.sleep(1)
    response = requests.get(take_misc_url, headers=headers, params=get_photo_query)
    response.raise_for_status()
    return response.content


class ClassProperty(object):

    def __get__(self, instance, clazz):
        return clazz


class BaseParameters(object):
    _name = ClassProperty()
    camera_url = URL('http://192.168.0.10/')
    allowed_values = []
    headers = {'User-Agent': 'OI.Share v2'}

    @property
    def name(self):
        return self._name.__name__.lower()

    def set_mode(self, **kwargs):
        query = [('mode', 'rec'), ('lvqty', '0320x0240')]
        if len(kwargs) > 0:
            query = [(key, kwargs[key]) for key in kwargs]
        url = self.camera_url.with_path('/switch_cammode.cgi')
        response = requests.get(url, headers=self.headers, params=query)
        response.raise_for_status()
        time.sleep(1)

    @property
    def value(self):
        self.set_mode()
        query = [('com', 'get'), ('name', self.name)]
        url = self.camera_url.with_path('/get_camprop.cgi')
        response = requests.get(url, headers=self.headers, params=query)
        response.raise_for_status()
        if response.status_code == 200:
            return etree.fromstring(response.content).xpath('value')[0].text

    @value.setter
    def value(self, value):
        self.set_mode()
        if value not in self.allowed_values:
            raise ValueError(
                    'Value {} was invalid. The following values are valid: \n{}'.format(value,
                                                                                        ', '.join(self.allowed_values)))
        self.set_mode()
        page = etree.Element('set')
        page_element = etree.SubElement(page, 'value')
        page_element.text = value
        xml_data = etree.tostring(page, pretty_print=True, encoding=None).decode()
        print(xml_data)
        query = [('com', 'set'), ('name', self.name)]
        headers = {'Content-Type': 'application/x-www-form-urlencoded', **self.headers}
        url = self.camera_url.with_path('/set_camprop.cgi')
        print(url.with_query(query))
        response = requests.post(url, headers=headers, params=query, data=xml_data)
        response.raise_for_status()


class TakeMode(BaseParameters):
    allowed_values = ['iAuto', 'P', 'A', 'S', 'M', 'ART', 'movie']


class DriveMode(BaseParameters):
    allowed_values = ['normal', 'lowvib-normal', 'silent-normal', 'continuous-H', 'silent-continuous-H', 'continuous-L',
                      'lowvib-continuous-L', 'silent-continuous-L', 'selftimer', 'lowvib-selftimer', 'silent-selftimer',
                      'customselftimer', 'lowvib-customselftimer', 'silent-customselftimer']


class FocalValue(BaseParameters):
    allowed_values = ['1.0', '1.1', '1.2', '1.4', '1.6', '1.8', '2.0', '2.2', '2.5', '2.8', '3.2', '3.5', '4.0', '4.5',
                      '5.0',
                      '5.6', '6.3', '7.1', '8.0', '9.0', '10', '11', '13', '14', '16', '18', '20', '22', '25', '29',
                      '32', '36',
                      '40', '45', '51', '57', '64', '72', '81', '91']


class ExposeCompensation(BaseParameters):
    name = 'expcomp'
    allowed_values = ['-5.0', '-4.7', '-4.3', '-4.0', '-3.7', '-3.3', '-3.0', '-2.7', '-2.3', '-2.0', '-1.7', '-1.3',
                      '-1.0',
                      '-0.7', '-0.3', '0.0', '+0.3', '+0.7', '+1.0', '+1.3', '+1.7', '+2.0', '+2.3', '+2.7', '+3.0',
                      '+3.3',
                      '+3.7', '+4.0', '+4.3', '+4.7', '+5.0']


class ShutterSpeed(BaseParameters):
    name = 'shutspeedvalue'
    allowed_values = ['livecomp', 'livetime', 'livebulb', '60"', '50"', '40"', '30"', '25"', '20"', '15"', '13"', '10"',
                      '8"', '6"', '5"', '4"', '3.2"', '2.5"', '2"', '1.6"', '1.3"', '1"', '1.3', '1.6', '2', '2.5', '3',
                      '4', '5', '6', '8', '10', '13', '15', '20', '25', '30', '40', '50', '60', '80', '100', '125',
                      '160',
                      '200', '250', '320', '400', '500', '640', '800', '1000', '1250', '1600', '2000', '2500', '3200',
                      '4000', '5000', '6400', '8000']


class ISOSpeed(BaseParameters):
    name = 'isospeedvalue'
    allowed_values = ['Auto', 'Low', '200', '250', '320', '400', '500', '640', '800', '1000', '1250', '1600', '2000',
                      '2500',
                      '3200', '4000', '5000', '6400', '8000', '10000', '12800', '16000', '20000', '25600']


class WhiteBalanceValue(BaseParameters):
    allowed_values = ['0', '18', '16', '17', '20', '35', '64', '23', '256', '257', '258', '259', '512']


class ArtFilter(BaseParameters):
    allowed_values = ['popart', 'fantasic_focus', 'daydream', 'light_tone', 'rough_monochrome', 'toy_photo',
                      'miniature',
                      'cross_process', 'gentle_sepia', 'dramatic_tone', 'ligne_clair', 'pastel', 'vintage', 'partcolor',
                      'program']


class ColorTone(BaseParameters):
    allowed_values = ['ifinish', 'vivid', 'natural', 'flat', 'portrait', 'monotone', 'custom', 'eportrait',
                      'underwater',
                      'colorcreator', 'popart', 'fantasic_focus', 'daydream', 'light_tone', 'rough_monochrome',
                      'toy_photo',
                      'miniature', 'cross_process', 'gentle_sepia', 'dramatic_tone', 'ligne_clair', 'pastel', 'vintage',
                      'partcolor']


class MovieExposure(BaseParameters):
    allowed_values = ['P', 'A', 'S', 'M']


class ColorPhase(BaseParameters):
    allowed_values = ['step0', 'step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7', 'step8', 'step9',
                      'step10',
                      'step11', 'step12', 'step13', 'step14', 'step15', 'step16', 'step17']
