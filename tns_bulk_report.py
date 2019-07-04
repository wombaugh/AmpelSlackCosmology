#!/usr/bin/env python
# -----------------------------------------------------------------------------
# A python sample code for sending a bulk report to the TNS.
#
# Original sample code by Ken Smith (May 2016) modified by Jakob Nordin (Feb 2018)
# -----------------------------------------------------------------------------

# The only required additional python module for this code is "requests" (pip install requests).
import requests
import json
import logging
import time
from collections import OrderedDict

AT_REPORT_FORM = "bulk-report"
AT_REPORT_REPLY = "bulk-report-reply"
TNS_ARCHIVE = {'OTHER': '0', 'SDSS': '1', 'DSS': '2'}
TNS_BASE_URL_SANDBOX = "https://sandbox-tns.weizmann.ac.il/api/"
TNS_BASE_URL_REAL    = "https://wis-tns.weizmann.ac.il/api/"

httpErrors = {
    304: 'Error 304: Not Modified: There was no new data to return.',
    400: 'Error 400: Bad Request: The request was invalid. An accompanying error message will explain why.',
    403: 'Error 403: Forbidden: The request is understood, but it has been refused. An accompanying error message will explain why',
    404: 'Error 404: Not Found: The URI requested is invalid or the resource requested, such as a category, does not exists.',
    500: 'Error 500: Internal Server Error: Something is broken.',
    503: 'Error 503: Service Unavailable.'
}



class TNSClient(object):
    """Send Bulk TNS Request."""

    def __init__(self, logger, sandbox, options = {}):
        """
        Constructor. 

        :param baseURL: Base URL of the TNS API
        :param options:  (Default value = {})

        """

        if sandbox:
            self.baseAPIUrl = TNS_BASE_URL_SANDBOX
        else:
            self.baseAPIUrl = TNS_BASE_URL_REAL
            
        self.generalOptions = options
        self.logger = logger

    def buildUrl(self, resource):
        """
        Build the full URL

        :param resource: the resource requested
        :return complete URL

        """
        return self.baseAPIUrl + resource

    def buildParameters(self, parameters = {}):
        """
        Merge the input parameters with the default parameters created when
        the class is constructed.

        :param parameters: input dict  (Default value = {})
        :return p: merged dict

        """
        p = self.generalOptions.copy()
        p.update(parameters)
        return p

    def jsonResponse(self, r):
        """
        Send JSON response given requests object. Should be a python dict.

        :param r: requests object - the response we got back from the server
        :return d: json response converted to python dict

        """

        d = {}
        # What response did we get?
        message = None
        status = r.status_code

        if status != 200:
            try:
                message = httpErrors[status]
            except ValueError as e:
                message = 'Error %d: Undocumented error' % status

        if message is not None:
            self.logger.warn('TNS bulk submit: '+ message)
            return d
        
        # Did we get a JSON object?
        try:
            d = r.json()
        except ValueError as e:
            self.logger.error('TNS bulk submit: '+ e)
            d = {}
            return d


        # If so, what error messages if any did we get?
        #self.logger.info(json.dumps(d, indent=4, sort_keys=True))

        if 'id_code' in d.keys() and 'id_message' in d.keys() and d['id_code'] != 200:
            self.logger.error("'TNS bulk submit: '+ Bad response: code = %d, error = '%s'" % (d['id_code'], d['id_message']))
        return d



    def checkTNS(self, ra,dec,searchradius=5):
        """
        Find out whether a TNS report has been filed for a given position and search radius.
        """

        
        # change json_list to json format
        search_obj=[("ra",ra), ("dec",dec), ("radius",searchradius), ("units","arcsec"),
            ("objname",""), ("internal_name","")]                    
        json_file=OrderedDict(search_obj)
   
        # construct the list of (key,value) pairs                        
        search_data=[('api_key',(None, self.generalOptions["api_key"] )),                        
                    ('data',(None,json.dumps(json_file)))]
    
        try:
            # search obj using request module                                
            r=requests.post(self.buildUrl("get/search"), files=search_data)            
            rinterp = self.jsonResponse(r)
            
            if rinterp["id_message"]=="OK":
                
                if len(rinterp['data']['reply'])==0:
                    # Not in TNS
                    return [False, None]
                elif len(rinterp['data']['reply'])==1:                
                    return [True, rinterp['data']['reply'][0]['prefix']+rinterp['data']['reply'][0]['objname']]
                else:
                    return [None, "Cannot understand reply %s"%(json.dumps(rinterp, indent=4, sort_keys=True)) ] 
            else:
                return [False, None]
        except Exception as e:                                             
            return [None,'Error message : \n'+str(e)]    

    

    def sendBulkReport(self, options):
        """
        Send the JSON TNS request

        :param options: the JSON TNS request
        :return: dict

        """
        feed_url = self.buildUrl(AT_REPORT_FORM);
        feed_parameters = self.buildParameters({'data': (None, json.dumps(options))});
        
        # The requests.post method needs to receive a "files" entry, not "data".  And the "files"
        # entry needs to be a dictionary of tuples.  The first value of the tuple is None.
        self.logger.info('TNS bulk submit: '+ 'sending request')
        r = requests.post(feed_url, files = feed_parameters, timeout = 300)
        # Construct the JSON response and return it.
        self.logger.info('TNS bulk submit: '+ 'got response (or timed out)')
        return self.jsonResponse(r)

    def bulkReportReply(self, options):
        """
        Get the report back from the TNS

        :param options: dict containing the report ID
        :return: dict

        """
        feed_url = self.buildUrl(AT_REPORT_REPLY);
        feed_parameters = self.buildParameters(options);

        self.logger.info('TNS bulk submit: '+ 'looking for reply report')
        r = requests.post(feed_url, files = feed_parameters, timeout = 300)
        self.logger.info('TNS bulk submit: '+ 'got report (or timed out)')
        return self.jsonResponse(r)


