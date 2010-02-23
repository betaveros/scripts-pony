# -*- coding: utf-8 -*-
"""Models relating to tracking information on .mit.edu hostname requests."""

from sqlalchemy import *
from elixir import (ManyToOne, Entity, Field, OneToMany,
                    using_options, using_table_options,
                    ManyToMany, setup_all,
                    drop_all, create_all, session)
import datetime

from .. import auth,log

def tname(typ):
    return typ.__name__.lower()

class Ticket(Entity):
    using_options(tablename=tname)
    using_table_options(mysql_engine='InnoDB',mysql_charset='utf8')

    # Athena username
    requestor = Field(Unicode(255), index=True)
    # Locker name
    locker = Field(Unicode(255), index=True)
    # Hostname involved
    hostname = Field(Unicode(255), index=True)
    # path
    path = Field(Unicode(255))
    # "open" or "moira" or "dns" or "resolved"
    state = Field(Unicode(32))
    
    events = OneToMany('Event')

    @staticmethod
    def create(locker,hostname,path):
        t = Ticket(requestor=auth.current_user(),
                   hostname=hostname,locker=locker,path=path,
                   state="open")
        session.flush()
        t.addEvent(type='request',state="open",target='us')
    
    def addEvent(self,type,state,by=None,target=None,subject=None,body=None):
        if by is None:
            by = auth.current_user()
        Event(ticket=self,type=type,target=target,subject=subject,body=body)
        log.zwrite("%s's %s changed the ticket re: %s to %s"
                   % (by,type,self.hostname,state),
                   id=self.id)

class Event(Entity):
    using_options(tablename=tname)
    using_table_options(mysql_engine='InnoDB',mysql_charset='utf8')

    ticket = ManyToOne('Ticket',required=True)
    # 'mail' or 'dns' or 'request'
    type = Field(Unicode(32))
    # 'jweiss' or 'us' or 'user'
    target = Field(Unicode(32))
    by = Field(Unicode(255))
    timestamp = Field(DateTime, default=datetime.datetime.now)
    subject = Field(UnicodeText())
    body = Field(UnicodeText())

setup_all()
