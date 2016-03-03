#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision$
##  $LastChangedBy$
##  $LastChangedDate$
##

# Mail-related stuff
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Parse json table
import json
import sibis

class XnatEmail:
    """ Class handling email communication with XNAT users and admin."""

    # Initialize class.
    def __init__(self, interface ):
        self._interface = interface
        # Determine server config to get admin email and public URL
        server_config = json.loads( self._interface._exec( '/data/services/settings' ) )[u'ResultSet'][u'Result']
        self._admin_email = server_config[u'siteAdminEmail']
        self._site_url = server_config[u'siteUrl']
        self._site_name = server_config[u'siteId']
        self._smtp_server = server_config[u'smtpHost']
        self._messages_by_user = dict()
        self._admin_messages = []

    # Add to the message building up for a specific user
    def add_user_message( self, uname, msg ):
        if uname not in self._messages_by_user:
            self._messages_by_user[uname] = [msg]
        else:
            self._messages_by_user[uname].append( msg )

    # Add to the message building up for the admin
    def add_admin_message( self, msg ):
        self._admin_messages.append( msg )

    # Send pre-formatted mail message
    def send( self, subject, from_email, to_email, html ):
        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = ', '.join( to_email )

        # Record the MIME types of both parts - text/plain and text/html.
        text = ''
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        # Send the message via local SMTP server.
        s = smtplib.SMTP( self._smtp_server )
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        s.sendmail( from_email, to_email, msg.as_string() )
        s.quit()

    # Send mail to one user
    def mail_user( self, uid, msglist ):
        # Get user full name and email address
        try:
            user_firstname = self._interface.manage.users.firstname( uid )
            user_lastname = self._interface.manage.users.lastname( uid )
            user_email = self._interface.manage.users.email( uid )
        except:
            error = "ERROR: failed to get detail information for user"
            sibis.logging(uid,error)
            return

            problem_list = [ '<ol>' ]
            for m in msglist:
                problem_list.append( '<li>%s</li>' % m )
            problem_list.append( '</ol>' )

        # Create the body of the message (a plain-text and an HTML version).
        html = '<html>\n\
<head></head>\n\
<body>\n\
<p>Dear %s %s:<br><br>\n\
We have detected the following problem(s) with data you uploaded to the <a href="%s">%s XNAT image repository</a>:</br>\n\
%s\n\
Please address these issues as soon as possible (direct links to the respective data items are provided above for your convenience).\n\
You may want to consult the <a href="http://www.nitrc.org/docman/view.php/672/1206/N-CANDA%%20MRI%%20and%%20Image%%20Management%%20Manual">N-CANDA MRI and Image Management Manual</a> for instructions.<br></br>\n\
If you have further questions, feel free to contact the <a href="mailto:%s">Site Administrator</a>\n\
</p>\n\
</body>\n\
</html>' % (user_firstname, user_lastname, self._site_url, self._site_name, '\n'.join( problem_list ), self._admin_email)

        self.send( "N-CANDA XNAT: problems with your uploaded data", self._admin_email, [ user_email ], html )

    # Send summary mail to admin
    def mail_admin( self ):
        problem_list = []
        if len( self._messages_by_user ) > 0:
            problem_list.append( '<ul>' )
            for (uname,msglist) in self._messages_by_user.iteritems():
                problem_list.append( '<li>User: %s</li>' % uname )
                problem_list.append( '<ol>' )
                for m in msglist:
                    problem_list.append( '<li>%s</li>' % m )
                problem_list.append( '</ol>' )
            problem_list.append( '</ul>' )

        if len( self._admin_messages ) > 0:
            problem_list.append( '<ol>' )
            for m in self._admin_messages:
                problem_list.append( '<li>%s</li>' % m )
            problem_list.append( '</ol>' )

        text = ''

        # Create the body of the message (a plain-text and an HTML version).
        html = '<html>\n\
<head></head>\n\
<body>\n\
We have detected the following problem(s) with data on <a href="%s">N-CANDA XNAT image repository</a>:</br>\n\
%s\n\
</p>\n\
</body>\n\
</html>' % (self._site_url, '\n'.join( problem_list ))

        self.send( "%s XNAT problem update" % self._site_name, self._admin_email, [ self._admin_email ], html )

    def send_all( self ):
        # Run through list of messages by user
        if len( self._messages_by_user ):
            for (uname,msglist) in self._messages_by_user.iteritems():
                self.mail_user( uname, msglist )

        if len( self._messages_by_user ) or len( self._admin_messages ):
            self.mail_admin

    def dump_all( self ):
        print "USER MESSAGES:"
        print self._messages_by_user
        print "ADMIN_MESSAGES:"
        print self._admin_messages