def addBulkReport(report, tnsApiKey, logger, sandbox=True):
    """
    Send the report to the TNS

    :param report: 
    :param tnsBaseURL: TNS base URL
    :param tnsApiKey: TNS API Key
    :param sandbox: Submits to TNS sandbox area if true
    :return reportId: TNS report ID

    """


    
    feed_handler = TNSClient(logger, True, {'api_key': (None, tnsApiKey)})
    reply = feed_handler.sendBulkReport(report)

    reportId = None

    if reply:
        try:
            reportId = reply['data']['report_id']
            logger.info('TNS bulk submit: '+ 'successful with ID %s'%(reportId))
        except ValueError as e:
            logger.error("Empty response. Something went wrong.  Is the API Key OK?")
        except KeyError as e:
            logger.error("Cannot find the data key. Something is wrong.")

    return reportId


def getBulkReportReply(reportId, tnsApiKey, logger, sandbox=True):
    """
    Get the TNS response for the specified report ID

    :param reportId: 
    :param tnsApiKey: TNS API Key
    :return request: The original request
    :return response: The TNS response

    """

    feed_handler = TNSClient(logger, True, {'api_key': (None, tnsApiKey)})
    reply = feed_handler.bulkReportReply({'report_id': (None, str(reportId))})

    
    request = None
    response = None
    # reply should be a dict
    if (reply and 'id_code' in reply.keys() and reply['id_code'] == 404):
        logger.warn("TNS bulk submit %s:Unknown report.  Perhaps the report has not yet been processed."%(reportId))

    if (reply and 'id_code' in reply.keys() and reply['id_code'] == 200):
        try:
            response = reply['data']['feedback']['at_report']
        except ValueError as e:
            logger.error('TNS bulk submit: '+ "Cannot find the response feedback payload.")
    logger.info('TNS bulk submit: '+ 'got response %s for request %s'%(response, request))

    return response




