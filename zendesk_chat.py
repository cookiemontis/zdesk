from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from time import mktime
from datetime import datetime, timedelta
from urllib import urlencode
import json
import requests
import re
import socket
import pytz as tz
import sys
from zdesk import Zendesk
from . import defs
reload(sys)
sys.setdefaultencoding('utf8')


def mk_timestamp(dt):
    return (int)(mktime(dt.timetuple()))


def gslog(ts, mark, data):
    with open("/var/log/django/whmcs_chat.log", "a") as myfile:
        myfile.write("[{t}] {ts} | {m}\n".format(t=str(now()), ts=ts, m=mark))
        if data:
            myfile.write("{d}\n\n".format(d=json.dumps(data, indent=2)))
        myfile.flush()


#Convert Zendesk Chat Transcript and Create Ticket in WHMCS
@csrf_exempt
def vWHMCSchat(request):
    if request.method == 'GET':
        return JsonResponse({"service":"ZenDesk triggers entry point","status":"ok"})
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "bad method"})
    try:
        data = json.loads(request.body, strict=False)
        tid = int(data['id'])
    except:
        return JsonResponse({"status": "error", "message": "bad input"})

    if data.get('trigger') != "whmcs_chat":
        return JsonResponse({"status": "error", "message": "missed trigger"})

    ts = mk_timestamp(now())

    system = data.get('system', 'sandbox')
    if system not in defs.ZDC:
        system = 'sandbox' ##will be updated to prod

    gslog(ts, "INFO: Zen-> Webhook received from {s} for {k}".format(s=system.upper(),k=tid), data)
    zdo = Zendesk(**defs.ZDC[system]['ZDC']) ##Set Zendesk credentials

    try:
        ta = zdo.ticket_audits(ticket_id=tid)
        gslog(ts, ("INFO: Zen-> zdo.ticket_audits({})".format(tid)), {})
    except Exception, err:
        gslog(ts, "ERROR: Zen-> failed to get ticket {k} audit".format(k=tid), {})
        gslog(ts, "DBG: {e} :: {msg}".format(e=Exception, msg=err), {})
        return JsonResponse({"status": "error"})

    if ta['audits'][0]['events'][0]['type'] == 'ChatStartedEvent':
        try:
           tad = ta['audits'][0]['events'][0]['value']['history']
        except Exception as e:
           gslog(ts, "ERROR: Zen-> Ticket {k} missing chat history".format(k=tid), {})
           return JsonResponse({"status": "error"})
    else:
        gslog(ts, "ERROR: Zen-> Ticket {k} incorrect type ChatStartedEvent missing".format(k=tid), {})
        return JsonResponse({"status": "error"})

    try:
        td = zdo.ticket_show(tid)
        gslog(ts, ("INFO: Zen-> zdo.ticket_show({})".format(tid)), {})
    except Exception, err:
        gslog(ts, "ERROR: Zen-> failed to get ticket {k} data".format(k=tid), {})
        gslog(ts, "DBG: {e} :: {msg}".format(e=Exception, msg=err), {})
        return JsonResponse({"status": "error"})
    uid = td['ticket']['requester_id']
    subject = td['ticket']['subject']
    brand = td['ticket']['brand_id']
    group = td['ticket']['group_id']

    try:
        user = zdo.user_show(uid)
        gslog(ts, ("INFO: Zen-> zdo.user_show({})".format(uid)), {})
    except Exception as e:
        gslog(ts, "ERROR: Zen-> failed to get user data for {k}".format(k=uid), {})
        return JsonResponse({"status": "error"})
    email = user['user']['email']
    name = user['user']['name']

    chatTranscript = []

    for event in tad:
        chatTimestamp = str(datetime.fromtimestamp(event['timestamp']/1000))
        chatActor = event['actor_name']
        chatAgent = event['actor_type']
        chatAction = event['type']

        try:
            if 'message' in event:
                chatMsg = event['message']
            else:
                chatMsg = ""
        except:
            chatMsg = ""

        chatLine = chatTimestamp + ' ' + chatAgent + ' ' + chatActor + ' ' + chatAction + ' ' + chatMsg
        chatTranscript.append(chatLine)

    chatTranscript = '\n'.join(chatTranscript)

    whmcso = (defs.WHMCSC[system]['WHMCSC'])
    if defs.WHMCSC[system].get('groups'):
        zdgid = defs.WHMCSC[system].get('groups')
        for gid in zdgid:
            if gid == str(group):
                whmcso.update({'deptid': zdgid[gid]})

    whmcsConn = dict(filter(lambda item: item[0] != 'apiurl', whmcso.items()))
    whmcsParams = {
        'name': name,
        'email': email,
        'subject': subject,
        'message': chatTranscript,
        'responsetype': 'json'
    }
    whmcsPostUrl = whmcso['apiurl'] + urlencode(whmcsConn) + '&' + urlencode(whmcsParams)

    try:
        whmcsResponse = requests.post(whmcsPostUrl)
        gslog(ts, "INFO: Zen->WHMCS Chat Sync attempt being sent for {k}".format(k=tid), {})
        whmcsResponse.raise_for_status()
        gslog(ts, "INFO: Zen->WHMCS Chat Sync Successful for {k}".format(k=tid),whmcsResponse.json())
        return JsonResponse({"status": "ok","ticket_id": whmcsResponse.json()['tid']})
    except requests.exceptions.HTTPError as errh:
        gslog(ts, "ERROR: Zen->WHMCS Chat Sync failed for {k}".format(k=tid), {})
        gslog(ts, "DBG: HTTP ERROR {s} {r}".format(s=whmcsResponse.status_code,r=whmcsResponse.reason), {})
        return JsonResponse({"status": "error"})
    except requests.exceptions.RequestException as err:
        gslog(ts, "ERROR: Zen->WHMCS Chat Sync failed for {k}".format(k=tid), {})
        gslog(ts, "DBG: HTTP ERROR\n", err)
        return JsonResponse({"status": "error"})
