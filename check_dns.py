#!/usr/bin/python

import site,os.path
site.addsitedir(os.path.dirname(__file__))

import urllib2

import transaction

from scriptspony.model import queue
from scriptspony import util,keytab,mail,log,auth,vhosts

@log.exceptions
def check_dns():
    if keytab.exists():
        keytab.auth()

    for t in queue.Ticket.query.filter_by(state=u'dns'):

        if util.points_at_scripts(t.hostname):
            path = '/mit/%s/web_scripts/%s' % (t.locker,
                                               vhosts.get_path(t.locker,t.hostname))
            
            # Try to figure out what's up with the hostname currently
            try:
                page = urllib2.urlopen('http://%s/'%t.hostname)
                content = page.read()
                if '<meta name="generator" content="WordPress' in content:
                    sitestatus = "This site looks like a WordPress blog; for the new URL to work properly, you'll need to access the WordPress admin interface via your old URL, go to General Settings, and change the WordPress address and Blog address to 'http://%s'." % hostname
                else:
                    sitestatus = "Your site appears to be working properly."
            except urllib2.HTTPError,e:
                if e.code == 404:
                    sitestatus = "There doesn't seem to be any content currently at %s; make sure that directory exists and has an index.html, index.cgi, or similar, or change this hostname to point somewhere else at http://pony.scripts.mit.edu." % path
                elif e.code == 403:
                    sitestatus = "Visiting that page yields a Forbidden error; this is often caused by a lack of valid content at %s.  Putting an index.html, index.cgi, or similar there may solve this." % path
                else:
                    sitestatus = "Visiting that page yields a %s error, suggesting a problem with the content at %s.  Email us at scripts@mit.edu if you need help resolving this." % (e.code, path)
        
            subject = u"Hostname %s now working"%t.hostname
            body = u"""Hello,

Just wanted to let you know that the hostname %(hostname)s is now configured and working.  It currently points to %(path)s.

%(sitestatus)s

Let us know if you run into any issues.

~The SIPB Scripts Team
http://scripts.mit.edu/

/set status=resolved
""" % dict(hostname=t.hostname,locker=t.locker,path=path,sitestatus=sitestatus)
            mail.send_correspondence(subject,body,t.id,rtid=t.rtid)        
            t.addEvent(type=u'mail',state=u'resolved',by=u'dns',
                       target=u'user',
                       subject=subject,
                       body=body)

    transaction.commit()

if __name__ == '__main__':
    auth.set_user_from_parent_process()
    from paste.deploy import loadapp
    loadapp('config:development.ini',
            relative_to=os.path.dirname(__file__))
    check_dns()