def sendZTF_AT(internalid, nondetection_date, nondetection_limit, ra, dec, obsdates, fluxs, dfluxs, maglim, filterid, logger, apikey):
    '''
    Transmit and wait for response for sending an AT to TNS.

    internalid : the interal ZTF name
    nondetection_date, nondetection_limit : the date and mag limit for the latest visit prior to detection. Set to None if not known.
    ra, dec : position
    obsdates, fluxs, dfluxs, maglim, filterid : lists of LC values of detections which will be transmitted
    logger : logging instance

    This method only sends a single alert. If possible, use a version of this
    for sending bulk (up to 100) reports.

    '''
    # Instrument/survey values
    ztf_tns = {"flux_units":"1", "instrument_value":"196","exptime":"30","Observer":"Robot"}

    # Have to tie to TNS filter numbering
    # ZTFg 110 ZTFr 111 ZTFi 112
    tnsfilterid = {1:"110",2:"111",3:"112"}
    print("warning- confirm filter")
    MAX_LOOP = 10
    REPLY_SLEEP = 1

    # Start defining AT dict
    atdict = {"groupid":"48", "reporter":"ZTF MSIP submitted by AMPEL", "at_type":"1"}
    atdict["internal_name"] = internalid
    atdict["ra"] = {"value": ra, "error" : "2", "units":"arcsec"}
    atdict["dec"] = {"value": dec, "error" : "2", "units":"arcsec"}
    
    # Use archival for now for now, presumably we will get non-detection
    if nondetection_date:
        atdict["non_detection"] = {"obsdate":nondetection_date, "limiting_flux":nondetection_limit}
    else:
        atdict["non_detection"] = {"archiveid":"0", "archival_remarks":"Non-detection limits not available w/o active survey"}
    atdict["non_detection"].update(ztf_tns)  # Add the default ZTF values


    # Now we must loop through photometry
    atdict["photometry"] = {"photometry_group":{}}
    atdict["discovery_datetime"] = 10**30
    for photid, (d, f, df, flim, filt) in enumerate(zip(obsdates, fluxs, dfluxs, maglim, filterid)):
        photdict = {"obsdate":d,
                    "flux":"f",
                   "flux_error":"df",
                   "limiting_flux":"flim",
                   "filter_value":tnsfilterid[filt]
        }
        photdict.update(ztf_tns)
        atdict["photometry"]["photometry_group"][photid] = photdict
        if( d<atdict["discovery_datetime"] ):
            atdict["discovery_datetime"] = d



    # Have our report - submit
    logger.info("Submitting transient ID %s w. report %s to TNS"%(internalid,atdict))
    reportid = addBulkReport({"at_report":{"0":atdict}}, apikey, logger)
    if reportid:
        print('TNS report ID %s'%(reportid) )
    else:
        print('Send failure - why? Try again?')
        logger.warning("TNS send failure")
    
    
    # Try to read reply
    counter = 0
    while True:
        time.sleep(REPLY_SLEEP)
        response = getBulkReportReply(reportid, apikey, logger)
        counter += 1
        if (response and 'id_code' in response.keys() and response['id_code'] != 404) or counter >= MAX_LOOP:
            break
    print(response)
    
    print("This is where we should go back and update the DB.")
    
    
# Note that the following code uses the low level API rather than the two
# wrapper methods written above. It is designed to look as close to the PHP
# code as possible.

def main(argv = None):
    """
    Test harness.  Check that the code works as designed.

    :param argv:  (Default value = None)

    """

    import sys

    if argv is None:
        argv = sys.argv

    usage = "Usage: %s <api key> <example json file>" % argv[0]
    if len(argv) != 3:
        sys.exit(usage)

    apiKey = argv[1]
    exampleJsonFile = argv[2]

    with open(exampleJsonFile) as jsonFile:
        at_rep_example = json.load(jsonFile)

    TNS_BASE_URL_SANDBOX = "https://sandbox-tns.weizmann.ac.il/api/"
    TNS_BASE_URL_REAL    = "https://wis-tns.weizmann.ac.il/api/"

    SLEEP_SEC = 1
    LOOP_COUNTER = 10

    feed_handler = TNSClient(TNS_BASE_URL_SANDBOX, {'api_key': (None, apiKey)})
    js = at_rep_example
    logger.debug('EXAMPLE BULK AT REPORT')
    logger.debug(json.dumps(js, indent=4, sort_keys=True))
    response = feed_handler.sendBulkReport(js)
    if response:
        try:
            report_id = response['data']['report_id']
        except ValueError as e:
            logger.error("Empty response. Something went wrong.  Is the API Key OK?")
    else:
        # We got no valid JSON back
        logger.error("Empty response. Something went wrong.  Is the API Key OK?")
        return 1

    report_id = response['data']['report_id']
    logger.info("REPORT ID = %s" % report_id)

    counter = 0
    while True:
        time.sleep(SLEEP_SEC)
        response = feed_handler.bulkReportReply({'report_id': (None, str(report_id))})
        counter += 1
        if (response and 'id_code' in response.keys() and response['id_code'] != 404) or counter >= LOOP_COUNTER:
            break

    logger.info("Done")
    return 0


if __name__ == '__main__':
    main()
